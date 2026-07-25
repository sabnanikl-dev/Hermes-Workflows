"""Classification, the GitHub boundary, redaction, config, and the CLI."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from _support import BUILDER_LOGIN, HEAD_A, make_source_repo
from pr_prover import cli, redaction
from pr_prover.commands import CommandResult
from pr_prover.config import RunConfig
from pr_prover.errors import CommandContractError, ConfigError, GitHubError, StateError
from pr_prover.findings import Finding, classify
from pr_prover.github import GhCliGitHub


def finding(identifier: str, severity: str = "blocking", source: str = "reviewer:A") -> Finding:
    return Finding(id=identifier, severity=severity, summary="s", source=source, head=HEAD_A)


class ClassificationTests(unittest.TestCase):
    def test_the_four_buckets(self) -> None:
        result = classify(
            [
                finding("a", "blocking"),
                finding("b", "non-blocking"),
                finding("c", "needs-karan"),
            ]
        )
        self.assertEqual([item.finding.id for item in result.blocking], ["a"])
        self.assertEqual([item.finding.id for item in result.non_blocking], ["b"])
        self.assertEqual([item.finding.id for item in result.needs_karan], ["c"])
        self.assertEqual(result.false_positive, ())

    def test_the_default_adjudicator_never_invents_a_false_positive(self) -> None:
        result = classify([finding("a", "blocking")])
        self.assertEqual(result.false_positive, ())
        self.assertEqual(result.blocking_ids, {"a"})

    def test_both_reviewers_raising_one_id_yields_one_finding_with_both_sources(self) -> None:
        result = classify([finding("a", "blocking"), finding("a", "blocking", source="reviewer:B")])
        self.assertEqual(len(result.blocking), 1)
        self.assertEqual(result.blocking[0].sources, ("reviewer:A", "reviewer:B"))

    def test_the_stronger_claim_wins_a_disagreement(self) -> None:
        result = classify([finding("a", "non-blocking"), finding("a", "blocking", source="reviewer:B")])
        self.assertEqual([item.finding.id for item in result.blocking], ["a"])
        self.assertEqual(result.non_blocking, ())

    def test_an_escalation_outranks_a_blocker(self) -> None:
        result = classify([finding("a", "blocking"), finding("a", "needs-karan", source="reviewer:B")])
        self.assertEqual([item.finding.id for item in result.needs_karan], ["a"])

    def test_an_adjudicator_returning_nonsense_fails_closed(self) -> None:
        with self.assertRaises(StateError):
            classify([finding("a")], adjudicator=lambda _finding: "probably fine")

    def test_an_adjudicator_that_raises_fails_closed(self) -> None:
        def explode(_finding: Finding) -> str:
            raise RuntimeError("boom")

        with self.assertRaises(StateError):
            classify([finding("a")], adjudicator=explode)

    def test_an_unknown_severity_cannot_be_constructed(self) -> None:
        with self.assertRaises(StateError):
            Finding(id="a", severity="critical", summary="s", source="reviewer:A", head=HEAD_A)


class GhBoundaryTests(unittest.TestCase):
    def boundary(self, stdout: str, *, returncode: int = 0) -> GhCliGitHub:
        class OneShot:
            def run(self, argv, *, cwd=None, env=None, timeout=None):
                return CommandResult(argv=tuple(argv), returncode=returncode, stdout=stdout, stderr="denied")

        return GhCliGitHub(OneShot())

    def payload(self, **overrides: object) -> str:
        body = {
            "number": 7,
            "state": "OPEN",
            "isDraft": True,
            "title": "example",
            "url": "https://example.invalid/pull/7",
            "headRefName": "feat/example",
            "headRefOid": HEAD_A,
            "baseRefName": "main",
        }
        body.update(overrides)
        return json.dumps(body)

    def test_a_well_formed_payload_is_bound(self) -> None:
        pull = self.boundary(self.payload()).pull_request("example/repo", 7)
        self.assertEqual(pull.head_ref_oid, HEAD_A)
        self.assertTrue(pull.is_draft)

    def test_gh_is_invoked_as_an_argv_array_with_the_json_fields(self) -> None:
        seen: list[tuple[str, ...]] = []

        class Recorder:
            def run(self, argv, *, cwd=None, env=None, timeout=None):
                seen.append(tuple(argv))
                return CommandResult(argv=tuple(argv), returncode=0, stdout=json.dumps({"comments": []}), stderr="")

        GhCliGitHub(Recorder()).comments("example/repo", 7)
        self.assertEqual(seen[0][:6], ("gh", "pr", "view", "7", "--repo", "example/repo"))

    def test_a_short_head_ref_oid_fails_closed(self) -> None:
        with self.assertRaises(GitHubError):
            self.boundary(self.payload(headRefOid="abc1234")).pull_request("example/repo", 7)

    def test_a_payload_for_another_pr_fails_closed(self) -> None:
        with self.assertRaises(GitHubError):
            self.boundary(self.payload(number=8)).pull_request("example/repo", 7)

    def test_a_missing_field_fails_closed(self) -> None:
        body = json.loads(self.payload())
        del body["headRefName"]
        with self.assertRaises(GitHubError):
            self.boundary(json.dumps(body)).pull_request("example/repo", 7)

    def test_unparsable_output_fails_closed(self) -> None:
        with self.assertRaises(GitHubError):
            self.boundary("not json").pull_request("example/repo", 7)

    def test_a_failing_gh_call_fails_closed_without_leaking_the_token(self) -> None:
        class Failing:
            def run(self, argv, *, cwd=None, env=None, timeout=None):
                return CommandResult(
                    argv=tuple(argv),
                    returncode=1,
                    stdout="",
                    stderr="HTTP 401 using GH_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz012345",
                )

        with self.assertRaises(GitHubError) as caught:
            GhCliGitHub(Failing()).pull_request("example/repo", 7)
        self.assertNotIn("ghp_abcdefghij", caught.exception.evidence["stderr"])

    def test_comments_carry_their_author_and_stable_id(self) -> None:
        payload = json.dumps(
            {"comments": [{"id": "IC_kwDO123", "author": {"login": "karanagent1"}, "body": "hi"}]}
        )
        comments = self.boundary(payload).comments("example/repo", 7)
        self.assertEqual(comments[0].author, "karanagent1")
        self.assertEqual(comments[0].identifier, "IC_kwDO123")

    def test_a_comment_without_a_stable_id_fails_closed(self) -> None:
        """Without an id there is no way to tell a comment from a copy of it."""
        payload = json.dumps({"comments": [{"author": {"login": "karanagent1"}, "body": "hi"}]})
        with self.assertRaises(GitHubError):
            self.boundary(payload).comments("example/repo", 7)

    def test_a_comment_without_an_author_fails_closed(self) -> None:
        payload = json.dumps({"comments": [{"id": "IC_kwDO123", "body": "hi"}]})
        with self.assertRaises(GitHubError):
            self.boundary(payload).comments("example/repo", 7)


class RedactionTests(unittest.TestCase):
    def test_github_tokens_are_removed(self) -> None:
        for token in ("ghp_abcdefghijklmnopqrstuvwxyz012345", "gho_abcdefghijklmnopqrstuvwxyz012345"):
            with self.subTest(token=token):
                self.assertNotIn(token, redaction.scrub(f"failed with {token} attached"))

    def test_fine_grained_pats_are_removed(self) -> None:
        secret = "github_pat_" + "A1b2C3d4E5f6G7h8I9j0K1"
        self.assertNotIn(secret, redaction.scrub(f"token={secret}"))

    def test_credential_shaped_assignments_are_removed(self) -> None:
        scrubbed = redaction.scrub("GH_TOKEN=hunter2 REVIEWER_SECRET: swordfish")
        self.assertNotIn("hunter2", scrubbed)
        self.assertNotIn("swordfish", scrubbed)

    def test_inline_url_credentials_are_removed(self) -> None:
        scrubbed = redaction.scrub("https://user:p4ssw0rd@github.com/example/repo.git")
        self.assertNotIn("p4ssw0rd", scrubbed)

    def test_private_keys_are_removed(self) -> None:
        pem = "-----BEGIN RSA PRIVATE KEY-----\nMIIEow\n-----END RSA PRIVATE KEY-----"
        self.assertNotIn("MIIEow", redaction.scrub(pem))

    def test_ordinary_output_survives(self) -> None:
        text = "3 tests failed in tests/test_thing.py::test_case"
        self.assertEqual(redaction.scrub(text), text)

    def test_long_output_keeps_both_ends(self) -> None:
        text = "start" + ("x" * 9000) + "DONE: STATUS=pass"
        clipped = redaction.clip(text, limit=400)
        self.assertTrue(clipped.startswith("start"))
        self.assertTrue(clipped.endswith("DONE: STATUS=pass"))
        self.assertLess(len(clipped), 500)


# Representative credential shapes, assembled at runtime so the literals in this
# file are not themselves scannable as secrets.
GH_TOKEN = "ghp_" + ("A1b2C3d4E5" * 3) + "fg"
FINE_GRAINED_PAT = "github_pat_" + ("Z9y8X7w6V5" * 3)
PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\n-----END RSA PRIVATE KEY-----"
URL_WITH_CREDENTIALS = "https://ci-bot:sup3rs3cret@github.com/example/repo.git"
SECRETS = (GH_TOKEN, FINE_GRAINED_PAT, "MIIEowIBAAKCAQEA", "sup3rs3cret")


class SanitizerTests(unittest.TestCase):
    """REVIEW-A-P1-004: the recursive final boundary over evidence structures."""

    def test_strings_nested_in_dicts_and_lists_are_scrubbed(self) -> None:
        payload = {
            "lock": {"body": f"held with {GH_TOKEN}"},
            "argv": ["git", "clone", URL_WITH_CREDENTIALS],
            "keys": [{"pem": PRIVATE_KEY}, {"pat": FINE_GRAINED_PAT}],
        }
        rendered = json.dumps(redaction.sanitize(payload))
        for secret in SECRETS:
            with self.subTest(secret=secret[:12]):
                self.assertNotIn(secret, rendered)

    def test_dictionary_keys_are_scrubbed_too(self) -> None:
        sanitized = redaction.sanitize({f"env {GH_TOKEN}": "value"})
        self.assertNotIn(GH_TOKEN, json.dumps(sanitized))

    def test_structure_and_scalar_types_survive(self) -> None:
        payload = {"count": 3, "ok": True, "ratio": 0.5, "missing": None, "items": ["a"]}
        sanitized = redaction.sanitize(payload)
        self.assertEqual(sanitized, payload)
        self.assertIsInstance(sanitized["count"], int)
        self.assertIsInstance(sanitized["ok"], bool)
        self.assertIsInstance(sanitized["ratio"], float)
        self.assertIsNone(sanitized["missing"])
        self.assertIsInstance(sanitized["items"], list)

    def test_tuples_stay_tuples_and_are_scrubbed(self) -> None:
        sanitized = redaction.sanitize({"argv": ("gh", "auth", GH_TOKEN)})
        self.assertIsInstance(sanitized["argv"], tuple)
        self.assertNotIn(GH_TOKEN, "".join(sanitized["argv"]))

    def test_a_secret_below_many_layers_is_still_scrubbed(self) -> None:
        value: object = GH_TOKEN
        for _ in range(redaction.MAX_DEPTH - 1):
            value = {"next": [value]}
        self.assertNotIn(GH_TOKEN, json.dumps(redaction.sanitize(value)))

    def test_nesting_past_the_depth_cap_is_elided_not_leaked(self) -> None:
        value: object = GH_TOKEN
        for _ in range(redaction.MAX_DEPTH * 3):
            value = {"next": value}
        rendered = json.dumps(redaction.sanitize(value))
        self.assertNotIn(GH_TOKEN, rendered)
        self.assertIn("nested deeper", rendered)

    def test_a_self_referential_structure_terminates(self) -> None:
        payload: dict[str, object] = {"token": GH_TOKEN}
        payload["self"] = payload
        rendered = json.dumps(redaction.sanitize(payload))
        self.assertNotIn(GH_TOKEN, rendered)
        self.assertIn("circular", rendered)

    def test_an_arbitrary_object_is_rendered_as_scrubbed_text(self) -> None:
        sanitized = redaction.sanitize(Path(f"/tmp/{GH_TOKEN}/run.lock"))
        self.assertIsInstance(sanitized, str)
        self.assertNotIn(GH_TOKEN, sanitized)


class FinalBoundaryRedactionTests(unittest.TestCase):
    """A report whose evidence was never scrubbed at its call site still cannot leak."""

    def result_with_nested_evidence(self):
        from pr_prover.loop import NEEDS_KARAN, RunResult

        return RunResult(
            outcome=NEEDS_KARAN,
            reason="lock-contention",
            head=HEAD_A,
            branch="feat/example",
            events=(f"fail-closed: could not authenticate with {GH_TOKEN}",),
            retained_paths=(f"/tmp/pr-prover-{FINE_GRAINED_PAT}",),
            evidence={
                "reason": "lock-contention",
                "message": "another run holds the lockfile",
                "evidence": {
                    "lock_file": "/tmp/run.lock",
                    "existing_lock": {"raw": f"owner token {GH_TOKEN}"},
                    "attempts": 2,
                    "argv": ["git", "push", URL_WITH_CREDENTIALS],
                    "keys": [PRIVATE_KEY, {"pat": FINE_GRAINED_PAT}],
                },
            },
        )

    def test_the_json_report_carries_no_nested_secret(self) -> None:
        from pr_prover import report

        rendered = report.to_json(self.result_with_nested_evidence())
        for secret in SECRETS:
            with self.subTest(secret=secret[:12]):
                self.assertNotIn(secret, rendered)

    def test_the_markdown_report_carries_no_nested_secret(self) -> None:
        from pr_prover import report

        rendered = report.to_markdown(self.result_with_nested_evidence())
        for secret in SECRETS:
            with self.subTest(secret=secret[:12]):
                self.assertNotIn(secret, rendered)

    def test_the_report_keeps_its_useful_structure(self) -> None:
        """Redaction must not flatten the evidence into one opaque string."""
        from pr_prover import report

        payload = json.loads(report.to_json(self.result_with_nested_evidence()))
        evidence = payload["fail_closed"]["evidence"]
        self.assertEqual(evidence["lock_file"], "/tmp/run.lock")
        self.assertEqual(evidence["attempts"], 2)
        self.assertIsInstance(evidence["argv"], list)
        self.assertEqual(evidence["argv"][:2], ["git", "push"])
        self.assertIsInstance(evidence["existing_lock"], dict)
        self.assertIsInstance(evidence["keys"][1], dict)

    def test_markdown_renders_a_nested_evidence_value_as_json_not_python_repr(self) -> None:
        from pr_prover import report

        rendered = report.to_markdown(self.result_with_nested_evidence())
        self.assertIn('- argv: ["git", "push"', rendered)
        self.assertIn("- attempts: 2", rendered)


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-config-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.clone = make_source_repo(self.tmp)

    def payload(self, **overrides: object) -> dict:
        body: dict = {
            "schema_version": 1,
            "repo": "example/repo",
            "pr": 7,
            "source_repo": str(self.clone),
            "worktree_root": "worktrees",
            "state_file": "state.json",
            "lock_file": "run.lock",
            "gates": [{"name": "tests", "argv": ["make", "test"]}],
            "reviewers": [
                {"name": "A", "argv": ["reviewer-a", "{head}"]},
                {"name": "B", "argv": ["reviewer-b", "{head}"]},
            ],
            "builder": {
                "argv": ["builder", "{blockers_file}"],
                "signature": "Fixed by: Claude Code",
                "comment_author": BUILDER_LOGIN,
            },
        }
        body.update(overrides)
        return body

    def load(self, **overrides: object) -> RunConfig:
        return RunConfig.from_mapping(self.payload(**overrides), base_dir=self.tmp)

    def test_a_valid_config_resolves_relative_paths(self) -> None:
        config = self.load()
        self.assertEqual(config.state_file, self.tmp / "state.json")
        self.assertEqual(config.owner, "example")
        self.assertEqual(config.name, "repo")

    def test_an_unknown_key_fails_closed(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(telegram_grammar={"approve": "yes"})
        self.assertEqual(caught.exception.evidence["unknown_keys"], ["telegram_grammar"])

    def test_a_shell_string_command_fails_closed(self) -> None:
        with self.assertRaises(CommandContractError) as caught:
            self.load(gates=[{"name": "tests", "argv": "make test && deploy"}])
        self.assertEqual(caught.exception.reason, "invalid-command")

    def test_one_reviewer_lane_is_not_enough(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(reviewers=[{"name": "A", "argv": ["reviewer-a"]}])

    def test_duplicate_lane_names_fail_closed(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(
                reviewers=[{"name": "A", "argv": ["a"]}, {"name": "A", "argv": ["b"]}]
            )

    def test_required_visual_qa_without_a_visual_gate_fails_closed(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(visual_qa_required=True)
        self.assertIn("visual", caught.exception.message)

    def test_a_visual_gate_is_recognised(self) -> None:
        config = self.load(
            visual_qa_required=True,
            gates=[{"name": "shots", "kind": "visual", "argv": ["shoot", "{head}"]}],
        )
        self.assertEqual([gate.name for gate in config.visual_gates], ["shots"])

    def test_an_unusable_repo_slug_fails_closed(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(repo="not-a-slug")

    def test_a_weak_builder_signature_fails_closed(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(
                builder={
                    "argv": ["builder"],
                    "signature": "ok",
                    "comment_author": BUILDER_LOGIN,
                }
            )

    def test_a_missing_builder_comment_author_fails_closed(self) -> None:
        """REVIEW-A-P1-002: there is no 'any author will do' configuration."""
        with self.assertRaises(ConfigError) as caught:
            self.load(builder={"argv": ["builder"], "signature": "Fixed by: Claude Code"})
        self.assertIn("comment_author", caught.exception.message)

    def test_a_null_builder_comment_author_fails_closed(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(
                builder={
                    "argv": ["builder"],
                    "signature": "Fixed by: Claude Code",
                    "comment_author": None,
                }
            )

    def test_an_unusable_builder_comment_author_fails_closed(self) -> None:
        for author in ("", "not a login", "-leading-hyphen", "trailing-", "a" * 40):
            with self.subTest(author=author):
                with self.assertRaises(ConfigError):
                    self.load(
                        builder={
                            "argv": ["builder"],
                            "signature": "Fixed by: Claude Code",
                            "comment_author": author,
                        }
                    )

    def test_a_bot_login_is_accepted_as_the_builder_comment_author(self) -> None:
        config = self.load(
            builder={
                "argv": ["builder"],
                "signature": "Fixed by: Claude Code",
                "comment_author": "hermes-builder[bot]",
            }
        )
        self.assertEqual(config.builder.comment_author, "hermes-builder[bot]")

    def test_the_shipped_example_config_is_valid(self) -> None:
        """The example is documentation; it must not model a rejected shape."""
        example = Path(__file__).resolve().parents[1] / "examples" / "run.example.json"
        payload = json.loads(example.read_text(encoding="utf-8"))
        payload["source_repo"] = str(self.clone)
        self.assertEqual(
            RunConfig.from_mapping(payload, base_dir=self.tmp).builder.comment_author,
            "the-builder-login",
        )


class CliTests(unittest.TestCase):
    def cli(self, argv: list[str]) -> int:
        """Run the CLI with its reporting muted so test output stays readable."""
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return cli.main(argv)

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-cli-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.clone = make_source_repo(self.tmp)
        self.config_path = self.tmp / "run.json"
        self.config_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "repo": "example/repo",
                    "pr": 7,
                    "source_repo": str(self.clone),
                    "worktree_root": str(self.tmp / "worktrees"),
                    "state_file": str(self.tmp / "state.json"),
                    "lock_file": str(self.tmp / "run.lock"),
                    "gates": [],
                    "reviewers": [
                        {"name": "A", "argv": ["reviewer-a", "{head}"]},
                        {"name": "B", "argv": ["reviewer-b", "{head}"]},
                    ],
                    "builder": {
                "argv": ["builder", "{blockers_file}"],
                "signature": "Fixed by: Claude Code",
                "comment_author": BUILDER_LOGIN,
            },
                }
            ),
            encoding="utf-8",
        )

    def test_check_config_accepts_a_valid_config(self) -> None:
        self.assertEqual(self.cli(["check-config", "--config", str(self.config_path)]), 0)

    def test_check_config_rejects_a_bad_config(self) -> None:
        bad = self.tmp / "bad.json"
        bad.write_text('{"schema_version": 1}', encoding="utf-8")
        self.assertEqual(self.cli(["check-config", "--config", str(bad)]), cli.USAGE_ERROR)

    def test_reset_removes_the_state_file(self) -> None:
        state = self.tmp / "state.json"
        state.write_text("{}", encoding="utf-8")
        self.assertEqual(self.cli(["reset", "--config", str(self.config_path)]), 0)
        self.assertFalse(state.exists())

    def test_reset_refuses_a_held_lock_without_force(self) -> None:
        lock = self.tmp / "run.lock"
        lock.write_text("held\n", encoding="utf-8")
        self.assertEqual(self.cli(["reset", "--config", str(self.config_path)]), cli.USAGE_ERROR)
        self.assertTrue(lock.exists())

    def test_reset_force_removes_the_lock(self) -> None:
        lock = self.tmp / "run.lock"
        lock.write_text("held\n", encoding="utf-8")
        self.assertEqual(self.cli(["reset", "--config", str(self.config_path), "--force"]), 0)
        self.assertFalse(lock.exists())

    def test_a_missing_config_is_a_usage_error(self) -> None:
        self.assertEqual(
            self.cli(["run", "--config", str(self.tmp / "absent.json")]), cli.USAGE_ERROR
        )


class ReportTests(unittest.TestCase):
    def build_result(self):
        from pr_prover.loop import MERGE_READY, RunResult

        return RunResult(
            outcome=MERGE_READY,
            reason="no-blocking-findings",
            head=HEAD_A,
            branch="feat/example",
            attempts_used=1,
            classification=classify([finding("a", "non-blocking")]),
            events=("inspected", "outcome merge-ready"),
        )

    def test_json_report_is_machine_readable(self) -> None:
        from pr_prover import report

        payload = json.loads(report.to_json(self.build_result()))
        self.assertEqual(payload["outcome"], "merge-ready")
        self.assertEqual(payload["head"], HEAD_A)
        self.assertEqual(payload["attempt_cap"], 2)
        self.assertEqual(len(payload["classification"]["non-blocking"]), 1)

    def test_markdown_report_states_the_head_and_attempts(self) -> None:
        from pr_prover import report

        text = report.to_markdown(self.build_result())
        self.assertIn("pr-prover — merge-ready", text)
        self.assertIn(HEAD_A, text)
        self.assertIn("**Attempts used:** 1/2", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
