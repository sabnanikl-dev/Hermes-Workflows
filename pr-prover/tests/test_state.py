"""The one JSON state file and the one run-exists lockfile."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

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

    def write(self, **overrides: object) -> None:
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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
