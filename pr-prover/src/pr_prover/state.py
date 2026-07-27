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

That refusal only works if the version is not the only thing checked. A journal
must carry the *complete* saved key set to be read at all — no key is defaulted
— because an older journal whose version field is edited forward is otherwise
indistinguishable from a current one that genuinely owes nothing. The same rule
rejects the attempt/phase/head combinations this writer cannot produce: an
opened attempt with no inspected head, an in-flight phase without a full
attempt head, and an in-flight attempt bound to a different head than the run.
There is no migration path; an incomplete journal is reset, not repaired.

``classification`` is the third key that exists for something a restart cannot
reconstruct. The four buckets are written with the full provenance and
classification lineage each finding was created with, so an escalation read
after a crash still says who found what, where, on which head, and how it was
categorized — rather than a bare list of ids nobody can act on. It is held to
the same strictness as the rest: a stored finding whose provenance is
incomplete, whose bucket disagrees with its own category, or whose head is not
the head the run is bound to is unexpected state, because none of those is a
journal this writer can produce. And because a finding is evidence *for one
exact head*, binding the run to a new head drops it rather than carrying it
forward — the same invalidate-on-push rule the loop applies to every verdict.

``verified_artifacts`` is the fourth, and it is deliberately the one key a head
change does *not* drop. It maps GitHub's own id for each artifact this run
watched appear and verified as its own lanes' publications — reviewer artifacts
and builder fix comments — to
:func:`~pr_prover.feedback.publication_evidence` for that artifact as readback
found it. Ownership is a fact about a specific id this run caused, established
at the only moment it is knowable: between the snapshot taken before a lane
launched and the read taken after it. A second fix cycle still has to recognise
what the first cycle published, and rediscovering that from body shape is
impossible, because a signature, a role line, and a canonical head declaration
all become copyable the moment a real artifact is posted.

The paired evidence answers the question an id alone cannot: publication is not
the last thing that can happen to a post. Comments and review bodies stay
editable, and the account that can edit a verified lane artifact is the same
shared account a human types into — so "this run published id X" must not harden
into "id X can never be feedback again". An artifact nobody touched stays owned;
one whose body or review state changed no longer matches what was proven, and
goes back to being ordinary feedback. Every other post on the PR stays what it
already was: feedback — which is where ownership's job ends and
:mod:`pr_prover.feedback` takes over, clearing an item only on native
resolution or an explicit acknowledgement, and otherwise leaving it unresolved.

Persistence itself fails closed. Every filesystem step of :meth:`RunState.save`
— creating the parent, writing the temporary file, replacing the real one — is
translated into :class:`~pr_prover.errors.StateError`, because a raw ``OSError``
escaping the loop would break the one promise the public entry point makes:
that an expected failure mode becomes ``needs-karan`` rather than a traceback.

The lock is a plain ``O_EXCL`` create. There is no PID inspection,
proof-of-death, or takeover path: if the lock exists, this run stops and asks.
Acquiring it is a single transaction — create, open, write, flush, close — that
either ends with the lock held or leaves nothing behind at all, because a
half-written lockfile no run holds would stop every later run for a reason that
never existed.

Deleting it is the same question in reverse, and a pathname is not an answer to
it. A lock path that is removed — by ``reset --force``, say — and then acquired
again names a *different* inode, so an older owner that unlinks by pathname
alone deletes the newer owner's lock and two runs proceed at once. So each
acquisition keeps the identity of the inode its own ``O_EXCL`` create produced,
read from the descriptor it still owns before ``fdopen`` can take it over, and
one ownership-aware deletion serves both failed-acquisition cleanup and ordinary
release: the pathname is removed only while it still resolves to *that* inode,
and a replacement is left to the run that owns it.

Checking the identity and unlinking it are two syscalls, so they are held
together by a short exclusive ``flock`` on the lock's parent directory — the
same guard every acquisition takes across its create-and-identify step. That is
the whole cross-process protocol: a conforming acquisition cannot publish in the
gap between another run's identity check and its unlink, because publishing
requires the guard that the deleter is holding. Out-of-band removal of a lock
path while a run is live remains unsupported rather than defended against.

