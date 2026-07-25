"""The child environment allowlist: what a child gets, and what it can never get."""
from __future__ import annotations

import unittest

from _support import FORBIDDEN_VALUES, parent_env

from pr_prover.childenv import (
    DEFAULT_ALLOW,
    EnvironmentPolicy,
    assert_scoped,
    carries_none_of,
    is_denied,
    validate_env_name,
)
from pr_prover.errors import LaunchPolicyError

GUARDS = {
    "GH_CONFIG_DIR": "/tmp/scratch/gh",
    "GIT_CONFIG_GLOBAL": "/tmp/scratch/gitconfig",
    "GIT_CONFIG_SYSTEM": "/dev/null",
}


class DenyListTests(unittest.TestCase):
    def test_github_authority_is_denied_by_name(self) -> None:
        for name in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GH_HOST"):
            self.assertTrue(is_denied(name), name)

    def test_anything_named_like_a_credential_is_denied(self) -> None:
        for name in (
            "KARAN_APPROVAL_TOKEN",
            "DEPLOY_SECRET",
            "DB_PASSWORD",
            "SERVICE_API_KEY",
            "SESSION_COOKIE",
            "MY_PRIVATE_KEY",
            "SOME_CREDENTIAL_FILE",
        ):
            self.assertTrue(is_denied(name), name)

    def test_whole_vendors_are_denied_by_prefix(self) -> None:
        for name in (
            "JMD_ANYTHING",
            "VERCEL_ORG_ID",
            "AWS_REGION",
            "SANITY_PROJECT",
            "N8N_HOST",
            "TELEGRAM_CHAT",
            "LINEAR_TEAM",
        ):
            self.assertTrue(is_denied(name), name)

    def test_an_unknown_deploy_token_is_denied_without_being_enumerated(self) -> None:
        self.assertTrue(is_denied("ACME_ROLLOUT_TOKEN"))

    def test_agent_sockets_are_denied(self) -> None:
        self.assertTrue(is_denied("SSH_AUTH_SOCK"))
        self.assertTrue(is_denied("GIT_SSH_COMMAND"))

    def test_ordinary_toolchain_variables_are_not_denied(self) -> None:
        for name in ("PATH", "HOME", "LANG", "TMPDIR", "NODE_ENV"):
            self.assertFalse(is_denied(name), name)

    def test_an_unusable_variable_name_fails_closed(self) -> None:
        for name in ("", "not-a-name", "3STARTS", "WITH SPACE", 7):
            with self.assertRaises(LaunchPolicyError):
                validate_env_name(name, what="test")


class BuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = EnvironmentPolicy()
        self.parent = parent_env()

    def build(self, **kwargs: object) -> dict[str, str]:
        return self.policy.build(self.parent, inject=dict(GUARDS), **kwargs)  # type: ignore[arg-type]

    def test_only_allowlisted_names_survive(self) -> None:
        env = self.build()
        self.assertEqual(
            set(env) - set(GUARDS), {"HOME", "PATH", "LANG"}
        )

    def test_no_credential_from_the_parent_reaches_the_child(self) -> None:
        env = self.build()
        for name in (
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "KARAN_APPROVAL_TOKEN",
            "JMD_DEPLOY_KEY",
            "VERCEL_TOKEN",
            "SANITY_WRITE_TOKEN",
            "AWS_SECRET_ACCESS_KEY",
            "N8N_API_KEY",
            "ANTHROPIC_API_KEY",
            "SSH_AUTH_SOCK",
            "STRIPE_SECRET",
        ):
            self.assertNotIn(name, env)

    def test_no_forbidden_value_appears_anywhere_in_the_child_environment(self) -> None:
        self.assertTrue(carries_none_of(self.build(), FORBIDDEN_VALUES))

    def test_the_scoped_credential_the_launcher_owns_is_injected(self) -> None:
        env = self.policy.build(self.parent, inject={**GUARDS, "GH_TOKEN": "ghp_" + "z" * 36})
        self.assertEqual(env["GH_TOKEN"], "ghp_" + "z" * 36)

    def test_the_parent_variable_a_credential_was_read_from_is_not_passed_on(self) -> None:
        env = self.policy.build(self.parent, inject={**GUARDS, "GH_TOKEN": "ghp_" + "z" * 36})
        self.assertNotIn("PR_PROVER_BUILDER_TOKEN", env)

    def test_env_allow_widens_only_to_harmless_names(self) -> None:
        policy = EnvironmentPolicy(extra_allow=frozenset({"NODE_ENV"}))
        env = policy.build({**self.parent, "NODE_ENV": "test"}, inject=dict(GUARDS))
        self.assertEqual(env["NODE_ENV"], "test")

    def test_env_allow_cannot_name_a_credential(self) -> None:
        with self.assertRaises(LaunchPolicyError):
            EnvironmentPolicy(extra_allow=frozenset({"DEPLOY_TOKEN"}))

    def test_model_auth_may_be_permitted_explicitly(self) -> None:
        policy = EnvironmentPolicy(permit=frozenset({"ANTHROPIC_API_KEY"}))
        env = policy.build(self.parent, inject=dict(GUARDS))
        self.assertEqual(env["ANTHROPIC_API_KEY"], self.parent["ANTHROPIC_API_KEY"])

    def test_github_authority_can_never_be_permitted(self) -> None:
        for name in ("GITHUB_TOKEN", "SSH_AUTH_SOCK", "GIT_ASKPASS"):
            with self.assertRaises(LaunchPolicyError):
                EnvironmentPolicy(permit=frozenset({name}))

    def test_quiet_settings_may_be_overridden_by_the_launcher(self) -> None:
        env = self.policy.build(
            self.parent, inject=dict(GUARDS), overrides={"NO_COLOR": "1", "PR_PROVER_ROLE": "A"}
        )
        self.assertEqual(env["NO_COLOR"], "1")
        self.assertEqual(env["PR_PROVER_ROLE"], "A")

    def test_a_launcher_cannot_smuggle_a_variable_in_as_an_override(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            self.policy.build(self.parent, inject=dict(GUARDS), overrides={"DEPLOY_TOKEN": "x"})
        self.assertIn("declared injection", caught.exception.message)

    def test_a_non_string_value_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError):
            self.policy.build(self.parent, inject={**GUARDS, "GH_TOKEN": 7})  # type: ignore[dict-item]

    def test_evidence_lists_dropped_names_and_no_values(self) -> None:
        dropped = self.policy.dropped(self.parent)
        self.assertIn("GH_TOKEN", dropped)
        self.assertIn("JMD_DEPLOY_KEY", dropped)
        self.assertTrue(all(isinstance(name, str) for name in dropped))
        self.assertTrue(carries_none_of({name: name for name in dropped}, FORBIDDEN_VALUES))


class ScopeAssertionTests(unittest.TestCase):
    """The last gate before a launch, and the one a future change has to pass."""

    def test_a_clean_environment_passes(self) -> None:
        assert_scoped(
            {"PATH": "/usr/bin", "HOME": "/tmp/home", **GUARDS},
            injected=frozenset(GUARDS),
            policy=EnvironmentPolicy(),
        )

    def test_a_leaked_credential_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            assert_scoped(
                {"PATH": "/usr/bin", "DEPLOY_TOKEN": "x"},
                injected=frozenset(),
                policy=EnvironmentPolicy(),
            )
        self.assertEqual(caught.exception.reason, "launch-policy")

    def test_a_variable_outside_the_allowlist_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError):
            assert_scoped({"SOMETHING_ELSE": "x"}, injected=frozenset(), policy=EnvironmentPolicy())

    def test_an_injected_name_that_can_never_be_passed_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError):
            assert_scoped(
                {"GITHUB_TOKEN": "x"}, injected=frozenset({"GITHUB_TOKEN"}), policy=EnvironmentPolicy()
            )

    def test_home_without_the_toolchain_guards_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            assert_scoped({"HOME": "/tmp/home"}, injected=frozenset(), policy=EnvironmentPolicy())
        self.assertIn("GH_CONFIG_DIR", caught.exception.message)

    def test_the_default_allowlist_carries_nothing_with_authority(self) -> None:
        self.assertFalse([name for name in DEFAULT_ALLOW if is_denied(name)])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
