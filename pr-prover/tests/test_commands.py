"""Argv discipline, template rendering, and the real subprocess boundary."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import _support  # noqa: F401 - inserts the package on sys.path
from pr_prover.commands import (
    SubprocessRunner,
    group_is_alive,
    render_argv,
    terminate_group,
    validate_argv,
)
from pr_prover.errors import CommandContractError


class ArgvValidationTests(unittest.TestCase):
    def test_a_shell_string_is_refused(self) -> None:
        with self.assertRaises(CommandContractError) as caught:
            validate_argv("git status && rm -rf /")
        self.assertIn("argv array", caught.exception.message)

    def test_bytes_are_refused(self) -> None:
        with self.assertRaises(CommandContractError):
            validate_argv(b"git")

    def test_an_empty_array_is_refused(self) -> None:
        with self.assertRaises(CommandContractError):
            validate_argv([])

    def test_a_non_string_element_is_refused(self) -> None:
        with self.assertRaises(CommandContractError):
            validate_argv(["git", 7])

    def test_an_empty_element_is_refused(self) -> None:
        with self.assertRaises(CommandContractError):
            validate_argv(["git", ""])

    def test_a_nul_byte_is_refused(self) -> None:
        with self.assertRaises(CommandContractError):
            validate_argv(["git", "sta\x00tus"])

    def test_a_valid_array_becomes_a_tuple(self) -> None:
        self.assertEqual(validate_argv(["git", "status"]), ("git", "status"))


class RenderTests(unittest.TestCase):
    values = {"head": "a" * 40, "repo": "example/repo"}

    def test_placeholders_are_substituted(self) -> None:
        rendered = render_argv(["review", "--head", "{head}", "--repo", "{repo}"], self.values)
        self.assertEqual(rendered, ("review", "--head", "a" * 40, "--repo", "example/repo"))

    def test_an_unknown_placeholder_fails_closed(self) -> None:
        with self.assertRaises(CommandContractError) as caught:
            render_argv(["review", "{token}"], self.values)
        self.assertEqual(caught.exception.evidence["placeholder"], "token")

    def test_a_substituted_value_is_never_re_parsed(self) -> None:
        """Shell metacharacters in a value stay inside one argv element."""
        rendered = render_argv(["review", "{head}"], {"head": "; rm -rf / #"})
        self.assertEqual(rendered, ("review", "; rm -rf / #"))

    def test_format_spec_syntax_is_not_honoured(self) -> None:
        rendered = render_argv(["review", "{head!r:>90}"], self.values)
        self.assertEqual(rendered[1], "{head!r:>90}")

    def test_attribute_access_is_not_honoured(self) -> None:
        rendered = render_argv(["review", "{head.__class__}"], self.values)
        self.assertEqual(rendered[1], "{head.__class__}")


class SubprocessRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = SubprocessRunner(default_timeout=30.0)

    def test_stdout_and_exit_code_are_captured(self) -> None:
        result = self.runner.run([sys.executable, "-c", "print('hello')"])
        self.assertTrue(result.ok)
        self.assertEqual(result.stdout.strip(), "hello")

    def test_a_non_zero_exit_is_reported_not_raised(self) -> None:
        result = self.runner.run([sys.executable, "-c", "raise SystemExit(3)"])
        self.assertFalse(result.ok)
        self.assertEqual(result.returncode, 3)

    def test_a_shell_string_never_reaches_the_shell(self) -> None:
        with self.assertRaises(CommandContractError):
            self.runner.run("echo hello > /tmp/pr-prover-should-not-exist")

    def test_a_timeout_is_reported_as_a_failure(self) -> None:
        result = self.runner.run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.2)
        self.assertTrue(result.timed_out)
        self.assertFalse(result.ok)

    def test_a_missing_executable_fails_closed(self) -> None:
        with self.assertRaises(CommandContractError):
            self.runner.run(["pr-prover-no-such-executable-zzz"])

    def test_children_get_no_stdin(self) -> None:
        result = self.runner.run([sys.executable, "-c", "import sys; print(repr(sys.stdin.read()))"])
        self.assertEqual(result.stdout.strip(), "''")


# A lane that backgrounds a long-lived descendant and exits or hangs. The
# descendant writes its pid where the test can read it, then sleeps well past
# the run: nothing but a group-wide signal will stop it.
_SPAWNER = """
import os, subprocess, sys, time
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(300)"])
open(sys.argv[1], "w").write(str(child.pid))
sys.stdout.write("spawned\\n")
sys.stdout.flush()
{tail}
"""


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError as exc:
        import errno

        return exc.errno == errno.EPERM
    return True


def _settled(pid: int, *, seconds: float = 5.0) -> bool:
    """True once ``pid`` is gone. Polls, because a signal is not instantaneous."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not _alive(pid):
            return True
        time.sleep(0.02)
    return not _alive(pid)


