"""The credential-free reviewer lifecycle, driven through real processes.

Every other reviewer test uses a runner double that publishes as a side effect
of being called, which proves the loop's rules but not that a real Codex lane
could ever reach GitHub through this tool. So these tests use the real
:class:`SubprocessRunner`, real reviewer and relay executables, and a GitHub
boundary that can only see what a real process actually published:

    credential-free audit  ->  prepared artifact under the OS temp directory
      ->  trusted relay publishing under the reviewer identity
      ->  readback of what landed

The reviewer script refuses to write anything to the publication spool, and the
boundary reads only that spool, so readback can succeed only after the relay has
genuinely run. The shipped ``scripts/codex-reviewer.sh`` adapter is exercised
here too, against a stub Codex, so the executable the example config names is
covered rather than assumed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _support import (
    HEAD_A,
    REVIEWER_LOGIN,
    REVIEWER_SIGNATURE,
    Call,
    FakeRemote,
    FakeRunner,
    LaneScript,
    make_source_repo,
)
from pr_prover.commands import SubprocessRunner, validate_argv
from pr_prover.config import RunConfig
from pr_prover.github import Comment, PullRequest, ReviewThread
from pr_prover.loop import MERGE_READY, NEEDS_KARAN, ProverLoop
from pr_prover.reviewers import CREDENTIAL_ENV
from pr_prover.worktrees import SourceRepo, WorktreeProvider

ADAPTER = Path(__file__).resolve().parents[1] / "scripts" / "codex-reviewer.sh"

# The reviewer lane: an audit with no GitHub credential, which records the
# credential-shaped variables it could see, writes its finished artifact, and
# prints its verdict. It cannot publish, and does not try.
REVIEWER_SOURCE = """\
import json, os, sys

artifact, probe, head, role, signature = sys.argv[1:6]
credentials = sorted(
    name
    for name in os.environ
    if name in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN")
)
with open(probe, "w", encoding="utf-8") as stream:
    json.dump({"credentials": credentials, "home": os.environ.get("HOME")}, stream)
body = os.environ.get("PR_PROVER_TEST_BODY")
if body is None:
    body = "Audited this head.\\n\\n---\\n%s\\nROLE=%s\\nHEAD=%s\\n" % (signature, role, head)
if body != "<none>":
    with open(artifact, "w", encoding="utf-8") as stream:
        stream.write(body)
print("DONE: STATUS=pass BLOCKING=0 HEAD=%s" % head)
"""

# The relay: the only half that publishes. It copies the prepared artifact into
# the spool the GitHub boundary reads, under the configured reviewer login.
RELAY_SOURCE = """\
import json, os, sys

artifact, spool, author = sys.argv[1:4]
if os.environ.get("PR_PROVER_TEST_RELAY_FAILS") == "1":
    sys.stderr.write("relay refused\\n")
    raise SystemExit(1)
body = open(artifact, encoding="utf-8").read()
os.makedirs(spool, exist_ok=True)
name = "artifact-%d.json" % (len(os.listdir(spool)) + 1)
with open(os.path.join(spool, name), "w", encoding="utf-8") as stream:
    json.dump({"author": author, "body": body}, stream)
