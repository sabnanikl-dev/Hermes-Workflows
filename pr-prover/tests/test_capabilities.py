"""PAPI90-P1-001: the narrow operations a child may ask the launcher to perform.

Every test here is about something a child used to be able to do with the raw
token it was handed, and can no longer express: merge, push another ref, push
another repository, approve a review, or run an arbitrary ``gh`` call.
"""
from __future__ import annotations

import ast
import inspect
import json
import os
import socket
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _support import BUILDER_TOKEN, HEAD_A, HEAD_B

from pr_prover.capabilities import (
    AUTH_REFUSED,
    COMMENT_PR,
    GITHUB_HOST,
    MAX_BODY_CHARS,
    MAX_OPERATIONS,
    PUSH_BRANCH,
    REQUEST_FIELDS,
    REVIEW_PR,
    SECRET_CHARS,
    SHIM_NAME,
    SHIM_SOURCE,
    CapabilityBroker,
    CapabilityChannel,
    CapabilityScope,
    _ChannelHandler,
    authenticates,
    frame,
    request,
    split_frame,
    write_shim,
)
from pr_prover.childenv import MIN_CAPABILITY_SECRET_CHARS
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
        reply = request(
            channel.path,
            {"operation": COMMENT_PR, "body": "over the wire"},
            secret=channel.secret,
        )
        self.assertTrue(reply["ok"], reply)
        self.assertEqual(channel.broker.granted, [COMMENT_PR])

    def test_a_closed_channel_serves_nothing(self) -> None:
        channel = CapabilityChannel(self.broker(), label="lane-b")
        path, secret = channel.path, channel.secret
        channel.close()
        self.assertFalse(path.exists())
        with self.assertRaises(OSError):
            request(path, {"operation": COMMENT_PR, "body": "too late"}, secret=secret)

    def test_two_lanes_get_two_different_channels(self) -> None:
        first = self.channel()
        second = CapabilityChannel(self.broker(REVIEWER_CAPABILITIES), label="lane-b")
        self.addCleanup(second.close)
        self.assertNotEqual(first.path, second.path)
        self.assertNotEqual(first.secret, second.secret)
        self.assertFalse(
            request(second.path, {"operation": PUSH_BRANCH}, secret=second.secret)["ok"]
        )
        self.assertTrue(
            request(first.path, {"operation": PUSH_BRANCH}, secret=first.secret)["ok"]
        )

    def test_one_lane_cannot_spend_another_lanes_capabilities(self) -> None:
        """PAPI-90 item 2, former-red: finding a live socket is not enough.

        Both lanes run as the same user, so the mode bits on the socket keep
        nobody out. The reviewer lane holds no ``push-branch`` capability, so it
        has an obvious reason to want the builder's channel — and knowing the
        path of it gets the reviewer exactly nowhere, because the request is
        refused before it is parsed and no subprocess is started.
        """
        builder = self.channel()
        reviewer = CapabilityChannel(self.broker(REVIEWER_CAPABILITIES), label="lane-r")
        self.addCleanup(reviewer.close)

        stolen = request(
            builder.path, {"operation": PUSH_BRANCH}, secret=reviewer.secret
        )

        self.assertFalse(stolen["ok"])
        self.assertEqual(stolen["error"], AUTH_REFUSED)
        self.assertEqual(builder.broker.granted, [])
        self.assertEqual(builder.broker.refused, [])
        self.assertEqual(self.runner.calls, [])
        self.assertEqual(builder.unauthenticated, 1)

    def test_a_request_with_no_secret_at_all_is_refused(self) -> None:
        channel = self.channel()
        reply = request(channel.path, {"operation": PUSH_BRANCH}, secret="")
        self.assertFalse(reply["ok"])
        self.assertEqual(reply["error"], AUTH_REFUSED)
        self.assertEqual(self.runner.calls, [])

    def test_a_replayed_secret_after_close_reaches_nothing(self) -> None:
        """A secret is not a bearer token for a channel that no longer exists."""
        channel = CapabilityChannel(self.broker(), label="lane-c")
        path, secret = channel.path, channel.secret
        channel.close()
        with self.assertRaises(OSError):
            request(path, {"operation": PUSH_BRANCH}, secret=secret)
        self.assertEqual(self.runner.calls, [])

    def test_the_lane_secret_is_long_and_never_repeats(self) -> None:
        secrets = set()
        for index in range(4):
            channel = CapabilityChannel(self.broker(), label=f"lane-{index}")
            self.addCleanup(channel.close)
            self.assertEqual(len(channel.secret), SECRET_CHARS)
            self.assertGreaterEqual(len(channel.secret), MIN_CAPABILITY_SECRET_CHARS)
            secrets.add(channel.secret)
        self.assertEqual(len(secrets), 4)


