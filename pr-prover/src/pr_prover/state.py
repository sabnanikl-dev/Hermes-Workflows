"""One local JSON state file and one run-exists lockfile.

The state file holds a single attempt integer, the immutable GitHub ids of the
artifacts this run proved it published together with what each held when that
was proved, and the minimum else needed to keep the attempt cap honest across
process restarts. It is deliberately small and strict: an unknown key, an
out-of-range attempt, a repeated artifact id, an artifact missing its
publication evidence, or a mismatched PR is unexpected state, and unexpected
state stops the run.

The artifact records are here rather than in memory for the same reason the
attempt counter is: they have to survive both a new head and a restarted
process. They are the run's own published evidence, and the alternative —
recognising a lane's artifact by its author, signature, role line and head — is
a predicate anybody sharing the publishing login can satisfy on purpose. The
stored evidence digest is what keeps that recognition honest afterwards: a
retained artifact whose body or review state has since been edited no longer
matches it, so it stops being recognised instead of staying excluded forever.

The lock is a plain ``O_EXCL`` create. There is no PID inspection,
proof-of-death, or takeover path: if the lock exists, this run stops and asks.
Acquiring it is fail-closed end to end — parent creation, the create itself,
and initializing the file's contents all reach the caller as prover errors, so
an unusable lock path is reported as ``needs-karan`` rather than escaping as a
raw filesystem traceback.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import LockContention, StateError
from .redaction import evidence as redact_evidence

SCHEMA_VERSION = 1
MAX_ATTEMPTS = 2
OUTCOMES = ("merge-ready", "blocked", "needs-karan")
_ALLOWED_KEYS = frozenset(
    {
        "schema_version",
        "repo",
        "pr",
        "attempt",
        "head",
        "corrective_rerun_attempts",
        "outcome",
        "verified_artifacts",
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
    # GitHub's own id for each artifact this run proved it published, paired with
    # a digest of the evidence readback verified for it, in the order they were
    # verified. They are kept here rather than in memory because they have to
    # outlive the head they were published for: a second cycle classifies a new
    # head, and the reviewer artifacts and fix comment from the first cycle are
    # still this run's own evidence rather than human feedback. The digest rides
    # along because a published artifact stays editable — see
    # :func:`~pr_prover.feedback.publication_evidence` — so what has to survive a
    # restart is not just which posts were this run's, but what they were when
    # that was established.
    verified_artifacts: tuple[tuple[str, str], ...] = ()
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

        artifacts = raw.get("verified_artifacts", [])
        if not isinstance(artifacts, list):
            raise StateError(
                "state file verified_artifacts is not a list",
                evidence={"state_file": str(path)},
            )
        verified: list[tuple[str, str]] = []
        seen: set[str] = set()
        for value in artifacts:
            if not isinstance(value, dict) or set(value) != {"id", "evidence"}:
                raise StateError(
                    "state file verified_artifacts holds an entry that is not an "
                    "id/evidence pair",
                    evidence={"state_file": str(path)},
                )
            identifier = value["id"]
            attested = value["evidence"]
            if not isinstance(identifier, str) or not identifier.strip():
                raise StateError(
                    "state file verified_artifacts holds a non-identifier value",
                    evidence={"state_file": str(path)},
                )
            if not isinstance(attested, str) or not attested.strip():
                raise StateError(
                    "state file verified_artifacts holds an artifact without its "
                    "publication evidence",
                    evidence={"state_file": str(path), "artifact": identifier},
                )
            if identifier in seen:
                raise StateError(
                    "state file records a repeated verified artifact id",
                    evidence={"state_file": str(path), "artifact": identifier},
                )
            seen.add(identifier)
            verified.append((identifier, attested))

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
            verified_artifacts=tuple(verified),
        )

    def save(self) -> None:
        """Write the state file atomically, or fail closed with the reason.

        This file is how the attempt cap survives a restart, so a directory that
        is really a file, a read-only parent, a full disk, or a replacement that
        cannot complete is unexpected state — not an exception to let escape. It
        reaches the caller as :class:`StateError`, which is what turns it into
        the documented needs-Karan report with evidence instead of a traceback.
        """
        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "repo": self.repo,
            "pr": self.pr,
            "attempt": self.attempt,
            "head": self.head,
            "corrective_rerun_attempts": list(self.corrective_rerun_attempts),
            "outcome": self.outcome,
            "verified_artifacts": [
                {"id": identifier, "evidence": attested}
                for identifier, attested in self.verified_artifacts
            ],
        }
        temporary = self.path.with_name(self.path.name + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            os.replace(temporary, self.path)
        except OSError as exc:
            _discard(temporary)
            raise StateError(
                f"could not persist the run state file: {exc}",
                evidence={
                    "state_file": str(self.path),
                    "temp_file": str(temporary),
                    "error": type(exc).__name__,
                    "attempt": self.attempt,
                    "outcome": self.outcome,
                },
            ) from exc

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

    def remember_artifact(self, identifier: str, evidence: str) -> bool:
        """Retain one immutable GitHub id, and what it held when it was proved.

        Returns whether the id was new, so the caller only journals a retention
        that actually happened. Retention is append-only and never removes an id:
        an artifact this run published on an earlier head stays this run's own
        evidence after the head moves, which is exactly the case where rebuilding
        ownership from body shape would hand a lane's own artifact back to the
        feedback seam as human feedback.

        ``evidence`` is :func:`~pr_prover.feedback.publication_evidence` for the
        artifact readback verified. It is retained rather than recomputed later
        because recomputing it from the post as it stands now would prove only
        that the post equals itself, which is the whole hole this closes.
        """
        if not identifier or not identifier.strip():
            raise StateError(
                "a verified artifact must carry GitHub's own identifier",
                evidence={"artifact": identifier},
            )
        if not evidence or not evidence.strip():
            raise StateError(
                "a verified artifact must carry the evidence proved at publication",
                evidence={"artifact": identifier},
            )
        if any(identifier == known for known, _ in self.verified_artifacts):
            return False
        self.verified_artifacts = self.verified_artifacts + ((identifier, evidence),)
        return True

    def record(self, event: str) -> None:
        self.events.append(event)


def _is_full_sha(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdef" for character in value)


def _discard(path: Path) -> None:
    """Drop a half-written temporary. Best effort: the real failure is the news."""
    try:
        path.unlink()
    except OSError:
        pass


def _close_descriptor(handle: int) -> None:
    """Release a descriptor that could not be wrapped in a stream."""
    try:
        os.close(handle)
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
        """Acquire the lock, or fail closed with a reason the public loop can report.

        Every step here can fail on a real filesystem — a parent that is a
        regular file, a read-only directory, a full disk, a descriptor that
        cannot be wrapped, a write or a close that does not complete — and none
        of those may escape as a raw ``OSError``. ``ProverLoop.run()`` translates
        prover errors only, so an untranslated one would bypass the sanitized
        report entirely and surface a traceback before any inspection began.

        If initialization fails after the ``O_EXCL`` create won, this run owns a
        lockfile that no run holds. It is removed here so the next run is not
        blocked by a lock nobody is using — but the initialization failure stays
        the reason, and a cleanup that also fails is recorded as evidence
        alongside it rather than replacing it.
        """
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StateError(
                f"could not create the run lockfile's parent directory: {exc}",
                evidence={
                    "lock_file": str(self.path),
                    "lock_parent": str(self.path.parent),
                    "error": type(exc).__name__,
                    "stage": "parent",
                },
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
                f"could not create the lockfile: {exc}",
                evidence={
                    "lock_file": str(self.path),
                    "error": type(exc).__name__,
                    "stage": "create",
                },
            ) from exc
        try:
            stream = os.fdopen(handle, "w", encoding="utf-8")
        except OSError as exc:
            _close_descriptor(handle)
            raise self._initialization_failed(exc, stage="open")
        try:
            with stream:
                json.dump({"repo": self.repo, "pr": self.pr}, stream, sort_keys=True)
                stream.write("\n")
                stream.flush()
        except (OSError, ValueError, TypeError) as exc:
            raise self._initialization_failed(exc, stage="write")
        self._held = True
        return self

    def _initialization_failed(self, exc: BaseException, *, stage: str) -> StateError:
        """Turn a failed lock initialization into the error the loop reports.

        The partial lock this acquisition created is removed first, because a
        lockfile with no run behind it would stop every later run for a reason
        that no longer exists. Whether that removal worked is evidence; the
        initialization failure remains the primary reason either way.
        """
        evidence: dict[str, Any] = {
            "lock_file": str(self.path),
            "error": type(exc).__name__,
            "stage": stage,
            "partial_lock_cleanup": self._remove_partial_lock(),
            "resolution": (
                "confirm no other run is active, then check the lockfile's directory "
                "is writable before starting another run"
            ),
        }
        return StateError(
            f"could not initialize the run lockfile: {exc}", evidence=evidence
        )

    def _remove_partial_lock(self) -> str:
        """Best-effort removal of a lock created by a failed acquisition."""
        try:
            self.path.unlink()
        except FileNotFoundError:
            return "already absent"
        except OSError as exc:
            return f"failed: {type(exc).__name__}"
        return "removed"

    def __exit__(self, exc_type: object = None, *_rest: object) -> None:
        if not self._held:
            return
        self._held = False
        try:
            self.path.unlink()
        except FileNotFoundError:
            return
        except OSError as exc:
            if exc_type is not None:
                # Something is already failing closed and that reason is the one
                # worth keeping; a lock this run could not release is reported
                # by the next run refusing to start.
                return
            raise StateError(
                f"could not release the run lockfile: {exc}",
                evidence={
                    "lock_file": str(self.path),
                    "error": type(exc).__name__,
                    "resolution": (
                        "confirm no other run is active, then remove the lockfile by hand"
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


__all__ = ["MAX_ATTEMPTS", "OUTCOMES", "SCHEMA_VERSION", "RunLock", "RunState"]
