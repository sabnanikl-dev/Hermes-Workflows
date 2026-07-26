"""One local JSON state file and one run-exists lockfile.

The state file holds a single attempt integer plus the minimum needed to keep
the attempt cap honest — and the builder verification owed — across process
restarts. It is deliberately small and strict: an unknown key, an out-of-range
attempt, an unknown phase, or a mismatched PR is unexpected state, and
unexpected state stops the run.

Two of those keys exist only so a *crash* cannot be laundered into a clean
result. A fix attempt is not finished when the builder exits: the push must be
bound to one new head and the signed fix comment must be read back. ``phase``
and ``attempt_head`` are written **before** the builder is invoked and cleared
only after that verification passes, so a run interrupted anywhere in between
restarts holding explicit proof that it owes work — and stops rather than
re-inspecting its way to a head whose push nobody ever verified. That is also
why the schema version moved: a journal written before those keys existed
cannot say whether it owes verification, so it is refused rather than trusted.

Persistence itself fails closed. Every filesystem step of :meth:`RunState.save`
— creating the parent, writing the temporary file, replacing the real one — is
translated into :class:`~pr_prover.errors.StateError`, because a raw ``OSError``
escaping the loop would break the one promise the public entry point makes:
that an expected failure mode becomes ``needs-karan`` rather than a traceback.

The lock is a plain ``O_EXCL`` create. There is no PID inspection,
proof-of-death, or takeover path: if the lock exists, this run stops and asks.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import LockContention, StateError
from .redaction import evidence as redact_evidence

SCHEMA_VERSION = 2
MAX_ATTEMPTS = 2
OUTCOMES = ("merge-ready", "blocked", "needs-karan")
# The two phases of a run. ``attempt-in-flight`` means a builder was invoked (or
# was about to be) and the push/comment verification for that attempt has not
# completed; anything else about that attempt is unknown until a human looks.
PHASE_IDLE = "idle"
PHASE_ATTEMPT_IN_FLIGHT = "attempt-in-flight"
PHASES = (PHASE_IDLE, PHASE_ATTEMPT_IN_FLIGHT)
_ALLOWED_KEYS = frozenset(
    {
        "schema_version",
        "repo",
        "pr",
        "attempt",
        "head",
        "corrective_rerun_attempts",
        "outcome",
        "phase",
        "attempt_head",
    }
)


@dataclass
class RunState:
    """The whole durable local journal for one PR run."""

    repo: str
    pr: int
    path: Path
    attempt: int = 0
    head: str | None = None
    corrective_rerun_attempts: tuple[int, ...] = ()
    outcome: str | None = None
    phase: str = PHASE_IDLE
    attempt_head: str | None = None
    events: list[str] = field(default_factory=list, repr=False, compare=False)

    # -- persistence ------------------------------------------------------
    @classmethod
    def load(cls, path: Path, *, repo: str, pr: int) -> RunState:
        """Load existing state, or start a fresh run at attempt 0."""
        path = Path(path)
        if not path.exists():
            return cls(repo=repo, pr=pr, path=path)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StateError(
                f"state file is unreadable: {exc}", evidence={"state_file": str(path)}
            ) from exc
        if not isinstance(raw, dict):
            raise StateError("state file is not a JSON object", evidence={"state_file": str(path)})
        unknown = sorted(set(raw) - _ALLOWED_KEYS)
        if unknown:
            raise StateError(
                "state file has unknown keys",
                evidence={"state_file": str(path), "unknown_keys": unknown},
            )
        if raw.get("schema_version") != SCHEMA_VERSION:
            raise StateError(
                "state file schema_version is not supported",
                evidence={
                    "state_file": str(path),
                    "found": raw.get("schema_version"),
                    "expected": SCHEMA_VERSION,
                },
            )
        if raw.get("repo") != repo or raw.get("pr") != pr:
            raise StateError(
                "state file belongs to a different repo/PR",
                evidence={
                    "state_file": str(path),
                    "found": f"{raw.get('repo')}#{raw.get('pr')}",
                    "expected": f"{repo}#{pr}",
                },
            )

        attempt = raw.get("attempt")
        if not isinstance(attempt, int) or isinstance(attempt, bool) or not 0 <= attempt <= MAX_ATTEMPTS:
            raise StateError(
                "state file attempt is not an integer within the attempt cap",
                evidence={"state_file": str(path), "attempt": attempt, "max_attempts": MAX_ATTEMPTS},
            )

        head = raw.get("head")
        if head is not None and not (isinstance(head, str) and _is_full_sha(head)):
            raise StateError(
                "state file head is not a full 40-hex SHA",
                evidence={"state_file": str(path), "head": head},
            )

        reruns = raw.get("corrective_rerun_attempts", [])
        if not isinstance(reruns, list):
            raise StateError(
                "state file corrective_rerun_attempts is not a list",
                evidence={"state_file": str(path)},
            )
        normalized: list[int] = []
        for value in reruns:
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_ATTEMPTS:
                raise StateError(
                    "state file corrective_rerun_attempts holds an out-of-range attempt",
                    evidence={"state_file": str(path), "value": value},
                )
            if value in normalized:
                raise StateError(
                    "state file records a repeated corrective rerun",
                    evidence={"state_file": str(path), "attempt": value},
                )
            normalized.append(value)
        if any(value > attempt for value in normalized):
            raise StateError(
                "state file records a corrective rerun for an attempt that never opened",
                evidence={"state_file": str(path), "attempt": attempt, "reruns": normalized},
            )

        phase = raw.get("phase", PHASE_IDLE)
        if phase not in PHASES:
            raise StateError(
                "state file phase is not a known phase",
                evidence={"state_file": str(path), "phase": phase, "known_phases": list(PHASES)},
            )
        attempt_head = raw.get("attempt_head")
        if attempt_head is not None and not (
            isinstance(attempt_head, str) and _is_full_sha(attempt_head)
        ):
            raise StateError(
                "state file attempt_head is not a full 40-hex SHA",
                evidence={"state_file": str(path), "attempt_head": attempt_head},
            )
        # The phase and the head it is bound to only mean something together: an
        # in-flight attempt with no head names no verification, and a head with
        # no in-flight attempt claims verification nobody owes.
        if phase == PHASE_ATTEMPT_IN_FLIGHT and (attempt < 1 or attempt_head is None):
            raise StateError(
                "state file records an in-flight attempt without an attempt number and head",
                evidence={
                    "state_file": str(path),
                    "phase": phase,
                    "attempt": attempt,
                    "attempt_head": attempt_head,
                },
            )
        if phase == PHASE_IDLE and attempt_head is not None:
            raise StateError(
                "state file records an attempt head while no attempt is in flight",
                evidence={"state_file": str(path), "phase": phase, "attempt_head": attempt_head},
            )

        outcome = raw.get("outcome")
        if outcome is not None and outcome not in OUTCOMES:
            raise StateError(
                "state file outcome is not a known outcome",
                evidence={"state_file": str(path), "outcome": outcome},
            )
        if outcome is not None:
            raise StateError(
                "state file records a finished run; review it and reset before starting another",
                evidence={"state_file": str(path), "outcome": outcome, "attempt": attempt},
            )

        return cls(
            repo=repo,
            pr=pr,
            path=path,
            attempt=attempt,
            head=head,
            corrective_rerun_attempts=tuple(sorted(normalized)),
            outcome=None,
            phase=phase,
            attempt_head=attempt_head,
        )

    def save(self) -> None:
        """Write the state file atomically, or fail closed with the stage that broke.

        Each filesystem step is translated into :class:`StateError` rather than
        allowed to escape as an ``OSError`` subclass: the caller's contract is
        that an expected failure becomes ``needs-karan`` with evidence, and a
        bare ``FileExistsError`` from an unusable ``state_file`` path is exactly
        that kind of expected failure. The temporary file is discarded when the
        replace fails, and that discard can never mask why the replace failed.
        """
        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "repo": self.repo,
            "pr": self.pr,
            "attempt": self.attempt,
            "head": self.head,
            "corrective_rerun_attempts": list(self.corrective_rerun_attempts),
            "outcome": self.outcome,
            "phase": self.phase,
            "attempt_head": self.attempt_head,
        }
        body = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        temporary = self.path.with_name(self.path.name + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise self._unsaveable(exc, stage="parent-directory") from exc
        try:
            temporary.write_text(body, encoding="utf-8")
        except OSError as exc:
            raise self._unsaveable(exc, stage="temporary-write") from exc
        try:
            os.replace(temporary, self.path)
        except OSError as exc:
            _discard(temporary)
            raise self._unsaveable(exc, stage="replace") from exc

    def _unsaveable(self, exc: OSError, *, stage: str) -> StateError:
        return StateError(
            f"the run state could not be saved: {redact_evidence(str(exc), limit=300)}",
            evidence={"state_file": str(self.path), "stage": stage},
        )

    # -- invariants -------------------------------------------------------
    @property
    def attempts_remaining(self) -> int:
        return MAX_ATTEMPTS - self.attempt

    def begin_attempt(self) -> int:
        """Open the next fix attempt. Attempt 3 is structurally unreachable."""
        if self.attempt >= MAX_ATTEMPTS:
            raise StateError(
                "attempt cap reached; a third fix attempt cannot be opened",
                evidence={"attempt": self.attempt, "max_attempts": MAX_ATTEMPTS},
            )
        self.attempt += 1
        return self.attempt

    @property
    def verification_pending(self) -> bool:
        """True while an attempt's push and fix-comment readback are still owed."""
        return self.phase == PHASE_ATTEMPT_IN_FLIGHT

    def begin_pending_verification(self, head: str) -> None:
        """Record, before the builder runs, that this attempt owes verification.

        Written first and cleared last on purpose: an interruption at any point
        in between leaves the phase set, which is what a restart reads to know
        that a push it never checked may already exist.
        """
        if self.attempt < 1:
            raise StateError(
                "pending verification requires an already-open attempt",
                evidence={"attempt": self.attempt},
            )
        if self.verification_pending:
            raise StateError(
                "an attempt's verification is already pending",
                evidence={"attempt": self.attempt, "attempt_head": self.attempt_head},
            )
        if not (isinstance(head, str) and _is_full_sha(head)):
            raise StateError(
                "pending verification requires the exact pre-attempt head",
                evidence={"attempt": self.attempt, "head": head},
            )
        self.phase = PHASE_ATTEMPT_IN_FLIGHT
        self.attempt_head = head

    def complete_pending_verification(self) -> None:
        """Clear the phase only once the push and the fix comment were verified."""
        if not self.verification_pending:
            raise StateError(
                "no attempt verification is pending",
                evidence={"attempt": self.attempt, "phase": self.phase},
            )
        self.phase = PHASE_IDLE
        self.attempt_head = None

    def corrective_rerun_available(self) -> bool:
        return self.attempt >= 1 and self.attempt not in self.corrective_rerun_attempts

    def use_corrective_rerun(self) -> None:
        """Consume this attempt's single, non-repeatable corrective builder rerun."""
        if self.attempt < 1:
            raise StateError(
                "a corrective rerun requires an already-open attempt",
                evidence={"attempt": self.attempt},
            )
        if self.attempt in self.corrective_rerun_attempts:
            raise StateError(
                "this attempt already used its corrective rerun",
                evidence={"attempt": self.attempt},
            )
        self.corrective_rerun_attempts = tuple(sorted(self.corrective_rerun_attempts + (self.attempt,)))

    def record(self, event: str) -> None:
        self.events.append(event)


