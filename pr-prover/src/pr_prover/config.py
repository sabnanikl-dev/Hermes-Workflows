"""Strict run configuration.

One JSON file names the PR, the clone to borrow objects from, where the local
state/lock live, and the argv templates for baseline gates, the two reviewer
lanes, and the builder lane. Unknown keys are rejected: a typo that silently
disables a gate is exactly the kind of quiet drift this loop must not have.

Placeholders available to every template::

    {repo} {owner} {name} {pr} {branch} {base} {head} {worktree}

Reviewer templates also get ``{reviewer}``; builder templates also get
``{attempt}``, ``{mode}`` (``initial`` or ``corrective``), and
``{blockers_file}`` — a path under the OS temp directory, never inside a repo.

``builder.comment_author`` is required: the fix-comment readback is only worth
anything if the expected commenter is pinned, so there is no "any author will
do" configuration to fall into.
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .commands import validate_argv
from .errors import ConfigError

SCHEMA_VERSION = 1
GATE_KINDS = ("baseline", "visual")
_REPO = re.compile(r"\A[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\Z")
_NAME = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9 ._-]{0,39}\Z")
# A GitHub login: alphanumerics and single hyphens, 39 characters at most, with
# the "[bot]" suffix apps carry. Matched exactly, so no near-login gets through.
_LOGIN = re.compile(r"\A[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}(?:\[bot\])?\Z")

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "repo",
        "pr",
        "branch",
        "base",
        "source_repo",
        "worktree_root",
        "state_file",
        "lock_file",
        "visual_qa_required",
        "gates",
        "reviewers",
        "builder",
    }
)
_GATE_KEYS = frozenset({"name", "argv", "kind", "timeout"})
_REVIEWER_KEYS = frozenset({"name", "argv", "timeout"})
_BUILDER_KEYS = frozenset({"argv", "signature", "comment_author", "timeout"})


@dataclass(frozen=True)
class GateConfig:
    """One baseline gate, or one browser/visual QA gate."""

    name: str
    argv: tuple[str, ...]
    kind: str = "baseline"
    timeout: float | None = None


@dataclass(frozen=True)
class ReviewerConfig:
    """One exact-head reviewer lane."""

    name: str
    argv: tuple[str, ...]
    timeout: float | None = None


@dataclass(frozen=True)
class BuilderConfig:
    """The fix lane, plus who its PR comment must come from and what it must say.

    ``comment_author`` is required, not optional. The signature and the head SHA
    are both public the moment the builder comments, so on their own they prove
    only that somebody read the PR. The expected login is the part an arbitrary
    commenter cannot supply.
    """

    argv: tuple[str, ...]
    signature: str
    comment_author: str
    timeout: float | None = None


@dataclass(frozen=True)
class RunConfig:
    """Everything one ``pr-prover run`` needs."""

    repo: str
    pr: int
    source_repo: Path
    worktree_root: Path
    state_file: Path
    lock_file: Path
    builder: BuilderConfig
    reviewers: tuple[ReviewerConfig, ...]
    gates: tuple[GateConfig, ...] = ()
    branch: str | None = None
    base: str | None = None
    visual_qa_required: bool = False
    source: Path | None = field(default=None, compare=False)

    @property
    def owner(self) -> str:
        return self.repo.split("/", 1)[0]

    @property
    def name(self) -> str:
        return self.repo.split("/", 1)[1]

    @property
    def baseline_gates(self) -> tuple[GateConfig, ...]:
        return tuple(gate for gate in self.gates if gate.kind == "baseline")

    @property
    def visual_gates(self) -> tuple[GateConfig, ...]:
        return tuple(gate for gate in self.gates if gate.kind == "visual")

    @classmethod
    def load(cls, path: Path) -> RunConfig:
        path = Path(path).expanduser().resolve()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ConfigError(f"config file is unreadable: {exc}", evidence={"config": str(path)}) from exc
        except json.JSONDecodeError as exc:
            raise ConfigError(f"config file is not valid JSON: {exc}", evidence={"config": str(path)}) from exc
        return cls.from_mapping(raw, base_dir=path.parent, source=path)

    @classmethod
    def from_mapping(
        cls, raw: object, *, base_dir: Path | None = None, source: Path | None = None
    ) -> RunConfig:
        if not isinstance(raw, Mapping):
            raise ConfigError("config must be a JSON object")
        unknown = sorted(set(raw) - _TOP_LEVEL_KEYS)
        if unknown:
            raise ConfigError("config has unknown keys", evidence={"unknown_keys": unknown})
        if raw.get("schema_version") != SCHEMA_VERSION:
            raise ConfigError(
                "config schema_version is not supported",
                evidence={"found": raw.get("schema_version"), "expected": SCHEMA_VERSION},
            )

        repo = raw.get("repo")
        if not isinstance(repo, str) or not _REPO.match(repo):
            raise ConfigError("config repo must be 'owner/name'", evidence={"repo": repo})
        pr = raw.get("pr")
        if not isinstance(pr, int) or isinstance(pr, bool) or pr < 1:
            raise ConfigError("config pr must be a positive integer", evidence={"pr": pr})

        root = Path(base_dir).resolve() if base_dir is not None else Path.cwd()

        def resolve(key: str) -> Path:
            value = raw.get(key)
            if not isinstance(value, str) or not value:
                raise ConfigError(f"config {key} must be a non-empty path", evidence={"key": key})
            candidate = Path(value).expanduser()
            return candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()

        visual_required = raw.get("visual_qa_required", False)
        if not isinstance(visual_required, bool):
            raise ConfigError(
                "config visual_qa_required must be a boolean",
                evidence={"visual_qa_required": visual_required},
            )

        gates = tuple(_gate(item, index) for index, item in enumerate(_sequence(raw, "gates", required=False)))
        _reject_duplicates([gate.name for gate in gates], what="gate")
        reviewers = tuple(
            _reviewer(item, index) for index, item in enumerate(_sequence(raw, "reviewers", required=True))
        )
        if len(reviewers) < 2:
            raise ConfigError(
                "config must define two independent reviewer lanes",
                evidence={"reviewers": len(reviewers)},
            )
        _reject_duplicates([reviewer.name for reviewer in reviewers], what="reviewer")

        if visual_required and not any(gate.kind == "visual" for gate in gates):
            raise ConfigError(
                "visual_qa_required is set but no gate of kind 'visual' is configured",
                evidence={"gate_kinds": sorted({gate.kind for gate in gates})},
            )

        branch = _optional_text(raw, "branch")
        base = _optional_text(raw, "base")

        return cls(
            repo=repo,
            pr=pr,
            source_repo=resolve("source_repo"),
            worktree_root=resolve("worktree_root"),
            state_file=resolve("state_file"),
            lock_file=resolve("lock_file"),
            builder=_builder(raw.get("builder")),
            reviewers=reviewers,
            gates=gates,
            branch=branch,
            base=base,
            visual_qa_required=visual_required,
            source=source,
        )


def _sequence(raw: Mapping[str, Any], key: str, *, required: bool) -> list[Any]:
    value = raw.get(key, [])
    if not isinstance(value, list):
        raise ConfigError(f"config {key} must be a list", evidence={"key": key})
    if required and not value:
        raise ConfigError(f"config {key} must not be empty", evidence={"key": key})
    return value


def _optional_text(raw: Mapping[str, Any], key: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ConfigError(f"config {key} must be a non-empty string when present", evidence={"key": key})
    return value


def _timeout(raw: Mapping[str, Any], *, what: str) -> float | None:
    value = raw.get("timeout")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ConfigError(f"{what} timeout must be a positive number", evidence={"timeout": value})
    return float(value)


def _checked_name(raw: Mapping[str, Any], *, what: str, index: int) -> str:
    value = raw.get("name")
    if not isinstance(value, str) or not _NAME.match(value):
        raise ConfigError(f"{what}[{index}] name is missing or unusable", evidence={"name": value})
    return value


def _gate(item: object, index: int) -> GateConfig:
    if not isinstance(item, Mapping):
        raise ConfigError(f"gates[{index}] must be an object")
    unknown = sorted(set(item) - _GATE_KEYS)
    if unknown:
        raise ConfigError(f"gates[{index}] has unknown keys", evidence={"unknown_keys": unknown})
    kind = item.get("kind", "baseline")
    if kind not in GATE_KINDS:
        raise ConfigError(
            f"gates[{index}] kind must be one of {list(GATE_KINDS)}", evidence={"kind": kind}
        )
    return GateConfig(
        name=_checked_name(item, what="gates", index=index),
        argv=validate_argv(item.get("argv"), what=f"gates[{index}].argv"),
        kind=kind,
        timeout=_timeout(item, what=f"gates[{index}]"),
    )


def _reviewer(item: object, index: int) -> ReviewerConfig:
    if not isinstance(item, Mapping):
        raise ConfigError(f"reviewers[{index}] must be an object")
    unknown = sorted(set(item) - _REVIEWER_KEYS)
    if unknown:
        raise ConfigError(f"reviewers[{index}] has unknown keys", evidence={"unknown_keys": unknown})
    return ReviewerConfig(
        name=_checked_name(item, what="reviewers", index=index),
        argv=validate_argv(item.get("argv"), what=f"reviewers[{index}].argv"),
        timeout=_timeout(item, what=f"reviewers[{index}]"),
    )


def _builder(item: object) -> BuilderConfig:
    if not isinstance(item, Mapping):
        raise ConfigError("config builder must be an object")
    unknown = sorted(set(item) - _BUILDER_KEYS)
    if unknown:
        raise ConfigError("config builder has unknown keys", evidence={"unknown_keys": unknown})
    signature = item.get("signature")
    if not isinstance(signature, str) or len(signature.strip()) < 8:
        raise ConfigError(
            "config builder.signature must be a distinctive string to read back",
            evidence={"signature": signature},
        )
    author = item.get("comment_author")
    if not isinstance(author, str) or not _LOGIN.match(author):
        raise ConfigError(
            "config builder.comment_author is required and must be the exact GitHub "
            "login the builder comments under; a signature alone is public and forgeable",
            evidence={"comment_author": author},
        )
    return BuilderConfig(
        argv=validate_argv(item.get("argv"), what="builder.argv"),
        signature=signature.strip(),
        comment_author=author,
        timeout=_timeout(item, what="builder"),
    )


def _reject_duplicates(names: list[str], *, what: str) -> None:
    seen: set[str] = set()
    for name in names:
        if name in seen:
            raise ConfigError(f"duplicate {what} name {name!r}", evidence={"name": name})
        seen.add(name)


__all__ = [
    "GATE_KINDS",
    "SCHEMA_VERSION",
    "BuilderConfig",
    "GateConfig",
    "ReviewerConfig",
    "RunConfig",
]
