"""The one JSON state file and the one run-exists lockfile."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import _support  # noqa: F401 - inserts the package on sys.path
from pr_prover.errors import LockContention, StateError
from pr_prover.state import (
    MAX_ATTEMPTS,
    PHASE_ATTEMPT_IN_FLIGHT,
    PHASE_IDLE,
    SCHEMA_VERSION,
    RunLock,
    RunState,
)

HEAD = "a" * 40
OTHER_HEAD = "b" * 40
DEV_NULL = Path("/dev/null")


class StateFileHarness(unittest.TestCase):
    """One temp state file, plus the payload writer the strictness tests use."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-state-")
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "state.json"

    def load(self) -> RunState:
        return RunState.load(self.path, repo="example/repo", pr=7)

    def payload(self, **overrides: object) -> dict:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "repo": "example/repo",
            "pr": 7,
            "attempt": 0,
            "head": None,
            "corrective_rerun_attempts": [],
            "outcome": None,
            "phase": PHASE_IDLE,
            "attempt_head": None,
        }
        payload.update(overrides)
        return payload

    def write(self, **overrides: object) -> None:
        self.path.write_text(json.dumps(self.payload(**overrides)), encoding="utf-8")

    def write_without(self, *missing: str, **overrides: object) -> None:
        """Write a schema-v2 object with some saved keys simply absent."""
        payload = self.payload(**overrides)
        for key in missing:
            payload.pop(key)
        self.path.write_text(json.dumps(payload), encoding="utf-8")


class StateFileTests(StateFileHarness):
    def test_a_missing_file_starts_a_fresh_run(self) -> None:
        state = self.load()
        self.assertEqual(state.attempt, 0)
        self.assertIsNone(state.head)
        self.assertEqual(state.corrective_rerun_attempts, ())

    def test_round_trip(self) -> None:
        state = self.load()
        state.begin_attempt()
        state.use_corrective_rerun()
        state.head = HEAD
        state.save()

        reloaded = self.load()
        self.assertEqual(reloaded.attempt, 1)
        self.assertEqual(reloaded.corrective_rerun_attempts, (1,))
        self.assertEqual(reloaded.head, HEAD)

    def test_the_written_file_holds_exactly_one_attempt_integer(self) -> None:
        state = self.load()
        state.begin_attempt()
        state.save()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(payload["attempt"], 1)
        self.assertEqual(
            set(payload),
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
            },
        )

    def test_unknown_keys_are_unexpected_state(self) -> None:
        self.write(hash_journal=["deadbeef"])
        with self.assertRaises(StateError) as caught:
            self.load()
        self.assertEqual(caught.exception.evidence["unknown_keys"], ["hash_journal"])

    def test_a_future_schema_version_is_unexpected_state(self) -> None:
        self.write(schema_version=99)
        with self.assertRaises(StateError):
            self.load()

    def test_an_attempt_above_the_cap_is_unexpected_state(self) -> None:
        self.write(attempt=MAX_ATTEMPTS + 1)
        with self.assertRaises(StateError):
            self.load()

    def test_a_boolean_attempt_is_unexpected_state(self) -> None:
        self.write(attempt=True)
        with self.assertRaises(StateError):
            self.load()

    def test_a_short_head_is_unexpected_state(self) -> None:
        self.write(head="abc1234")
        with self.assertRaises(StateError):
            self.load()

    def test_corrupt_json_is_unexpected_state(self) -> None:
        self.path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(StateError):
            self.load()

    def test_a_rerun_recorded_for_an_unopened_attempt_is_unexpected_state(self) -> None:
        self.write(attempt=1, corrective_rerun_attempts=[2])
        with self.assertRaises(StateError):
            self.load()

    def test_a_repeated_rerun_entry_is_unexpected_state(self) -> None:
        self.write(attempt=2, corrective_rerun_attempts=[1, 1])
        with self.assertRaises(StateError):
            self.load()

    def test_a_finished_run_must_be_reset_before_it_restarts(self) -> None:
        self.write(outcome="merge-ready")
        with self.assertRaises(StateError) as caught:
            self.load()
        self.assertIn("reset", caught.exception.message)