@unittest.skipUnless(hasattr(os, "killpg"), "process groups are a POSIX feature")
class ProcessGroupTests(unittest.TestCase):
    """PAPI90-P1-004: a lane is a process group, and the group does not survive it.

    Each case starts a real child that backgrounds a real grandchild. Before this
    fix only the direct child was signalled, so the grandchild — holding the
    lane's worktree and, now, its capability channel — outlived the run.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.pidfile = Path(self._tmp.name) / "descendant.pid"
        self.runner = SubprocessRunner(default_timeout=30.0, term_grace=1.0, kill_grace=2.0)

    def descendant(self) -> int:
        pid = int(self.pidfile.read_text(encoding="utf-8"))
        self.addCleanup(self._make_sure_it_is_gone, pid)
        return pid

    def _make_sure_it_is_gone(self, pid: int) -> None:
        try:  # pragma: no cover - only runs if the assertion under test failed
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

    def test_a_descendant_does_not_survive_a_lane_timeout(self) -> None:
        result = self.runner.run(
            [sys.executable, "-c", _SPAWNER.format(tail="time.sleep(300)"), str(self.pidfile)],
            timeout=2.0,
        )
        self.assertTrue(result.timed_out)
        self.assertTrue(
            _settled(self.descendant()),
            "the lane timed out but its descendant is still running",
        )

    def test_a_descendant_does_not_survive_a_lane_that_exits_cleanly(self) -> None:
        """The classic orphan: the lane returns 0 and leaves a server behind."""
        result = self.runner.run(
            [sys.executable, "-c", _SPAWNER.format(tail=""), str(self.pidfile)]
        )
        self.assertTrue(result.ok, result.stderr)
        self.assertEqual(result.stdout.strip(), "spawned")
        self.assertTrue(
            _settled(self.descendant()),
            "the lane exited cleanly but its descendant is still running",
        )

    def test_a_descendant_does_not_survive_a_cancelled_run(self) -> None:
        class Cancelled(SubprocessRunner):
            def __init__(self, pidfile: Path) -> None:
                super().__init__(default_timeout=30.0, term_grace=1.0, kill_grace=2.0)
                self.pidfile = pidfile

        runner = Cancelled(self.pidfile)
        original = subprocess.Popen.wait

        def interrupted(self, *arguments, **keywords):  # type: ignore[no-untyped-def]
            # Wait until the grandchild exists, then behave like Ctrl-C.
            deadline = time.monotonic() + 10.0
            while time.monotonic() < deadline and not runner.pidfile.exists():
                time.sleep(0.02)
            subprocess.Popen.wait = original  # type: ignore[method-assign]
            raise KeyboardInterrupt

        subprocess.Popen.wait = interrupted  # type: ignore[method-assign]
        self.addCleanup(setattr, subprocess.Popen, "wait", original)
        with self.assertRaises(KeyboardInterrupt):
            runner.run(
                [sys.executable, "-c", _SPAWNER.format(tail="time.sleep(300)"), str(self.pidfile)]
            )
        self.assertTrue(
            _settled(self.descendant()),
            "the run was cancelled but the lane's descendant is still running",
        )

    def test_a_lane_runs_in_a_group_of_its_own(self) -> None:
        result = self.runner.run(
            [sys.executable, "-c", "import os; print(os.getpid() == os.getpgid(0))"]
        )
        self.assertEqual(result.stdout.strip(), "True")
        self.assertNotEqual(os.getpgrp(), os.getpid() + 1)

    def test_terminating_a_group_that_is_already_gone_is_not_an_error(self) -> None:
        terminate_group(None)
        terminate_group(999_999_999, term_grace=0.1, kill_grace=0.1)
        self.assertFalse(group_is_alive(999_999_999))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
