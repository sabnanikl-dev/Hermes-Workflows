"""The trusted-agent contract: session, observability, and published identity.

The doubles elsewhere prove the loop's own logic. This module proves the parts
that decide whether a real Claude or Codex lane can be orchestrated at all:

* the lane inherits Karan's session and can only adjust it by name;
* a quiet lane is observed, not killed, and how it ended stays readable;
* what a lane says about GitHub is only believed once GitHub says it too —
  the builder's push, worktree, commit list, and signed comment, and each
  reviewer's own published artifact under its login, role, and exact head.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from _support import (
    HEAD_A,
    HEAD_B,
    HEAD_C,
    REVIEWER_LOGIN,
    REVIEWER_SIGNATURE,
    FakeGitHub,
    FakeRemote,
    FakeRunner,
    LaneScript,
    builder_output,
    fix_comment,
    make_config,
    make_source_repo,
    reviewer_artifact,
    reviewer_output,
)
from pr_prover import cli
from pr_prover.commands import EXITED, TIMED_OUT, Progress, SubprocessRunner
from pr_prover.config import REALISTIC_BUILDER_BUDGET, LaneEnv, RunConfig
from pr_prover.errors import CommandContractError, ConfigError
from pr_prover.loop import BLOCKED, MERGE_READY, NEEDS_KARAN, ProverLoop
from pr_prover.report import as_dict
from pr_prover.worktrees import SourceRepo, WorktreeProvider

BLOCKER = ("blocking", "null-deref", "crashes on empty input")


class TrustedLaneHarness(unittest.TestCase):
    """One loop over a temp directory, a fake remote, and scripted lanes."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-trusted-")
        self.tmp = Path(self._tmp.name).resolve()
        self.addCleanup(self._tmp.cleanup)
        self.source_repo = make_source_repo(self.tmp)
        self.remote = FakeRemote()
        self.script = LaneScript()
        self.runner = FakeRunner(self.remote, self.script)
        self.github = FakeGitHub(self.remote)

    def build(self, **config_kwargs) -> ProverLoop:
        config = make_config(self.tmp, source_repo=self.source_repo, **config_kwargs)
        self.config = config
        source = SourceRepo(runner=self.runner, path=config.source_repo)
        return ProverLoop(
            config,
            runner=self.runner,
            github=self.github,
            worktrees=WorktreeProvider(source, config.worktree_root),
            scratch_root=self.tmp / "scratch",
        )

    def review_round(self, head: str, findings=()) -> None:
        self.script.add("lane-reviewer-A", reviewer_output(head, findings))
        self.script.add("lane-reviewer-B", reviewer_output(head))

    def fix_round(self, new_head: str, *, addressed=("null-deref",), comment: bool = True) -> None:
        self.script.add(
            "lane-builder",
            builder_output(new_head, addressed=list(addressed)),
            after=lambda: self.remote.push(
                new_head, comment=fix_comment(new_head) if comment else None
            ),
        )


# -- the session the trusted agents authenticate with ----------------------
class LaneEnvironmentTests(unittest.TestCase):
    def test_an_empty_overlay_means_inherit_untouched(self) -> None:
        self.assertIsNone(LaneEnv().apply({"HOME": "/Users/karan", "PATH": "/usr/bin"}))

    def test_the_overlay_adds_and_removes_by_name_over_the_real_environment(self) -> None:
        overlay = LaneEnv(set=(("CLAUDE_LANE", "builder"),), unset=("GH_TOKEN",))
        env = overlay.apply({"HOME": "/Users/karan", "GH_TOKEN": "secret", "PATH": "/usr/bin"})
        self.assertEqual(
            env, {"HOME": "/Users/karan", "PATH": "/usr/bin", "CLAUDE_LANE": "builder"}
        )

    def test_unsetting_a_variable_that_is_absent_is_not_an_error(self) -> None:
        self.assertEqual(LaneEnv(unset=("GH_TOKEN",)).apply({"HOME": "/h"}), {"HOME": "/h"})


class LaneEnvironmentConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-env-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.clone = make_source_repo(self.tmp)

    def load(self, **builder_overrides: object) -> RunConfig:
        builder: dict = {
            "argv": ["claude", "--print", "--", "fix {pr}"],
            "signature": "Fixed by: Claude Code via Hermes orchestration",
            "comment_author": "the-builder-login",
        }
        builder.update(builder_overrides)
        return RunConfig.from_mapping(
            {
                "schema_version": 1,
                "repo": "example/repo",
                "pr": 7,
                "source_repo": str(self.clone),
                "worktree_root": "worktrees",
                "state_file": "state.json",
                "lock_file": "run.lock",
                "reviewers": [
                    {
                        "name": "A",
                        "role": "reviewer-a",
                        "argv": ["codex", "{role}", "{head}"],
                        "artifact_author": REVIEWER_LOGIN,
                        "artifact_signature": REVIEWER_SIGNATURE,
                    },
                    {
                        "name": "B",
                        "role": "reviewer-b",
                        "argv": ["codex", "{role}", "{head}"],
                        "artifact_author": REVIEWER_LOGIN,
                        "artifact_signature": REVIEWER_SIGNATURE,
                    },
                ],
                "builder": builder,
            },
            base_dir=self.tmp,
        )

    def test_a_lane_can_drop_the_operator_token_so_the_agent_uses_its_own_identity(self) -> None:
        config = self.load(env_unset=["GH_TOKEN"])
        self.assertEqual(config.builder.env.unset, ("GH_TOKEN",))

    def test_a_lane_cannot_retarget_the_session_home(self) -> None:
        for overlay in ({"env": {"HOME": "/tmp/synthetic"}}, {"env_unset": ["HOME"]}):
            with self.subTest(overlay=overlay):
                with self.assertRaises(ConfigError) as caught:
                    self.load(**overlay)
                self.assertEqual(caught.exception.evidence["name"], "HOME")

    def test_a_lane_cannot_retarget_the_session_user(self) -> None:
        for name in ("USER", "LOGNAME", "SHELL"):
            with self.subTest(name=name):
                with self.assertRaises(ConfigError):
                    self.load(env={name: "someone-else"})

    def test_a_credential_value_is_refused_in_the_run_config(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(env={"GH_TOKEN": "ghp_" + "x" * 36})
        self.assertIn("keychain", caught.exception.message)

    def test_an_unusable_variable_name_is_refused(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(env={"not a name": "value"})

    def test_a_non_string_value_is_refused(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(env={"CLAUDE_LANE": 7})

    def test_a_lane_environment_reaches_the_runner_over_the_real_environment(self) -> None:
        harness = _MinimalLoop(self)
        harness.run_clean_pass(
            reviewer_env={"env": {"PR_PROVER_LANE": "reviewer"}, "env_unset": ["GH_TOKEN"]}
        )
        overlays = [env for env in harness.runner.envs if env is not None]
        self.assertTrue(overlays)
        for env in overlays:
            self.assertEqual(env["PR_PROVER_LANE"], "reviewer")
            self.assertNotIn("GH_TOKEN", env)
            # Inherited, not rebuilt: the session variables are still there.
            self.assertEqual(env.get("HOME"), os.environ.get("HOME"))

    def test_a_lane_without_an_overlay_inherits_the_environment_untouched(self) -> None:
        harness = _MinimalLoop(self)
        harness.run_clean_pass()
        self.assertTrue(harness.runner.envs)
        self.assertTrue(all(env is None for env in harness.runner.envs))


class _MinimalLoop:
    """A clean pass, used by the environment tests to reach the runner."""

    def __init__(self, test: unittest.TestCase) -> None:
        self._dir = tempfile.TemporaryDirectory(prefix="pr-prover-envloop-")
        test.addCleanup(self._dir.cleanup)
        self.tmp = Path(self._dir.name).resolve()
        self.remote = FakeRemote()
        self.script = LaneScript()
        self.runner = FakeRunner(self.remote, self.script)
        self.github = FakeGitHub(self.remote)
        self.source_repo = make_source_repo(self.tmp)

    def run_clean_pass(self, *, reviewer_env: dict | None = None) -> None:
        config = make_config(self.tmp, source_repo=self.source_repo, reviewer_env=reviewer_env)
        source = SourceRepo(runner=self.runner, path=config.source_repo)
        loop = ProverLoop(
            config,
            runner=self.runner,
            github=self.github,
            worktrees=WorktreeProvider(source, config.worktree_root),
            scratch_root=self.tmp / "scratch",
        )
        self.script.add("lane-reviewer-A", reviewer_output(HEAD_A))
        self.script.add("lane-reviewer-B", reviewer_output(HEAD_A))
        loop.run()


# -- quiet is not a hang ---------------------------------------------------
@unittest.skipIf(not sys.executable, "a python interpreter is required")
class ObservableProcessStateTests(unittest.TestCase):
    def runner(self, **kwargs) -> SubprocessRunner:
        kwargs.setdefault("poll_interval", 0.01)
        kwargs.setdefault("progress_interval", 0.05)
        return SubprocessRunner(default_timeout=30.0, **kwargs)

    def python(self, source: str) -> list[str]:
        return [sys.executable, "-c", source]

    def test_a_quiet_lane_that_finishes_is_a_success_not_a_hang(self) -> None:
        seen: list[Progress] = []
        result = self.runner().run(
            self.python("import time; time.sleep(0.4); print('DONE: STATUS=pass')"),
            progress=seen.append,
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.state, EXITED)
        self.assertIn("DONE: STATUS=pass", result.stdout)
        self.assertTrue(seen, "a long-running lane must be observed while it runs")
        # It was observed producing nothing at all, and still succeeded.
        self.assertEqual(seen[0].output_bytes, 0)
        self.assertGreater(seen[0].quiet_seconds, 0.0)

    def test_progress_reports_output_as_it_appears(self) -> None:
        seen: list[Progress] = []
        result = self.runner().run(
            self.python(
                "import sys, time\n"
                "print('working', flush=True)\n"
                "time.sleep(0.4)\n"
                "print('DONE: STATUS=pass')\n"
            ),
            progress=seen.append,
        )

        self.assertTrue(result.ok)
        self.assertTrue(any(update.output_bytes > 0 for update in seen))

    def test_a_lane_is_only_ended_by_its_own_budget(self) -> None:
        result = self.runner().run(
            self.python("import time; time.sleep(30)"), timeout=0.3
        )

        self.assertTrue(result.timed_out)
        self.assertEqual(result.state, TIMED_OUT)
        self.assertEqual(result.returncode, 124)
        self.assertGreaterEqual(result.duration, 0.3)

    def test_partial_output_from_a_timed_out_lane_is_preserved(self) -> None:
        result = self.runner().run(
            self.python("import time; print('partial', flush=True); time.sleep(30)"),
            timeout=0.3,
        )

        self.assertTrue(result.timed_out)
        self.assertIn("partial", result.stdout)

    def test_a_child_that_ignores_the_polite_stop_is_still_ended(self) -> None:
        result = self.runner(kill_grace=0.2).run(
            self.python(
                "import signal, time\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "time.sleep(30)\n"
            ),
            timeout=0.3,
        )

        self.assertTrue(result.timed_out)

    def test_a_failing_lane_reports_its_exit_code_rather_than_raising(self) -> None:
        result = self.runner().run(self.python("raise SystemExit(3)"))

        self.assertFalse(result.ok)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.state, EXITED)

    def test_a_lane_that_cannot_be_launched_fails_closed(self) -> None:
        with self.assertRaises(CommandContractError) as caught:
            self.runner().run(["pr-prover-no-such-agent-binary"])
        self.assertEqual(caught.exception.reason, "invalid-command")

    def test_the_lane_environment_is_inherited_unless_it_is_replaced(self) -> None:
        os.environ["PR_PROVER_SESSION_PROBE"] = "inherited"
        self.addCleanup(os.environ.pop, "PR_PROVER_SESSION_PROBE", None)

        result = self.runner().run(
            self.python("import os; print(os.environ.get('PR_PROVER_SESSION_PROBE', 'missing'))")
        )

        self.assertEqual(result.stdout.strip(), "inherited")

    def test_a_lane_gets_no_stdin_to_block_on(self) -> None:
        result = self.runner().run(self.python("print(repr(__import__('sys').stdin.read()))"))

        self.assertTrue(result.ok)
        self.assertEqual(result.stdout.strip(), "''")


class LaneObservationReportTests(TrustedLaneHarness):
    def test_every_lane_result_reaches_the_report(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        payload = as_dict(loop.run())

        lanes = {lane["lane"]: lane for lane in payload["lanes"]}
        self.assertEqual(set(lanes), {"reviewer A", "reviewer B"})
        for lane in lanes.values():
            self.assertEqual(lane["state"], "exited")
            self.assertEqual(lane["returncode"], 0)

    def test_a_timed_out_lane_is_reported_as_timed_out(self) -> None:
        loop = self.build()
        self.script.add("lane-reviewer-A", reviewer_output(HEAD_A), timed_out=True, returncode=124)

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "lane-failure")
        self.assertEqual([lane.state for lane in result.lanes], ["timed-out"])

    def test_a_lane_that_cannot_be_launched_stops_the_run(self) -> None:
        """A missing agent binary or a broken auth wrapper is not a verdict."""
        loop = self.build()

        def refuse() -> None:
            raise CommandContractError(
                "could not launch lane-reviewer-A: No such file or directory",
                evidence={"argv": ["lane-reviewer-A"]},
            )

        self.script.add("lane-reviewer-A", "", after=refuse)

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "invalid-command")
        self.assertEqual(result.lanes, ())

    def test_the_run_log_records_the_launch_and_the_budget(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertIn("reviewer A launched: lane-reviewer-A (budget unbounded)", result.events)


# -- reviewer artifacts: identity, role, exact head ------------------------
class ReviewerArtifactReadbackTests(TrustedLaneHarness):
    def test_a_published_comment_under_the_configured_identity_satisfies_readback(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertIn(
            f"reviewer A comment IC_comment1 read back for {HEAD_A} as ROLE=reviewer-a",
            result.events,
        )

    def test_a_formal_review_binds_through_its_own_commit_id(self) -> None:
        loop = self.build()
        self.runner.reviewer_artifact_kind = "review"
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertEqual([review.commit_id for review in self.remote.reviews], [HEAD_A, HEAD_A])

    def test_a_review_submitted_against_another_commit_does_not_satisfy_readback(self) -> None:
        loop = self.build()
        self.runner.reviewer_artifact_kind = "review"
        self.runner.reviewer_artifact_head = HEAD_C
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "readback-mismatch")

    def test_a_lane_that_publishes_nothing_stops_the_run(self) -> None:
        loop = self.build()
        self.runner.publish_reviewer_artifacts = False
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "readback-mismatch")
        self.assertEqual(result.evidence["evidence"]["reviewer"], "A")

    def test_an_artifact_from_another_login_does_not_satisfy_readback(self) -> None:
        loop = self.build()
        self.runner.reviewer_artifact_author = "sabnanikl-dev"
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.reason, "readback-mismatch")
        self.assertEqual(result.evidence["evidence"]["expected_author"], REVIEWER_LOGIN)

    def test_an_artifact_for_another_role_does_not_satisfy_readback(self) -> None:
        loop = self.build()
        self.runner.reviewer_artifact_role = "reviewer-b"
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.reason, "readback-mismatch")
        self.assertEqual(result.evidence["evidence"]["expected_role_line"], "ROLE=reviewer-a")

    def test_a_role_line_is_matched_whole_not_as_a_prefix(self) -> None:
        loop = self.build()
        self.runner.reviewer_artifact_role = "reviewer-away"
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.reason, "readback-mismatch")

    def test_an_artifact_for_another_head_does_not_satisfy_readback(self) -> None:
        loop = self.build()
        self.runner.reviewer_artifact_head = HEAD_C
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.reason, "readback-mismatch")

    def test_an_unsigned_artifact_does_not_satisfy_readback(self) -> None:
        loop = self.build()
        self.runner.reviewer_artifact_signature = "posted by somebody"
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.reason, "readback-mismatch")

    def test_an_artifact_that_predates_the_lane_does_not_satisfy_readback(self) -> None:
        """A copy sitting on the PR already is by construction not this run's."""
        loop = self.build()
        self.remote.comment(reviewer_artifact("reviewer-a", HEAD_A), author=REVIEWER_LOGIN)
        self.runner.publish_reviewer_artifacts = False
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.reason, "readback-mismatch")
        self.assertEqual(result.evidence["evidence"]["artifacts_since_lane_launched"], 0)

    def test_a_fresh_artifact_is_required_again_after_a_fix_push(self) -> None:
        """The head moved, so the previous head's artifacts prove nothing now."""
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.fix_round(HEAD_B)
        self.review_round(HEAD_B)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertEqual(result.head, HEAD_B)
        published = [comment for comment in self.remote.comments if comment.author == REVIEWER_LOGIN]
        self.assertEqual(len(published), 4)
        self.assertEqual(sum(1 for item in published if HEAD_B in item.body), 2)