class ChannelHandlerTests(BrokerTestCase):
    """The wire protocol itself, driven over a socket pair.

    :class:`ChannelTests` needs a bound unix socket, which some hardened
    sandboxes refuse outright. These tests reach the same handler — the same
    authentication, the same parse, the same dispatch — through a connected
    socket pair instead, so the rule that matters ("a request that cannot prove
    it is this lane starts no subprocess") is checked wherever the suite runs.
    """

    def serve(self, secret: str, payload: bytes, *, capabilities=BUILDER_CAPABILITIES):  # type: ignore[no-untyped-def]
        """Hand one raw frame to a real handler and return the parsed reply."""
        broker = self.broker(capabilities)
        server = _FakeChannelServer(broker, secret)
        near, far = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            far.sendall(payload)
            far.shutdown(socket.SHUT_WR)
            # Constructing the handler runs setup/handle/finish, exactly as the
            # threading server does for one accepted connection.
            _ChannelHandler(near, ("", 0), server)
            near.close()
            reply = b""
            while True:
                chunk = far.recv(65536)
                if not chunk:
                    break
                reply += chunk
        finally:
            far.close()
        return json.loads(reply.decode("utf-8")), broker, server

    def test_the_right_secret_reaches_the_broker(self) -> None:
        reply, broker, _ = self.serve(
            "s" * 64, frame("s" * 64, {"operation": COMMENT_PR, "body": "hello"})
        )
        self.assertTrue(reply["ok"], reply)
        self.assertEqual(broker.granted, [COMMENT_PR])

    def test_a_wrong_secret_never_reaches_the_broker(self) -> None:
        """Former-red: refused before the JSON is even decoded."""
        reply, broker, server = self.serve(
            "s" * 64, frame("w" * 64, {"operation": PUSH_BRANCH})
        )
        self.assertFalse(reply["ok"])
        self.assertEqual(reply["error"], AUTH_REFUSED)
        self.assertEqual(broker.granted, [])
        self.assertEqual(broker.refused, [])
        self.assertEqual(self.runner.calls, [])
        self.assertEqual(server.unauthenticated, 1)

    def test_a_frame_with_no_secret_line_is_refused(self) -> None:
        reply, broker, _ = self.serve(
            "s" * 64, json.dumps({"operation": PUSH_BRANCH}).encode("utf-8")
        )
        self.assertFalse(reply["ok"])
        self.assertEqual(reply["error"], AUTH_REFUSED)
        self.assertEqual(self.runner.calls, [])

    def test_a_secret_that_is_a_prefix_of_the_real_one_is_refused(self) -> None:
        secret = "s" * 64
        reply, _, _ = self.serve(secret, frame(secret[:32], {"operation": PUSH_BRANCH}))
        self.assertFalse(reply["ok"])
        self.assertEqual(self.runner.calls, [])

    def test_the_refusal_is_the_same_whatever_was_wrong(self) -> None:
        """The reply is not an oracle for which lane a socket belongs to."""
        secret = "s" * 64
        wrong = self.serve(secret, frame("w" * 64, {"operation": PUSH_BRANCH}))[0]
        absent = self.serve(secret, b"\n" + json.dumps({"operation": PUSH_BRANCH}).encode())[0]
        self.assertEqual(wrong, absent)

    def test_authentication_is_a_constant_time_comparison(self) -> None:
        self.assertTrue(authenticates(b"abc", "abc"))
        self.assertFalse(authenticates(b"abc", "abd"))
        self.assertFalse(authenticates(b"", "abc"))
        self.assertFalse(authenticates(b"abc", ""))
        source = inspect.getsource(authenticates)
        self.assertIn("compare_digest", source)

    def test_a_frame_splits_into_secret_and_request(self) -> None:
        self.assertEqual(split_frame(b"sec\n{}"), (b"sec", b"{}"))
        self.assertEqual(split_frame(b"{}"), (b"", b""))
        self.assertEqual(split_frame(b""), (b"", b""))

    def test_an_authenticated_request_still_cannot_name_its_own_target(self) -> None:
        """Authentication is not authorisation: the vocabulary is still closed."""
        secret = "s" * 64
        reply, _, _ = self.serve(
            secret,
            frame(secret, {"operation": PUSH_BRANCH, "repo": "someone/else"}),
        )
        self.assertFalse(reply["ok"])
        self.assertIn("cannot name its own repository", reply["error"])
        self.assertEqual(self.runner.calls, [])


