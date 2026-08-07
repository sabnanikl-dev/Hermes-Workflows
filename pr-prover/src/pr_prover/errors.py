"""Fail-closed error taxonomy for the PR prover, and the failure record it renders.

Every failure the loop can reach carries a stable ``reason`` code plus a
redacted evidence mapping. :class:`FailClosed` is the marker for "stop and ask
Karan": the loop never guesses past one of these, and the CLI reports the run
as ``needs-karan`` with the preserved evidence.

A reason code and a message are enough for a human reading a log and not enough
for the trusted builder that has to act next. :class:`FailureRecord` is the one
structured form every failure — a failed gate, a readback mismatch, a malformed
marker, a stale head, a classification stop — is expressed in, and it answers
four questions the builder otherwise has to guess at:

1. what failed;
2. the exact evidence, including expected versus actual or the command run;
3. the **bounded** remediation the builder may attempt;
4. the escalation condition, for when the fix would fall outside those bounds.

The human summary and the builder-facing next-instruction block are two
renderings of that single record (see :mod:`pr_prover.report`), never two
separately maintained descriptions of the same failure.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
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
    """A reviewer's artifact could not be prepared or published under its identity."""

    reason = "relay-failure"


class EvidencePacketError(FailClosed):
    """The frozen evidence a credential-free reviewer judges from is unusable.

    Distinct from :class:`ReviewerRelayError` because it stops the lane at the
    other end of the lifecycle: the packet is what a lane with no GitHub
    credential reads *before* it reviews, so an empty, malformed, or
    wrongly-bound one means the review would have been formed against the wrong
    head — or against nothing — rather than that transport failed.
    """

    reason = "evidence-packet"


class EnvironmentEvidenceError(FailClosed):
    """A gate's declared environment revision binding could not be established.

    Distinct from :class:`EvidencePacketError`, which is about the evidence a
    reviewer lane is *given*. This one is about evidence a gate was configured to
    *produce*: an operator declared that the gate observes an external
    environment and binds it to this head, and the file that would have proved
    it is missing, malformed, or names another repository, PR, gate,
    environment, head, or revision. The endpoint may well have answered; what
    failed is the claim that it was serving this head, and reporting around that
    is exactly what the disclosure contract forbids.
    """

    reason = "environment-evidence"


class HumanFeedbackPresent(FailClosed):
    """The PR carries human feedback this run cannot prove anybody resolved.

    Raised both for unresolved feedback and for feedback surfaces that would not
    hold still long enough to be observed once. They are the same stop: in
    either case the run cannot say what the conversation currently asks for.
    """

    reason = "human-feedback"


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


# -- the structured failure record ---------------------------------------
# Two failure classes have no exception of their own. A failing gate becomes a
# blocking finding rather than stopping the run, and a needs-karan
# classification is a decision the loop reached rather than an error it hit —
# but the builder and Karan need the same four answers for both, so they are
# recorded in the same shape as every fail-closed reason code.
GATE_FAILURE = "gate-failure"
CLASSIFICATION_STOP = "classification-stop"

FAILURE_CLASSES = (
    GATE_FAILURE,
    CLASSIFICATION_STOP,
    FailClosed.reason,
    ConfigError.reason,
    CommandContractError.reason,
    LockContention.reason,
    StateError.reason,
    MalformedVerdict.reason,
    LaneFailure.reason,
    StaleHead.reason,
    AmbiguousPush.reason,
    ReadbackMismatch.reason,
    ReviewerRelayError.reason,
    EvidencePacketError.reason,
    EnvironmentEvidenceError.reason,
    HumanFeedbackPresent.reason,
    ScopeContamination.reason,
    BuilderRefusal.reason,
    GitHubError.reason,
    WorktreeError.reason,
)

# What the builder is allowed to do about each class, and the line past which it
# must stop and hand the run back. Remediation is deliberately narrow: every
# entry either names work inside the frozen blocker set or says plainly that
# there is none, because "try something" is the instruction that turns a failed
# gate into an unscoped refactor.
_STOP_ONLY = (
    "make no further change and push nothing for this head",
    "report the failure verbatim, including the evidence below",
)


@dataclass(frozen=True)
class _Playbook:
    remediation: tuple[str, ...]
    escalation: str