What cleanup actually achieved is then reported rather than assumed. Removal,
an already-absent path, a preserved replacement, and a failed unlink are four
different outcomes, and the last two mean a lockfile is still on disk; saying
"removed" for any of them sends the operator looking for a file that is either
someone else's or still exactly where it was.
"""
from __future__ import annotations

import fcntl
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import LockContention, StateError
from .findings import Classification
from .redaction import evidence as redact_evidence

# Bumped to 5 when ``verified_artifacts`` stopped being a bare id list. A v4
# journal records ids with no publication evidence beside them, and reading one
# under v5 rules would have to invent that evidence — which is exactly the
# "retained id can never be feedback again" behaviour the pairing exists to end.
SCHEMA_VERSION = 5
MAX_ATTEMPTS = 2
OUTCOMES = ("merge-ready", "blocked", "needs-karan")
# The two phases of a run. ``attempt-in-flight`` means a builder was invoked (or
# was about to be) and the push/comment verification for that attempt has not
# completed; anything else about that attempt is unknown until a human looks.
PHASE_IDLE = "idle"
PHASE_ATTEMPT_IN_FLIGHT = "attempt-in-flight"
PHASES = (PHASE_IDLE, PHASE_ATTEMPT_IN_FLIGHT)
# What an ownership-aware lock deletion actually achieved. Only the first means
# no lockfile is left at the path; the last two mean one is, for two different
# reasons, and neither may be reported as a removal.
CLEANUP_REMOVED = "removed"
CLEANUP_ALREADY_ABSENT = "already-absent"
CLEANUP_REPLACEMENT_PRESERVED = "replacement-preserved"
CLEANUP_FAILED = "cleanup-failed"
CLEANUP_DISPOSITIONS = (
    CLEANUP_REMOVED,
    CLEANUP_ALREADY_ABSENT,
    CLEANUP_REPLACEMENT_PRESERVED,
    CLEANUP_FAILED,
)
# The operator-facing half of the same four outcomes. A disposition that leaves
# a file on disk has to say so and say what to do about it, because "the partial
# lock from this attempt was removed" is the sentence that used to be printed
# over a lockfile that was still there.
_CLEANUP_RESOLUTIONS = {
    CLEANUP_REMOVED: (
        "the partial lock from this attempt was removed; fix the reason above "
        "and start the run again"
    ),
    CLEANUP_ALREADY_ABSENT: (
        "this attempt's lockfile was already gone, so nothing was removed; fix "
        "the reason above and start the run again"
    ),
    CLEANUP_REPLACEMENT_PRESERVED: (
        "the lockfile at this path belongs to another run and was left "
        "untouched; fix the reason above and start the run again once that run "
        "has finished"
    ),
    CLEANUP_FAILED: (
        "this attempt's lockfile could not be removed, so a partial lock may "
        "remain; once no run is active, remove it by hand or use "
        "`pr-prover reset --force`, then start the run again"
    ),
}
# Exactly the keys :meth:`RunState.save` writes. The set is both the allowed
# keys and the required ones: an object is only a current-schema journal if it
# carries all of them. Defaulting an absent key is what let a journal written
# before the phase contract existed pass as one that satisfies it.
_SAVED_KEYS = frozenset(
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
        "classification",
        "verified_artifacts",
    }
)
# How many run-owned artifact identities one run may retain. A run publishes one
# artifact per reviewer lane per head plus one builder fix comment per attempt,
# so this is far above any real run and still bounds the journal.
MAX_VERIFIED_ARTIFACTS = 64


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
    classification: Classification | None = None
    # GitHub's own id for each artifact this run watched appear and verified as
    # its own lanes' publications, mapped to the publication evidence readback
    # found. Durable because a second fix cycle still has to recognise what the
    # first cycle published: ownership is a fact about a specific id this run
    # proved it caused, not a pattern a later read can rediscover from a body
    # anybody could copy. Unlike the classification, it is *not* dropped when the
    # run rebinds to a new head — an artifact this run published for an earlier
    # head is still not human feedback.
    verified_artifacts: dict[str, str] = field(default_factory=dict)
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
        unknown = sorted(set(raw) - _SAVED_KEYS)
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
        # Claiming schema v2 is a claim to carry the whole v2 contract. Filling
        # an absent key in from a default is how a journal that predates the
        # phase fields — or one whose version was simply edited to 2 — got read
        # as a run owing no verification, which is the interrupted-attempt
        # bypass the version bump existed to close. There is no migration here:
        # an incomplete journal is reset, not repaired.
        missing = sorted(_SAVED_KEYS - set(raw))
        if missing:
            raise StateError(
                "state file does not carry the complete key set for the current schema; "
                "an incomplete journal cannot say whether it owes verification",
                evidence={
                    "state_file": str(path),
                    "missing_keys": missing,
                    "expected": SCHEMA_VERSION,
                    "resolution": (
                        "confirm on the PR whether an interrupted attempt pushed and "
                        "commented, then run `pr-prover reset` before starting another run"
                    ),
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

        head = raw["head"]
        if head is not None and not (isinstance(head, str) and _is_full_sha(head)):
            raise StateError(
                "state file head is not a full 40-hex SHA",
                evidence={"state_file": str(path), "head": head},
            )
        # The head is recorded at inspection, before an attempt can open, so an
        # opened attempt with no head is a shape this writer cannot produce —
        # and one that would leave an attempt free to bind to any later head.
        if attempt >= 1 and head is None:
            raise StateError(
                "state file records an opened attempt with no inspected head",
                evidence={"state_file": str(path), "attempt": attempt, "head": head},
            )

        reruns = raw["corrective_rerun_attempts"]
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

        phase = raw["phase"]
        if phase not in PHASES:
            raise StateError(
                "state file phase is not a known phase",
                evidence={"state_file": str(path), "phase": phase, "known_phases": list(PHASES)},
            )
        attempt_head = raw["attempt_head"]
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
        # An attempt is opened on the head that was just inspected, so the two
        # are the same commit for as long as the attempt is in flight. A journal
        # where they differ has had one of them moved, which is exactly the
        # rebinding the phase contract exists to make impossible.
        if phase == PHASE_ATTEMPT_IN_FLIGHT and attempt_head != head:
            raise StateError(
                "state file records an in-flight attempt on a different head than the run",
                evidence={
                    "state_file": str(path),
                    "phase": phase,
                    "head": head,
                    "attempt_head": attempt_head,
                },
            )

        # The four buckets, with the provenance and lineage each finding was
        # created with. A journal that carries findings carries them completely
        # or not at all: half a provenance record is exactly the escalation
        # nobody can act on, and reconstructing the missing half from what is
        # left is the guess this whole file exists to refuse.
        classification: Classification | None = None
        if raw["classification"] is not None:
            try:
                classification = Classification.from_dict(raw["classification"])
            except StateError as exc:
                raise StateError(
                    f"state file classification is unusable: {exc.message}",
                    evidence={"state_file": str(path), **exc.evidence},
                ) from exc
            if head is None:
                raise StateError(
                    "state file records findings without an inspected head to bind them to",
                    evidence={"state_file": str(path)},
                )
            off_head = sorted(_finding_heads(classification) - {head})
            if off_head:
                raise StateError(
                    "state file records findings produced against a different head than the run",
                    evidence={"state_file": str(path), "head": head, "finding_heads": off_head},
                )

        artifacts = raw["verified_artifacts"]
        if not isinstance(artifacts, dict):
            raise StateError(
                "state file verified_artifacts is not an id-to-evidence object",
                evidence={"state_file": str(path)},
            )
        if len(artifacts) > MAX_VERIFIED_ARTIFACTS:
            raise StateError(
                "state file records more run-owned artifacts than a run can publish",
                evidence={
                    "state_file": str(path),
                    "count": len(artifacts),
                    "limit": MAX_VERIFIED_ARTIFACTS,
                },
            )
        owned: dict[str, str] = {}
        for identifier, evidence in artifacts.items():
            if not isinstance(identifier, str) or not identifier or len(identifier) > 200:
                raise StateError(
                    "state file verified_artifacts holds an unusable artifact id",
                    evidence={"state_file": str(path)},
                )
            # An id with no usable publication evidence beside it is an id whose
            # post can no longer be checked against what readback verified. It is
            # refused rather than treated as owned-forever.
            if not isinstance(evidence, str) or not _is_digest(evidence):
                raise StateError(
                    "state file verified_artifacts holds an artifact without usable "
                    "publication evidence",
                    evidence={"state_file": str(path), "artifact_id": identifier},
                )
            owned[identifier] = evidence

        outcome = raw["outcome"]
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
            classification=classification,
            verified_artifacts=owned,
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
            "classification": (
                self.classification.as_dict() if self.classification is not None else None
            ),
            "verified_artifacts": dict(self.verified_artifacts),
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

    def bind_head(self, head: str) -> None:
        """Bind the run to the head just inspected, dropping any earlier head's findings.

        A finding is evidence about one exact commit. Carrying it across a head
        change would let an escalation quote a reviewer about code that is no
        longer on the branch, so rebinding invalidates the recorded
        classification instead of aging it — the same rule the loop applies to
        gates and verdicts after a push.
        """
        if not _is_full_sha(head):
            raise StateError(
                "a run can only bind to a full 40-hex head",
                evidence={"head": head},
            )
        if self.head != head:
            self.classification = None
        self.head = head

    def record_classification(self, classification: Classification) -> None:
        """Record the frozen four buckets for the head this run is bound to."""
        if self.head is None:
            raise StateError(
                "a classification cannot be recorded before a head is inspected",
                evidence={"attempt": self.attempt},
            )
        off_head = sorted(_finding_heads(classification) - {self.head})
        if off_head:
            raise StateError(
                "a classification carries findings produced against a different head",
                evidence={"head": self.head, "finding_heads": off_head},
            )
        self.classification = classification

    def remember_artifact(self, identifier: str, evidence: str) -> bool:
        """Retain one artifact this run proved it published. ``False`` if already held.

        The id is the only part of a published artifact a human sharing the
        publishing account cannot reproduce: a signature, a role line, and a
        canonical head declaration are all copyable the moment a real artifact
        is posted, but an id this run watched appear between a pre-launch
        snapshot and a post-launch read is one this run's own lane caused.

        ``evidence`` is the digest of what readback actually verified that post
        holding. It is stored beside the id because the id alone cannot say
        whether the post is still that post, and a retained id that hardened into
        a permanent exemption is a way for an edited artifact to carry a human
        stop invisibly.
        """
        if not isinstance(identifier, str) or not identifier or len(identifier) > 200:
            raise StateError(
                "a run-owned artifact needs a usable GitHub id",
                evidence={"artifact_id": redact_evidence(str(identifier), limit=200)},
            )
        if not isinstance(evidence, str) or not _is_digest(evidence):
            raise StateError(
                "a run-owned artifact needs the publication evidence readback verified",
                evidence={"artifact_id": redact_evidence(identifier, limit=200)},
            )
        if self.verified_artifacts.get(identifier) == evidence:
            return False
        if (
            identifier not in self.verified_artifacts
            and len(self.verified_artifacts) >= MAX_VERIFIED_ARTIFACTS
        ):
            raise StateError(
                "this run has retained more artifacts than a run can publish",
                evidence={"limit": MAX_VERIFIED_ARTIFACTS},
            )
        self.verified_artifacts = {**self.verified_artifacts, identifier: evidence}
        return True

    def owns_artifact(self, identifier: str) -> bool:
        """Did this run watch that exact artifact id appear and verify it?

        Identity only. Whether the post is *still* what was verified is
        :meth:`~pr_prover.feedback.RunArtifacts.owns`' question, and it needs the
        live post to answer it.
        """
        return bool(identifier) and identifier in self.verified_artifacts

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


def _is_digest(value: str) -> bool:
    """One sha256 hex digest, the only shape publication evidence is written in."""
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _finding_heads(classification: Classification) -> set[str]:
    """Every head any origin of any classified finding was produced against.

    A finding two lanes raised carries both lanes' records, so the head check
    reads all of them: a runner-up origin bound to an older commit is evidence
    about code that may no longer be on the branch, and it must not ride into
    the journal behind a governing claim that is on the right head.
    """
    return {head for item in classification.all() for head in item.heads}


def _close_descriptor(handle: int) -> None:
    """Best-effort close of a raw descriptor, never at the cost of the reason."""
    try:
        os.close(handle)
    except OSError:
        pass


def _close_stream(stream: Any) -> None:
    """Best-effort close of a stream this call owns; a failed close is not the story."""
    try:
        stream.close()
    except OSError:
        pass


def _discard(path: Path) -> None:
    """Best-effort removal of a file this call created, never at the cost of the reason.

    This only ever runs while a more informative failure is on its way up, so a
    cleanup that fails too is swallowed rather than allowed to replace it.
    """
    try:
        path.unlink()
    except OSError:
        pass


def _acquire_guard(directory: Path) -> int:
    """Take the short exclusive guard that serializes publication against deletion.

    The guard is an ``flock`` on the lock's parent directory, which every
    ``RunLock`` already creates and none of them ever removes — so it needs no
    file of its own and leaves nothing behind. It is held across exactly two
    critical sections: the exclusive create plus the identity read that makes
    the new lock *this* run's, and the identity check plus unlink that removes
    it. Because both sides take the same guard, a conforming acquisition cannot
    slip its inode into the pathname between another run's check and its unlink.

    It is never held across the payload write, so an acquisition that stalls
    mid-transaction cannot wedge an unrelated run's release.
    """
    handle = os.open(directory, os.O_RDONLY)
    try:
        fcntl.flock(handle, fcntl.LOCK_EX)
    except OSError:
        _close_descriptor(handle)
        raise
    return handle


def _release_guard(handle: int) -> None:
    """Drop the guard. Closing the descriptor would release it anyway."""
    try:
        fcntl.flock(handle, fcntl.LOCK_UN)
    except OSError:
        pass
    _close_descriptor(handle)


def _remove_identified(path: Path, identity: tuple[int, int] | None) -> tuple[str, OSError | None]:
    """Unlink ``path`` only while it still names ``identity``; report which happened.

    The caller must already hold the guard, because the check and the unlink
    below are the gap this whole mechanism exists to close. ``identity`` is
    ``None`` only for a lock this call created and could not identify, which the
    caller handles while still inside the same guarded region — nothing
    conforming can have replaced it in between.

    Nothing here raises: a failure is a disposition, because the two callers are
    an ordinary release and a cleanup running underneath a more informative
    exception, and neither wants a second traceback more than it wants the truth
    about what is still on disk.
    """
    try:
        found = os.lstat(path)
    except FileNotFoundError:
        return CLEANUP_ALREADY_ABSENT, None
    except OSError as exc:
        return CLEANUP_FAILED, exc
    if identity is not None and (found.st_dev, found.st_ino) != identity:
        # Another run created this one. It is theirs even though this object
        # once created the pathname it sits at.
        return CLEANUP_REPLACEMENT_PRESERVED, None
    try:
        os.unlink(path)
    except FileNotFoundError:
        return CLEANUP_ALREADY_ABSENT, None
    except OSError as exc:
        return CLEANUP_FAILED, exc
    return CLEANUP_REMOVED, None


class RunLock:
    """A run-exists lockfile. Contention stops the run; it never takes over."""

    def __init__(self, path: Path, *, repo: str, pr: int) -> None:
        self.path = Path(path)
        self.repo = repo
        self.pr = pr
        self._held = False
        # The ``(st_dev, st_ino)`` of the inode this object's own ``O_EXCL``
        # create produced. Deletion is answerable only against this, never
        # against the pathname, which any later run may be using by then.
        self._identity: tuple[int, int] | None = None
        # What this object's last cleanup or release actually achieved, for the
        # caller and the report; ``None`` until one has run.
        self.cleanup_disposition: str | None = None

    def __enter__(self) -> RunLock:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise LockContention(
                f"could not create the lockfile directory: {redact_evidence(str(exc), limit=300)}",
                evidence={"lock_file": str(self.path)},
            ) from exc

        # Creating the lock and learning which inode it is are one step as far
        # as any other run is concerned: the guard makes publication and the
        # ownership-checked deletion below mutually exclusive, so no run can
        # publish into the window another run is deciding about.
        try:
            guard = _acquire_guard(self.path.parent)
        except OSError as exc:
            raise LockContention(
                f"could not guard the lockfile directory: {redact_evidence(str(exc), limit=300)}",
                evidence={"lock_file": str(self.path), "stage": "guard"},
            ) from exc
        try:
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
                    f"could not create the lockfile: {redact_evidence(str(exc), limit=300)}",
                    evidence={"lock_file": str(self.path), "stage": "create"},
                ) from exc

            # Read from the descriptor this call still owns, before ``fdopen``
            # can adopt it and before any close: once the descriptor is gone the
            # only handle left on that inode is a pathname, and a pathname is
            # exactly what stops being trustworthy the moment it is removed.
            try:
                created = os.fstat(handle)
            except OSError as exc:
                _close_descriptor(handle)
                # Already inside the guard this deletion needs, so it runs
                # directly rather than through the re-guarding helper.
                disposition, _ = _remove_identified(self.path, None)
                self.cleanup_disposition = disposition
                raise self._uninitialized(exc, stage="identify", disposition=disposition) from exc
            self._identity = (created.st_dev, created.st_ino)
        finally:
            _release_guard(guard)

        # Past this point the lockfile exists *because this call created it*, so
        # every remaining step is one ownership transaction: it either completes
        # and the lock is held, or it fails and leaves nothing behind. Each stage
        # is named so the report says which one broke, and none of them may
        # escape as a raw OSError — `run()` promises an expected failure becomes
        # `needs-karan`, and a half-written lock nobody holds is worse than none,
        # because the next run would contend against a ghost.
        try:
            stream = os.fdopen(handle, "w", encoding="utf-8")
        except OSError as exc:
            # fdopen did not take the descriptor over, so this call still owns it.
            _close_descriptor(handle)
            disposition, _ = self._remove_owned_lock()
            raise self._uninitialized(exc, stage="fdopen", disposition=disposition) from exc

        payload = {"repo": self.repo, "pr": self.pr}
        stages: tuple[tuple[str, Any], ...] = (
            ("payload", lambda: json.dump(payload, stream, sort_keys=True)),
            ("newline", lambda: stream.write("\n")),
            # A buffered write can succeed and still never reach the disk, so
            # the flush and the close are part of acquiring the lock, not
            # afterthoughts left to a context manager's exit.
            ("flush", stream.flush),
            ("close", stream.close),
        )
        for stage, step in stages:
            try:
                step()
            except OSError as exc:
                _close_stream(stream)
                disposition, _ = self._remove_owned_lock()
                raise self._uninitialized(exc, stage=stage, disposition=disposition) from exc

        # Held only now: __exit__ must never try to release a lock that was
        # never fully acquired, and must always release one that was.
        self._held = True
        return self

    def _uninitialized(self, exc: OSError, *, stage: str, disposition: str) -> LockContention:
        """The initialization failure, carrying what cleanup actually achieved.

        The initialization cause is the story and stays the message; the
        disposition is evidence beside it. The two are separate on purpose —
        this used to assert the partial lock "was removed" whether or not the
        unlink had worked, which is the one claim an operator acts on.
        """
        return LockContention(
            f"the lockfile could not be initialized: {redact_evidence(str(exc), limit=300)}",
            evidence={
                "lock_file": str(self.path),
                "stage": stage,
                "cleanup": disposition,
                "resolution": _CLEANUP_RESOLUTIONS[disposition],
            },
        )

    def _remove_owned_lock(self) -> tuple[str, OSError | None]:
        """The one ownership-aware deletion, for failed acquisition and release alike.

        Both callers want the same thing — remove the lockfile *this* acquisition
        created, and nothing else — so both get the same code rather than two
        pathname unlinks that happen to look similar. Under the guard the
        pathname either still resolves to this run's inode, in which case it is
        this run's to delete, or it does not, in which case it is absent or
        belongs to a run that acquired it afterwards and is left alone.

        Records and returns the disposition; it never raises, so a cleanup
        running underneath a live exception cannot displace it.
        """
        try:
            guard = _acquire_guard(self.path.parent)
        except OSError as exc:
            # No guard, no safe deletion. Absence is still answerable and still
            # true, so say that rather than claiming a failure that isn't one.
            if not self.path.exists():
                outcome: tuple[str, OSError | None] = (CLEANUP_ALREADY_ABSENT, None)
            else:
                outcome = (CLEANUP_FAILED, exc)
        else:
            try:
                outcome = _remove_identified(self.path, self._identity)
            finally:
                _release_guard(guard)
        self.cleanup_disposition = outcome[0]
        return outcome

    def __exit__(self, *_exc: object) -> None:
        if not self._held:
            return
        self._held = False
        disposition, failure = self._remove_owned_lock()
        if disposition != CLEANUP_FAILED:
            # Removed, already gone, or replaced by a run that owns it now. None
            # of those is this run's problem, and none of them is a removal this
            # run may claim credit for beyond what was recorded above.
            return
        # A lock that cannot be released is a fail-closed condition of its own —
        # the next run would contend with a lock nobody holds — but it never
        # displaces a failure already on its way out of the body.
        if _exc and _exc[0] is not None:
            return
        detail = f": {redact_evidence(str(failure), limit=300)}" if failure is not None else ""
        raise LockContention(
            f"the lockfile could not be released{detail}",
            evidence={
                "lock_file": str(self.path),
                "cleanup": disposition,
                "resolution": _CLEANUP_RESOLUTIONS[disposition],
            },
        ) from failure

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
    "CLEANUP_ALREADY_ABSENT",
    "CLEANUP_DISPOSITIONS",
    "CLEANUP_FAILED",
    "CLEANUP_REMOVED",
    "CLEANUP_REPLACEMENT_PRESERVED",
    "MAX_ATTEMPTS",
    "MAX_VERIFIED_ARTIFACTS",
    "OUTCOMES",
    "PHASES",
    "PHASE_ATTEMPT_IN_FLIGHT",
    "PHASE_IDLE",
    "SCHEMA_VERSION",
    "RunLock",
    "RunState",
]