class PendingVerificationTests(StateFileHarness):
    """PAPI88-RESUME-READBACK: the in-flight attempt survives a restart."""

    def test_a_pending_verification_round_trips(self) -> None:
        state = self.load()
        state.begin_attempt()
        state.head = HEAD
        state.begin_pending_verification(HEAD)
        state.save()

        reloaded = self.load()
        self.assertTrue(reloaded.verification_pending)
        self.assertEqual(reloaded.phase, PHASE_ATTEMPT_IN_FLIGHT)
        self.assertEqual(reloaded.attempt_head, HEAD)
        self.assertEqual(reloaded.attempt, 1)

    def test_completing_the_verification_clears_the_phase(self) -> None:
        state = self.load()
        state.begin_attempt()
        # The loop inspects before it opens an attempt, so the head is always
        # recorded by this point; the journal is only loadable when it is.
        state.head = HEAD
        state.begin_pending_verification(HEAD)
        state.complete_pending_verification()
        state.save()

        reloaded = self.load()
        self.assertFalse(reloaded.verification_pending)
        self.assertEqual(reloaded.phase, PHASE_IDLE)
        self.assertIsNone(reloaded.attempt_head)

    def test_pending_verification_requires_an_open_attempt(self) -> None:
        with self.assertRaises(StateError):
            self.load().begin_pending_verification(HEAD)

    def test_pending_verification_requires_a_full_head(self) -> None:
        state = self.load()
        state.begin_attempt()
        with self.assertRaises(StateError):
            state.begin_pending_verification("abc1234")

    def test_a_second_pending_verification_is_unexpected_state(self) -> None:
        state = self.load()
        state.begin_attempt()
        state.begin_pending_verification(HEAD)
        with self.assertRaises(StateError):
            state.begin_pending_verification(OTHER_HEAD)

    def test_completing_a_verification_nobody_owes_is_unexpected_state(self) -> None:
        with self.assertRaises(StateError):
            self.load().complete_pending_verification()

    def test_an_unknown_phase_is_unexpected_state(self) -> None:
        self.write(phase="halfway")
        with self.assertRaises(StateError) as caught:
            self.load()
        self.assertEqual(caught.exception.evidence["phase"], "halfway")

    def test_an_in_flight_phase_without_an_attempt_head_is_unexpected_state(self) -> None:
        self.write(attempt=1, phase=PHASE_ATTEMPT_IN_FLIGHT, attempt_head=None)
        with self.assertRaises(StateError):
            self.load()

    def test_an_in_flight_phase_without_an_open_attempt_is_unexpected_state(self) -> None:
        self.write(attempt=0, phase=PHASE_ATTEMPT_IN_FLIGHT, attempt_head=HEAD)
        with self.assertRaises(StateError):
            self.load()

    def test_an_attempt_head_recorded_while_idle_is_unexpected_state(self) -> None:
        self.write(attempt=1, phase=PHASE_IDLE, attempt_head=HEAD)
        with self.assertRaises(StateError):
            self.load()

    def test_a_short_attempt_head_is_unexpected_state(self) -> None:
        self.write(attempt=1, phase=PHASE_ATTEMPT_IN_FLIGHT, attempt_head="abc1234")
        with self.assertRaises(StateError):
            self.load()