"""


class SpoolGitHub:
    """A GitHub boundary that can only see what a real process published.

    Comments come from a directory on disk. Nothing in the loop and nothing in
    the reviewer lane writes there — only the relay does — so "the artifact was
    read back" means a relay process really ran and really published.
    """

    def __init__(self, remote: FakeRemote, spool: Path) -> None:
        self.remote = remote
        self.spool = spool

    def pull_request(self, repo: str, number: int) -> PullRequest:
        return self.remote.pull_request()

    def comments(self, repo: str, number: int) -> tuple[Comment, ...]:
        published = []
        for index, path in enumerate(sorted(self.spool.glob("*.json")), start=1):
            payload = json.loads(path.read_text(encoding="utf-8"))
            published.append(
                Comment(
                    identifier=f"IC_relayed{index}",
                    author=payload["author"],
                    body=payload["body"],
                )
            )
        return tuple(published)

    def reviews(self, repo: str, number: int) -> tuple[Comment, ...]:
        return ()

    def review_threads(self, repo: str, number: int) -> tuple[ReviewThread, ...]:
        return ()

    @property
    def published(self) -> int:
        return len(list(self.spool.glob("*.json")))


class RealLaneRunner(FakeRunner):
    """Scripted git, real everything else. Lanes are actual processes here."""

    def __init__(self, remote: FakeRemote, real: SubprocessRunner) -> None:
        super().__init__(remote, LaneScript())
        self.real = real

    def run(self, argv, *, cwd=None, env=None, timeout=None, progress=None):
        checked = validate_argv(argv)
        if checked[0] == "git":
            return super().run(argv, cwd=cwd, env=env, timeout=timeout, progress=progress)
        self.calls.append(Call(argv=checked, cwd=str(cwd) if cwd is not None else None))
        self.envs.append(env)
        return self.real.run(checked, cwd=cwd, env=env, timeout=timeout, progress=progress)


class ReviewerRelayLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-relay-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.spool = self.tmp / "published"
        self.spool.mkdir()
        self.probes = self.tmp / "probes"
        self.probes.mkdir()
        self.reviewer_script = self._write("reviewer.py", REVIEWER_SOURCE)
        self.relay_script = self._write("relay.py", RELAY_SOURCE)
        self.source_repo = make_source_repo(self.tmp)
        self.remote = FakeRemote()
        self.runner = RealLaneRunner(
            self.remote, SubprocessRunner(default_timeout=60.0, poll_interval=0.01)
        )
        self.github = SpoolGitHub(self.remote, self.spool)
        # The operator's own token is in the environment, which is the whole
        # point: the reviewer lane must not be able to see it.
        os.environ["GH_TOKEN"] = "ghp_" + "operator" * 4
        self.addCleanup(os.environ.pop, "GH_TOKEN", None)

    def _write(self, name: str, source: str) -> Path:
        path = self.tmp / name
        path.write_text(source, encoding="utf-8")
        return path

    def build(self, *, relay: bool = True) -> ProverLoop:
        reviewers = []
        for name, role in (("A", "reviewer-a"), ("B", "reviewer-b")):
            lane: dict[str, object] = {
                "name": name,
                "role": role,
                "argv": [
                    sys.executable,
                    str(self.reviewer_script),
                    "{artifact_file}",
                    str(self.probes / f"{name}.json"),
                    "{head}",
                    "{role}",
                    REVIEWER_SIGNATURE,
                ],
                "artifact_author": REVIEWER_LOGIN,
                "artifact_signature": REVIEWER_SIGNATURE,
                "timeout": 60,
            }
            if relay:
                lane["relay"] = {
                    "argv": [
                        sys.executable,
                        str(self.relay_script),
                        "{artifact_file}",
                        str(self.spool),
                        REVIEWER_LOGIN,
                    ],
                    "timeout": 60,
                }
            reviewers.append(lane)
        config = RunConfig.from_mapping(
            {
                "schema_version": 1,
                "repo": "example/repo",
                "pr": 7,
                "branch": self.remote.branch,
                "base": "main",
                "source_repo": str(self.source_repo),
                "worktree_root": str(self.tmp / "worktrees"),
                "state_file": str(self.tmp / "state.json"),
                "lock_file": str(self.tmp / "run.lock"),
                "reviewers": reviewers,
                "builder": {
                    "argv": ["lane-builder", "--head", "{head}"],
                    "signature": "Fixed by: Claude Code via Hermes orchestration",
                    "comment_author": "the-builder-login",
                },
            },
            base_dir=self.tmp,
        )
        self.config = config
        source = SourceRepo(runner=self.runner, path=config.source_repo)
        return ProverLoop(
            config,
            runner=self.runner,
            github=self.github,
            worktrees=WorktreeProvider(source, config.worktree_root),
            scratch_root=self.tmp / "scratch",
        )

    def probe(self, reviewer: str) -> dict:
        return json.loads((self.probes / f"{reviewer}.json").read_text(encoding="utf-8"))

    # -- the lifecycle end to end -----------------------------------------
    def test_audit_prepare_relay_and_readback_complete_a_clean_pass(self) -> None:
        result = self.build().run()

        self.assertEqual(result.outcome, MERGE_READY, result.evidence)
        self.assertEqual(self.github.published, 2)
        for reviewer in ("A", "B"):
            with self.subTest(reviewer=reviewer):
                self.assertTrue(
                    any(
                        f"reviewer {reviewer} artifact relayed for {HEAD_A}" in event
                        for event in result.events
                    ),
                    result.events,
                )
                self.assertTrue(
                    any(
                        f"reviewer {reviewer} comment" in event and "read back" in event
                        for event in result.events
                    ),
                    result.events,
                )

    def test_the_reviewer_process_never_holds_a_github_credential(self) -> None:
        self.build().run()

        for reviewer in ("A", "B"):
            with self.subTest(reviewer=reviewer):
                self.assertEqual(self.probe(reviewer)["credentials"], [])
                # Dropped by name, not by rebuilding the session around it.
                self.assertEqual(self.probe(reviewer)["home"], os.environ.get("HOME"))

    def test_the_relay_still_sees_the_identity_it_publishes_with(self) -> None:
        """Only the reviewer half is credential-free; the transport is not."""
        loop = self.build()
        loop.run()

        relay_calls = [
            call for call in self.runner.calls if str(self.relay_script) in call.argv
        ]
        self.assertEqual(len(relay_calls), 2)
        relay_envs = [env for env in self.runner.envs if env is None]
        self.assertTrue(relay_envs, "the relay inherits the session untouched")

    def test_nothing_is_published_until_the_relay_runs(self) -> None:
        """A lane that prepared nothing stops the run with an empty PR behind it."""
        os.environ["PR_PROVER_TEST_BODY"] = "<none>"
        self.addCleanup(os.environ.pop, "PR_PROVER_TEST_BODY", None)

        result = self.build().run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "relay-failure")
        self.assertIn("prepared no artifact", result.evidence["message"])
        self.assertEqual(self.github.published, 0)

    def test_an_artifact_bound_to_another_head_never_reaches_github(self) -> None:
        os.environ["PR_PROVER_TEST_BODY"] = (
            f"Audited something else.\n\n---\n{REVIEWER_SIGNATURE}\n"
            f"ROLE=reviewer-a\nHEAD={'d' * 40}\n"
        )
        self.addCleanup(os.environ.pop, "PR_PROVER_TEST_BODY", None)

        result = self.build().run()

        self.assertEqual(result.reason, "relay-failure")
        self.assertIn("not bound to this exact head", result.evidence["message"])
        self.assertEqual(self.github.published, 0)

    def test_an_artifact_without_its_role_line_never_reaches_github(self) -> None:
        os.environ["PR_PROVER_TEST_BODY"] = (
            f"Audited this head.\n\n---\n{REVIEWER_SIGNATURE}\nHEAD={HEAD_A}\n"
        )
        self.addCleanup(os.environ.pop, "PR_PROVER_TEST_BODY", None)

        result = self.build().run()

        self.assertEqual(result.reason, "relay-failure")
        self.assertIn("role on its own line", result.evidence["message"])
        self.assertEqual(self.github.published, 0)

    def test_an_unsigned_artifact_never_reaches_github(self) -> None:
        os.environ["PR_PROVER_TEST_BODY"] = f"Audited this head.\n\nROLE=reviewer-a\nHEAD={HEAD_A}\n"
        self.addCleanup(os.environ.pop, "PR_PROVER_TEST_BODY", None)

        result = self.build().run()

        self.assertEqual(result.reason, "relay-failure")
        self.assertIn("configured signature", result.evidence["message"])
        self.assertEqual(self.github.published, 0)

    def test_a_relay_that_cannot_publish_stops_the_run(self) -> None:
        os.environ["PR_PROVER_TEST_RELAY_FAILS"] = "1"
        self.addCleanup(os.environ.pop, "PR_PROVER_TEST_RELAY_FAILS", None)

        result = self.build().run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "relay-failure")
        self.assertIn("did not publish", result.evidence["message"])
        self.assertEqual(self.github.published, 0)

    def test_a_relayed_artifact_is_still_held_to_readback(self) -> None:
        """Relaying is transport, not proof: the wrong login still fails closed."""
        loop = self.build()
        # Publish under an account that is not the configured reviewer identity.
        for reviewer in self.config.reviewers:
            object.__setattr__(
                reviewer.relay,
                "argv",
                tuple(
                    "someone-else" if part == REVIEWER_LOGIN else part
                    for part in reviewer.relay.argv
                ),
            )

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "readback-mismatch")
        # It really did publish; the run stopped because of who published it.
        self.assertEqual(self.github.published, 1)
        self.assertEqual(self.github.comments("example/repo", 7)[0].author, "someone-else")

    def test_a_reviewer_without_a_relay_keeps_publishing_for_itself(self) -> None:
        """The older self-publishing path is unchanged, credential and all."""
        loop = self.build(relay=False)

        result = loop.run()

        # Nothing published: this lane was expected to do it and did not.
        self.assertEqual(result.reason, "readback-mismatch")
        self.assertEqual(self.probe("A")["credentials"], ["GH_TOKEN"])


class ShippedAdapterTests(unittest.TestCase):
    """The executable the example config names, against a stub Codex."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-adapter-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.artifact = self.tmp / "artifact.md"
        self.worktree = self.tmp / "worktree"
        self.worktree.mkdir()
        self.codex = self.tmp / "codex"
        self.codex.write_text(
            "#!/bin/sh\n"
            '# stub Codex: "exec" plus one prompt, which it echoes back.\n'
            '[ "$1" = "exec" ] || { echo "unexpected subcommand: $1" >&2; exit 2; }\n'
            'printf "%s\\n" "$2" > "$PR_PROVER_STUB_PROMPT"\n'
            'printf "DONE: STATUS=pass BLOCKING=0 HEAD=%s\\n" "$PR_PROVER_STUB_HEAD"\n',
            encoding="utf-8",
        )
        self.codex.chmod(0o755)
        self.prompt = self.tmp / "prompt.txt"

    def adapter(self, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        environment = dict(os.environ)
        for name in CREDENTIAL_ENV:
            environment.pop(name, None)
        environment.update(
            {
                "PR_PROVER_CODEX": str(self.codex),
                "PR_PROVER_STUB_PROMPT": str(self.prompt),
                "PR_PROVER_STUB_HEAD": HEAD_A,
            }
        )
        environment.update(env or {})
        return subprocess.run(
            [
                str(ADAPTER),
                "--role", "reviewer-a",
                "--repo", "example/repo",
                "--pr", "7",
                "--head", HEAD_A,
                "--worktree", str(self.worktree),
                "--artifact-file", str(self.artifact),
                "--signature", REVIEWER_SIGNATURE,
            ],
            capture_output=True,
            text=True,
            env=environment,
            timeout=60,
        )

    def test_it_runs_codex_and_passes_its_verdict_through(self) -> None:
        result = self.adapter()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip().splitlines()[-1],
            f"DONE: STATUS=pass BLOCKING=0 HEAD={HEAD_A}",
        )

    def test_the_prompt_names_the_artifact_file_the_role_and_the_exact_head(self) -> None:
        self.adapter()

        prompt = self.prompt.read_text(encoding="utf-8")
        self.assertIn(str(self.artifact), prompt)
        self.assertIn("ROLE=reviewer-a", prompt)
        self.assertIn(HEAD_A, prompt)
        self.assertIn(REVIEWER_SIGNATURE, prompt)
        self.assertIn("You have no GitHub credential", prompt.replace("\n", " "))

    def test_it_refuses_to_run_with_a_github_credential_in_its_environment(self) -> None:
        """Every name the lifecycle calls a credential, not just the first two.

        ``CREDENTIAL_ENV`` is what pr-prover strips from the lane; an adapter
        that rejects a subset of it lets a real credential reach Codex while
        still claiming the lane is credential-free.
        """
        self.assertEqual(
            CREDENTIAL_ENV,
            ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"),
        )
        for name in CREDENTIAL_ENV:
            with self.subTest(name=name):
                result = self.adapter(env={name: "ghp_" + "x" * 36})
                self.assertEqual(result.returncode, 78, result.stderr)
                self.assertIn("credential", result.stderr)
                self.assertIn(name, result.stderr)
                self.assertFalse(self.prompt.exists(), "Codex was launched anyway")

    def test_an_empty_credential_variable_is_not_a_credential(self) -> None:
        """Exported-but-empty is how a shell clears one; it must not fail closed."""
        result = self.adapter(env={name: "" for name in CREDENTIAL_ENV})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.prompt.exists(), "Codex was not launched")

    def test_a_credential_leaves_a_prepared_artifact_untouched(self) -> None:
        """The refusal happens before the adapter does anything at all."""
        self.artifact.write_text("an earlier artifact\n", encoding="utf-8")

        result = self.adapter(env={"GITHUB_ENTERPRISE_TOKEN": "ghp_" + "x" * 36})

        self.assertEqual(result.returncode, 78)
        self.assertEqual(self.artifact.read_text(encoding="utf-8"), "an earlier artifact\n")

    def test_a_missing_argument_is_a_usage_error_not_a_review(self) -> None:
        result = subprocess.run(
            [str(ADAPTER), "--role", "reviewer-a"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        self.assertEqual(result.returncode, 64)
        self.assertIn("usage:", result.stderr)

    def test_a_missing_codex_binary_fails_closed(self) -> None:
        result = self.adapter(env={"PR_PROVER_CODEX": str(self.tmp / "no-such-codex")})

        self.assertEqual(result.returncode, 127)
        self.assertIn("no Codex CLI found", result.stderr)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