class _FakeChannelServer:
    """The two attributes a handler reads, without binding anything."""

    def __init__(self, broker: CapabilityBroker, secret: str) -> None:
        self.broker = broker
        self.secret = secret
        self.unauthenticated = 0

    def note_unauthenticated(self) -> None:
        self.unauthenticated += 1


class GeneratedShimTests(unittest.TestCase):
    """The shim is source code this module writes, so it has to be source code."""

    def test_the_generated_shim_is_valid_python(self) -> None:
        """Former-red: an escaping slip made the generated program unparsable.

        SHIM_SOURCE is an ordinary (non-raw) string literal, so an escape meant
        for the *generated* program needs writing twice. Getting that wrong
        produced a shim that failed with a SyntaxError only when a lane ran it.
        """
        ast.parse(SHIM_SOURCE)

    def test_the_written_shim_compiles_and_reports_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shim = write_shim(Path(tmp) / "bin")
            compile(shim.read_text(encoding="utf-8"), str(shim), "exec")
            result = subprocess.run(
                [sys.executable, str(shim)],
                capture_output=True,
                text=True,
                env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
                timeout=60,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage", result.stderr.lower())
        self.assertNotIn("SyntaxError", result.stderr)

    def test_the_generated_shim_sends_the_secret_as_the_first_line(self) -> None:
        self.assertIn('b"\\n"', SHIM_SOURCE)
        self.assertIn("PR_PROVER_CAPABILITY_SECRET", SHIM_SOURCE)
        # ...and reads it from the environment, never from argv.
        self.assertIn('os.environ.get("PR_PROVER_CAPABILITY_SECRET"', SHIM_SOURCE)


class ShimTests(BrokerTestCase):
    """The program a child actually runs, executed for real."""

    def setUp(self) -> None:
        super().setUp()
        self.shim = write_shim(self.tmp / "bin")
        self.channel = CapabilityChannel(self.broker(), label="lane-a")
        self.addCleanup(self.channel.close)

    def shim_run(
        self,
        *arguments: str,
        socket_path: str | None = None,
        secret: str | None = None,
    ) -> subprocess.CompletedProcess:
        """Run the real shim the way a lane would: socket and secret from the environment.

        Both come from the narrow child environment. Neither is on argv, where
        every process on the machine could read it, and neither is read from a
        file the request names.
        """
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        path = self.channel.path if socket_path is None else socket_path
        if path:
            env["PR_PROVER_CAPABILITY_SOCKET"] = str(path)
        issued = self.channel.secret if secret is None else secret
        if issued:
            env["PR_PROVER_CAPABILITY_SECRET"] = issued
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
        result = self.shim_run(
            "push", socket_path=str(channel.path), secret=channel.secret
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not carry the capability", result.stderr)

    def test_a_child_with_no_channel_can_do_nothing(self) -> None:
        result = self.shim_run("push", socket_path="")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no capability channel", result.stderr)

    def test_a_child_with_no_secret_can_do_nothing(self) -> None:
        """PAPI-90 item 2, former-red: the socket path alone buys nothing."""
        result = self.shim_run("push", secret="")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no capability channel secret", result.stderr)
        self.assertEqual(self.runner.calls, [])

    def test_a_child_presenting_another_lanes_secret_is_refused(self) -> None:
        """A lane that reads a sibling's socket path still cannot spend it."""
        other = CapabilityChannel(self.broker(REVIEWER_CAPABILITIES), label="lane-r")
        self.addCleanup(other.close)
        result = self.shim_run("push", secret=other.secret)
        self.assertEqual(result.returncode, 1)
        self.assertIn("secret", result.stderr)
        self.assertEqual(self.channel.broker.granted, [])
        self.assertEqual(self.runner.calls, [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