_PLAYBOOK: dict[str, _Playbook] = {
    GATE_FAILURE: _Playbook(
        remediation=(
            "re-run the exact command in the evidence inside this attempt's worktree and read its output",
            "change only what the frozen blocker this record is attached to names",
            "leave unrelated files, gate definitions, and configuration untouched",
        ),
        escalation=(
            "the gate fails for a cause outside the frozen blocker set — missing tooling, an "
            "unrelated repository break, or a gate definition that would have to change"
        ),
    ),
    CLASSIFICATION_STOP: _Playbook(
        remediation=_STOP_ONLY,
        escalation=(
            "always: a needs-karan finding is a judgment call this loop does not make, so it goes "
            "to Karan with the provenance below rather than into a fix attempt"
        ),
    ),
    FailClosed.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation="always: the run stopped on evidence it could not classify",
    ),
    ConfigError.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation=(
            "always: the run configuration is the operator's, and this loop never edits the file "
            "that decides its own scope"
        ),
    ),
    CommandContractError.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation="always: a child command template is configuration, not builder work",
    ),
    LockContention.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation=(
            "always: another run may hold the lock, and this loop never takes one over; confirm no "
            "run is active before clearing it by hand"
        ),
    ),
    StateError.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation=(
            "always: local state disagrees with what the loop can produce, so what actually landed "
            "has to be confirmed on the PR first"
        ),
    ),
    MalformedVerdict.reason: _Playbook(
        remediation=(
            "print exactly one DONE: marker as the final non-empty line, in the documented field order",
            "quote the bound head as the full 40-hex SHA, byte for byte",
            "reconcile the declared BLOCKING count with the FINDING lines above it",
        ),
        escalation=(
            "the lane cannot produce a conforming marker for this head, or the run has already "
            "rejected the marker twice"
        ),
    ),
    LaneFailure.reason: _Playbook(
        remediation=(
            "re-read the lane's exit status and its marker together; they must agree",
            "let a lane that found blockers exit nonzero with a failing verdict rather than a clean one",
        ),
        escalation=(
            "the lane timed out or died from infrastructure rather than from what it was judging"
        ),
    ),
    StaleHead.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation=(
            "always: the head this work was measured against is no longer live, so every gate, "
            "verdict, and finding for it is historical evidence only"
        ),
    ),
    AmbiguousPush.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation=(
            "always: the push cannot be bound to exactly one new head, and this loop never "
            "force-pushes or credits a push it cannot account for"
        ),
    ),
    ReadbackMismatch.reason: _Playbook(
        remediation=(
            "post the fix comment from the configured builder login only",
            "include both the configured signature and the exact new 40-hex head in the body",
            "post it as a new comment; editing an existing one cannot satisfy the readback",
        ),
        escalation=(
            "the comment cannot be posted under the configured identity, or a comment already "
            "matched before this attempt ran"
        ),
    ),
    ReviewerRelayError.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation=(
            "always: a reviewer artifact is the reviewer lane's own output and the relay's "
            "own transport, and the builder never writes, edits, or republishes one"
        ),
    ),
    EvidencePacketError.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation=(
            "always: the frozen packet is this run's own read of GitHub, so a lane that cannot "
            "get one bound to the current head has nothing to review and the builder has "
            "nothing to fix about it"
        ),
    ),
    EnvironmentEvidenceError.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation=(
            "always: which environment a gate observes, and whether that gate can prove "
            "the revision it served, are the operator's configuration and the gate's own "
            "output; the builder never writes a gate's binding evidence and never relaxes "
            "the declaration that asked for it"
        ),
    ),
    HumanFeedbackPresent.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation=(
            "always: feedback this run cannot prove resolved is a human asking for "
            "something, and neither a builder nor a merge-ready report may act over a "
            "PR conversation nobody has reconciled"
        ),
    ),
    ScopeContamination.reason: _Playbook(
        remediation=(
            "commit or revert every change in the attempt worktree so it is clean",
            "claim ADDRESSED only for ids present in the frozen blocker set",
        ),
        escalation="fixing the frozen blocker genuinely requires work outside it",
    ),
    BuilderRefusal.reason: _Playbook(
        remediation=(
            "address every id in the frozen blocker set, or say plainly which one you could not and why",
        ),
        escalation=(
            "a frozen blocker cannot be fixed within this attempt's bounds, or the corrective rerun "
            "for this attempt is already spent"
        ),
    ),
    GitHubError.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation=(
            "always: the GitHub boundary failed, so nothing about the live PR can be asserted from "
            "local evidence"
        ),
    ),
    WorktreeError.reason: _Playbook(
        remediation=_STOP_ONLY,
        escalation=(
            "always: an isolated worktree could not be created or read safely, and the loop never "
            "falls back to the operational clone"
        ),
    ),
}


