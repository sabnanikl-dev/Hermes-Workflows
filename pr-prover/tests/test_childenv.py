"""The child environment allowlist: what a child gets, and what it can never get."""
from __future__ import annotations

import unittest

from _support import FORBIDDEN_VALUES, parent_env

from pr_prover.childenv import (
    CAPABILITY_CHANNEL,
    CAPABILITY_SECRET,
    CLAUDE_TMPDIR,
    DEFAULT_ALLOW,
    HOME_GUARDS,
    INJECTABLE,
    LAUNCHER_OVERRIDES,
    MODEL_AUTH_CHANNELS,
    EnvironmentPolicy,
    assert_scoped,
    carries_none_of,
    is_denied,
    model_auth_variable,
    validate_env_name,
)
from pr_prover.errors import LaunchPolicyError

SYNTHETIC_HOME = "/tmp/pr-prover-scratch/home/lane"

# What a launcher injects for every lane: a synthetic home, and every guard that
# keeps a toolchain from looking somewhere else for configuration.
GUARDS = {
    "HOME": SYNTHETIC_HOME,
    "CLAUDE_CONFIG_DIR": f"{SYNTHETIC_HOME}/.claude",
    "GH_CONFIG_DIR": f"{SYNTHETIC_HOME}/.config/gh",
    "GIT_CONFIG_GLOBAL": f"{SYNTHETIC_HOME}/.gitconfig",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "GNUPGHOME": f"{SYNTHETIC_HOME}/.gnupg",
    "XDG_CACHE_HOME": f"{SYNTHETIC_HOME}/.cache",
    "XDG_CONFIG_HOME": f"{SYNTHETIC_HOME}/.config",
    "XDG_DATA_HOME": f"{SYNTHETIC_HOME}/.local/share",
    "XDG_STATE_HOME": f"{SYNTHETIC_HOME}/.local/state",
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
            "KARAN_ANYTHING",
        ):
            self.assertTrue(is_denied(name), name)

    def test_an_unknown_deploy_token_is_denied_without_being_enumerated(self) -> None:
        self.assertTrue(is_denied("ACME_ROLLOUT_TOKEN"))

    def test_agent_sockets_are_denied(self) -> None:
        self.assertTrue(is_denied("SSH_AUTH_SOCK"))
        self.assertTrue(is_denied("GIT_SSH_COMMAND"))

    def test_the_operators_home_is_denied_like_a_credential(self) -> None:
        """PAPI90-P1-002: HOME carries gh, git, ssh and model-client credentials."""
        self.assertTrue(is_denied("HOME"))
        self.assertNotIn("HOME", DEFAULT_ALLOW)

    def test_every_configuration_discovery_guard_is_denied_from_the_parent(self) -> None:
        for name in HOME_GUARDS:
            self.assertTrue(is_denied(name), name)

    def test_ordinary_toolchain_variables_are_not_denied(self) -> None:
        for name in ("PATH", "LANG", "TMPDIR", "NODE_ENV"):
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
        self.assertEqual(set(env) - set(GUARDS), {"PATH", "LANG"})

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

    def test_the_operators_home_is_never_the_childs_home(self) -> None:
        """PAPI90-P1-002: a child gets the launcher's home, not the operator's."""
        env = self.build()
        self.assertEqual(env["HOME"], SYNTHETIC_HOME)
        self.assertNotEqual(env["HOME"], self.parent["HOME"])
        self.assertTrue(carries_none_of(env, [self.parent["HOME"]]))

    def test_a_child_given_the_operators_home_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            self.policy.build(
                self.parent, inject={**GUARDS, "HOME": self.parent["HOME"]}
            )
        self.assertIn("operator's own home", caught.exception.message)

    def test_every_configuration_lookup_is_pointed_inside_the_synthetic_home(self) -> None:
        env = self.build()
        for guard in HOME_GUARDS:
            self.assertIn(guard, env, guard)
        self.assertEqual(env["GIT_CONFIG_SYSTEM"], "/dev/null")
        for guard in HOME_GUARDS:
            if guard != "GIT_CONFIG_SYSTEM":
                self.assertTrue(env[guard].startswith(SYNTHETIC_HOME), guard)

    def test_a_child_without_a_synthetic_home_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            self.policy.build(self.parent, inject={})
        self.assertIn("synthetic HOME", caught.exception.message)

    def test_a_synthetic_home_without_every_guard_fails_closed(self) -> None:
        for guard in HOME_GUARDS:
            partial = {name: value for name, value in GUARDS.items() if name != guard}
            with self.assertRaises(LaunchPolicyError) as caught:
                self.policy.build(self.parent, inject=partial)
            self.assertIn(guard, str(caught.exception.evidence), guard)

    def test_the_parent_variable_a_credential_was_read_from_is_not_passed_on(self) -> None:
        env = self.build()
        self.assertNotIn("PR_PROVER_BUILDER_TOKEN", env)
        self.assertNotIn("PR_PROVER_REVIEWER_TOKEN", env)

    def test_no_github_credential_can_be_injected_under_any_name(self) -> None:
        """PAPI90-P1-001/008: injection is a closed set with no credential in it."""
        for name in ("GH_TOKEN", "GITHUB_TOKEN", "MY_OWN_CHANNEL", "GIT_ASKPASS"):
            with self.assertRaises(LaunchPolicyError) as caught:
                self.policy.build(self.parent, inject={**GUARDS, name: "ghp_" + "z" * 36})
            self.assertEqual(caught.exception.reason, "launch-policy")

    def test_the_injectable_set_is_exactly_the_closed_list(self) -> None:
        """The set is closed, and the one credential-shaped name in it is ours.

        ``PR_PROVER_CAPABILITY_SECRET`` matches the credential-shaped deny rules
        by design — it is a secret. It is on this list anyway because it grants
        nothing except the right to be heard on one lane's own capability
        socket, which the launcher created, and it is the only way that socket
        means anything at all. Nothing a *parent* environment supplies can reach
        a child under that name: the launcher mints the value, and a parent
        variable of the same name is denied like any other.
        """
        self.assertEqual(
            INJECTABLE,
            frozenset({"HOME", "PATH", CAPABILITY_CHANNEL, CAPABILITY_SECRET, *HOME_GUARDS}),
        )
        self.assertNotIn("GH_TOKEN", INJECTABLE)
        self.assertTrue(is_denied(CAPABILITY_SECRET))

    def test_the_capability_channel_is_the_one_internal_channel(self) -> None:
        env = self.policy.build(
            self.parent,
            inject={
                **GUARDS,
                CAPABILITY_CHANNEL: "/tmp/prcap-x/lane.sock",
                CAPABILITY_SECRET: "f" * 64,
            },
        )
        self.assertEqual(env[CAPABILITY_CHANNEL], "/tmp/prcap-x/lane.sock")
        self.assertTrue(carries_none_of(env, FORBIDDEN_VALUES))

    def test_a_channel_without_its_secret_is_refused(self) -> None:
        """PAPI-90 item 2: a socket path on its own is not an authenticator."""
        with self.assertRaises(LaunchPolicyError) as caught:
            self.policy.build(
                self.parent, inject={**GUARDS, CAPABILITY_CHANNEL: "/tmp/prcap-x/lane.sock"}
            )
        self.assertIn("secret", caught.exception.message)

    def test_a_secret_without_its_channel_is_refused(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            self.policy.build(self.parent, inject={**GUARDS, CAPABILITY_SECRET: "f" * 64})
        self.assertIn("secret", caught.exception.message)

    def test_a_short_channel_secret_is_refused(self) -> None:
        """An authenticator short enough to guess is not one."""
        with self.assertRaises(LaunchPolicyError) as caught:
            self.policy.build(
                self.parent,
                inject={
                    **GUARDS,
                    CAPABILITY_CHANNEL: "/tmp/prcap-x/lane.sock",
                    CAPABILITY_SECRET: "short",
                },
            )
        self.assertIn("too short", caught.exception.message)

    def test_an_override_cannot_collide_with_an_injected_name(self) -> None:
        """PAPI90-P1-008: one variable cannot have two owners."""
        for name in ("HOME", "PATH", CAPABILITY_CHANNEL):
            with self.assertRaises(LaunchPolicyError) as caught:
                self.policy.build(
                    self.parent,
                    inject={**GUARDS, CAPABILITY_CHANNEL: "/tmp/x.sock"},
                    overrides={name: "/somewhere/else"},
                )
            self.assertIn("two owners", caught.exception.message)

    def test_env_allow_widens_only_to_harmless_names(self) -> None:
        policy = EnvironmentPolicy(extra_allow=frozenset({"NODE_ENV"}))
        env = policy.build({**self.parent, "NODE_ENV": "test"}, inject=dict(GUARDS))
        self.assertEqual(env["NODE_ENV"], "test")

    def test_env_allow_cannot_name_a_credential(self) -> None:
        with self.assertRaises(LaunchPolicyError):
            EnvironmentPolicy(extra_allow=frozenset({"DEPLOY_TOKEN"}))

    def test_env_allow_cannot_shadow_launcher_owned_material(self) -> None:
        for name in ("HOME", "PATH", "GH_CONFIG_DIR", "NO_COLOR", "PR_PROVER_LANE"):
            with self.assertRaises(LaunchPolicyError):
                EnvironmentPolicy(extra_allow=frozenset({name}))

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
            self.policy.build(self.parent, inject={**GUARDS, "PATH": 7})  # type: ignore[dict-item]

    def test_evidence_lists_dropped_names_and_no_values(self) -> None:
        dropped = self.policy.dropped(self.parent)
        self.assertIn("GH_TOKEN", dropped)
        self.assertIn("JMD_DEPLOY_KEY", dropped)
        self.assertIn("HOME", dropped)
        self.assertTrue(all(isinstance(name, str) for name in dropped))
        self.assertTrue(carries_none_of({name: name for name in dropped}, FORBIDDEN_VALUES))


class ModelAuthChannelTests(unittest.TestCase):
    """PAPI90-P1-003: model access is a closed channel, not a variable name."""

    def setUp(self) -> None:
        self.parent = parent_env()

    def test_a_named_channel_passes_exactly_one_model_variable(self) -> None:
        policy = EnvironmentPolicy(model_auth="anthropic-api-key")
        env = policy.build(self.parent, inject=dict(GUARDS))
        self.assertEqual(env["ANTHROPIC_API_KEY"], self.parent["ANTHROPIC_API_KEY"])
        self.assertEqual(policy.permit, frozenset({"ANTHROPIC_API_KEY"}))

    def test_a_channel_admits_nothing_else_from_the_parent(self) -> None:
        policy = EnvironmentPolicy(model_auth="anthropic-api-key")
        env = policy.build(self.parent, inject=dict(GUARDS))
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
        ):
            self.assertNotIn(name, env, name)

    def test_no_environment_variable_name_can_be_used_as_a_channel(self) -> None:
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
        ):
            with self.assertRaises(LaunchPolicyError) as caught:
                EnvironmentPolicy(model_auth=name)
            self.assertIn("model-access channels", caught.exception.message)

    def test_an_unknown_channel_fails_closed(self) -> None:
        for channel in ("", "github", "deploy", None.__class__.__name__, 7):
            with self.assertRaises(LaunchPolicyError):
                model_auth_variable(channel)

    def test_every_channel_names_a_model_variable_and_nothing_else(self) -> None:
        for channel, name in MODEL_AUTH_CHANNELS.items():
            self.assertNotIn(name, INJECTABLE, channel)
            self.assertNotIn(name, DEFAULT_ALLOW, channel)
            self.assertFalse(name.startswith("PR_PROVER_"), channel)
            self.assertFalse(name.startswith(("GH_", "GITHUB_", "GIT_", "SSH_")), channel)


