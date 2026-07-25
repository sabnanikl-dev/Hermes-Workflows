"""One local JSON state file and one run-exists lockfile.

The state file holds a single attempt integer plus the minimum needed to keep
the attempt cap honest across process restarts. It is deliberately small and
strict: an unknown key, an out-of-range attempt, or a mismatched PR is
unexpected state, and unexpected state stops the run.

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

SCHEMA_VERSION = 1
MAX_ATTEMPTS = 2
OUTCOMES = ("merge-ready", "blocked", "needs-karan")
_ALLOWED_KEYS = frozenset(
    {"schema_version", "repo", "pr", "attempt", "head", "corrective_rerun_attempts", "outcome"}
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
        )

    def save(self) -> None:
        """Write the state file atomically."""
        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "repo": self.repo,
            "pr": self.pr,
            "attempt": self.attempt,
            "head": self.head,
            "corrective_rerun_attempts": list(self.corrective_rerun_attempts),
            "outcome": self.outcome,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.path)

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

    def record(self, event: str) -> None:
        self.events.append(event)


def _is_full_sha(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdef" for character in value)


class RunLock:
    """A run-exists lockfile. Contention stops the run; it never takes over."""

    def __init__(self, path: Path, *, repo: str, pr: int) -> None:
        self.path = Path(path)
        self.repo = repo
        self.pr = pr
        self._held = False

    def __enter__(self) -> RunLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
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

    def _peek(self) -> str:
        """Read the existing lock for evidence only; it is never used to decide."""
        try:
            return self.path.read_text(encoding="utf-8").strip()[:200]
        except OSError:
            return "<unreadable>"


__all__ = ["MAX_ATTEMPTS", "OUTCOMES", "SCHEMA_VERSION", "RunLock", "RunState"]
