"""The hardened launchers: argv composition, credential scope, and launch discipline."""
from __future__ import annotations

import inspect
import json
import os
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
    lane_bin,
    make_broker,
    make_config,
    make_source_repo,
    parent_env,
)

from pr_prover.childenv import (
    CAPABILITY_CHANNEL,
    CAPABILITY_SECRET,
    CLAUDE_TMPDIR,
    HOME_GUARDS,
    LAUNCHER_OVERRIDES,
    SUBPROCESS_ENV_SCRUB,
    carries_none_of,
)
from pr_prover.commands import CommandResult
from pr_prover.errors import IdentityError, LaunchPolicyError
from pr_prover.launchers import (
    BUDGET_MAX,
    BUDGET_MIN,
    DEFAULT_BUDGET,
    SETTING_SOURCES_ENTRY,
    SHIM_NAME,
    AgentSpec,
    BoundContext,
    LaunchBroker,
    assert_launchable,
    quiet,
)
from pr_prover.runtime import TRUSTED_SYSTEM_PATH
from pr_prover.sandbox import OUTSIDE_SANDBOX_TOOLS, decides, read_and_assert

BOUND = BoundContext(repo="example/repo", pr=7, branch="feat/example", base="main", head=HEAD_A)
# Both roles now get the same code-owned maximum: the only tool that runs inside
# the OS sandbox is Bash, and TodoWrite touches nothing outside the model's own
# scratch state. A lane reads, edits, and tests through sandboxed Bash.
BUILDER_AGENT = AgentSpec(program="claude", model="opus", tools=("Bash", "TodoWrite"))
REVIEWER_AGENT = AgentSpec(program="claude", model="sonnet", tools=("Bash", "TodoWrite"))


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
        self.config = make_config(self.tmp, source_repo=make_source_repo(self.tmp))
        self.worktree = self.config.worktree_root / "attempt1"
        self.worktree.mkdir(parents=True)
        self.runner = RecordingRunner()
        # The launcher resolves every configured program to a trusted absolute
        # path before it launches anything, so the agent program has to exist.
        # It is never executed here: RecordingRunner intercepts the call.
        self.lane_bin = lane_bin(self.tmp)
        self.parent = parent_env(PATH=f"{self.lane_bin}:/usr/bin:/bin")
        # The launcher copies the frozen packet into the lane's own read-only
        # input directory rather than pointing the lane at the run's scratch, so
        # the source has to be a real file.
        self.blockers = self.tmp / "blockers.json"
        self.blockers.write_text('{"blockers": []}\n', encoding="utf-8")
        self.broker = self.make_broker()

    def make_broker(self, **kwargs: object) -> LaunchBroker:
        kwargs.setdefault("env", self.parent)
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
            "blockers_file": self.blockers,
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

    @property
    def program(self) -> str:
        """The name of the program launched, without the trusted path it resolved to."""
        return Path(self.argv[0]).name

    @property
    def settings(self) -> dict:
        """The launcher-owned sandbox settings document this launch was given."""
        path = Path(self.argv[self.argv.index("--settings") + 1])
        return json.loads(path.read_text(encoding="utf-8"))


