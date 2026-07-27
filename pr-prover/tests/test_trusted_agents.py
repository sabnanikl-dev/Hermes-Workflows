"""How a trusted lane is actually launched, observed, and ended.

Four properties, and each of them is one a lane's own output cannot establish:

* the session the agent authenticates through is inherited, not rebuilt;
* the budget that is reported is the budget that is enforced, ``None`` included;
* silence is measured and reported, never converted into a failure;
* a lane is a process tree, and the tree is what ends when the budget does.

These drive the real :class:`~pr_prover.commands.SubprocessRunner` against small
POSIX shell children rather than a double, because every one of them is a claim
about ``subprocess`` behaviour that a double would simply agree with.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pr_prover.commands import (
    EXITED,
    RUNNER_DEFAULT,
    TIMED_OUT,
    CommandResult,
    Progress,
    SubprocessRunner,
    validate_argv,
)
from pr_prover.errors import CommandContractError

SHELL = shutil.which("sh")


@unittest.skipIf(SHELL is None, "no POSIX shell available")
class SubprocessRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-runner-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def sh(self, script: str) -> list[str]:
        return [SHELL, "-c", script]

    # -- the session is inherited -----------------------------------------
    def test_a_lane_with_no_overlay_inherits_the_real_session(self) -> None:
        """``env=None`` is the whole mechanism: no ``env -i``, no synthetic HOME."""
        runner = SubprocessRunner()
        marker = "pr-prover-inherited-session-marker"
        os.environ["PR_PROVER_SESSION_PROBE"] = marker
        self.addCleanup(os.environ.pop, "PR_PROVER_SESSION_PROBE", None)

        result = runner.run(self.sh('printf "%s" "$PR_PROVER_SESSION_PROBE"'), timeout=30)

        self.assertEqual(result.stdout, marker)
        self.assertTrue(result.ok)

    def test_a_named_overlay_replaces_the_environment_it_was_given(self) -> None:
        runner = SubprocessRunner()
        result = runner.run(
            self.sh('printf "%s" "$PR_PROVER_OVERLAY"'),
            env={**os.environ, "PR_PROVER_OVERLAY": "overlaid"},
            timeout=30,
        )
        self.assertEqual(result.stdout, "overlaid")

    # -- the reported budget is the enforced budget ------------------------
    def test_an_explicit_none_budget_means_no_deadline(self) -> None:
        """A lane the report calls unbounded must not meet a default nobody asked for.

        The default here is a tenth of a second and the child sleeps far longer
        than that, so a runner that fell back to ``default_timeout`` for an
        explicit ``None`` would time this out.
        """
        runner = SubprocessRunner(default_timeout=0.1, poll_interval=0.02)
        result = runner.run(self.sh("sleep 0.4; printf done"), timeout=None)
        self.assertFalse(result.timed_out)
        self.assertEqual(result.stdout, "done")
        self.assertEqual(result.state, EXITED)

    def test_omitting_the_budget_is_what_reaches_the_runner_default(self) -> None:
        runner = SubprocessRunner(default_timeout=0.1, poll_interval=0.02, kill_grace=0.5)
        result = runner.run(self.sh("sleep 5"))
        self.assertTrue(result.timed_out)
        self.assertEqual(result.state, TIMED_OUT)
        self.assertEqual(result.returncode, 124)

    def test_the_default_sentinel_is_not_none(self) -> None:
        """Distinguishable at the type level, so the two cases cannot merge again."""
        self.assertIsNotNone(RUNNER_DEFAULT)
        self.assertIsNot(RUNNER_DEFAULT, None)

    # -- silence is not a hang ---------------------------------------------
    def test_a_silent_lane_that_exits_cleanly_is_not_a_failure(self) -> None:
        """The builder case: twenty quiet minutes then one line and exit 0."""
        runner = SubprocessRunner(poll_interval=0.02, progress_interval=0.05)
        seen: list[Progress] = []

        result = runner.run(
            self.sh("sleep 0.3; printf 'DONE: fine'"),
            timeout=30,
            progress=seen.append,
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.stdout, "DONE: fine")
        self.assertEqual(result.state, EXITED)
        self.assertTrue(seen, "a quiet lane still reports that it is alive")
        self.assertTrue(all(update.output_bytes == 0 for update in seen))
        self.assertGreater(max(update.quiet_seconds for update in seen), 0)

    def test_progress_reports_output_growing_while_the_child_runs(self) -> None:
        runner = SubprocessRunner(poll_interval=0.02, progress_interval=0.05)
        seen: list[Progress] = []

        runner.run(
            self.sh("for i in 1 2 3 4 5 6; do printf 'chunk'; sleep 0.06; done"),
            timeout=30,
            progress=seen.append,
        )

        self.assertTrue(seen)
        self.assertGreater(max(update.output_bytes for update in seen), 0)
        self.assertGreater(max(update.elapsed for update in seen), 0)

    def test_a_finished_result_reports_how_long_it_took(self) -> None:
        runner = SubprocessRunner(poll_interval=0.02)
        result = runner.run(self.sh("sleep 0.2"), timeout=30)
        self.assertGreaterEqual(result.duration, 0.15)

    # -- a lane is a process tree ------------------------------------------
    def test_a_timed_out_lane_takes_what_it_started_with_it(self) -> None:
        """A builder that spawned a suite must not keep writing after the stop.

        The child starts a grandchild that would keep appending to a file for
        far longer than the budget, then blocks. If only the direct child were
        signalled, the grandchild would go on writing after ``run`` returned.
        """
        witness = self.tmp / "grandchild.log"
        script = (
            f"( while true; do printf x >> {witness}; sleep 0.05; done ) & "
            "sleep 30"
        )
        runner = SubprocessRunner(poll_interval=0.02, kill_grace=0.5)

        result = runner.run(self.sh(script), timeout=0.3)
        self.assertTrue(result.timed_out)

        # Let anything that survived prove it survived.
        settled = witness.stat().st_size if witness.exists() else 0
        time.sleep(0.4)
        after = witness.stat().st_size if witness.exists() else 0
        self.assertEqual(
            after,
            settled,
            "a process the lane started outlived the lane's own budget",
        )

    def test_a_lane_runs_in_its_own_process_group(self) -> None:
        """Which is what makes ending the tree possible without ending the prover."""
        runner = SubprocessRunner()
        result = runner.run(self.sh("echo $$; ps -o pgid= -p $$"), timeout=30)
        self.assertTrue(result.ok)
        printed = result.stdout.split()
        self.assertEqual(len(printed), 2)
        self.assertNotEqual(int(printed[1]), os.getpgrp())

    # -- ordinary contract --------------------------------------------------
    def test_stdin_is_never_inherited(self) -> None:
        """A lane that reads stdin gets EOF rather than the operator's terminal."""
        runner = SubprocessRunner()
        result = runner.run(self.sh("cat; printf '[eof]'"), timeout=30)
        self.assertEqual(result.stdout, "[eof]")

    def test_a_missing_program_is_a_command_contract_error(self) -> None:
        runner = SubprocessRunner()
        with self.assertRaises(CommandContractError):
            runner.run(["pr-prover-no-such-program-anywhere"], timeout=30)

    def test_large_output_survives_because_it_is_never_piped(self) -> None:
        """A lane may print megabytes without the loop having to drain it."""
        runner = SubprocessRunner(poll_interval=0.02)
        result = runner.run(
            self.sh("i=0; while [ $i -lt 4000 ]; do printf '0123456789abcdefghij'; i=$((i+1)); done"),
            timeout=60,
        )
        self.assertTrue(result.ok)
        self.assertEqual(len(result.stdout), 80_000)


class CommandResultTests(unittest.TestCase):
    def test_state_is_read_from_how_it_ended_not_from_how_quiet_it_was(self) -> None:
        quiet = CommandResult(
            argv=("x",), returncode=0, stdout="", stderr="", quiet_seconds=9_999.0
        )
        self.assertEqual(quiet.state, EXITED)
        self.assertTrue(quiet.ok)

        stopped = CommandResult(
            argv=("x",), returncode=124, stdout="noisy", stderr="", timed_out=True
        )
        self.assertEqual(stopped.state, TIMED_OUT)
        self.assertFalse(stopped.ok)

    def test_argv_validation_still_refuses_a_shell_string(self) -> None:
        with self.assertRaises(CommandContractError):
            validate_argv("sh -c 'rm -rf /'")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
