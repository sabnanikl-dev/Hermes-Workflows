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

The optional ``launch`` section names the scoped identities this run's launcher
owns and how far the child environment allowlist may be widened. A lane then
either keeps its own ``argv`` array — a repository-owned script, run with a
hardened environment — or declares an ``agent`` block, in which case the
launcher composes the whole child argv itself and the lane must name one
identity. Declaring both is refused: two sources for one command line is
exactly the ambiguity that fails closed.

Everything the configuration may say about an agent lane can only *narrow* it.
Tool sets are checked against a code-owned maximum per role, permission modes
against a closed list, capabilities against a vocabulary with no merge or
deploy form, and the budget against the 20-30 minute window. Credentials
themselves are never in this file: an identity names an environment variable or
a protected file to read one from.
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .childenv import EnvironmentPolicy
from .commands import validate_argv
from .errors import ConfigError, IdentityError, LaunchPolicyError
from .identities import BUILDER_CAPABILITIES, REVIEWER_CAPABILITIES, IdentitySpec
from .launchers import (
    BUDGET_MAX,
    BUDGET_MIN,
    BUILDER_TOOLS,
    DEFAULT_BUDGET,
    PERMISSION_MODES,
    REVIEWER_TOOLS,
    AgentSpec,
)

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
        "launch",
    }
)
_GATE_KEYS = frozenset({"name", "argv", "kind", "timeout"})
_REVIEWER_KEYS = frozenset({"name", "argv", "timeout", "identity", "agent"})
_BUILDER_KEYS = frozenset({"argv", "signature", "comment_author", "timeout", "identity", "agent"})
_LAUNCH_KEYS = frozenset({"identities", "env_allow", "model_auth_env"})
_IDENTITY_KEYS = frozenset({"login", "capabilities", "token_env", "token_file", "inject_as"})
_AGENT_KEYS = frozenset({"program", "model", "tools", "permission_mode"})
_MODEL = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")


@dataclass(frozen=True)
class GateConfig:
    """One baseline gate, or one browser/visual QA gate."""

    name: str
    argv: tuple[str, ...]
    kind: str = "baseline"
    timeout: float | None = None


@dataclass(frozen=True)
class LaunchConfig:
    """The identities this run's launcher owns, and how wide a child env may be."""

    identities: Mapping[str, IdentitySpec] = field(default_factory=dict)
    policy: EnvironmentPolicy = field(default_factory=EnvironmentPolicy)


@dataclass(frozen=True)
class ReviewerConfig:
    """One exact-head reviewer lane."""

    name: str
    argv: tuple[str, ...] | None = None
    timeout: float | None = None
    identity: str | None = None
    agent: AgentSpec | None = None


