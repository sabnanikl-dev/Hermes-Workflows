"""The one JSON state file and the one run-exists lockfile."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import _support  # noqa: F401 - inserts the package on sys.path
from pr_prover.errors import LockContention, StateError
from pr_prover.state import MAX_ATTEMPTS, SCHEMA_VERSION, RunLock, RunState

HEAD = "a" * 40


class StateFileTests(unittest.TestCase):
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
        }
        payload.update(overrides)
        self.path.write_text(json.dumps(payload), encoding="utf-8")

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
            {"schema_version", "repo", "pr", "attempt", "head", "corrective_rerun_attempts", "outcome"},
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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
