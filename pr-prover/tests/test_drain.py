"""PAPI-90 item 4: closing a capability channel drains and cancels its work.

``close()`` used to stop the serving thread and remove the socket, and return.
Nothing waited for a handler that had already been accepted, so a ``git push``
or a ``gh api`` the broker was part-way through could still land *after* the
lane was declared finished and its worktree removed — and the run would report
an outcome for a repository state it had not looked at since.

So closing is now ordered: stop accepting, stop the serving thread, close the
listening socket, tell the broker to refuse, drain what is already running,
cancel whatever is left with a bounded ``SIGTERM``-then-``SIGKILL``, join, and
only then remove anything.

These tests use real child processes, because "no subprocess survives" is not a
claim a double can make on the operating system's behalf.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path

from _support import HEAD_A, HEAD_B

from pr_prover.capabilities import (
    COMMENT_PR,
    PUSH_BRANCH,
    CapabilityBroker,
    CapabilityScope,
)
from pr_prover.commands import (
    KILL_GRACE_SECONDS,
    TERM_GRACE_SECONDS,
    CommandResult,
    LaunchWatch,
    SubprocessRunner,
    group_is_alive,
    run_watched,
)

SCOPE = CapabilityScope(repo="example/repo", pr=7, branch="feat/example", head=HEAD_A)
# Long enough that it is unambiguously still running when the test cancels it.
SLOW_SECONDS = 45


def script(path: Path, body: str) -> Path:
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(0o700)
    return path


def wait_for(predicate, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


class LaunchWatchTests(unittest.TestCase):
    """The handle a runner registers its process groups with."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.runner = SubprocessRunner(default_timeout=60.0, term_grace=2.0, kill_grace=2.0)
        self.marker = self.tmp / "side-effect"
        self.slow = script(
            self.tmp / "slow", f'sleep {SLOW_SECONDS}\ntouch "{self.marker}"'
        )

    def start(self, watch: LaunchWatch) -> threading.Thread:
        thread = threading.Thread(
            target=lambda: run_watched(self.runner, [str(self.slow)], watch=watch),
            daemon=True,
        )
        thread.start()
        return thread

    def test_a_runner_registers_and_forgets_its_group(self) -> None:
        watch = LaunchWatch()
        run_watched(self.runner, ["/bin/sh", "-c", "exit 0"], watch=watch)
        self.assertEqual(watch.open_groups, ())
        self.assertFalse(watch.cancelled)

    def test_cancel_terminates_a_running_group_and_leaves_no_side_effect(self) -> None:
        """Former-red: the child is gone, and what it was about to do never happens."""
        watch = LaunchWatch()
        thread = self.start(watch)
        self.assertTrue(wait_for(lambda: watch.open_groups), "the child never started")
        groups = watch.open_groups

        cancelled = watch.cancel(term_grace=2.0, kill_grace=2.0)

        thread.join(timeout=20.0)
        self.assertFalse(thread.is_alive())
        self.assertEqual(cancelled, groups)
        for group in groups:
            self.assertFalse(group_is_alive(group), group)
        self.assertFalse(self.marker.exists(), "the cancelled child still had its effect")

    def test_cancellation_latches_so_a_later_launch_never_starts(self) -> None:
        watch = LaunchWatch()
        watch.cancel()
        self.assertTrue(watch.cancelled)
        with self.assertRaises(Exception):
            run_watched(self.runner, [str(self.slow)], watch=watch)
        self.assertFalse(self.marker.exists())

    def test_a_runner_without_watch_support_is_simply_called_without_it(self) -> None:
        class Plain:
            def __init__(self) -> None:
                self.seen: list[tuple[str, ...]] = []

            def run(self, argv, *, cwd=None, env=None, timeout=None):  # type: ignore[no-untyped-def]
                self.seen.append(tuple(argv))
                return CommandResult(argv=tuple(argv), returncode=0, stdout="", stderr="")

        plain = Plain()
        run_watched(plain, ["anything"], watch=LaunchWatch())
        self.assertEqual(plain.seen, [("anything",)])

    def test_the_teardown_graces_are_bounded(self) -> None:
        self.assertLessEqual(TERM_GRACE_SECONDS, 30.0)
        self.assertLessEqual(KILL_GRACE_SECONDS, 30.0)