@dataclass(frozen=True)
class FailureRecord:
    """One failure, in the single form both renderings are derived from.

    ``evidence`` is whatever the failure can actually prove — an expected/actual
    pair, the command that ran, the ids involved — and it is rendered, never
    re-derived. ``remediation`` and ``escalation`` come from the playbook for
    the failure class, so two failures of the same class cannot drift into two
    different instructions.
    """

    failure_class: str
    what_failed: str
    evidence: dict[str, Any] = field(default_factory=dict)
    remediation: tuple[str, ...] = ()
    escalation: str = ""
    finding_id: str | None = None

    def __post_init__(self) -> None:
        if self.failure_class not in FAILURE_CLASSES:
            raise StateError(
                f"unknown failure class {self.failure_class!r}",
                evidence={"failure_class": str(self.failure_class), "known": list(FAILURE_CLASSES)},
            )
        for name, value in (("what_failed", self.what_failed), ("escalation", self.escalation)):
            if not isinstance(value, str) or not value.strip():
                raise StateError(
                    f"failure record is incomplete: {name} is missing",
                    evidence={"failure_class": self.failure_class, "incomplete_field": name},
                )
        if not self.remediation:
            raise StateError(
                "failure record is incomplete: remediation is missing",
                evidence={"failure_class": self.failure_class, "incomplete_field": "remediation"},
            )

    @classmethod
    def from_error(cls, exc: PrProverError, *, finding_id: str | None = None) -> FailureRecord:
        """Express any fail-closed stop as a record, keeping its evidence intact."""
        failure_class = exc.reason if exc.reason in FAILURE_CLASSES else FailClosed.reason
        playbook = _PLAYBOOK[failure_class]
        return cls(
            failure_class=failure_class,
            what_failed=exc.message,
            evidence=dict(exc.evidence),
            remediation=playbook.remediation,
            escalation=playbook.escalation,
            finding_id=finding_id,
        )

    @classmethod
    def for_gate(
        cls,
        *,
        name: str,
        kind: str,
        command: Sequence[str],
        returncode: int,
        timed_out: bool,
        output: str,
        finding_id: str,
    ) -> FailureRecord:
        """The record behind a gate that failed, carrying the command it ran."""
        actual = "timed out" if timed_out else f"exit status {returncode}"
        outcome = "timed out" if timed_out else f"exited {returncode}"
        playbook = _PLAYBOOK[GATE_FAILURE]
        return cls(
            failure_class=GATE_FAILURE,
            what_failed=f"{kind} gate {name!r} {outcome}",
            evidence={
                "gate": name,
                "kind": kind,
                "command": list(command),
                "expected": "exit status 0",
                "actual": actual,
                "output": output,
            },
            remediation=playbook.remediation,
            escalation=playbook.escalation,
            finding_id=finding_id,
        )

    @classmethod
    def for_classification_stop(cls, *, finding: Mapping[str, Any]) -> FailureRecord:
        """The record behind one needs-karan finding that stopped the run.

        ``finding`` is the classified finding's own mapping, so the provenance
        and lineage the escalation is judged on travel with the record rather
        than being summarized into it.
        """
        playbook = _PLAYBOOK[CLASSIFICATION_STOP]
        identifier = str(finding.get("id") or "")
        return cls(
            failure_class=CLASSIFICATION_STOP,
            what_failed=(
                f"finding {identifier!r} was classified needs-karan: "
                f"{finding.get('summary') or 'no summary'}"
            ),
            evidence={
                "expected": "every finding on this head classified blocking, non-blocking, or false-positive",
                "actual": f"finding {identifier!r} classified needs-karan",
                "finding": dict(finding),
            },
            remediation=playbook.remediation,
            escalation=playbook.escalation,
            finding_id=identifier or None,
        )

    def as_dict(self) -> dict[str, Any]:
        """The record itself. This *is* the builder-facing next-instruction block."""
        return {
            "failure_class": self.failure_class,
            "finding_id": self.finding_id,
            "what_failed": self.what_failed,
            "evidence": dict(self.evidence),
            "remediation": list(self.remediation),
            "escalation": self.escalation,
        }


__all__ = [
    "CLASSIFICATION_STOP",
    "FAILURE_CLASSES",
    "GATE_FAILURE",
    "AmbiguousPush",
    "BuilderRefusal",
    "CommandContractError",
    "ConfigError",
    "EnvironmentEvidenceError",
    "EvidencePacketError",
    "FailClosed",
    "FailureRecord",
    "GitHubError",
    "HumanFeedbackPresent",
    "LaneFailure",
    "LockContention",
    "MalformedVerdict",
    "PrProverError",
    "ReadbackMismatch",
    "ReviewerRelayError",
    "ScopeContamination",
    "StaleHead",
    "StateError",
    "WorktreeError",
]