class SchemaContractTests(StateFileHarness):
    """The complete schema-v2 key set is mandatory, not defaulted.

    The reproduced bypass: a journal carrying ``schema_version=2``, ``attempt=1``
    and the old head, but neither ``phase`` nor ``attempt_head``, loaded as a
    run owing nothing. Defaulting the two keys that exist purely to say "this
    attempt still owes verification" hands back exactly the interrupted-attempt
    acceptance the version bump was supposed to end, to anyone who edits a v1
    journal's version field.
    """

    SAVED_KEYS = (
        "schema_version",
        "repo",
        "pr",
        "attempt",
        "head",
        "corrective_rerun_attempts",
        "outcome",
        "phase",
        "attempt_head",
    )

    def test_the_writer_produces_exactly_the_required_key_set(self) -> None:
        """The contract is anchored to what save() actually writes."""
        self.load().save()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(set(payload), set(self.SAVED_KEYS))

    def test_every_saved_key_is_individually_required(self) -> None:
        for key in self.SAVED_KEYS:
            with self.subTest(missing=key):
                self.write_without(key)
                with self.assertRaises(StateError):
                    self.load()

    def test_a_v2_journal_missing_the_phase_keys_is_unexpected_state(self) -> None:
        """The exact reviewer/auditor shape: v2, attempt open, no phase contract."""
        self.write_without("phase", "attempt_head", attempt=1, head=HEAD)
        with self.assertRaises(StateError) as caught:
            self.load()
        self.assertEqual(caught.exception.reason, "unexpected-state")
        self.assertEqual(
            caught.exception.evidence["missing_keys"], ["attempt_head", "phase"]
        )

    def test_a_v2_journal_missing_only_phase_is_unexpected_state(self) -> None:
        self.write_without("phase", attempt=1, head=HEAD)
        with self.assertRaises(StateError) as caught:
            self.load()
        self.assertEqual(caught.exception.evidence["missing_keys"], ["phase"])

    def test_a_v2_journal_missing_only_attempt_head_is_unexpected_state(self) -> None:
        self.write_without("attempt_head", attempt=1, head=HEAD)
        with self.assertRaises(StateError) as caught:
            self.load()
        self.assertEqual(caught.exception.evidence["missing_keys"], ["attempt_head"])

    def test_a_missing_key_is_never_defaulted_into_an_idle_run(self) -> None:
        """The measurement that named the bypass: it must not load at all."""
        self.write_without("phase", "attempt_head", attempt=1, head=HEAD)
        with self.assertRaises(StateError):
            state = self.load()
            self.fail(
                f"a missing-key journal loaded as phase={state.phase} "
                f"attempt_head={state.attempt_head}"
            )

    def test_an_opened_attempt_with_no_recorded_head_is_unexpected_state(self) -> None:
        """The writer records the head before it opens an attempt, so this is impossible."""
        self.write(attempt=1, head=None)
        with self.assertRaises(StateError) as caught:
            self.load()
        self.assertEqual(caught.exception.evidence["attempt"], 1)

    def test_an_in_flight_attempt_head_that_differs_from_the_head_is_unexpected_state(self) -> None:
        self.write(
            attempt=1, head=HEAD, phase=PHASE_ATTEMPT_IN_FLIGHT, attempt_head=OTHER_HEAD
        )
        with self.assertRaises(StateError) as caught:
            self.load()
        self.assertEqual(caught.exception.evidence["attempt_head"], OTHER_HEAD)
        self.assertEqual(caught.exception.evidence["head"], HEAD)

    def test_schema_v1_is_still_refused_with_reset_guidance(self) -> None:
        """Changing a v1 journal's version field must not be a migration path."""
        self.path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "repo": "example/repo",
                    "pr": 7,
                    "attempt": 1,
                    "head": HEAD,
                    "corrective_rerun_attempts": [],
                    "outcome": None,
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaises(StateError) as caught:
            self.load()
        self.assertEqual(caught.exception.evidence["found"], 1)
        self.assertEqual(caught.exception.evidence["expected"], SCHEMA_VERSION)

    def test_the_shapes_the_writer_does_produce_still_load(self) -> None:
        """The positive control, so strictness did not become a refusal to resume."""
        fresh = self.load()
        fresh.save()
        self.assertEqual(self.load().attempt, 0)

        opened = self.load()
        opened.begin_attempt()
        opened.head = HEAD
        opened.save()
        self.assertEqual(self.load().attempt, 1)

        in_flight = self.load()
        in_flight.begin_pending_verification(HEAD)
        in_flight.save()
        reloaded = self.load()
        self.assertTrue(reloaded.verification_pending)
        self.assertEqual(reloaded.attempt_head, HEAD)