class ScopeAssertionTests(unittest.TestCase):
    """The last gate before a launch, and the one a future change has to pass."""

    def test_a_clean_environment_passes(self) -> None:
        assert_scoped(
            {"PATH": "/usr/bin", **GUARDS},
            injected=frozenset(GUARDS),
            policy=EnvironmentPolicy(),
        )

    def test_a_leaked_credential_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            assert_scoped(
                {"PATH": "/usr/bin", "DEPLOY_TOKEN": "x", **GUARDS},
                injected=frozenset(GUARDS),
                policy=EnvironmentPolicy(),
            )
        self.assertEqual(caught.exception.reason, "launch-policy")

    def test_a_variable_outside_the_allowlist_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError):
            assert_scoped(
                {"SOMETHING_ELSE": "x", **GUARDS},
                injected=frozenset(GUARDS),
                policy=EnvironmentPolicy(),
            )

    def test_an_injected_name_outside_the_closed_set_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            assert_scoped(
                {"GITHUB_TOKEN": "x", **GUARDS},
                injected=frozenset({"GITHUB_TOKEN", *GUARDS}),
                policy=EnvironmentPolicy(),
            )
        self.assertIn("closed injectable set", caught.exception.message)

    def test_home_without_the_configuration_guards_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            assert_scoped(
                {"HOME": SYNTHETIC_HOME}, injected=frozenset({"HOME"}), policy=EnvironmentPolicy()
            )
        self.assertIn("GH_CONFIG_DIR", str(caught.exception.evidence))

    def test_a_home_that_was_not_injected_fails_closed(self) -> None:
        """An inherited HOME is refused as a denied name before anything else."""
        with self.assertRaises(LaunchPolicyError) as caught:
            assert_scoped(
                {"HOME": "/Users/operator", **{k: v for k, v in GUARDS.items() if k != "HOME"}},
                injected=frozenset(GUARDS) - {"HOME"},
                policy=EnvironmentPolicy(),
            )
        self.assertEqual(caught.exception.reason, "launch-policy")
        self.assertEqual(caught.exception.evidence["name"], "HOME")

    def test_the_default_allowlist_carries_nothing_with_authority(self) -> None:
        self.assertFalse([name for name in DEFAULT_ALLOW if is_denied(name)])



