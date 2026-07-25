"""The hardened launchers: argv composition, credential scope, and launch discipline."""
from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from _support import (
    BUILDER_LOGIN,
    BUILDER_TOKEN,
    FORBIDDEN_VALUES,
    HEAD_A,
    REVIEWER_LOGIN,
    REVIEWER_TOKEN,
    FakeVerifier,
    make_broker,
    make_config,
    make_source_repo,
    parent_env,
)

from pr_prover.childenv import carries_none_of
from pr_prover.commands import CommandResult
from pr_prover.errors import IdentityError, LaunchPolicyError
from pr_prover.launchers import (
    BUDGET_MAX,
    BUDGET_MIN,
    DEFAULT_BUDGET,
    AgentSpec,
    BoundContext,
    LaunchBroker,
    assert_launchable,
    quiet,
)

BOUND = BoundContext(repo="example/repo", pr=7, branch="feat/example", base="main", head=HEAD_A)
BUILDER_AGENT = AgentSpec(program="claude", model="opus", tools=("Read", "Edit", "Bash"))
REVIEWER_AGENT = AgentSpec(program="claude", model="sonnet", tools=("Read", "Grep", "Bash"))


class RecordingRunner:
    """Records exactly what each child would have been launched with."""

    def __init__(self, stdout: str = "done\n", returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.calls: list[dict[str, object]] = []

    def run(self, argv, *, cwd=None, env=None, timeout=None):  # type: ignore[no-untyped-def]
        self.calls.append(
            {
                "argv": tuple(argv),
                "cwd": str(cwd) if cwd is not None else None,
                "env": dict(env or {}),
                "timeout": timeout,
            }
        )
        return CommandResult(
            argv=tuple(argv), returncode=self.returncode, stdout=self.stdout, stderr=""
        )

    @property
    def last(self) -> dict[str, object]:
        return self.calls[-1]


class LauncherTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.config = make_config(self.tmp, source_repo=make_source_repo(self.tmp), scoped=True)
        self.worktree = self.config.worktree_root / "attempt1"
        self.worktree.mkdir(parents=True)
        self.runner = RecordingRunner()
        self.broker = self.make_broker()

    def make_broker(self, **kwargs: object) -> LaunchBroker:
        broker = make_broker(self.config, self.runner, scratch_root=self.tmp, **kwargs)  # type: ignore[arg-type]
        self.addCleanup(broker.close)
        return broker

    def run_builder(self, **overrides: object) -> CommandResult:
        arguments: dict[str, object] = {
            "identity": "builder",
            "agent": BUILDER_AGENT,
            "argv": None,
            "bound": BOUND,
            "cwd": self.worktree,
            "timeout": None,
            "attempt": 1,
            "mode": "initial",
            "blockers_file": self.tmp / "blockers.json",
            "signature": "Fixed by: a signature long enough",
        }
        arguments.update(overrides)
        return self.broker.run_builder(**arguments)  # type: ignore[arg-type]

    def run_reviewer(self, **overrides: object) -> CommandResult:
        arguments: dict[str, object] = {
            "role": "A",
            "identity": "reviewer",
            "agent": REVIEWER_AGENT,
            "argv": None,
            "bound": BOUND,
            "cwd": self.worktree,
            "timeout": None,
        }
        arguments.update(overrides)
        return self.broker.run_reviewer(**arguments)  # type: ignore[arg-type]

    @property
    def env(self) -> dict[str, str]:
        return self.runner.last["env"]  # type: ignore[return-value]

    @property
    def argv(self) -> tuple[str, ...]:
        return self.runner.last["argv"]  # type: ignore[return-value]


class AgentArgvTests(LauncherTestCase):
    def test_the_child_is_launched_non_interactively_with_plain_output(self) -> None:
        self.run_builder()
        self.assertEqual(self.argv[0], "claude")
        self.assertIn("--print", self.argv)
        self.assertEqual(self.argv[self.argv.index("--output-format") + 1], "text")

    def test_mcp_is_empty_and_strict(self) -> None:
        self.run_builder()
        self.assertIn("--strict-mcp-config", self.argv)
        config = Path(self.argv[self.argv.index("--mcp-config") + 1])
        self.assertEqual(json.loads(config.read_text(encoding="utf-8")), {"mcpServers": {}})

    def test_tools_are_bounded_to_the_declared_set(self) -> None:
        self.run_builder()
        self.assertEqual(self.argv[self.argv.index("--tools") + 1], "Read,Edit,Bash")
        self.assertEqual(self.argv[self.argv.index("--allowedTools") + 1], "Read,Edit,Bash")

    def test_a_reviewer_is_launched_with_no_file_writing_tool(self) -> None:
        self.run_reviewer()
        tools = self.argv[self.argv.index("--tools") + 1].split(",")
        self.assertNotIn("Edit", tools)
        self.assertNotIn("Write", tools)

    def test_the_prompt_is_the_last_argument_and_cannot_be_read_as_an_option(self) -> None:
        self.run_builder()
        self.assertFalse(self.argv[-1].startswith("-"))
        self.assertIn("You are the builder lane", self.argv[-1])
        # The variadic tool options must be terminated by a non-variadic one,
        # or the prompt is swallowed as a tool name.
        self.assertEqual(self.argv[-3], "--model")

    def test_the_prompt_names_the_exact_bound_head_and_branch(self) -> None:
        self.run_builder()
        prompt = self.argv[-1]
        self.assertIn(HEAD_A, prompt)
        self.assertIn("feat/example", prompt)
        self.assertIn(str(self.tmp / "blockers.json"), prompt)

    def test_a_reviewer_prompt_carries_its_role_and_the_binding_tag(self) -> None:
        self.run_reviewer(role="B")
        prompt = self.argv[-1]
        self.assertIn("You are reviewer B", prompt)
        self.assertIn(f"PR-PROVER-REVIEW: repo=example/repo pr=7 role=B head={HEAD_A}", prompt)

    def test_a_permission_mode_that_dissolves_the_tool_boundary_is_refused(self) -> None:
        with self.assertRaises(LaunchPolicyError):
            self.run_builder(
                agent=AgentSpec(
                    program="claude",
                    model="opus",
                    tools=("Read",),
                    permission_mode="bypassPermissions",
                )
            )

    def test_no_composed_launch_carries_an_authority_broadening_flag(self) -> None:
        self.run_builder()
        self.run_reviewer()
        for call in self.runner.calls:
            for item in call["argv"]:  # type: ignore[union-attr]
                self.assertNotIn("dangerously", item)
                self.assertNotIn("--add-dir", item)

    def test_a_script_lane_carrying_a_forbidden_flag_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            assert_launchable(["./lane.sh", "--dangerously-skip-permissions"])
        self.assertEqual(caught.exception.reason, "launch-policy")

    def test_a_forbidden_flag_written_with_an_equals_sign_is_still_caught(self) -> None:
        with self.assertRaises(LaunchPolicyError):
            assert_launchable(["./lane.sh", "--add-dir=/"])


class ChildEnvironmentTests(LauncherTestCase):
    def test_the_builder_gets_exactly_its_own_scoped_credential(self) -> None:
        self.run_builder()
        self.assertEqual(self.env["GH_TOKEN"], BUILDER_TOKEN)

    def test_the_reviewer_gets_its_own_credential_and_not_the_builders(self) -> None:
        self.run_reviewer()
        self.assertEqual(self.env["GH_TOKEN"], REVIEWER_TOKEN)
        self.assertNotIn(BUILDER_TOKEN, json.dumps(self.env))

    def test_a_gate_gets_no_github_credential_at_all(self) -> None:
        self.broker.run_gate(name="tests", argv=["make", "test"], cwd=self.worktree, timeout=60)
        self.assertNotIn("GH_TOKEN", self.env)

    def test_no_child_environment_carries_merge_approval_jmd_or_deploy_credentials(self) -> None:
        self.run_builder()
        self.run_reviewer()
        self.broker.run_gate(name="tests", argv=["make", "test"], cwd=self.worktree, timeout=60)
        for call in self.runner.calls:
            env: dict[str, str] = call["env"]  # type: ignore[assignment]
            for name in (
                "GITHUB_TOKEN",
                "KARAN_APPROVAL_TOKEN",
                "JMD_DEPLOY_KEY",
                "VERCEL_TOKEN",
                "SANITY_WRITE_TOKEN",
                "AWS_SECRET_ACCESS_KEY",
                "N8N_API_KEY",
                "SSH_AUTH_SOCK",
                "STRIPE_SECRET",
            ):
                self.assertNotIn(name, env)
            self.assertTrue(carries_none_of(env, FORBIDDEN_VALUES))

    def test_the_child_is_told_what_it_is_bound_to(self) -> None:
        self.run_builder()
        self.assertEqual(self.env["PR_PROVER_REPO"], "example/repo")
        self.assertEqual(self.env["PR_PROVER_HEAD"], HEAD_A)
        self.assertEqual(self.env["PR_PROVER_BRANCH"], "feat/example")
        self.assertEqual(self.env["PR_PROVER_MODE"], "initial")

    def test_progress_rendering_is_turned_off_by_environment(self) -> None:
        self.run_builder()
        self.assertEqual(self.env["NO_COLOR"], "1")
        self.assertEqual(self.env["TERM"], "dumb")
        self.assertEqual(self.env["GIT_TERMINAL_PROMPT"], "0")

    def test_gh_and_git_are_pointed_at_launcher_owned_configuration(self) -> None:
        self.run_builder()
        self.assertTrue(Path(self.env["GH_CONFIG_DIR"]).is_dir())
        self.assertEqual(self.env["GIT_CONFIG_SYSTEM"], "/dev/null")
        gitconfig = Path(self.env["GIT_CONFIG_GLOBAL"]).read_text(encoding="utf-8")
        self.assertIn("[credential]", gitconfig)
        self.assertIn(BUILDER_LOGIN, gitconfig)

    def test_a_lane_that_may_push_gets_one_credential_helper_and_only_gh(self) -> None:
        self.run_builder()
        gitconfig = Path(self.env["GIT_CONFIG_GLOBAL"]).read_text(encoding="utf-8")
        self.assertIn("helper = !gh auth git-credential", gitconfig)

    def test_a_lane_that_may_not_push_gets_no_credential_helper(self) -> None:
        self.run_reviewer()
        gitconfig = Path(self.env["GIT_CONFIG_GLOBAL"]).read_text(encoding="utf-8")
        self.assertNotIn("gh auth git-credential", gitconfig)
        self.assertIn(REVIEWER_LOGIN, gitconfig)

    def test_the_credential_never_reaches_the_child_through_a_file_anyone_can_read(self) -> None:
        self.run_builder()
        gitconfig = Path(self.env["GIT_CONFIG_GLOBAL"])
        self.assertEqual(gitconfig.stat().st_mode & 0o077, 0)
        self.assertNotIn(BUILDER_TOKEN, gitconfig.read_text(encoding="utf-8"))

    def test_a_caller_cannot_hand_a_launcher_an_environment(self) -> None:
        for method in (LaunchBroker.run_gate, LaunchBroker.run_reviewer, LaunchBroker.run_builder):
            self.assertNotIn("env", inspect.signature(method).parameters)

    def test_the_scratch_directory_is_removed_when_the_broker_closes(self) -> None:
        self.run_builder()
        scratch = Path(self.env["GH_CONFIG_DIR"]).parent.parent
        self.broker.close()
        self.assertFalse(scratch.exists())


class IdentityBindingTests(LauncherTestCase):
    def test_an_identity_the_launcher_does_not_own_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            self.run_builder(identity="somebody-elses")
        self.assertIn("does not own", caught.exception.message)

    def test_a_role_cannot_borrow_the_other_roles_identity(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            self.run_builder(identity="reviewer")
        self.assertIn("capabilities", caught.exception.message)
        with self.assertRaises(LaunchPolicyError):
            self.run_reviewer(identity="builder")

    def test_a_credential_resolving_to_another_account_fails_closed(self) -> None:
        self.broker = self.make_broker(verifier=FakeVerifier(logins={BUILDER_TOKEN: "impostor"}))
        with self.assertRaises(IdentityError) as caught:
            self.run_builder()
        self.assertEqual(caught.exception.reason, "identity-error")

    def test_a_credential_that_could_merge_fails_closed(self) -> None:
        self.broker = self.make_broker(
            verifier=FakeVerifier(
                permissions={BUILDER_LOGIN: {"pull": True, "push": True, "admin": True}}
            )
        )
        with self.assertRaises(IdentityError):
            self.run_builder()

    def test_an_unverifiable_credential_is_never_launched_on(self) -> None:
        broker = LaunchBroker(
            runner=self.runner,
            policy=self.config.launch.policy,
            identities=self.config.launch.identities,
            verifier=None,
            parent_env=parent_env(),
            worktree_root=self.config.worktree_root,
            scratch_root=self.tmp,
        )
        self.addCleanup(broker.close)
        self.broker = broker
        with self.assertRaises(LaunchPolicyError) as caught:
            self.run_builder()
        self.assertIn("unverified", caught.exception.message)
        self.assertEqual(self.runner.calls, [])

    def test_an_agent_lane_without_an_identity_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            self.run_builder(identity=None)
        self.assertIn("one scoped identity", caught.exception.message)

    def test_a_missing_credential_stops_before_anything_is_launched(self) -> None:
        self.broker = self.make_broker(env={"HOME": "/tmp/home", "PATH": "/usr/bin"})
        with self.assertRaises(IdentityError):
            self.run_builder()
        self.assertEqual(self.runner.calls, [])

    def test_one_credential_is_verified_once_per_run(self) -> None:
        verifier = FakeVerifier()
        self.broker = self.make_broker(verifier=verifier)
        self.run_reviewer(role="A")
        self.run_reviewer(role="B")
        self.assertEqual(len(verifier.calls), 1)


class BudgetTests(LauncherTestCase):
    def test_the_default_budget_sits_inside_the_window(self) -> None:
        self.run_builder()
        self.assertEqual(self.runner.last["timeout"], DEFAULT_BUDGET)
        self.assertTrue(BUDGET_MIN <= DEFAULT_BUDGET <= BUDGET_MAX)

    def test_a_declared_budget_inside_the_window_is_used(self) -> None:
        self.run_builder(timeout=1700)
        self.assertEqual(self.runner.last["timeout"], 1700.0)

    def test_a_budget_outside_the_window_fails_closed_rather_than_being_clamped(self) -> None:
        for timeout in (60, 1199, 1801, 14400):
            with self.assertRaises(LaunchPolicyError) as caught:
                self.run_builder(timeout=timeout)
            self.assertIn("20 and 30 minutes", caught.exception.message)


class IsolationTests(LauncherTestCase):
    def test_a_lane_outside_the_worktree_root_is_refused(self) -> None:
        outside = self.tmp / "elsewhere"
        outside.mkdir()
        with self.assertRaises(LaunchPolicyError) as caught:
            self.run_builder(cwd=outside)
        self.assertIn("isolated worktree root", caught.exception.message)

    def test_a_worktree_that_does_not_exist_is_refused(self) -> None:
        with self.assertRaises(LaunchPolicyError):
            self.run_builder(cwd=self.config.worktree_root / "missing")


class QuietOutputTests(unittest.TestCase):
    def test_escape_sequences_are_stripped(self) -> None:
        self.assertEqual(quiet("\x1b[1mbold\x1b[0m\n"), "bold\n")

    def test_a_progress_line_collapses_to_the_frame_that_survived(self) -> None:
        self.assertEqual(quiet("10%\r50%\r100% done\n"), "100% done\n")

    def test_a_marker_reaches_the_parser_byte_for_byte(self) -> None:
        marker = f"DONE: STATUS=pass BLOCKING=0 HEAD={HEAD_A}"
        self.assertEqual(quiet(f"\x1b[32m...\x1b[0m\n{marker}\n").splitlines()[-1], marker)

    def test_runs_of_blank_lines_collapse(self) -> None:
        self.assertEqual(quiet("a\n\n\n\nb\n"), "a\n\nb\n")

    def test_trailing_noise_after_the_last_line_is_removed(self) -> None:
        self.assertEqual(quiet("a\n   \n\n"), "a\n")

    def test_empty_output_stays_empty(self) -> None:
        self.assertEqual(quiet(""), "")

    def test_windows_line_endings_survive_as_content(self) -> None:
        self.assertEqual(quiet("a\r\nb\r\n"), "a\nb\n")


class QuietedResultTests(LauncherTestCase):
    def test_a_lane_result_reaches_the_loop_already_quiet(self) -> None:
        self.runner.stdout = "\x1b[1mworking\x1b[0m\r\rdone\n"
        result = self.run_builder()
        self.assertEqual(result.stdout, "done\n")

    def test_the_process_result_itself_is_untouched(self) -> None:
        self.runner.returncode = 3
        result = self.run_builder()
        self.assertEqual(result.returncode, 3)
        self.assertFalse(result.ok)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
