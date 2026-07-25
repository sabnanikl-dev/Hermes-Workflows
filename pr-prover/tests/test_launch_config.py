"""What a run configuration may and may not say about launching children."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from _support import (
    BUILDER_LOGIN,
    REVIEWER_LOGIN,
    legacy_unscoped_payload,
    make_source_repo,
)

from pr_prover.childenv import MODEL_AUTH_CHANNELS
from pr_prover.cli import main
from pr_prover.config import RunConfig
from pr_prover.errors import ConfigError


def payload(tmp: Path, source_repo: Path) -> dict:
    return {
        "schema_version": 1,
        "repo": "example/repo",
        "pr": 7,
        "branch": "feat/example",
        "source_repo": str(source_repo),
        "worktree_root": str(tmp / "worktrees"),
        "state_file": str(tmp / "state.json"),
        "lock_file": str(tmp / "run.lock"),
        "launch": {
            "identities": {
                "builder": {
                    "login": BUILDER_LOGIN,
                    "capabilities": ["push-branch", "comment-pr"],
                    "token_env": "PR_PROVER_BUILDER_TOKEN",
                },
                "reviewer": {
                    "login": REVIEWER_LOGIN,
                    "capabilities": ["comment-pr", "review-pr"],
                    "token_env": "PR_PROVER_REVIEWER_TOKEN",
                },
            }
        },
        "reviewers": [
            {
                "name": "A",
                "identity": "reviewer",
                "agent": {"program": "claude", "model": "opus", "tools": ["Read", "Bash"]},
                "timeout": 1500,
            },
            {
                "name": "B",
                "identity": "reviewer",
                "agent": {"program": "claude", "model": "sonnet", "tools": ["Read", "Bash"]},
                "timeout": 1500,
            },
        ],
        "builder": {
            "identity": "builder",
            "agent": {
                "program": "claude",
                "model": "opus",
                "tools": ["Read", "Edit", "Write", "Bash"],
            },
            "signature": "Fixed by: Claude Code via Hermes orchestration",
            "comment_author": BUILDER_LOGIN,
            "timeout": 1500,
        },
    }


class LaunchConfigTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.source_repo = make_source_repo(self.tmp)

    def load(self, mutate=None) -> RunConfig:
        raw = payload(self.tmp, self.source_repo)
        if mutate is not None:
            mutate(raw)
        return RunConfig.from_mapping(raw, base_dir=self.tmp)

    def refuses(self, mutate) -> ConfigError:
        with self.assertRaises(ConfigError) as caught:
            self.load(mutate)
        return caught.exception

    def refuses_payload(self, raw: dict) -> ConfigError:
        with self.assertRaises(ConfigError) as caught:
            RunConfig.from_mapping(raw, base_dir=self.tmp)
        return caught.exception


class ValidConfigTests(LaunchConfigTestCase):
    def test_a_scoped_agent_configuration_loads(self) -> None:
        config = self.load()
        self.assertEqual(sorted(config.launch.identities), ["builder", "reviewer"])
        self.assertEqual(config.builder.identity, "builder")
        self.assertIsNone(config.builder.argv)
        self.assertEqual(config.builder.agent.program, "claude")
        self.assertEqual(config.reviewers[0].agent.tools, ("Read", "Bash"))

    def test_a_script_lane_configuration_still_loads(self) -> None:
        def script_lanes(raw: dict) -> None:
            raw["builder"].pop("agent")
            raw["builder"]["argv"] = ["./builder.sh", "{head}"]
            raw["builder"]["timeout"] = 60
            for reviewer in raw["reviewers"]:
                reviewer.pop("agent")
                reviewer["argv"] = ["./reviewer.sh", "{reviewer}"]

        config = self.load(script_lanes)
        self.assertIsNone(config.builder.agent)
        self.assertEqual(config.builder.argv, ("./builder.sh", "{head}"))
        self.assertEqual(config.builder.identity, "builder")

    def test_a_legacy_unscoped_configuration_is_refused_with_a_migration_error(self) -> None:
        """PAPI90-P1-007: an unscoped script lane can no longer be loaded at all."""

        def unscoped(raw: dict) -> None:
            raw.pop("launch")
            raw["builder"].pop("identity")
            raw["builder"].pop("agent")
            raw["builder"]["argv"] = ["./builder.sh"]
            for reviewer in raw["reviewers"]:
                reviewer.pop("identity")
                reviewer.pop("agent")
                reviewer["argv"] = ["./reviewer.sh"]

        error = self.refuses(unscoped)
        self.assertIn("declares no scoped identity", error.message)
        self.assertIn("script lanes included", error.message)
        self.assertIn("Add launch.identities", error.message)

    def test_an_unscoped_script_reviewer_is_refused_too(self) -> None:
        def unscoped_reviewer(raw: dict) -> None:
            for reviewer in raw["reviewers"]:
                reviewer.pop("identity")
                reviewer.pop("agent")
                reviewer["argv"] = ["./reviewer.sh"]

        error = self.refuses(unscoped_reviewer)
        self.assertIn("declares no scoped identity", error.message)

    def test_the_shipped_legacy_shape_is_refused(self) -> None:
        error = self.refuses_payload(
            legacy_unscoped_payload(self.tmp, source_repo=self.source_repo)
        )
        self.assertIn("declares no scoped identity", error.message)


class LaneCommandTests(LaunchConfigTestCase):
    def test_a_lane_cannot_declare_both_a_script_and_an_agent(self) -> None:
        error = self.refuses(lambda raw: raw["builder"].update(argv=["./builder.sh"]))
        self.assertIn("exactly one command line", error.message)

    def test_a_lane_with_neither_fails_closed(self) -> None:
        error = self.refuses(lambda raw: raw["builder"].pop("agent"))
        self.assertIn("either an argv array or an agent", error.message)

    def test_an_agent_lane_without_an_identity_fails_closed(self) -> None:
        error = self.refuses(lambda raw: raw["builder"].pop("identity"))
        self.assertIn("no scoped identity", error.message)

    def test_an_unknown_agent_key_fails_closed(self) -> None:
        self.refuses(lambda raw: raw["builder"]["agent"].update(extra_args=["--add-dir", "/"]))

    def test_an_agent_lane_must_name_a_model(self) -> None:
        self.refuses(lambda raw: raw["builder"]["agent"].pop("model"))
        self.refuses(lambda raw: raw["builder"]["agent"].update(model="not a model"))


class BoundedAuthorityTests(LaunchConfigTestCase):
    def test_a_reviewer_cannot_be_given_a_file_writing_tool(self) -> None:
        error = self.refuses(
            lambda raw: raw["reviewers"][0]["agent"].update(tools=["Read", "Write"])
        )
        self.assertIn("narrow", error.message)

    def test_a_lane_cannot_ask_for_a_tool_outside_the_built_in_set(self) -> None:
        self.refuses(lambda raw: raw["builder"]["agent"].update(tools=["Read", "MergePullRequest"]))

    def test_tools_may_be_narrowed(self) -> None:
        config = self.load(lambda raw: raw["builder"]["agent"].update(tools=["Read"]))
        self.assertEqual(config.builder.agent.tools, ("Read",))

    def test_a_permission_mode_that_bypasses_the_boundary_is_refused(self) -> None:
        for mode in ("bypassPermissions", "auto", "whatever"):
            self.refuses(lambda raw, mode=mode: raw["builder"]["agent"].update(permission_mode=mode))

    def test_an_agent_budget_outside_the_window_is_refused(self) -> None:
        for timeout in (60, 1199, 1801, 14400):
            error = self.refuses(lambda raw, timeout=timeout: raw["builder"].update(timeout=timeout))
            self.assertIn("20-30 minute", error.message)

    def test_an_agent_lane_without_a_declared_budget_gets_one_inside_the_window(self) -> None:
        config = self.load(lambda raw: raw["builder"].pop("timeout"))
        self.assertEqual(config.builder.timeout, 1500.0)


class IdentityConfigTests(LaunchConfigTestCase):
    def test_an_identity_cannot_declare_merge_or_deploy_authority(self) -> None:
        for capability in ("merge-pr", "deploy", "admin"):
            error = self.refuses(
                lambda raw, capability=capability: raw["launch"]["identities"]["builder"].update(
                    capabilities=["push-branch", "comment-pr", capability]
                )
            )
            self.assertIn("capability", error.message)

    def test_a_lane_naming_an_undeclared_identity_fails_closed(self) -> None:
        error = self.refuses(lambda raw: raw["builder"].update(identity="karan"))
        self.assertIn("does not define", error.message)

    def test_a_role_cannot_use_the_other_roles_identity(self) -> None:
        self.refuses(lambda raw: raw["builder"].update(identity="reviewer"))
        self.refuses(lambda raw: raw["reviewers"][0].update(identity="builder"))

    def test_the_builder_identity_and_the_expected_commenter_must_be_one_account(self) -> None:
        error = self.refuses(lambda raw: raw["builder"].update(comment_author="somebody-else"))
        self.assertIn("different accounts", error.message)

    def test_an_identity_needs_exactly_one_credential_source(self) -> None:
        self.refuses(lambda raw: raw["launch"]["identities"]["builder"].pop("token_env"))
        self.refuses(
            lambda raw: raw["launch"]["identities"]["builder"].update(token_file="/tmp/token")
        )

    def test_an_identity_cannot_be_injected_as_ambient_github_authority(self) -> None:
        self.refuses(
            lambda raw: raw["launch"]["identities"]["builder"].update(inject_as="GITHUB_TOKEN")
        )

    def test_a_credential_file_path_is_resolved_against_the_config(self) -> None:
        def by_file(raw: dict) -> None:
            raw["launch"]["identities"]["builder"].pop("token_env")
            raw["launch"]["identities"]["builder"]["token_file"] = "secrets/builder.token"

        config = self.load(by_file)
        self.assertEqual(
            config.launch.identities["builder"].token_file, self.tmp / "secrets/builder.token"
        )

    def test_an_unknown_identity_key_fails_closed(self) -> None:
        self.refuses(lambda raw: raw["launch"]["identities"]["builder"].update(token="ghp_x"))


class EnvironmentAllowlistTests(LaunchConfigTestCase):
    def test_a_harmless_variable_may_be_allowed_through(self) -> None:
        config = self.load(lambda raw: raw["launch"].update(env_allow=["NODE_ENV"]))
        self.assertIn("NODE_ENV", config.launch.policy.allow)

    def test_a_credential_shaped_variable_cannot_be_allowed_through(self) -> None:
        error = self.refuses(lambda raw: raw["launch"].update(env_allow=["DEPLOY_TOKEN"]))
        self.assertIn("credential-shaped", error.message)

    def test_model_access_is_chosen_by_channel_not_by_variable_name(self) -> None:
        config = self.load(lambda raw: raw["launch"].update(model_auth="anthropic-api-key"))
        self.assertEqual(config.launch.policy.permit, frozenset({"ANTHROPIC_API_KEY"}))

    def test_every_shipped_channel_loads(self) -> None:
        for channel in MODEL_AUTH_CHANNELS:
            config = self.load(lambda raw, channel=channel: raw["launch"].update(model_auth=channel))
            self.assertEqual(config.launch.policy.permit, frozenset({MODEL_AUTH_CHANNELS[channel]}))

    def test_no_credential_variable_can_be_named_as_a_channel(self) -> None:
        """PAPI90-P1-003: the exact probes from the blocker, plus their siblings."""
        for name in (
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "JMD_DEPLOY_KEY",
            "VERCEL_TOKEN",
            "AWS_SECRET_ACCESS_KEY",
            "KARAN_APPROVAL_TOKEN",
            "SANITY_WRITE_TOKEN",
            "N8N_API_KEY",
            "STRIPE_SECRET",
            "SSH_AUTH_SOCK",
            "GIT_ASKPASS",
            "ANTHROPIC_API_KEY",
            "PR_PROVER_CAPABILITY_SOCKET",
            "PATH",
            "HOME",
        ):
            error = self.refuses(lambda raw, name=name: raw["launch"].update(model_auth=name))
            self.assertIn("model-access channels", error.message, name)

    def test_the_retired_model_auth_env_key_is_a_migration_error(self) -> None:
        error = self.refuses(
            lambda raw: raw["launch"].update(model_auth_env="ANTHROPIC_API_KEY")
        )
        self.assertIn("launch.model_auth_env named an arbitrary environment variable", error.message)
        self.assertIn("code-owned channels", error.message)

    def test_the_retired_inject_as_key_is_a_migration_error(self) -> None:
        """PAPI90-P1-008: there is no injection name left to configure."""
        error = self.refuses(
            lambda raw: raw["launch"]["identities"]["builder"].update(inject_as="MY_TOKEN")
        )
        self.assertIn("No credential is injected into a child any more", error.message)

    def test_an_unknown_launch_key_fails_closed(self) -> None:
        self.refuses(lambda raw: raw["launch"].update(inherit_environment=True))


class CheckConfigTests(LaunchConfigTestCase):
    def test_check_config_reports_each_identity_without_its_credential(self) -> None:
        import io
        from contextlib import redirect_stdout

        path = self.tmp / "run.json"
        path.write_text(json.dumps(payload(self.tmp, self.source_repo)), encoding="utf-8")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = main(["check-config", "--config", str(path)])

        printed = stream.getvalue()
        self.assertEqual(code, 0)
        self.assertIn(f"identity builder: {BUILDER_LOGIN}", printed)
        self.assertIn("comment-pr, push-branch", printed)
        self.assertIn("env:PR_PROVER_BUILDER_TOKEN", printed)
        self.assertIn(f"identity reviewer: {REVIEWER_LOGIN}", printed)

    def test_the_shipped_example_declares_scoped_identities(self) -> None:
        config = self.example("run.example.json")
        self.assertEqual(config.launch.identities["reviewer"].login, "karanagent1")
        self.assertEqual(
            sorted(config.launch.identities["builder"].capabilities),
            ["comment-pr", "push-branch"],
        )
        self.assertIsNone(config.builder.argv)

    def test_the_shipped_script_lane_example_is_valid_and_still_scoped(self) -> None:
        config = self.example("run.script-lanes.example.json")
        self.assertIsNone(config.builder.agent)
        self.assertEqual(config.builder.identity, "builder")
        self.assertEqual([reviewer.identity for reviewer in config.reviewers], ["reviewer"] * 2)

    def example(self, name: str) -> RunConfig:
        path = Path(__file__).resolve().parents[1] / "examples" / name
        raw = copy.deepcopy(json.loads(path.read_text(encoding="utf-8")))
        return RunConfig.from_mapping(raw, base_dir=path.parent)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
