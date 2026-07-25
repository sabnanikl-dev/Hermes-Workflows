"""Scoped identities: what may be declared, how it is read, and what it may do."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from _support import BUILDER_LOGIN, BUILDER_TOKEN, REVIEWER_LOGIN

from pr_prover.commands import CommandResult
from pr_prover.errors import IdentityError
from pr_prover.identities import (
    BUILDER_CAPABILITIES,
    REVIEWER_CAPABILITIES,
    GhIdentityVerifier,
    IdentityFacts,
    IdentitySpec,
    assert_scope,
    resolve,
)


def builder_spec(**overrides: object) -> IdentitySpec:
    fields: dict[str, object] = {
        "name": "builder",
        "login": BUILDER_LOGIN,
        "capabilities": BUILDER_CAPABILITIES,
        "token_env": "PR_PROVER_BUILDER_TOKEN",
    }
    fields.update(overrides)
    return IdentitySpec(**fields)  # type: ignore[arg-type]


class SpecTests(unittest.TestCase):
    def test_a_well_formed_identity_is_accepted(self) -> None:
        spec = builder_spec()
        self.assertEqual(spec.login, BUILDER_LOGIN)
        self.assertEqual(spec.source_name, "env:PR_PROVER_BUILDER_TOKEN")

    def test_merge_is_not_in_the_capability_vocabulary(self) -> None:
        for capability in ("merge-pr", "approve", "deploy", "admin", "karan-approval"):
            with self.assertRaises(IdentityError) as caught:
                builder_spec(capabilities=frozenset({capability}))
            self.assertEqual(caught.exception.reason, "identity-error")

    def test_an_identity_with_no_capabilities_fails_closed(self) -> None:
        with self.assertRaises(IdentityError):
            builder_spec(capabilities=frozenset())

    def test_an_unusable_login_fails_closed(self) -> None:
        for login in ("", "not a login", "-leading", "x" * 40):
            with self.assertRaises(IdentityError):
                builder_spec(login=login)

    def test_exactly_one_credential_source_is_required(self) -> None:
        with self.assertRaises(IdentityError):
            builder_spec(token_env=None)
        with self.assertRaises(IdentityError):
            builder_spec(token_file=Path("/tmp/token"))

    def test_an_identity_cannot_be_injected_as_github_authority(self) -> None:
        with self.assertRaises(IdentityError):
            builder_spec(inject_as="GITHUB_TOKEN")

    def test_the_source_name_never_carries_the_credential(self) -> None:
        self.assertNotIn(BUILDER_TOKEN, builder_spec().source_name)


class ResolveTests(unittest.TestCase):
    def test_a_credential_is_read_from_the_named_variable(self) -> None:
        identity = resolve(builder_spec(), {"PR_PROVER_BUILDER_TOKEN": BUILDER_TOKEN})
        self.assertEqual(identity.token, BUILDER_TOKEN)
        self.assertEqual(identity.injection(), {"GH_TOKEN": BUILDER_TOKEN})

    def test_a_missing_variable_fails_closed(self) -> None:
        with self.assertRaises(IdentityError) as caught:
            resolve(builder_spec(), {})
        self.assertIn("not set", caught.exception.message)

    def test_an_empty_or_implausible_credential_fails_closed(self) -> None:
        for value in ("", "   ", "short", "two words here that are long"):
            with self.assertRaises(IdentityError):
                resolve(builder_spec(), {"PR_PROVER_BUILDER_TOKEN": value})

    def test_a_source_holding_two_credentials_is_ambiguous(self) -> None:
        with self.assertRaises(IdentityError) as caught:
            resolve(builder_spec(), {"PR_PROVER_BUILDER_TOKEN": f"{BUILDER_TOKEN}\n{BUILDER_TOKEN}"})
        self.assertIn("exactly one", caught.exception.message)

    def test_neither_the_repr_nor_the_evidence_carries_the_credential(self) -> None:
        identity = resolve(builder_spec(), {"PR_PROVER_BUILDER_TOKEN": BUILDER_TOKEN})
        self.assertNotIn(BUILDER_TOKEN, repr(identity))
        self.assertNotIn(BUILDER_TOKEN, json.dumps(identity.as_evidence()))
        self.assertEqual(identity.as_evidence()["login"], BUILDER_LOGIN)


class CredentialFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "token"

    def spec(self) -> IdentitySpec:
        return builder_spec(token_env=None, token_file=self.path)

    def test_an_owner_only_file_is_read(self) -> None:
        self.path.write_text(BUILDER_TOKEN + "\n", encoding="utf-8")
        self.path.chmod(0o600)
        self.assertEqual(resolve(self.spec(), {}).token, BUILDER_TOKEN)

    def test_a_file_readable_by_anyone_else_fails_closed(self) -> None:
        self.path.write_text(BUILDER_TOKEN + "\n", encoding="utf-8")
        self.path.chmod(0o644)
        with self.assertRaises(IdentityError) as caught:
            resolve(self.spec(), {})
        self.assertIn("beyond its owner", caught.exception.message)

    def test_a_missing_file_fails_closed(self) -> None:
        with self.assertRaises(IdentityError):
            resolve(self.spec(), {})

    def test_a_directory_is_not_a_credential(self) -> None:
        self.path.mkdir()
        self.path.chmod(0o700)
        with self.assertRaises(IdentityError):
            resolve(self.spec(), {})


class ScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = resolve(builder_spec(), {"PR_PROVER_BUILDER_TOKEN": BUILDER_TOKEN})
        self.reviewer = resolve(
            builder_spec(
                name="reviewer",
                login=REVIEWER_LOGIN,
                capabilities=REVIEWER_CAPABILITIES,
            ),
            {"PR_PROVER_BUILDER_TOKEN": BUILDER_TOKEN},
        )

    def facts(self, login: str, **permissions: bool) -> IdentityFacts:
        held = {"pull": True, "push": False, "maintain": False, "admin": False}
        held.update(permissions)
        return IdentityFacts(login=login, permissions=held)

    def test_a_correctly_scoped_builder_credential_passes(self) -> None:
        assert_scope(self.builder, self.facts(BUILDER_LOGIN, push=True), repo="o/n", lane="builder")

    def test_a_correctly_scoped_reviewer_credential_passes(self) -> None:
        assert_scope(self.reviewer, self.facts(REVIEWER_LOGIN), repo="o/n", lane="reviewer A")

    def test_another_account_fails_closed(self) -> None:
        with self.assertRaises(IdentityError) as caught:
            assert_scope(self.builder, self.facts("someone-else", push=True), repo="o/n", lane="builder")
        self.assertIn("different GitHub account", caught.exception.message)

    def test_a_login_differing_only_in_case_is_the_same_account(self) -> None:
        assert_scope(
            self.builder, self.facts(BUILDER_LOGIN.upper(), push=True), repo="o/n", lane="builder"
        )

    def test_a_credential_that_can_merge_is_refused(self) -> None:
        for permission in ("admin", "maintain"):
            with self.assertRaises(IdentityError) as caught:
                assert_scope(
                    self.builder,
                    self.facts(BUILDER_LOGIN, push=True, **{permission: True}),
                    repo="o/n",
                    lane="builder",
                )
            self.assertIn("merge", caught.exception.message)

    def test_a_builder_credential_that_cannot_push_is_refused(self) -> None:
        with self.assertRaises(IdentityError):
            assert_scope(self.builder, self.facts(BUILDER_LOGIN), repo="o/n", lane="builder")

    def test_a_reviewer_credential_that_can_push_is_refused(self) -> None:
        with self.assertRaises(IdentityError) as caught:
            assert_scope(
                self.reviewer, self.facts(REVIEWER_LOGIN, push=True), repo="o/n", lane="reviewer A"
            )
        self.assertIn("no push capability", caught.exception.message)

    def test_a_credential_that_cannot_read_the_repository_is_refused(self) -> None:
        with self.assertRaises(IdentityError):
            assert_scope(
                self.builder,
                self.facts(BUILDER_LOGIN, push=True, pull=False),
                repo="o/n",
                lane="builder",
            )


class ScriptedRunner:
    """Returns queued results and records the environment each call was given."""

    def __init__(self, *results: tuple[int, str]) -> None:
        self.results = list(results)
        self.calls: list[tuple[tuple[str, ...], dict[str, str]]] = []

    def run(self, argv, *, cwd=None, env=None, timeout=None):  # type: ignore[no-untyped-def]
        self.calls.append((tuple(argv), dict(env or {})))
        code, stdout = self.results.pop(0)
        return CommandResult(argv=tuple(argv), returncode=code, stdout=stdout, stderr="")


class GhVerifierTests(unittest.TestCase):
    def test_the_login_and_permissions_are_read_with_the_child_environment(self) -> None:
        runner = ScriptedRunner(
            (0, BUILDER_LOGIN + "\n"), (0, '{"admin":false,"push":true,"pull":true}\n')
        )
        facts = GhIdentityVerifier(runner).facts({"GH_TOKEN": BUILDER_TOKEN}, repo="o/n")
        self.assertEqual(facts.login, BUILDER_LOGIN)
        self.assertTrue(facts.permissions["push"])
        self.assertFalse(facts.permissions["admin"])
        self.assertEqual(runner.calls[0][1], {"GH_TOKEN": BUILDER_TOKEN})
        self.assertEqual(runner.calls[1][0][2], "repos/o/n")

    def test_a_failing_call_fails_closed(self) -> None:
        with self.assertRaises(IdentityError):
            GhIdentityVerifier(ScriptedRunner((1, ""))).facts({}, repo="o/n")

    def test_an_unusable_login_fails_closed(self) -> None:
        with self.assertRaises(IdentityError):
            GhIdentityVerifier(ScriptedRunner((0, "not a login\n"))).facts({}, repo="o/n")

    def test_unparsable_permissions_fail_closed(self) -> None:
        runner = ScriptedRunner((0, BUILDER_LOGIN + "\n"), (0, "not json"))
        with self.assertRaises(IdentityError):
            GhIdentityVerifier(runner).facts({}, repo="o/n")

    def test_absent_permissions_fail_closed(self) -> None:
        runner = ScriptedRunner((0, BUILDER_LOGIN + "\n"), (0, "null"))
        with self.assertRaises(IdentityError):
            GhIdentityVerifier(runner).facts({}, repo="o/n")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