class StatePersistenceFailureTests(unittest.TestCase):
    """PAPI88-STATE-FAIL-CLOSED: a filesystem failure is a StateError, not an OSError."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-save-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()

    def state(self, path: Path) -> RunState:
        return RunState(repo="example/repo", pr=7, path=path)

    @unittest.skipUnless(DEV_NULL.exists(), "/dev/null is not available")
    def test_a_parent_that_cannot_be_created_is_a_state_error(self) -> None:
        """The Integration Auditor's probe: /dev/null/state.json escaped as OSError."""
        with self.assertRaises(StateError) as caught:
            self.state(DEV_NULL / "state.json").save()
        self.assertEqual(caught.exception.reason, "unexpected-state")
        self.assertEqual(caught.exception.evidence["stage"], "parent-directory")

    def test_a_temporary_file_that_cannot_be_written_is_a_state_error(self) -> None:
        path = self.tmp / "state.json"
        (self.tmp / "state.json.tmp").mkdir()
        with self.assertRaises(StateError) as caught:
            self.state(path).save()
        self.assertEqual(caught.exception.evidence["stage"], "temporary-write")

    def test_a_replace_that_cannot_complete_is_a_state_error_and_discards_the_temp(self) -> None:
        path = self.tmp / "state.json"
        path.mkdir()
        (path / "occupied").write_text("in the way\n", encoding="utf-8")

        with self.assertRaises(StateError) as caught:
            self.state(path).save()

        self.assertEqual(caught.exception.evidence["stage"], "replace")
        self.assertFalse(
            (self.tmp / "state.json.tmp").exists(),
            "the temporary file must not survive a failed replace",
        )

    def test_a_state_error_never_carries_a_raw_oserror_out(self) -> None:
        for path in (DEV_NULL / "state.json", self.tmp / "nested" / "state.json"):
            with self.subTest(path=str(path)):
                if path.parent == DEV_NULL and not DEV_NULL.exists():
                    continue
                try:
                    self.state(path).save()
                except StateError:
                    pass
                except OSError as exc:  # pragma: no cover - the regression itself
                    self.fail(f"save() raised a raw OSError: {exc!r}")


class AttemptInvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-attempt-")
        self.addCleanup(self._tmp.cleanup)
        self.state = RunState(repo="example/repo", pr=7, path=Path(self._tmp.name) / "state.json")

    def test_the_cap_is_two(self) -> None:
        self.assertEqual(MAX_ATTEMPTS, 2)
        self.assertEqual(self.state.begin_attempt(), 1)
        self.assertEqual(self.state.begin_attempt(), 2)
        with self.assertRaises(StateError):
            self.state.begin_attempt()
        self.assertEqual(self.state.attempt, 2)

    def test_a_corrective_rerun_needs_an_open_attempt(self) -> None:
        with self.assertRaises(StateError):
            self.state.use_corrective_rerun()

    def test_a_corrective_rerun_cannot_repeat_within_an_attempt(self) -> None:
        self.state.begin_attempt()
        self.assertTrue(self.state.corrective_rerun_available())
        self.state.use_corrective_rerun()
        self.assertFalse(self.state.corrective_rerun_available())
        with self.assertRaises(StateError):
            self.state.use_corrective_rerun()

    def test_each_attempt_gets_its_own_corrective_rerun(self) -> None:
        self.state.begin_attempt()
        self.state.use_corrective_rerun()
        self.state.begin_attempt()
        self.assertTrue(self.state.corrective_rerun_available())
        self.state.use_corrective_rerun()
        self.assertEqual(self.state.corrective_rerun_attempts, (1, 2))

    def test_a_corrective_rerun_never_raises_the_attempt_count(self) -> None:
        self.state.begin_attempt()
        self.state.use_corrective_rerun()
        self.assertEqual(self.state.attempt, 1)


class LockTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-lock-")
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "run.lock"

    def test_the_lock_is_created_and_released(self) -> None:
        with RunLock(self.path, repo="example/repo", pr=7):
            self.assertTrue(self.path.exists())
        self.assertFalse(self.path.exists())

    def test_a_second_lock_contends_and_never_takes_over(self) -> None:
        with RunLock(self.path, repo="example/repo", pr=7):
            with self.assertRaises(LockContention) as caught:
                with RunLock(self.path, repo="example/repo", pr=7):
                    self.fail("the second run must not acquire the lock")
            self.assertIn("example/repo", caught.exception.evidence["existing_lock"])
            self.assertTrue(self.path.exists())
        self.assertFalse(self.path.exists())

    def test_a_contending_run_does_not_delete_the_holders_lock(self) -> None:
        self.path.write_text("held elsewhere\n", encoding="utf-8")
        with self.assertRaises(LockContention):
            with RunLock(self.path, repo="example/repo", pr=7):
                pass
        self.assertEqual(self.path.read_text(encoding="utf-8"), "held elsewhere\n")

    def test_the_lock_releases_when_the_body_raises(self) -> None:
        with self.assertRaises(ValueError):
            with RunLock(self.path, repo="example/repo", pr=7):
                raise ValueError("boom")
        self.assertFalse(self.path.exists())

    @unittest.skipUnless(DEV_NULL.exists(), "/dev/null is not available")
    def test_a_lock_directory_that_cannot_be_created_is_lock_contention(self) -> None:
        """PAPI88-STATE-FAIL-CLOSED: an unusable lock path is not a raw OSError."""
        with self.assertRaises(LockContention) as caught:
            with RunLock(DEV_NULL / "run.lock", repo="example/repo", pr=7):
                self.fail("the lock must not be acquired under an unusable path")
        self.assertEqual(caught.exception.reason, "lock-contention")


class _StageBreaker:
    """A text stream that fails deterministically at exactly one write stage.

    It wraps the real stream so the underlying descriptor is still closed by the
    end of the test; only the named stage raises.
    """

    def __init__(self, stream, stage: str, message: str) -> None:
        self._stream = stream
        self._stage = stage
        self._message = message
        self.close_calls = 0

    def write(self, text: str) -> int:
        if self._stage == "newline" and text == "\n":
            raise OSError(self._message)
        return self._stream.write(text)

    def flush(self) -> None:
        if self._stage == "flush":
            raise OSError(self._message)
        self._stream.flush()

    def close(self) -> None:
        self.close_calls += 1
        # Always release the real descriptor, then fail if this is the stage
        # under test, so a "close failed" run still leaks nothing.
        self._stream.close()
        if self._stage == "close":
            raise OSError(self._message)


# Obvious fakes. They exist only to prove the redaction boundary runs; nothing
# here is or ever was a real credential.
FAKE_TOKEN = "ghp_" + "A" * 30
BROKEN_MESSAGE = f"no space left on device while writing GITHUB_TOKEN={FAKE_TOKEN}"