class AgentArgvTests(LauncherTestCase):
    def test_the_child_is_launched_non_interactively_with_plain_output(self) -> None:
        self.run_builder()
        self.assertEqual(self.program, "claude")
        # Resolved, not passed through: the child's PATH no longer contains the
        # operator's directories, so the launcher decides which file runs.
        self.assertEqual(self.argv[0], str((self.lane_bin / "claude").resolve()))
        self.assertIn("--print", self.argv)
        self.assertEqual(self.argv[self.argv.index("--output-format") + 1], "text")

    def test_no_settings_source_is_consulted(self) -> None:
        """Not the operator's, and not one the PR under review could add."""
        self.run_builder()
        self.assertIn(SETTING_SOURCES_ENTRY, self.argv)
        self.assertEqual(
            [item for item in self.argv if item.startswith("--setting-sources")],
            [SETTING_SOURCES_ENTRY],
        )

    def test_mcp_is_empty_and_strict(self) -> None:
        self.run_builder()
        self.assertIn("--strict-mcp-config", self.argv)
        config = Path(self.argv[self.argv.index("--mcp-config") + 1])
        self.assertEqual(json.loads(config.read_text(encoding="utf-8")), {"mcpServers": {}})

    def test_tools_are_bounded_to_the_declared_set(self) -> None:
        self.run_builder()
        self.assertEqual(self.argv[self.argv.index("--tools") + 1], "Bash,TodoWrite")
        self.assertEqual(self.argv[self.argv.index("--allowedTools") + 1], "Bash,TodoWrite")

    def test_no_lane_is_launched_with_a_tool_that_bypasses_the_bash_sandbox(self) -> None:
        """PAPI-90 item 1: the client's own file and network tools are not sandboxed."""
        for run in (self.run_builder, self.run_reviewer):
            run()
            granted = set(self.argv[self.argv.index("--tools") + 1].split(","))
            granted |= set(self.argv[self.argv.index("--allowedTools") + 1].split(","))
            self.assertEqual(granted & set(OUTSIDE_SANDBOX_TOOLS), set())
            self.assertIn("Bash", granted)

    def test_an_agent_asked_for_an_unsandboxed_tool_fails_closed(self) -> None:
        """A widened AgentSpec is refused at the launch, not only at config load."""
        for tool in OUTSIDE_SANDBOX_TOOLS:
            with self.subTest(tool=tool), self.assertRaises(LaunchPolicyError) as caught:
                self.run_builder(
                    agent=AgentSpec(
                        program="claude", model="opus", tools=("Bash", tool)
                    )
                )
            self.assertEqual(caught.exception.reason, "launch-policy")

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
        # Not the run's own copy: the lane is pointed at the exact file the
        # launcher put in its own read-only input directory.
        packet = self.argv[self.argv.index("--settings") + 1]
        lane = Path(packet).parent
        self.assertIn(str(lane / "input" / "blockers.json"), prompt)
        self.assertNotIn(str(self.tmp / "blockers.json"), prompt)

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
    def test_the_builder_gets_no_credential_only_a_capability_channel(self) -> None:
        """PAPI90-P1-001: a child holds no GitHub token under any name."""
        self.run_builder()
        self.assertNotIn("GH_TOKEN", self.env)
        self.assertNotIn("GITHUB_TOKEN", self.env)
        self.assertNotIn(BUILDER_TOKEN, json.dumps(self.env))
        self.assertTrue(self.env[CAPABILITY_CHANNEL].endswith(".sock"))

    def test_the_reviewer_gets_neither_credential(self) -> None:
        self.run_reviewer()
        self.assertNotIn("GH_TOKEN", self.env)
        self.assertNotIn(REVIEWER_TOKEN, json.dumps(self.env))
        self.assertNotIn(BUILDER_TOKEN, json.dumps(self.env))
        self.assertIn(CAPABILITY_CHANNEL, self.env)

    def test_the_capability_shim_is_first_on_every_lane_path(self) -> None:
        self.run_builder()
        entries = self.env["PATH"].split(os.pathsep)
        first = entries[0]
        self.assertEqual(Path(first).name, "bin")
        self.assertIn(SHIM_NAME, [entry.name for entry in Path(first).iterdir()])
        # ...and the rest of PATH is the trusted system list, not the operator's.
        self.assertEqual(entries[1:], list(TRUSTED_SYSTEM_PATH))
        self.assertNotIn(str(self.lane_bin), entries)

    def test_two_lanes_never_share_a_runtime_directory(self) -> None:
        """PAPI-90 item 3: no lane can modify what a later lane runs."""
        self.run_builder()
        first = self.env["PATH"].split(os.pathsep)[0]
        self.run_reviewer()
        second = self.env["PATH"].split(os.pathsep)[0]
        self.assertNotEqual(first, second)

    def test_a_lane_gets_its_channel_secret_and_a_scrubbed_subprocess_env(self) -> None:
        """PAPI-90 item 2: the secret travels here, and no further down."""
        self.run_builder()
        secret = self.env[CAPABILITY_SECRET]
        self.assertGreaterEqual(len(secret), 32)
        self.assertEqual(self.env[SUBPROCESS_ENV_SCRUB], "1")
        self.run_reviewer()
        self.assertNotEqual(self.env[CAPABILITY_SECRET], secret)

    def test_a_gate_gets_no_github_credential_and_no_capability_channel(self) -> None:
        self.broker.run_gate(name="tests", argv=["make", "test"], cwd=self.worktree, timeout=60)
        self.assertNotIn("GH_TOKEN", self.env)
        self.assertNotIn(CAPABILITY_CHANNEL, self.env)

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

    def test_every_lane_gets_a_synthetic_home_not_the_operators(self) -> None:
        """PAPI90-P1-002: HOME is the launcher's, and every guard points inside it."""
        self.run_builder()
        home = Path(self.env["HOME"])
        self.assertNotEqual(str(home), parent_env()["HOME"])
        self.assertTrue(home.is_dir())
        self.assertTrue(home.is_relative_to(self.tmp))
        for guard in HOME_GUARDS:
            self.assertIn(guard, self.env, guard)
            if guard != "GIT_CONFIG_SYSTEM":
                self.assertTrue(Path(self.env[guard]).is_relative_to(home), guard)

    def test_a_secret_in_the_operators_home_is_not_reachable_through_the_childs(self) -> None:
        """PAPI90-P1-002: nothing under the operator's home is copied or pointed at."""
        operator_home = self.tmp / "operator-home"
        (operator_home / ".config" / "gh").mkdir(parents=True)
        (operator_home / ".config" / "gh" / "hosts.yml").write_text(
            "github.com:\n  oauth_token: ghp_" + "s" * 36 + "\n", encoding="utf-8"
        )
        broker = self.make_broker(
            env=parent_env(HOME=str(operator_home), PATH=f"{self.lane_bin}:/usr/bin:/bin")
        )
        broker.run_builder(
            identity="builder",
            agent=BUILDER_AGENT,
            argv=None,
            bound=BOUND,
            cwd=self.worktree,
            timeout=None,
            attempt=1,
            mode="initial",
            blockers_file=self.blockers,
            signature="Fixed by: a signature long enough",
        )
        env = self.runner.last["env"]
        self.assertNotEqual(env["HOME"], str(operator_home))
        self.assertFalse(Path(env["GH_CONFIG_DIR"]).is_relative_to(operator_home))
        self.assertEqual(list(Path(env["GH_CONFIG_DIR"]).iterdir()), [])
        self.assertTrue(carries_none_of(env, [str(operator_home)]))

    def test_gh_and_git_are_pointed_at_launcher_owned_configuration(self) -> None:
        self.run_builder()
        self.assertTrue(Path(self.env["GH_CONFIG_DIR"]).is_dir())
        self.assertEqual(self.env["GIT_CONFIG_SYSTEM"], "/dev/null")
        gitconfig = Path(self.env["GIT_CONFIG_GLOBAL"]).read_text(encoding="utf-8")
        self.assertIn("[credential]", gitconfig)
        self.assertIn(BUILDER_LOGIN, gitconfig)

    def test_no_lane_gets_a_credential_helper_at_all(self) -> None:
        """PAPI90-P1-001: even the pushing lane has nothing for a helper to offer."""
        for lane in (self.run_builder, self.run_reviewer):
            lane()
            gitconfig = Path(self.env["GIT_CONFIG_GLOBAL"]).read_text(encoding="utf-8")
            self.assertNotIn("gh auth git-credential", gitconfig)
            self.assertIn("[credential]", gitconfig)

    def test_a_lane_still_commits_under_its_own_login(self) -> None:
        self.run_reviewer()
        gitconfig = Path(self.env["GIT_CONFIG_GLOBAL"]).read_text(encoding="utf-8")
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



