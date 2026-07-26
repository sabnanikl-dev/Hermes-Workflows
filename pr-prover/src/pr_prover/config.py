"""Strict run configuration.

One JSON file names the PR, the clone to borrow objects from, where the local
state/lock live, and the argv templates for baseline gates, the reviewer lanes,
and the builder lane. Unknown keys are rejected: a typo that silently disables a
gate is exactly the kind of quiet drift this loop must not have.

Placeholders available to every template::

    {repo} {owner} {name} {pr} {branch} {base} {head} {worktree}

Reviewer templates also get ``{reviewer}``, ``{role}``, and ``{artifact_file}``;
builder templates also get ``{attempt}``, ``{mode}`` (``initial`` or
``corrective``), and ``{blockers_file}``. Both file paths live under the OS temp
directory, never inside a repo.

The ``reviewers`` array is the acceptance lifecycle, not a free list of lanes:
it must be exactly ``reviewer-a``, ``reviewer-b``, and ``integration-auditor``,
in that order. The loop runs the lanes in the order given, and the auditor's job
is to reconcile the artifacts the other two publish, so a missing, duplicated,
or reordered required role is a configuration error rather than a run that
quietly proves less than it claims.

A reviewer may publish its own artifact, or — the shipped default — declare a
``relay``: the reviewer writes its finished artifact to ``{artifact_file}`` with
no GitHub credential in its environment, and the separately configured relay
argv publishes that file under the reviewer identity. The relay is an ordinary
command; it is given no credential by this tool and uses whatever ``gh`` session
it already has.

The argv arrays are where the trusted agents are named. Hermes writes the exact
invocation of the installed Claude/Codex wrapper it wants — model, empty MCP
config, task-scoped tools, pointer-first prompt file — and the loop runs it
unchanged. There is no role abstraction between the two.

Two identities are pinned rather than inferred:

* ``builder.comment_author`` — the login the fix comment must come from;
* each reviewer's ``artifact_author`` — the login its published review or
  comment must come from, alongside the ``role`` line and the exact head that
  artifact must carry.

Both are required. A signature and a head SHA are public the moment an artifact
is posted, so on their own they prove only that somebody read the PR; the login
is the part an arbitrary account cannot supply. There is no "any author will do"
configuration to fall into.

``env``/``env_unset`` are a small named overlay on the inherited environment,
not a replacement for it: the trusted lanes run as Karan's own user with the
normal Claude OAuth/keychain session, so the session variables cannot be
retargeted and credentials do not belong in this file.
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
from .reviewers import CREDENTIAL_ENV

SCHEMA_VERSION = 1
GATE_KINDS = ("baseline", "visual")
# The acceptance lifecycle, as configuration rather than operator convention.
#
# The mission fixes one ordered review sequence for a merge-readiness run:
# Reviewer A, then Reviewer B, then the Integration Auditor — whose whole job is
# to reconcile the two artifacts that must already exist when it runs. The loop
# executes reviewer lanes in the order the config lists them, so "the auditor
# ran last" is only true if the schema says it must be; a config with two lanes,
# a duplicated role, or the auditor first would otherwise pass ``check-config``
# and produce a run that never integrated anything.
REQUIRED_REVIEWER_ROLES = ("reviewer-a", "reviewer-b", "integration-auditor")
# A trusted builder reads the live PR, edits, runs verification, commits,
# pushes, and comments. Twenty minutes is the floor of a realistic budget for
# that; anything shorter tends to be killed mid-verification and misread as a
# hang. Advisory, not enforced: a repo with a two-minute suite may know better.
REALISTIC_BUILDER_BUDGET = 1200.0
REALISTIC_REVIEWER_BUDGET = 900.0
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
_GATE_KEYS = frozenset({"name", "argv", "kind", "timeout", "env", "env_unset"})
_REVIEWER_KEYS = frozenset(
    {
        "name",
        "argv",
        "timeout",
        "role",
        "artifact_author",
        "artifact_signature",
        "relay",
        "env",
        "env_unset",
    }
)
_RELAY_KEYS = frozenset({"argv", "timeout", "env", "env_unset"})
# The token every relayed lane has to be handed, on both sides of the handoff:
# the reviewer needs somewhere to write, and the relay needs something to post.
_ARTIFACT_FILE = "{artifact_file}"
_BUILDER_KEYS = frozenset(
    {"argv", "signature", "comment_author", "timeout", "env", "env_unset"}
)
_ENV_NAME = re.compile(r"\A[A-Za-z_][A-Za-z0-9_]{0,63}\Z")
# The variables that carry the logged-in macOS session the trusted agents
# authenticate through. Overriding or clearing any of them is how a lane ends up
# running against a synthetic home with no Claude OAuth/keychain session.
_SESSION_ENV = frozenset({"HOME", "USER", "LOGNAME", "SHELL"})
_CREDENTIAL_PREFIXES = ("ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_")


@dataclass(frozen=True)
class LaneEnv:
    """A named overlay on the environment a lane inherits.

    Empty by default, and empty means "inherit exactly what this process has".
    The overlay can add a variable a lane needs and remove one it must not see
    — ``GH_TOKEN``, so a trusted agent uses its own configured ``gh`` identity
    rather than the operator's — but it cannot touch the session variables and
    it may not carry a credential value: tokens belong in the keychain and in
    ``gh``'s own auth, not in a run config that ends up in evidence.
    """

    set: tuple[tuple[str, str], ...] = ()
    unset: tuple[str, ...] = ()

    @property
    def empty(self) -> bool:
        return not self.set and not self.unset

    def apply(self, base: Mapping[str, str]) -> dict[str, str] | None:
        """The environment for one lane, or ``None`` to inherit untouched."""
        if self.empty:
            return None
        env = dict(base)
        for name in self.unset:
            env.pop(name, None)
        env.update(self.set)
        return env


@dataclass(frozen=True)
class GateConfig:
    """One baseline gate, or one browser/visual QA gate."""

    name: str
    argv: tuple[str, ...]
    kind: str = "baseline"
    timeout: float | None = None
    env: LaneEnv = LaneEnv()


@dataclass(frozen=True)
class RelayConfig:
    """The trusted command that publishes one reviewer's prepared artifact.

    It runs after the reviewer lane has exited and its prepared artifact has
    validated, under whatever GitHub identity its own session already holds.
    This tool hands it a file path and nothing else.
    """

    argv: tuple[str, ...]
    timeout: float | None = None
    env: LaneEnv = LaneEnv()


@dataclass(frozen=True)
class ReviewerConfig:
    """One exact-head reviewer lane, and the artifact it must publish.

    ``role`` is what the lane is: Reviewer A, Reviewer B, Integration Auditor.
    It is substituted into the argv template and it must appear on its own line
    in the published artifact, so one reviewer's post can never be read back as
    another's.

    With a ``relay``, the lane itself is credential-free: it writes its artifact
    to ``{artifact_file}`` and the relay publishes it. Without one, the lane
    publishes for itself, which is the older path and still supported.
    """

    name: str
    argv: tuple[str, ...]
    artifact_author: str
    artifact_signature: str
    role: str
    timeout: float | None = None
    env: LaneEnv = LaneEnv()
    relay: RelayConfig | None = None


@dataclass(frozen=True)
class BuilderConfig:
    """The fix lane, plus who its PR comment must come from and what it must say."""

    argv: tuple[str, ...]
    signature: str
    comment_author: str
    timeout: float | None = None
    env: LaneEnv = LaneEnv()


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

    def advisories(self) -> tuple[str, ...]:
        """Non-fatal notes ``check-config`` prints before a real run.

        The budgets are the ones that matter operationally: a trusted agent cut
        off mid-verification looks exactly like a hang, and that misreading is
        what the two-cycle loop pays for. An omitted budget is the other end of
        the same problem — nothing will ever end that lane — so it is said out
        loud here rather than quietly capped somewhere the report cannot see.
        """
        notes: list[str] = []
        for lane, timeout in self._budgets():
            if timeout is None:
                notes.append(
                    f"{lane} has no timeout, so nothing but the lane itself will ever end it; "
                    "the run log will report its budget as unbounded"
                )
        if self.builder.timeout is not None and self.builder.timeout < REALISTIC_BUILDER_BUDGET:
            notes.append(
                f"builder timeout is {self.builder.timeout:.0f}s; a trusted builder that reads "
                f"the PR, edits, verifies, pushes, and comments usually needs "
                f"{REALISTIC_BUILDER_BUDGET:.0f}s or more"
            )
        for reviewer in self.reviewers:
            if reviewer.timeout is not None and reviewer.timeout < REALISTIC_REVIEWER_BUDGET:
                notes.append(
                    f"reviewer {reviewer.name!r} timeout is {reviewer.timeout:.0f}s; "
                    f"exact-head review usually needs {REALISTIC_REVIEWER_BUDGET:.0f}s or more"
                )
        return tuple(notes)

    def _budgets(self) -> tuple[tuple[str, float | None], ...]:
        """Every lane that runs a child, and the budget it will actually get."""
        return (
            ("builder", self.builder.timeout),
            *((f"gate {gate.name!r}", gate.timeout) for gate in self.gates),
            *(
                (f"reviewer {reviewer.name!r}", reviewer.timeout)
                for reviewer in self.reviewers
            ),
            *(
                (f"reviewer {reviewer.name!r} relay", reviewer.relay.timeout)
                for reviewer in self.reviewers
                if reviewer.relay is not None
            ),
        )

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
        _reject_duplicates([reviewer.name for reviewer in reviewers], what="reviewer")
        # Two lanes sharing a role could each satisfy the other's artifact
        # readback, which is exactly the independence the lanes exist for; and
        # the required sequence is the acceptance lifecycle itself, so a missing
        # auditor or a reordered one is rejected here rather than discovered
        # afterwards in a run that already reported.
        _reject_duplicates([reviewer.role for reviewer in reviewers], what="reviewer role")
        roles = tuple(reviewer.role for reviewer in reviewers)
        if roles != REQUIRED_REVIEWER_ROLES:
            raise ConfigError(
                "config reviewers must be exactly "
                + ", ".join(REQUIRED_REVIEWER_ROLES)
                + ", in that order: the Integration Auditor reconciles the Reviewer A "
                "and Reviewer B artifacts, so it cannot be missing, duplicated, or run first",
                evidence={"required_roles": list(REQUIRED_REVIEWER_ROLES), "configured_roles": list(roles)},
            )

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
        env=_lane_env(item, what=f"gates[{index}]"),
    )


def _reviewer(item: object, index: int) -> ReviewerConfig:
    if not isinstance(item, Mapping):
        raise ConfigError(f"reviewers[{index}] must be an object")
    unknown = sorted(set(item) - _REVIEWER_KEYS)
    if unknown:
        raise ConfigError(f"reviewers[{index}] has unknown keys", evidence={"unknown_keys": unknown})
    name = _checked_name(item, what="reviewers", index=index)
    role = item.get("role", name)
    if not isinstance(role, str) or not _NAME.match(role):
        raise ConfigError(f"reviewers[{index}] role is unusable", evidence={"role": role})
    author = item.get("artifact_author")
    if not isinstance(author, str) or not _LOGIN.match(author):
        raise ConfigError(
            f"reviewers[{index}].artifact_author is required and must be the exact GitHub "
            "login this reviewer publishes under; without it a review cannot be told "
            "apart from any other account's",
            evidence={"artifact_author": author},
        )
    signature = item.get("artifact_signature")
    if not isinstance(signature, str) or len(signature.strip()) < 8:
        raise ConfigError(
            f"reviewers[{index}].artifact_signature must be a distinctive string to read back",
            evidence={"artifact_signature": signature},
        )
    argv = validate_argv(item.get("argv"), what=f"reviewers[{index}].argv")
    env = _lane_env(item, what=f"reviewers[{index}]")
    relay = _relay(item.get("relay"), what=f"reviewers[{index}].relay")
    if relay is not None:
        # The handoff only works if both halves are handed the file: a reviewer
        # with nowhere to write, or a relay with nothing to post, would fail at
        # readback with no way to tell which half was misconfigured.
        if not any(_ARTIFACT_FILE in part for part in argv):
            raise ConfigError(
                f"reviewers[{index}] has a relay but its argv never receives "
                f"{_ARTIFACT_FILE}, so the lane has nowhere to prepare its artifact",
                evidence={"reviewer": name},
            )
        if not any(_ARTIFACT_FILE in part for part in relay.argv):
            raise ConfigError(
                f"reviewers[{index}].relay argv never receives {_ARTIFACT_FILE}, "
                "so it has no prepared artifact to publish",
                evidence={"reviewer": name},
            )
        # A relayed lane is the credential-free one. Naming a token for it in
        # the config contradicts the lifecycle rather than tightening it.
        for variable, _ in env.set:
            if variable in CREDENTIAL_ENV:
                raise ConfigError(
                    f"reviewers[{index}] uses the relay lifecycle, so it runs without a "
                    f"GitHub credential; remove {variable} from its env and let the relay publish",
                    evidence={"reviewer": name, "name": variable},
                )
    return ReviewerConfig(
        name=name,
        argv=argv,
        artifact_author=author,
        artifact_signature=signature.strip(),
        role=role,
        timeout=_timeout(item, what=f"reviewers[{index}]"),
        env=env,
        relay=relay,
    )


def _relay(item: object, *, what: str) -> RelayConfig | None:
    if item is None:
        return None
    if not isinstance(item, Mapping):
        raise ConfigError(f"{what} must be an object")
    unknown = sorted(set(item) - _RELAY_KEYS)
    if unknown:
        raise ConfigError(f"{what} has unknown keys", evidence={"unknown_keys": unknown})
    return RelayConfig(
        argv=validate_argv(item.get("argv"), what=f"{what}.argv"),
        timeout=_timeout(item, what=what),
        env=_lane_env(item, what=what),
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
        env=_lane_env(item, what="builder"),
    )


def _lane_env(raw: Mapping[str, Any], *, what: str) -> LaneEnv:
    """Validate one lane's environment overlay."""
    overlay = raw.get("env", {})
    if not isinstance(overlay, Mapping):
        raise ConfigError(f"{what} env must be an object of NAME: value pairs")
    pairs: list[tuple[str, str]] = []
    for name, value in overlay.items():
        _checked_env_name(name, what=what)
        if not isinstance(value, str) or "\x00" in value:
            raise ConfigError(
                f"{what} env {name} must be a string value", evidence={"name": name}
            )
        if value.startswith(_CREDENTIAL_PREFIXES):
            raise ConfigError(
                f"{what} env {name} looks like a credential; keep tokens in the keychain "
                "and in gh's own auth, and let the lane read them there",
                evidence={"name": name},
            )
        pairs.append((name, value))
    names = raw.get("env_unset", [])
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        raise ConfigError(f"{what} env_unset must be a list of variable names")
    for name in names:
        _checked_env_name(name, what=what)
    return LaneEnv(set=tuple(pairs), unset=tuple(names))


def _checked_env_name(name: object, *, what: str) -> str:
    if not isinstance(name, str) or not _ENV_NAME.match(name):
        raise ConfigError(f"{what} environment variable name is unusable", evidence={"name": name})
    if name in _SESSION_ENV:
        raise ConfigError(
            f"{what} may not set or clear {name}: the trusted lanes run in Karan's own "
            "session and need the real Claude OAuth/keychain environment",
            evidence={"name": name, "session_variables": sorted(_SESSION_ENV)},
        )
    return name


def _reject_duplicates(names: list[str], *, what: str) -> None:
    seen: set[str] = set()
    for name in names:
        if name in seen:
            raise ConfigError(f"duplicate {what} name {name!r}", evidence={"name": name})
        seen.add(name)


__all__ = [
    "GATE_KINDS",
    "REALISTIC_BUILDER_BUDGET",
    "REALISTIC_REVIEWER_BUDGET",
    "REQUIRED_REVIEWER_ROLES",
    "SCHEMA_VERSION",
    "BuilderConfig",
    "GateConfig",
    "LaneEnv",
    "RelayConfig",
    "ReviewerConfig",
    "RunConfig",
]