class BrokerShutdownTests(unittest.TestCase):
    """The broker's own stop and cancel, over real GitHub subprocesses."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.marker = self.tmp / "posted-after-close"
        self.slow_gh = script(
            self.tmp / "slow-gh",
            f'sleep {SLOW_SECONDS}\ntouch "{self.marker}"\necho \'{{"id": 1}}\'',
        )
        self.fast_gh = script(
            self.tmp / "fast-gh", f'touch "{self.marker}"\necho \'{{"id": 1}}\''
        )
        self.runner = SubprocessRunner(default_timeout=120.0, term_grace=2.0, kill_grace=2.0)
        self.events: list[str] = []

    def broker(self, gh: Path) -> CapabilityBroker:
        return CapabilityBroker(
            runner=self.runner,
            scope=SCOPE,
            capabilities=frozenset({COMMENT_PR, PUSH_BRANCH}),
            worktree=self.tmp,
            credential_env={"PATH": "/usr/bin:/bin"},
            scratch=self.tmp,
            gh=str(gh),
            git=str(script(self.tmp / "git", f'echo {HEAD_B}')),
            timeout=120.0,
            on_event=self.events.append,
        )

    def comment(self, broker: CapabilityBroker, into: list[dict]) -> threading.Thread:
        thread = threading.Thread(
            target=lambda: into.append(
                broker.handle(json.dumps({"operation": COMMENT_PR, "body": "hello"}))
            ),
            daemon=True,
        )
        thread.start()
        return thread

    def test_work_that_finishes_is_drained_rather_than_cancelled(self) -> None:
        broker = self.broker(self.fast_gh)
        replies: list[dict] = []
        self.comment(broker, replies).join(timeout=60.0)
        self.assertTrue(replies[0]["ok"], replies)
        self.assertEqual(broker.granted, [COMMENT_PR])
        self.assertTrue(self.marker.exists())
        self.assertEqual(broker.watch.open_groups, ())

    def test_cancel_kills_in_flight_work_and_no_side_effect_lands(self) -> None:
        """Former-red: the close race.

        A handler is part-way through a real ``gh`` call when the broker is
        cancelled. When cancel returns, that process group is gone and the
        effect it was about to have has not happened — which is what lets the
        launcher remove the lane's socket, scratch, and worktree behind it.
        """
        broker = self.broker(self.slow_gh)
        replies: list[dict] = []
        thread = self.comment(broker, replies)
        self.assertTrue(
            wait_for(lambda: broker.watch.open_groups), "the gh call never started"
        )
        groups = broker.watch.open_groups

        cancelled = broker.cancel()

        thread.join(timeout=30.0)
        self.assertFalse(thread.is_alive(), "a handler outlived the cancellation")
        self.assertEqual(cancelled, groups)
        for group in groups:
            self.assertFalse(group_is_alive(group), group)
        self.assertFalse(self.marker.exists(), "the cancelled call still reached GitHub")
        self.assertEqual(broker.granted, [])
        self.assertFalse(replies[0]["ok"], replies)

    def test_a_stopped_broker_refuses_without_starting_a_subprocess(self) -> None:
        broker = self.broker(self.fast_gh)
        broker.stop()
        reply = broker.handle(json.dumps({"operation": COMMENT_PR, "body": "too late"}))
        self.assertFalse(reply["ok"])
        self.assertIn("closing", reply["error"])
        self.assertFalse(self.marker.exists())
        self.assertEqual(broker.granted, [])

    def test_a_cancelled_broker_starts_no_further_subprocess(self) -> None:
        """Latching: a handler cannot outrun the closer between two commands."""
        broker = self.broker(self.fast_gh)
        broker.cancel()
        reply = broker.handle(json.dumps({"operation": PUSH_BRANCH}))
        self.assertFalse(reply["ok"])
        self.assertFalse(self.marker.exists())
        self.assertTrue(broker.stopped)

    def test_stopping_twice_is_safe(self) -> None:
        broker = self.broker(self.fast_gh)
        broker.stop()
        broker.cancel()
        broker.cancel()
        self.assertTrue(broker.stopped)


class ChannelCloseOrderTests(unittest.TestCase):
    """The order close() works in, and what it leaves behind."""

    def test_close_stops_the_broker_before_it_removes_anything(self) -> None:
        import inspect

        from pr_prover.capabilities import CapabilityChannel

        source = inspect.getsource(CapabilityChannel.close)
        order = [
            source.index("stop_accepting()"),
            source.index("server.shutdown()"),
            source.index("server_close()"),
            source.index("self.broker.stop()"),
            source.index("join_handlers(DRAIN_SECONDS)"),
            source.index("self.broker.cancel()"),
            source.index("Path(path).unlink"),
        ]
        self.assertEqual(order, sorted(order), "close() no longer drains before it removes")

    def test_a_channel_that_could_not_account_for_a_handler_records_a_refusal(self) -> None:
        from pr_prover.capabilities import CapabilityChannel

        self.assertIn("shutdown_error", CapabilityChannel.close.__doc__ or "")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