class LockAcquisitionTransactionTests(unittest.TestCase):
    """PAPI88-STATE-FAIL-CLOSED: acquisition is one fail-closed ownership transaction.

    The reproduced defect: exclusive creation succeeded and then ``os.fdopen``,
    the payload write, the newline, the flush, and the close all ran outside any
    error boundary. Each stage escaped ``__enter__`` as a raw ``OSError`` — past
    a ``run()`` that promises not to raise for an expected failure — and left
    behind an empty or partial lockfile that no run holds, so the next run
    contends against nothing.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-lock-txn-")
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "run.lock"

    def lock(self) -> RunLock:
        return RunLock(self.path, repo="example/repo", pr=7)

    def breaking(self, stage: str):
        """Patch ``os.fdopen`` so the acquired stream fails at ``stage``."""
        real = os.fdopen

        def fake(fd, *args, **kwargs):
            return _StageBreaker(real(fd, *args, **kwargs), stage, BROKEN_MESSAGE)

        return patch("pr_prover.state.os.fdopen", fake)

    def acquire_failing(self, stage: str) -> LockContention:
        """Acquire with ``stage`` broken; return the structured failure."""
        lock = self.lock()
        if stage == "payload":
            # Reviewer B's exact reproducer.
            context = patch("pr_prover.state.json.dump", side_effect=OSError(BROKEN_MESSAGE))
        else:
            context = self.breaking(stage)
        with context:
            with self.assertRaises(LockContention) as caught:
                lock.__enter__()
        self.lock_after_failure = lock
        return caught.exception

    def test_every_acquisition_stage_fails_closed_without_stranding_the_lock(self) -> None:
        for stage in ("payload", "newline", "flush", "close"):
            with self.subTest(stage=stage):
                self.setUp()
                failure = self.acquire_failing(stage)

                self.assertEqual(failure.reason, "lock-contention")
                self.assertEqual(failure.evidence["stage"], stage)
                self.assertFalse(
                    self.path.exists(),
                    f"the {stage} failure stranded a lock no run holds",
                )
                self.assertFalse(
                    self.lock_after_failure._held,
                    "a lock is only held once initialization completed",
                )

    def test_no_raw_oserror_escapes_any_acquisition_stage(self) -> None:
        """The regression itself: each stage used to escape as a raw OSError."""
        for stage in ("payload", "newline", "flush", "close"):
            with self.subTest(stage=stage):
                self.setUp()
                try:
                    self.acquire_failing(stage)
                except OSError as exc:  # pragma: no cover - the regression itself
                    self.fail(f"acquisition raised a raw OSError at {stage}: {exc!r}")

    def test_an_fdopen_failure_closes_the_descriptor_it_owned(self) -> None:
        acquired: list[int] = []

        def fake(fd, *args, **kwargs):
            acquired.append(fd)
            raise OSError(BROKEN_MESSAGE)

        lock = self.lock()
        with patch("pr_prover.state.os.fdopen", fake):
            with self.assertRaises(LockContention) as caught:
                lock.__enter__()

        self.assertEqual(caught.exception.evidence["stage"], "fdopen")
        self.assertEqual(len(acquired), 1)
        with self.assertRaises(OSError):
            os.fstat(acquired[0])
        self.assertFalse(self.path.exists())
        self.assertFalse(lock._held)

    def test_the_original_cause_is_preserved_and_sanitized(self) -> None:
        failure = self.acquire_failing("payload")

        self.assertIsInstance(failure.__cause__, OSError)
        self.assertIn("no space left on device", failure.message)
        self.assertIn("<redacted>", failure.message)
        self.assertNotIn(FAKE_TOKEN, failure.message)
        self.assertNotIn(FAKE_TOKEN, json.dumps(failure.as_dict()))

    def test_a_cleanup_failure_never_replaces_the_acquisition_failure(self) -> None:
        real_unlink = Path.unlink

        def refuse(self_path, *args, **kwargs):
            if self_path == self.path:
                raise OSError("cleanup is broken too")
            return real_unlink(self_path, *args, **kwargs)

        lock = self.lock()
        with patch("pr_prover.state.json.dump", side_effect=OSError(BROKEN_MESSAGE)):
            with patch.object(Path, "unlink", refuse):
                with self.assertRaises(LockContention) as caught:
                    lock.__enter__()

        self.assertEqual(caught.exception.evidence["stage"], "payload")
        self.assertIn("no space left on device", caught.exception.message)
        self.assertNotIn("cleanup is broken too", caught.exception.message)
        self.assertFalse(lock._held)

    def test_a_failed_acquisition_leaves_the_path_free_for_the_next_run(self) -> None:
        """The point of unlinking: the next run must not contend with a ghost."""
        self.acquire_failing("payload")
        with self.lock():
            self.assertTrue(self.path.exists())
        self.assertFalse(self.path.exists())

    def test_a_contended_lock_written_by_someone_else_is_never_removed(self) -> None:
        """Cleanup is scoped to the lock this acquisition created."""
        self.path.write_text("held elsewhere\n", encoding="utf-8")
        with patch("pr_prover.state.json.dump", side_effect=OSError(BROKEN_MESSAGE)):
            with self.assertRaises(LockContention):
                self.lock().__enter__()
        self.assertEqual(self.path.read_text(encoding="utf-8"), "held elsewhere\n")

    def test_a_successful_acquisition_still_writes_the_whole_payload(self) -> None:
        """The positive control: the transaction did not stop writing the lock."""
        with self.lock():
            body = self.path.read_text(encoding="utf-8")
        self.assertEqual(json.loads(body), {"pr": 7, "repo": "example/repo"})
        self.assertTrue(body.endswith("\n"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
