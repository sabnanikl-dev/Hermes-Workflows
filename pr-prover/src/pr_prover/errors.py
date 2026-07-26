"""Fail-closed error taxonomy for the PR prover.

Every failure the loop can reach carries a stable ``reason`` code plus a
redacted evidence mapping. :class:`FailClosed` is the marker for "stop and ask
Karan": the loop never guesses past one of these, and the CLI reports the run
as ``needs-karan`` with the preserved evidence.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class PrProverError(Exception):
    """Base error. Subclasses fix a stable machine-readable reason code."""

    reason = "error"

    def __init__(self, message: str, *, evidence: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.evidence: dict[str, Any] = dict(evidence or {})

    def as_dict(self) -> dict[str, Any]:
        return {"reason": self.reason, "message": self.message, "evidence": dict(self.evidence)}


class FailClosed(PrProverError):
    """Ambiguity or unexpected state: stop the run and ask Karan."""

    reason = "fail-closed"


class ConfigError(FailClosed):
    """The run configuration is missing, malformed, or internally inconsistent."""

    reason = "invalid-config"


class CommandContractError(FailClosed):
    """A child command was not expressed as a well-formed argv array."""

    reason = "invalid-command"


class LockContention(FailClosed):
    """Another run already holds the run-exists lockfile."""

    reason = "lock-contention"


class StateError(FailClosed):
    """The local JSON state file is unexpected, or an invariant was violated."""

    reason = "unexpected-state"


class MalformedVerdict(FailClosed):
    """A reviewer or builder produced no single parsable machine-readable verdict."""

    reason = "malformed-verdict"


class LaneFailure(FailClosed):
    """A lane's child-process result cannot support the verdict it printed."""

    reason = "lane-failure"


class StaleHead(FailClosed):
    """A verdict, remote ref, or worktree is not bound to the exact expected head."""

    reason = "stale-head"


class AmbiguousPush(FailClosed):
    """The builder push cannot be bound to exactly one new remote head."""

    reason = "ambiguous-push"


class ReadbackMismatch(FailClosed):
    """A GitHub artifact could not be read back for the exact verified head."""

    reason = "readback-mismatch"


class ReviewerRelayError(FailClosed):
    """A credential-free reviewer's prepared artifact is unusable, or the relay failed."""

    reason = "relay-failure"


class ScopeContamination(FailClosed):
    """Work appeared outside the frozen blocker set or the attempt worktree is dirty."""

    reason = "scope-contamination"


class BuilderRefusal(FailClosed):
    """The builder declined, omitted, or could not complete the frozen blocker set."""

    reason = "builder-refusal"


class GitHubError(FailClosed):
    """The GitHub boundary failed or returned an unusable payload."""

    reason = "github-error"


class WorktreeError(FailClosed):
    """An isolated worktree could not be created safely, or a path guard tripped."""

    reason = "worktree-error"