@dataclass(frozen=True)
class BuilderConfig:
    """The fix lane, plus who its PR comment must come from and what it must say.

    ``comment_author`` is required, not optional. The signature and the head SHA
    are both public the moment the builder comments, so on their own they prove
    only that somebody read the PR. The expected login is the part an arbitrary
    commenter cannot supply.
    """

    signature: str
    comment_author: str
    argv: tuple[str, ...] | None = None
    timeout: float | None = None
    identity: str | None = None
    agent: AgentSpec | None = None


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
    launch: LaunchConfig = field(default_factory=LaunchConfig)
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

        launch = _launch(raw.get("launch"), base_dir=root)

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

        builder = _builder(raw.get("builder"))
        _bind_identities(builder, reviewers, launch)

        return cls(
            repo=repo,
            pr=pr,
            source_repo=resolve("source_repo"),
            worktree_root=resolve("worktree_root"),
            state_file=resolve("state_file"),
            lock_file=resolve("lock_file"),
            builder=builder,
            reviewers=reviewers,
            gates=gates,
            branch=branch,
            base=base,
            visual_qa_required=visual_required,
            launch=launch,
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
    what = f"reviewers[{index}]"
    agent = _agent(item.get("agent"), what=what, tools=REVIEWER_TOOLS)
    return ReviewerConfig(
        name=_checked_name(item, what="reviewers", index=index),
        argv=_lane_argv(item, what=what, agent=agent),
        timeout=_lane_timeout(item, what=what, agent=agent),
        identity=_optional_text(item, "identity"),
        agent=agent,
    )


def _lane_argv(item: Mapping[str, Any], *, what: str, agent: AgentSpec | None) -> tuple[str, ...] | None:
    """A lane is either a repository-owned script or a launcher-composed agent.

    Both would leave two answers to "what command runs here", and the launcher
    would have to pick one. It refuses to.
    """
    has_argv = item.get("argv") is not None
    if agent is not None and has_argv:
        raise ConfigError(
            f"{what} declares both argv and agent; a lane has exactly one command line",
            evidence={"lane": what},
        )
    if agent is None and not has_argv:
        raise ConfigError(
            f"{what} needs either an argv array or an agent launch block",
            evidence={"lane": what},
        )
    if agent is not None:
        return None
    return validate_argv(item.get("argv"), what=f"{what}.argv")


def _lane_timeout(item: Mapping[str, Any], *, what: str, agent: AgentSpec | None) -> float | None:
    """An agent lane's budget is bounded; a script lane's is the operator's business."""
    timeout = _timeout(item, what=what)
    if agent is None:
        return timeout
    budget = DEFAULT_BUDGET if timeout is None else timeout
    if not BUDGET_MIN <= budget <= BUDGET_MAX:
        raise ConfigError(
            f"{what} timeout is outside the 20-30 minute agent budget",
            evidence={"lane": what, "timeout": budget, "minimum": BUDGET_MIN, "maximum": BUDGET_MAX},
        )
    return budget


def _agent(item: object, *, what: str, tools: tuple[str, ...]) -> AgentSpec | None:
    """Parse an agent launch block, narrowing only within the code-owned maxima."""
    if item is None:
        return None
    if not isinstance(item, Mapping):
        raise ConfigError(f"{what}.agent must be an object")
    unknown = sorted(set(item) - _AGENT_KEYS)
    if unknown:
        raise ConfigError(f"{what}.agent has unknown keys", evidence={"unknown_keys": unknown})
    program = item.get("program")
    if not isinstance(program, str) or not program.strip():
        raise ConfigError(
            f"{what}.agent.program must name the executable to launch",
            evidence={"program": program},
        )
    model = item.get("model")
    if not isinstance(model, str) or not _MODEL.match(model):
        raise ConfigError(f"{what}.agent.model must be a model name", evidence={"model": model})
    mode = item.get("permission_mode", "acceptEdits")
    if mode not in PERMISSION_MODES:
        raise ConfigError(
            f"{what}.agent.permission_mode must be one of {list(PERMISSION_MODES)}; the modes "
            "that bypass the tool boundary are not configurable",
            evidence={"permission_mode": mode},
        )
    requested = item.get("tools", list(tools))
    if not isinstance(requested, list) or not requested:
        raise ConfigError(f"{what}.agent.tools must be a non-empty list", evidence={"tools": requested})
    chosen = []
    for entry in requested:
        if not isinstance(entry, str) or entry not in tools:
            raise ConfigError(
                f"{what}.agent.tools may only narrow this role's tool set",
                evidence={"tool": entry, "allowed": list(tools)},
            )
        if entry not in chosen:
            chosen.append(entry)
    return AgentSpec(
        program=program.strip(),
        model=model,
        tools=tuple(chosen),
        permission_mode=mode,
    )


def _launch(item: object, *, base_dir: Path) -> LaunchConfig:
    """Parse the launcher's own section: the identities it owns and the env allowlist."""
    if item is None:
        return LaunchConfig()
    if not isinstance(item, Mapping):
        raise ConfigError("config launch must be an object")
    unknown = sorted(set(item) - _LAUNCH_KEYS)
    if unknown:
        raise ConfigError("config launch has unknown keys", evidence={"unknown_keys": unknown})

    allow = item.get("env_allow", [])
    if not isinstance(allow, list) or any(not isinstance(entry, str) for entry in allow):
        raise ConfigError("launch.env_allow must be a list of variable names", evidence={"env_allow": allow})
    model_auth = item.get("model_auth_env")
    if model_auth is not None and not isinstance(model_auth, str):
        raise ConfigError(
            "launch.model_auth_env must name one environment variable",
            evidence={"model_auth_env": model_auth},
        )
    try:
        policy = EnvironmentPolicy(
            extra_allow=frozenset(allow),
            permit=frozenset({model_auth} if model_auth else ()),
        )
    except LaunchPolicyError as exc:
        raise ConfigError(exc.message, evidence=exc.evidence) from exc

    raw_identities = item.get("identities", {})
    if not isinstance(raw_identities, Mapping):
        raise ConfigError("launch.identities must be an object keyed by identity name")
    identities: dict[str, IdentitySpec] = {}
    for name, spec in raw_identities.items():
        if not isinstance(name, str) or not _NAME.match(name):
            raise ConfigError("launch.identities has an unusable identity name", evidence={"name": name})
        identities[name] = _identity(name, spec, base_dir=base_dir)
    return LaunchConfig(identities=identities, policy=policy)


def _identity(name: str, item: object, *, base_dir: Path) -> IdentitySpec:
    if not isinstance(item, Mapping):
        raise ConfigError(f"launch.identities.{name} must be an object")
    unknown = sorted(set(item) - _IDENTITY_KEYS)
    if unknown:
        raise ConfigError(
            f"launch.identities.{name} has unknown keys", evidence={"unknown_keys": unknown}
        )
    capabilities = item.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise ConfigError(
            f"launch.identities.{name} must declare its capabilities",
            evidence={"capabilities": capabilities},
        )
    if any(not isinstance(entry, str) for entry in capabilities):
        raise ConfigError(f"launch.identities.{name} capabilities must be strings")
    token_file = item.get("token_file")
    if token_file is not None:
        if not isinstance(token_file, str) or not token_file:
            raise ConfigError(f"launch.identities.{name} token_file must be a path")
        candidate = Path(token_file).expanduser()
        token_file = candidate if candidate.is_absolute() else (base_dir / candidate)
    try:
        return IdentitySpec(
            name=name,
            login=item.get("login") if isinstance(item.get("login"), str) else "",
            capabilities=frozenset(capabilities),
            token_env=item.get("token_env"),
            token_file=token_file,
            inject_as=item.get("inject_as", "GH_TOKEN"),
        )
    except IdentityError as exc:
        raise ConfigError(exc.message, evidence=exc.evidence) from exc


def _bind_identities(
    builder: BuilderConfig, reviewers: tuple[ReviewerConfig, ...], launch: LaunchConfig
) -> None:
    """Cross-check that every lane names an identity the launcher owns and may use.

    The builder's identity and its expected comment author must be the same
    account. Otherwise the run would launch as one login and then accept a fix
    comment from another, and the readback would prove nothing about the child
    that actually ran.
    """
    _require_identity(builder.identity, builder.agent, launch, what="builder", allowed=BUILDER_CAPABILITIES)
    if builder.identity is not None:
        login = launch.identities[builder.identity].login
        if login != builder.comment_author:
            raise ConfigError(
                "the builder's identity and its expected comment author are different accounts",
                evidence={"identity_login": login, "comment_author": builder.comment_author},
            )
    for reviewer in reviewers:
        _require_identity(
            reviewer.identity,
            reviewer.agent,
            launch,
            what=f"reviewer {reviewer.name!r}",
            allowed=REVIEWER_CAPABILITIES,
        )


def _require_identity(
    identity: str | None,
    agent: AgentSpec | None,
    launch: LaunchConfig,
    *,
    what: str,
    allowed: frozenset[str],
) -> None:
    if identity is None:
        if agent is not None:
            raise ConfigError(
                f"{what} declares an agent launch but no scoped identity to run as",
                evidence={"lane": what},
            )
        return
    spec = launch.identities.get(identity)
    if spec is None:
        raise ConfigError(
            f"{what} names an identity that launch.identities does not define",
            evidence={"identity": identity, "known": sorted(launch.identities)},
        )
    if spec.capabilities != allowed:
        raise ConfigError(
            f"{what} must use an identity with exactly this role's capabilities",
            evidence={
                "identity": identity,
                "declared": sorted(spec.capabilities),
                "required": sorted(allowed),
            },
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
    agent = _agent(item.get("agent"), what="builder", tools=BUILDER_TOOLS)
    return BuilderConfig(
        signature=signature.strip(),
        comment_author=author,
        argv=_lane_argv(item, what="builder", agent=agent),
        timeout=_lane_timeout(item, what="builder", agent=agent),
        identity=_optional_text(item, "identity"),
        agent=agent,
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
    "LaunchConfig",
    "ReviewerConfig",
    "RunConfig",
]