class LaneTemporaryDirectoryTests(unittest.TestCase):
    """``CLAUDE_CODE_TMPDIR`` is the launcher's to write, and nobody else's."""

    def test_it_is_a_launcher_owned_name(self) -> None:
        self.assertIn(CLAUDE_TMPDIR, LAUNCHER_OVERRIDES)
        self.assertNotIn(CLAUDE_TMPDIR, DEFAULT_ALLOW)
        self.assertNotIn(CLAUDE_TMPDIR, INJECTABLE)

    def test_a_configuration_cannot_claim_it(self) -> None:
        """Former-red: a run config that named it could point a lane's temp anywhere."""
        for name in (CLAUDE_TMPDIR, "TMPDIR"):
            with self.subTest(name=name), self.assertRaises(LaunchPolicyError) as caught:
                EnvironmentPolicy(extra_allow=frozenset({name}))
            self.assertIn("launcher-owned", caught.exception.message)

    def lane_injection(self) -> dict[str, str]:
        home = {name: f"/lane/home/{name.lower()}" for name in HOME_GUARDS}
        home["HOME"] = "/lane/home"
        return home

    def test_a_parent_value_cannot_shadow_it(self) -> None:
        child = EnvironmentPolicy().build(
            {"HOME": "/operator", CLAUDE_TMPDIR: "/operator/tmp", "TMPDIR": "/operator/tmp"},
            inject=self.lane_injection(),
            overrides={CLAUDE_TMPDIR: "/lane/scratch/tmp", "TMPDIR": "/lane/scratch/tmp"},
        )
        self.assertEqual(child[CLAUDE_TMPDIR], "/lane/scratch/tmp")
        self.assertEqual(child["TMPDIR"], "/lane/scratch/tmp")

    def test_it_cannot_be_injected_instead_of_overridden(self) -> None:
        """The injectable set is closed; a temp directory is not authority material."""
        with self.assertRaises(LaunchPolicyError) as caught:
            EnvironmentPolicy().build(
                {"HOME": "/operator"},
                inject={**self.lane_injection(), CLAUDE_TMPDIR: "/lane/scratch/tmp"},
            )
        self.assertIn("outside the closed injectable set", caught.exception.message)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