def _is_full_sha(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdef" for character in value)


def _discard(path: Path) -> None:
    """Best-effort removal of a temporary file, never at the cost of the reason.

    This only ever runs while a more informative failure is on its way up, so a
    cleanup that fails too is swallowed rather than allowed to replace it.
    """
    try:
        path.unlink()
    except OSError:
        pass


class RunLock:
    """A run-exists lockfile. Contention stops the run; it never takes over."""

    def __init__(self, path: Path, *, repo: str, pr: int) -> None:
        self.path = Path(path)
        self.repo = repo
        self.pr = pr
        self._held = False

    def __enter__(self) -> RunLock:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise LockContention(
                f"could not create the lockfile directory: {redact_evidence(str(exc), limit=300)}",
                evidence={"lock_file": str(self.path)},
            ) from exc
        try:
            handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise LockContention(
                "another pr-prover run holds the lockfile",
                evidence={
                    "lock_file": str(self.path),
                    "existing_lock": self._peek(),
                    "resolution": (
                        "confirm no other run is active, then remove the lockfile by hand; "
                        "this loop never takes a lock over"
                    ),
                },
            ) from exc
        except OSError as exc:
            raise LockContention(
                f"could not create the lockfile: {exc}", evidence={"lock_file": str(self.path)}
            ) from exc
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump({"repo": self.repo, "pr": self.pr}, stream, sort_keys=True)
            stream.write("\n")
        self._held = True
        return self

    def __exit__(self, *_exc: object) -> None:
        if not self._held:
            return
        self._held = False
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            # A lock that cannot be released is a fail-closed condition of its
            # own — the next run would contend with a lock nobody holds — but it
            # never displaces a failure already on its way out of the body.
            if _exc and _exc[0] is not None:
                return
            raise LockContention(
                f"the lockfile could not be released: {redact_evidence(str(exc), limit=300)}",
                evidence={
                    "lock_file": str(self.path),
                    "resolution": (
                        "remove the lockfile by hand once no run is active, or use "
                        "`pr-prover reset --force`"
                    ),
                },
            ) from exc

    def _peek(self) -> str:
        """Read the existing lock for evidence only; it is never used to decide.

        A lockfile this run did not write is untrusted content of unknown
        origin — it may have been hand-edited or clobbered by an unrelated tool
        — so it is scrubbed here rather than attached raw.
        """
        try:
            raw = self.path.read_text(encoding="utf-8").strip()
        except OSError:
            return "<unreadable>"
        return redact_evidence(raw, limit=200)


__all__ = [
    "MAX_ATTEMPTS",
    "OUTCOMES",
    "PHASES",
    "PHASE_ATTEMPT_IN_FLIGHT",
    "PHASE_IDLE",
    "SCHEMA_VERSION",
    "RunLock",
    "RunState",
]