# -- builder claims, reconciled against GitHub -----------------------------
class BuilderPushReconciliationTests(TrustedLaneHarness):
    def test_a_fix_push_is_bound_to_the_commit_it_added(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.fix_round(HEAD_B)
        self.review_round(HEAD_B)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertIn(f"push verified: {HEAD_A} -> {HEAD_B} (1 new commit(s))", result.events)
        self.assertIn(f"attempt worktree local head verified as {HEAD_B}", result.events)

    def test_a_rewritten_branch_is_not_an_ordinary_fix_push(self) -> None:
        """The reviewed commit is gone from the branch: history was replaced."""
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])

        def rewrite() -> None:
            self.remote.head = HEAD_B
            self.remote.history = [HEAD_C, HEAD_B]

        self.script.add(
            "lane-builder", builder_output(HEAD_B, addressed=["null-deref"]), after=rewrite
        )

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "stale-head")
        self.assertEqual(result.evidence["evidence"]["dropped"], [HEAD_A])

    def test_a_worktree_that_is_not_on_the_pushed_commit_stops_the_run(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.fix_round(HEAD_B)
        self.runner.local_head = HEAD_C

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "readback-mismatch")
        self.assertEqual(result.evidence["evidence"]["local_head"], HEAD_C)

    def test_two_cycles_then_blocked_with_every_push_reconciled(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.fix_round(HEAD_B)
        self.review_round(HEAD_B, [BLOCKER])
        self.fix_round(HEAD_C)
        self.review_round(HEAD_C, [BLOCKER])

        result = loop.run()

        self.assertEqual(result.outcome, BLOCKED)
        self.assertEqual(result.reason, "attempt-cap-reached")
        self.assertEqual(result.attempts_used, 2)
        self.assertEqual(result.head, HEAD_C)
        self.assertTrue(self.script.exhausted)
        self.assertIn(f"push verified: {HEAD_B} -> {HEAD_C} (1 new commit(s))", result.events)


# -- shipped configuration -------------------------------------------------
class ShippedConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-shipped-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.clone = make_source_repo(self.tmp)
        self.examples = Path(__file__).resolve().parents[1] / "examples"

    def example(self) -> RunConfig:
        payload = json.loads((self.examples / "run.example.json").read_text(encoding="utf-8"))
        payload["source_repo"] = str(self.clone)
        return RunConfig.from_mapping(payload, base_dir=self.tmp)

    def test_the_example_configures_three_exact_head_review_roles(self) -> None:
        config = self.example()
        self.assertEqual(
            [reviewer.role for reviewer in config.reviewers],
            ["reviewer-a", "reviewer-b", "integration-auditor"],
        )

    def test_the_example_builder_is_a_real_claude_invocation(self) -> None:
        argv = self.example().builder.argv
        self.assertEqual(argv[0], "claude")
        self.assertIn("--print", argv)
        # Empty MCP for non-interactive reliability, and a task-scoped tool set.
        self.assertIn("--strict-mcp-config", argv)
        self.assertIn("--allowedTools", argv)
        # The prompt points at the live PR and the blocker file rather than
        # pasting reviewer prose into the lane.
        self.assertIn("Read the live PR yourself", argv[-1])
        self.assertIn("{blockers_file}", argv[-1])

    def test_the_example_budgets_are_realistic_and_raise_no_advisory(self) -> None:
        config = self.example()
        self.assertGreaterEqual(config.builder.timeout, REALISTIC_BUILDER_BUDGET)
        self.assertEqual(config.advisories(), ())

    def test_the_example_lanes_drop_the_operator_token(self) -> None:
        config = self.example()
        self.assertEqual(config.builder.env.unset, ("GH_TOKEN",))
        for reviewer in config.reviewers:
            self.assertEqual(reviewer.env.unset, ("GH_TOKEN",))

    def test_the_shipped_empty_mcp_config_is_empty(self) -> None:
        payload = json.loads((self.examples / "claude-empty-mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(payload, {"mcpServers": {}})

    def test_a_short_builder_budget_is_flagged_as_an_advisory_not_an_error(self) -> None:
        payload = json.loads((self.examples / "run.example.json").read_text(encoding="utf-8"))
        payload["source_repo"] = str(self.clone)
        payload["builder"]["timeout"] = 120
        config = RunConfig.from_mapping(payload, base_dir=self.tmp)
        self.assertTrue(any("builder timeout" in note for note in config.advisories()))

    def test_check_config_prints_the_identities_it_will_hold_lanes_to(self) -> None:
        payload = json.loads((self.examples / "run.example.json").read_text(encoding="utf-8"))
        payload["source_repo"] = str(self.clone)
        payload["worktree_root"] = str(self.tmp / "worktrees")
        payload["state_file"] = str(self.tmp / "state.json")
        payload["lock_file"] = str(self.tmp / "run.lock")
        config_path = self.tmp / "run.json"
        config_path.write_text(json.dumps(payload), encoding="utf-8")

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = cli.main(["check-config", "--config", str(config_path)])

        self.assertEqual(code, 0)
        printed = stdout.getvalue()
        self.assertIn("reviewer Integration Auditor: role integration-auditor", printed)
        self.assertIn("publishes as the-reviewer-login", printed)
        self.assertIn("builder: comments as the-builder-login", printed)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
