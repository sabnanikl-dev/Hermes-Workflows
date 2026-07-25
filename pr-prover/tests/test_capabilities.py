"""PAPI90-P1-001: the narrow operations a child may ask the launcher to perform.

Every test here is about something a child used to be able to do with the raw
token it was handed, and can no longer express: merge, push another ref, push
another repository, approve a review, or run an arbitrary ``gh`` call.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _support import BUILDER_TOKEN, HEAD_A, HEAD_B

from pr_prover.capabilities import (
    COMMENT_PR,
    GITHUB_HOST,
    MAX_BODY_CHARS,
    MAX_OPERATIONS,
    PUSH_BRANCH,
    REQUEST_FIELDS,
    REVIEW_PR,
    SHIM_NAME,
    CapabilityBroker,
    CapabilityChannel,
    CapabilityScope,
    request,
    write_shim,
)
from pr_prover.commands import CommandResult
from pr_prover.errors import CapabilityRefused
from pr_prover.identities import BUILDER_CAPABILITIES, REVIEWER_CAPABILITIES

SCOPE = CapabilityScope(repo="example/repo", pr=7, branch="feat/example", head=HEAD_A)


class ScriptedRunner:
    """Answers the git and gh calls the broker composes, and records them."""

    def __init__(self, *, worktree_head: str = HEAD_B, returncode: int = 0) -> None:
        self.calls: list[dict[str, object]] = []
        self.worktree_head = worktree_head
        self.returncode = returncode

    def run(self, argv, *, cwd=None, env=None, timeout=None):  # type: ignore[no-untyped-def]
        argv = tuple(argv)
        self.calls.append({"argv": argv, "cwd": str(cwd), "env": dict(env or {})})
        stdout = ""
        if "rev-parse" in argv:
            stdout = self.worktree_head + "\n"
        elif "--input" in argv:
            payload = json.loads(Path(argv[argv.index("--input") + 1]).read_text(encoding="utf-8"))
            stdout = json.dumps(
                {
                    "id": 4242,
                    "html_url": "https://github.com/example/repo/pull/7#x",
                    "state": "COMMENTED",
                    "echo": payload,
                }
            )
        return CommandResult(
            argv=argv, returncode=self.returncode, stdout=stdout, stderr="", timed_out=False
        )

    @property
    def last(self) -> tuple[str, ...]:
        return self.calls[-1]["argv"]  # type: ignore[return-value]


class BrokerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.worktree = self.tmp / "worktree"
        self.worktree.mkdir()
        self.runner = ScriptedRunner()

    def broker(self, capabilities=BUILDER_CAPABILITIES, **overrides) -> CapabilityBroker:  # type: ignore[no-untyped-def]
        fields: dict[str, object] = {
            "runner": self.runner,
            "scope": SCOPE,
            "capabilities": capabilities,
            "worktree": self.worktree,
            "credential_env": {"GH_TOKEN": BUILDER_TOKEN, "PATH": "/usr/bin"},
            "scratch": self.tmp,
        }
        fields.update(overrides)
        return CapabilityBroker(**fields)  # type: ignore[arg-type]

    def ask(self, payload: dict, **overrides) -> dict:  # type: ignore[no-untyped-def]
        return self.broker(**overrides).handle(json.dumps(payload))


class RefusedOperationTests(BrokerTestCase):
    """The vocabulary is closed, so the dangerous verbs are not expressible."""

    def test_merge_is_not_an_operation_this_launcher_has(self) -> None:
        for operation in ("merge-pr", "merge", "approve", "approve-pr", "deploy", "admin", "gh"):
            reply = self.ask({"operation": operation})
            self.assertFalse(reply["ok"], operation)
            self.assertIn("no merge, approve, deploy, admin", reply["error"])

    def test_the_operation_vocabulary_is_exactly_the_capability_vocabulary(self) -> None:
        self.assertEqual(set(REQUEST_FIELDS), {PUSH_BRANCH, COMMENT_PR, REVIEW_PR})
        self.assertEqual(BUILDER_CAPABILITIES | REVIEWER_CAPABILITIES, set(REQUEST_FIELDS))

    def test_a_request_cannot_name_another_repository(self) -> None:
        reply = self.ask({"operation": PUSH_BRANCH, "repo": "someone/else"})
        self.assertFalse(reply["ok"])
        self.assertIn("cannot name its own repository", reply["error"])

    def test_a_request_cannot_name_another_ref_branch_or_commit(self) -> None:
        for field, value in (
            ("ref", "refs/heads/main"),
            ("branch", "main"),
            ("commit", HEAD_A),
            ("sha", HEAD_A),
            ("pr", 99),
            ("force", True),
            ("remote", "https://github.com/other/repo.git"),
            ("event", "APPROVE"),
        ):
            reply = self.ask({"operation": PUSH_BRANCH, field: value})
            self.assertFalse(reply["ok"], field)
            self.assertEqual(reply["evidence"]["unknown_fields"], [field])

    def test_a_reviewer_cannot_push(self) -> None:
        reply = self.ask({"operation": PUSH_BRANCH}, capabilities=REVIEWER_CAPABILITIES)
        self.assertFalse(reply["ok"])
        self.assertIn("does not carry the capability", reply["error"])
        self.assertEqual(self.runner.calls, [])

    def test_a_builder_cannot_submit_a_review(self) -> None:
        reply = self.ask({"operation": REVIEW_PR, "body": "looks fine"})
        self.assertFalse(reply["ok"])
        self.assertIn("does not carry the capability", reply["error"])

    def test_a_malformed_request_is_refused_without_a_traceback(self) -> None:
        for raw in ("", "not json", "[]", '"push-branch"', "null"):
            reply = self.broker().handle(raw)
            self.assertFalse(reply["ok"], raw)
            self.assertIsInstance(reply["error"], str)

    def test_a_body_that_is_missing_empty_or_oversized_is_refused(self) -> None:
        for body in (None, "", "   ", 7, "x" * (MAX_BODY_CHARS + 1), "with\x00nul"):
            reply = self.ask({"operation": COMMENT_PR, "body": body})
            self.assertFalse(reply["ok"], repr(body)[:40])

    def test_a_lane_cannot_post_without_bound(self) -> None:
        broker = self.broker()
        for _ in range(MAX_OPERATIONS):
            self.assertTrue(broker.handle(json.dumps({"operation": COMMENT_PR, "body": "hi"}))["ok"])
        reply = broker.handle(json.dumps({"operation": COMMENT_PR, "body": "hi"}))
        self.assertFalse(reply["ok"])
        self.assertIn("whole budget", reply["error"])


class BoundOperationTests(BrokerTestCase):
    """What the launcher actually runs is composed from the bound context alone."""

    def test_a_push_targets_exactly_the_bound_repository_and_branch(self) -> None:
        reply = self.ask({"operation": PUSH_BRANCH})
        self.assertTrue(reply["ok"], reply)
        argv = self.runner.last
        self.assertEqual(argv[-2], f"{GITHUB_HOST}/example/repo.git")
        self.assertEqual(argv[-1], f"{HEAD_B}:refs/heads/feat/example")
        self.assertEqual(reply["head"], HEAD_B)

    def test_a_push_is_never_forced_and_never_touches_another_ref(self) -> None:
        self.ask({"operation": PUSH_BRANCH})
        argv = self.runner.last
        for flag in ("--force", "-f", "--force-with-lease", "--delete", "--mirror", "--all", "--tags"):
            self.assertNotIn(flag, argv, flag)
        self.assertEqual([item for item in argv if item.startswith("refs/")], [])
        self.assertEqual(argv.count("refs/heads/feat/example"), 0)

    def test_a_push_that_would_move_nothing_is_refused(self) -> None:
        self.runner.worktree_head = HEAD_A
        reply = self.ask({"operation": PUSH_BRANCH})
        self.assertFalse(reply["ok"])
        self.assertIn("nothing new to push", reply["error"])

    def test_a_comment_goes_to_the_bound_pull_request_only(self) -> None:
        reply = self.ask({"operation": COMMENT_PR, "body": "fixed it"})
        self.assertTrue(reply["ok"], reply)
        self.assertIn("repos/example/repo/issues/7/comments", self.runner.last)
        self.assertEqual(reply["id"], "4242")

    def test_a_review_is_always_a_plain_comment_at_the_bound_head(self) -> None:
        """A child cannot approve: the event and the commit are not its to choose."""
        sent: list[dict] = []
        original = self.runner.run

        def capture(argv, *, cwd=None, env=None, timeout=None):  # type: ignore[no-untyped-def]
            if "--input" in argv:
                path = Path(argv[list(argv).index("--input") + 1])
                sent.append(json.loads(path.read_text(encoding="utf-8")))
            return original(argv, cwd=cwd, env=env, timeout=timeout)

        self.runner.run = capture  # type: ignore[method-assign]
        reply = self.ask(
            {"operation": REVIEW_PR, "body": "PR-PROVER-REVIEW: ..."},
            capabilities=REVIEWER_CAPABILITIES,
        )
        self.assertTrue(reply["ok"], reply)
        self.assertIn("repos/example/repo/pulls/7/reviews", self.runner.last)
        self.assertEqual(sent[-1]["event"], "COMMENT")
        self.assertEqual(sent[-1]["commit_id"], HEAD_A)

    def test_a_failed_git_or_gh_call_is_a_refusal_with_no_credential_in_it(self) -> None:
        self.runner.returncode = 1
        reply = self.ask({"operation": COMMENT_PR, "body": "hi"})
        self.assertFalse(reply["ok"])
        self.assertNotIn(BUILDER_TOKEN, json.dumps(reply))

    def test_a_channel_can_only_be_bound_to_a_well_formed_scope(self) -> None:
        for overrides in (
            {"repo": "not-a-repo"},
            {"repo": "a/b/c"},
            {"pr": 0},
            {"branch": "--upload-pack=evil"},
            {"branch": "feat/../../main"},
            {"head": "abc"},
            {"head": HEAD_A.upper()},
        ):
            fields = {"repo": "example/repo", "pr": 7, "branch": "feat/example", "head": HEAD_A}
            fields.update(overrides)
            with self.assertRaises(CapabilityRefused, msg=str(overrides)):
                CapabilityScope(**fields)  # type: ignore[arg-type]


class ChannelTests(BrokerTestCase):
    """The socket itself: who can reach it, and what a real shim gets back."""

    def channel(self, capabilities=BUILDER_CAPABILITIES) -> CapabilityChannel:  # type: ignore[no-untyped-def]
        channel = CapabilityChannel(self.broker(capabilities), label="lane-a")
        self.addCleanup(channel.close)
        return channel

    def test_the_socket_and_its_directory_are_owner_only(self) -> None:
        channel = self.channel()
        self.assertEqual(channel.path.stat().st_mode & 0o077, 0)
        self.assertEqual(channel.path.parent.stat().st_mode & stat.S_IRWXO, 0)
        self.assertEqual(channel.path.parent.stat().st_mode & stat.S_IRWXG, 0)

    def test_a_request_over_the_real_socket_is_served(self) -> None:
        channel = self.channel()
        reply = request(channel.path, {"operation": COMMENT_PR, "body": "over the wire"})
        self.assertTrue(reply["ok"], reply)
        self.assertEqual(channel.broker.granted, [COMMENT_PR])

    def test_a_closed_channel_serves_nothing(self) -> None:
        channel = CapabilityChannel(self.broker(), label="lane-b")
        path = channel.path
        channel.close()
        self.assertFalse(path.exists())
        with self.assertRaises(OSError):
            request(path, {"operation": COMMENT_PR, "body": "too late"})

    def test_two_lanes_get_two_different_channels(self) -> None:
        first = self.channel()
        second = CapabilityChannel(self.broker(REVIEWER_CAPABILITIES), label="lane-b")
        self.addCleanup(second.close)
        self.assertNotEqual(first.path, second.path)
        self.assertFalse(request(second.path, {"operation": PUSH_BRANCH})["ok"])
        self.assertTrue(request(first.path, {"operation": PUSH_BRANCH})["ok"])


class ShimTests(BrokerTestCase):
    """The program a child actually runs, executed for real."""

    def setUp(self) -> None:
        super().setUp()
        self.shim = write_shim(self.tmp / "bin")
        self.channel = CapabilityChannel(self.broker(), label="lane-a")
        self.addCleanup(self.channel.close)

    def shim_run(self, *arguments: str, socket_path: str | None = None) -> subprocess.CompletedProcess:
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        path = self.channel.path if socket_path is None else socket_path
        if path:
            env["PR_PROVER_CAPABILITY_SOCKET"] = str(path)
        return subprocess.run(
            [sys.executable, str(self.shim), *arguments],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
            check=False,
        )

    def body_file(self, text: str) -> str:
        path = self.tmp / "body.md"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_the_shim_is_owner_only_and_carries_no_credential(self) -> None:
        self.assertEqual(self.shim.name, SHIM_NAME)
        self.assertEqual(self.shim.stat().st_mode & 0o077, 0)
        self.assertNotIn(BUILDER_TOKEN, self.shim.read_text(encoding="utf-8"))

    def test_a_child_with_no_credential_can_still_comment_through_the_launcher(self) -> None:
        result = self.shim_run("comment", "--body-file", self.body_file("all fixed"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])
        self.assertEqual(self.channel.broker.granted, [COMMENT_PR])
        # The credential never left the launcher process.
        self.assertNotIn(BUILDER_TOKEN, result.stdout + result.stderr)

    def test_a_child_can_push_only_the_bound_branch(self) -> None:
        result = self.shim_run("push")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.runner.last[-1], f"{HEAD_B}:refs/heads/feat/example")

    def test_a_child_asking_for_anything_else_gets_a_usage_error(self) -> None:
        for arguments in ((), ("merge",), ("approve",), ("push", "--force"), ("comment",)):
            result = self.shim_run(*arguments)
            self.assertNotEqual(result.returncode, 0, arguments)
            self.assertIn("usage", result.stderr.lower())

    def test_a_refused_operation_exits_nonzero_with_the_reason(self) -> None:
        channel = CapabilityChannel(self.broker(REVIEWER_CAPABILITIES), label="lane-r")
        self.addCleanup(channel.close)
        result = self.shim_run("push", socket_path=str(channel.path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not carry the capability", result.stderr)

    def test_a_child_with_no_channel_can_do_nothing(self) -> None:
        result = self.shim_run("push", socket_path="")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no capability channel", result.stderr)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