class LaneScopedLaunchMaterialTests(unittest.TestCase):
    """Former-red (PAPI-90 item 2): what one real launch owns, and what it does not.

    Built through the broker rather than by hand, and deliberately without
    opening a capability channel, so the assertions are about the directories and
    the settings file an actual launch produces.
    """

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.config = make_config(self.tmp, source_repo=make_source_repo(self.tmp))
        self.worktree = self.config.worktree_root / "attempt1"
        self.worktree.mkdir(parents=True)
        self.runner = RecordingRunner()
        self.lane_bin = lane_bin(self.tmp)
        self.operator_home = self.tmp / "operator-home"
        self.operator_home.mkdir()
        self.broker = make_broker(
            self.config,
            self.runner,
            scratch_root=self.tmp / "scratch-root",
            env=parent_env(
                HOME=str(self.operator_home), PATH=f"{self.lane_bin}:/usr/bin:/bin"
            ),
        )
        self.addCleanup(self.broker.close)
        self.first = self.broker._material("builder (initial)", identity=None)
        self.second = self.broker._material("reviewer A", identity=None)

    def settings_for(self, material, *, writable_worktree: bool = True) -> dict:
        path = self.broker._sandbox_settings(
            lane="builder (initial)",
            cwd=self.worktree,
            material=material,
            socket=None,
            writable_worktree=writable_worktree,
        )
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def test_two_launches_share_no_directory_at_all(self) -> None:
        self.assertNotEqual(self.first.directory, self.second.directory)
        for name in ("directory", "scratch", "tmp", "inputs", "settings"):
            self.assertNotEqual(getattr(self.first, name), getattr(self.second, name))
        self.assertNotEqual(self.first.home_directory, self.second.home_directory)
        self.assertNotEqual(
            self.first.runtime.directory, self.second.runtime.directory
        )

    def test_the_lane_writes_its_own_scratch_and_home_and_nothing_else(self) -> None:
        settings = self.settings_for(self.first)
        for root in self.first.writable_roots:
            self.assertTrue(decides(settings, root, write=True), str(root))
        self.assertTrue(decides(settings, self.first.tmp / "build.log", write=True))

    def test_the_lane_cannot_write_its_runtime_settings_or_input(self) -> None:
        settings = self.settings_for(self.first)
        for root in self.first.readonly_roots:
            with self.subTest(root=str(root)):
                self.assertTrue(decides(settings, root, write=False), str(root))
                self.assertFalse(decides(settings, root, write=True), str(root))
        shim = self.first.runtime.directory / "bin" / SHIM_NAME
        self.assertFalse(decides(settings, shim, write=True))

    def test_the_lane_cannot_reach_the_empty_mcp_config_for_writing(self) -> None:
        settings = self.settings_for(self.first)
        mcp = self.broker._empty_mcp_config()
        self.assertTrue(decides(settings, mcp, write=False))
        self.assertFalse(decides(settings, mcp, write=True))

    def test_the_lane_cannot_reach_the_launcher_scratch_or_a_sibling(self) -> None:
        settings = self.settings_for(self.first)
        foreign = self.broker._foreign_paths(self.first)
        self.assertNotIn(self.broker._empty_mcp_config(), foreign)
        for path in (
            *self.broker._denied_roots(),
            *foreign,
            self.second.directory,
            self.second.scratch,
            self.second.settings,
            self.second.runtime.directory,
            Path(self.second.home_directory),
            Path(self.second.home_directory) / ".gitconfig",
        ):
            with self.subTest(path=str(path)):
                self.assertFalse(decides(settings, path, write=False), str(path))
                self.assertFalse(decides(settings, path, write=True), str(path))

    def test_the_launcher_side_broker_home_is_not_a_lanes_to_read(self) -> None:
        """The broker acts with a real credential; a lane is never given one."""
        settings = self.settings_for(self.first)
        broker_home = self.broker._scratch_dir() / "broker"
        self.assertFalse(decides(settings, broker_home, write=False))

    def test_the_builder_worktree_stays_usable(self) -> None:
        settings = self.settings_for(self.first, writable_worktree=True)
        self.assertTrue(decides(settings, self.worktree, write=False))
        self.assertTrue(decides(settings, self.worktree / "src" / "app.py", write=True))
        self.assertFalse(decides(settings, self.worktree / ".git", write=True))

    def test_a_reviewer_worktree_is_readable_and_never_writable(self) -> None:
        settings = self.settings_for(self.second, writable_worktree=False)
        self.assertTrue(decides(settings, self.worktree, write=False))
        self.assertFalse(decides(settings, self.worktree / "src" / "app.py", write=True))

    def test_the_generated_document_passes_the_full_launch_time_check(self) -> None:
        path = self.broker._sandbox_settings(
            lane="builder (initial)",
            cwd=self.worktree,
            material=self.first,
            socket=None,
            writable_worktree=True,
        )
        read_and_assert(
            path,
            worktree=str(self.worktree),
            socket=None,
            operator_home=str(self.operator_home),
            writable_worktree=True,
            lane_writable=self.first.writable_roots,
            lane_readonly=self.first.readonly_roots,
            denied_roots=self.broker._denied_roots(),
            foreign_paths=self.broker._foreign_paths(self.first),
        )

    def test_the_lane_tmpdir_is_inside_its_own_writable_scratch(self) -> None:
        env = self.broker._environment(
            cwd=self.worktree, bound=None, lane="gate x", channel=None, material=self.first
        )
        self.assertEqual(env["TMPDIR"], str(self.first.tmp))
        self.assertTrue(Path(env["TMPDIR"]).is_dir())
        self.assertNotEqual(env["TMPDIR"], self.parent_tmpdir())
        settings = self.settings_for(self.first)
        self.assertTrue(decides(settings, env["TMPDIR"], write=True))

    def test_a_claude_lane_gets_the_temp_variable_its_sandboxed_bash_reads(self) -> None:
        """Former-red (live): ``TMPDIR`` alone left the lane in a shared directory.

        A live probe of Claude Code 2.1.219 reported ``TMPDIR=/tmp/claude-501``
        inside a sandboxed shell whatever the launcher had set, because the client
        supplies its own session temporary directory. ``CLAUDE_CODE_TMPDIR`` is
        the documented name that overrides it, and Hermes confirmed a sandboxed
        Bash then reports the exact lane path.
        """
        env = self.broker._environment(
            cwd=self.worktree, bound=None, lane="gate x", channel=None, material=self.first
        )
        self.assertEqual(env[CLAUDE_TMPDIR], str(self.first.tmp))
        self.assertEqual(env[CLAUDE_TMPDIR], env["TMPDIR"])
        settings = self.settings_for(self.first)
        self.assertTrue(decides(settings, env[CLAUDE_TMPDIR], write=True))
        # And it is this lane's, not a sibling's and not the launcher's.
        self.assertNotEqual(env[CLAUDE_TMPDIR], str(self.second.tmp))
        self.assertFalse(decides(settings, self.second.tmp, write=True))

    def test_the_lane_may_write_its_worktree_scratch_and_home_for_real(self) -> None:
        """Former-red (live): the three writes the generated policy used to refuse."""
        settings = self.settings_for(self.first, writable_worktree=True)
        for path in (
            self.worktree,
            self.worktree / "src" / "app.py",
            self.first.scratch,
            self.first.tmp / "build.log",
            Path(self.first.home_directory),
            Path(self.first.home_directory) / ".cache" / "thing",
        ):
            with self.subTest(path=str(path)):
                self.assertTrue(decides(settings, path, write=True), str(path))
        filesystem = json.loads(json.dumps(settings))["sandbox"]["filesystem"]
        for allowed in filesystem["allowWrite"]:
            for denied in filesystem["denyWrite"]:
                self.assertFalse(
                    allowed == denied or allowed.startswith(f"{denied}/"),
                    f"{denied} covers {allowed}",
                )

    def test_no_broad_region_is_ever_denied_for_writing(self) -> None:
        """The launcher's scratch and the operator's home stay out of ``denyWrite``."""
        settings = self.settings_for(self.first)
        denied = settings["sandbox"]["filesystem"]["denyWrite"]
        for root in (*self.broker._denied_roots(), self.operator_home):
            self.assertNotIn(str(root), denied)

    def parent_tmpdir(self) -> str:
        return os.environ.get("TMPDIR", "/tmp")

    def test_the_operator_tmpdir_is_never_inherited(self) -> None:
        broker = make_broker(
            self.config,
            self.runner,
            scratch_root=self.tmp / "scratch-two",
            env=parent_env(
                HOME=str(self.operator_home),
                PATH=f"{self.lane_bin}:/usr/bin:/bin",
                TMPDIR="/Users/operator/private-tmp",
            ),
        )
        self.addCleanup(broker.close)
        material = broker._material("gate x", identity=None)
        env = broker._environment(
            cwd=self.worktree, bound=None, lane="gate x", channel=None, material=material
        )
        self.assertEqual(env["TMPDIR"], str(material.tmp))

    def test_the_frozen_packet_is_copied_into_the_lanes_own_input(self) -> None:
        """The run's scratch holds every attempt's packet; the lane sees one file."""
        source = self.tmp / "blockers.json"
        source.write_text('{"blockers": [{"id": "B1"}]}\n', encoding="utf-8")
        packet = self.broker.lane_input(self.first, source, name="blockers.json")
        self.assertEqual(packet.parent, self.first.inputs)
        self.assertEqual(packet.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))
        settings = self.settings_for(self.first)
        self.assertTrue(decides(settings, packet, write=False))
        self.assertFalse(decides(settings, packet, write=True))
        # And the directory the original came from stays out of reach entirely.
        self.assertFalse(decides(settings, source, write=False))
        self.assertFalse(decides(settings, source.parent, write=False))

    def test_no_configured_program_may_resolve_inside_the_launcher_scratch(self) -> None:
        planted = self.broker._scratch_dir() / "planted.sh"
        planted.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        planted.chmod(0o700)
        with self.assertRaises(LaunchPolicyError) as caught:
            self.broker._script_argv(
                [str(planted)], lane="gate x", cwd=self.worktree
            )
        self.assertIn("launcher-owned lane runtime", caught.exception.message)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
