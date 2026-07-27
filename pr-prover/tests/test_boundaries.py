"""Classification, the GitHub boundary, redaction, config, and the CLI."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from _support import BUILDER_LOGIN, HEAD_A, make_finding, make_source_repo
from pr_prover import cli, redaction
from pr_prover.commands import CommandResult
from pr_prover.config import _V1_UPGRADE_STEPS as V1_UPGRADE_STEPS
from pr_prover.config import MAX_GOVERNING_ISSUES, SCHEMA_VERSION, RunConfig
from pr_prover.errors import CommandContractError, ConfigError, GitHubError, StateError
from pr_prover.findings import Finding, classify
from pr_prover.github import _PR_FIELDS, GhCliGitHub


def finding(identifier: str, severity: str = "blocking", source: str = "reviewer:A") -> Finding:
    return make_finding(identifier, severity, source)


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
            finding("a", "critical")


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
            "body": "the change's own stated contract",
        }
        body.update(overrides)
        return json.dumps(body)

    def test_a_well_formed_payload_is_bound(self) -> None:
        pull = self.boundary(self.payload()).pull_request("example/repo", 7)
        self.assertEqual(pull.head_ref_oid, HEAD_A)
        self.assertTrue(pull.is_draft)
        self.assertEqual(pull.body, "the change's own stated contract")

    def test_the_pr_body_is_read_because_the_reviewer_cannot_read_it(self) -> None:
        """The body is the contract a reviewer checks stale claims against.

        A relayed lane has no credential and no second chance at this text, so
        an absent or null field is a read that did not deliver it — not a PR
        that has nothing to say about itself.
        """
        self.assertIn("body", _PR_FIELDS.split(","))
        empty = self.boundary(self.payload(body="")).pull_request("example/repo", 7)
        self.assertEqual(empty.body, "")
        for label, value in (("missing", None), ("null", None), ("not text", 12)):
            with self.subTest(body=label):
                body = json.loads(self.payload())
                if label == "missing":
                    del body["body"]
                else:
                    body["body"] = value
                with self.assertRaises(GitHubError) as caught:
                    self.boundary(json.dumps(body)).pull_request("example/repo", 7)
                self.assertIn("missing its body", caught.exception.message)

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

    def test_the_commit_list_is_bound_to_full_shas_in_order(self) -> None:
        """PAPI88-LOCAL-HEAD: the commit list is one of the views a push must match."""
        payload = json.dumps({"commits": [{"oid": HEAD_A.upper()}, {"oid": "b" * 40}]})
        self.assertEqual(
            self.boundary(payload).commits("example/repo", 7), (HEAD_A, "b" * 40)
        )

    def test_a_short_commit_oid_fails_closed(self) -> None:
        payload = json.dumps({"commits": [{"oid": "abc1234"}]})
        with self.assertRaises(GitHubError):
            self.boundary(payload).commits("example/repo", 7)

    def test_an_empty_commit_list_fails_closed(self) -> None:
        with self.assertRaises(GitHubError):
            self.boundary(json.dumps({"commits": []})).commits("example/repo", 7)


class GhReviewEvidenceTests(unittest.TestCase):
    """The surfaces read only so a credential-free lane can be handed them.

    A reviewer that cannot reach GitHub reads whatever this returns and nothing
    else, so a first page silently presented as a whole surface is not a cosmetic
    problem: it is a reviewer concluding there is no feedback because it was
    handed none.
    """

    INLINE = [
        {
            "id": 11,
            "user": {"login": "karanagent1"},
            "body": "this line",
            "path": "src/thing.py",
            "line": 12,
            "commit_id": HEAD_A.upper(),
            "html_url": "https://example.invalid/c/11",
        }
    ]
    CHECKS = {
        "total_count": 1,
        "check_runs": [
            {"name": "tests", "status": "completed", "conclusion": "success"}
        ],
    }
    ISSUES = {
        "closingIssuesReferences": [
            {"number": 1, "title": "mission", "state": "OPEN", "url": "https://example.invalid/1"}
        ]
    }
    GOVERNING = {
        "number": 1,
        "title": "mission contract",
        "state": "OPEN",
        "url": "https://example.invalid/issues/1",
        "body": "ACCEPTANCE: the contract this change is measured against",
    }

    def boundary(self, *, inline=None, checks=None, issues=None, governing=None) -> GhCliGitHub:
        """A runner that answers each of the four reads with its own payload."""
        pages = {
            "comments?": json.dumps([self.INLINE if inline is None else inline]),
            "check-runs?": json.dumps([self.CHECKS if checks is None else checks]),
            "closingIssuesReferences": json.dumps(self.ISSUES if issues is None else issues),
            "gh issue view": json.dumps(self.GOVERNING if governing is None else governing),
        }
        self.seen: list[tuple[str, ...]] = []

        class Scripted:
            def run(inner, argv, *, cwd=None, env=None, timeout=None):
                self.seen.append(tuple(argv))
                joined = " ".join(argv)
                for marker, payload in pages.items():
                    if marker in joined:
                        return CommandResult(
                            argv=tuple(argv), returncode=0, stdout=payload, stderr=""
                        )
                raise AssertionError(f"unexpected gh call: {list(argv)}")

        return GhCliGitHub(Scripted())

    def read(self, boundary: GhCliGitHub, *, governing_issues=(1,)):
        return boundary.review_evidence("example/repo", 7, HEAD_A, governing_issues)

    def test_the_four_surfaces_are_read_and_carried(self) -> None:
        evidence = self.read(self.boundary())

        self.assertEqual(evidence.inline_comments[0].identifier, "inline:11")
        self.assertEqual(evidence.inline_comments[0].path, "src/thing.py")
        self.assertEqual(evidence.inline_comments[0].line, 12)
        # Lower-cased like every other head binding this tool compares.
        self.assertEqual(evidence.inline_comments[0].commit_id, HEAD_A)
        self.assertEqual(evidence.check_runs[0].conclusion, "success")
        self.assertEqual(evidence.linked_issues[0].number, 1)
        self.assertEqual(evidence.governing_issues[0].number, 1)
        self.assertIn("ACCEPTANCE", evidence.governing_issues[0].body)

    def test_the_governing_issue_is_asked_for_by_configured_number(self) -> None:
        """Authority comes from the run config, never from the PR's own prose."""
        self.read(self.boundary(), governing_issues=(1,))
        issue_reads = [argv for argv in self.seen if argv[1:3] == ("issue", "view")]
        self.assertEqual(len(issue_reads), 1)
        self.assertEqual(issue_reads[0][:6], ("gh", "issue", "view", "1", "--repo", "example/repo"))
        self.assertIn("body", issue_reads[0][-1].split(","))

    def test_a_governing_issue_without_a_body_fails_closed(self) -> None:
        """A contract read that delivered no contract is not a thin issue."""
        for label, payload in (
            ("no body", {"number": 1, "title": "x", "state": "OPEN"}),
            ("null body", {"number": 1, "body": None}),
            ("another issue", {"number": 2, "body": "wrong contract"}),
        ):
            with self.subTest(payload=label):
                with self.assertRaises(GitHubError):
                    self.read(self.boundary(governing=payload))

    def test_each_read_that_can_prove_completeness_claims_it(self) -> None:
        evidence = self.read(self.boundary())

        self.assertTrue(evidence.inline_comments_complete)
        self.assertTrue(evidence.check_runs_complete)
        self.assertTrue(evidence.linked_issues_complete)
        self.assertTrue(evidence.governing_issues_complete)
        self.assertTrue(evidence.reviews_complete)
        # ...and the one that cannot does not. M5 is owed by PAPI-97.
        self.assertFalse(evidence.conversation_comments_complete)

    def test_no_configured_governing_issue_is_not_a_complete_contract(self) -> None:
        """Config refuses this, and the boundary does not paper over it either."""
        evidence = self.read(self.boundary(), governing_issues=())
        self.assertEqual(evidence.governing_issues, ())
        self.assertFalse(evidence.governing_issues_complete)

    def test_the_paginated_reads_ask_gh_to_paginate(self) -> None:
        self.read(self.boundary())
        paginated = [argv for argv in self.seen if "--paginate" in argv]
        self.assertEqual(len(paginated), 2)
        for argv in paginated:
            self.assertIn("--slurp", argv)
        self.assertTrue(any(HEAD_A in part for argv in paginated for part in argv))

    def test_fewer_check_runs_than_github_counted_is_not_complete(self) -> None:
        """The one surface that states its own total, held to it."""
        evidence = self.read(
            self.boundary(checks={"total_count": 3, "check_runs": self.CHECKS["check_runs"]})
        )
        self.assertEqual(len(evidence.check_runs), 1)
        self.assertFalse(evidence.check_runs_complete)

    def test_a_head_with_no_checks_is_complete_rather_than_unknown(self) -> None:
        evidence = self.read(self.boundary(checks={"total_count": 0, "check_runs": []}))
        self.assertEqual(evidence.check_runs, ())
        self.assertTrue(evidence.check_runs_complete)

    def test_a_full_page_of_closing_issues_cannot_claim_completeness(self) -> None:
        """A full page and a truncated one are the same response."""
        issues = {
            "closingIssuesReferences": [
                {"number": index + 1, "title": "x", "state": "OPEN"} for index in range(100)
            ]
        }
        evidence = self.read(self.boundary(issues=issues))
        self.assertEqual(len(evidence.linked_issues), 100)
        self.assertFalse(evidence.linked_issues_complete)

    def test_a_pr_that_closes_nothing_says_so_with_an_empty_array(self) -> None:
        """Present-and-empty is a fact; absent is a read that did not happen.

        This PR's own ``Refs #1`` closes nothing, so the empty array is the
        ordinary shipped answer — and it must stay distinguishable from a
        response that never carried the requested field at all.
        """
        evidence = self.read(self.boundary(issues={"closingIssuesReferences": []}))
        self.assertEqual(evidence.linked_issues, ())
        self.assertTrue(evidence.linked_issues_complete)

    def test_absent_or_null_closing_references_are_not_a_complete_empty_read(self) -> None:
        """Former red: both used to arrive as an empty, *complete* surface."""
        for label, issues in (("absent", {}), ("null", {"closingIssuesReferences": None})):
            with self.subTest(payload=label):
                with self.assertRaises(GitHubError) as caught:
                    self.read(self.boundary(issues=issues))
                self.assertIn("closingIssuesReferences", caught.exception.message)

    def test_an_unusable_payload_fails_closed_rather_than_reading_as_empty(self) -> None:
        for label, kwargs in (
            ("inline comment with no author", {"inline": [{"id": 1, "body": "x"}]}),
            ("inline comment with no id", {"inline": [{"user": {"login": "a"}, "body": "x"}]}),
            ("check-run page that is not an object", {"checks": ["nope"]}),
            ("check-run page with no check_runs", {"checks": {"total_count": 0}}),
            ("closing reference with no number", {"issues": {"closingIssuesReferences": [{}]}}),
            ("closing references that are not an array", {"issues": {"closingIssuesReferences": 3}}),
        ):
            with self.subTest(payload=label):
                with self.assertRaises(GitHubError):
                    self.read(self.boundary(**kwargs))


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
            "schema_version": SCHEMA_VERSION,
            "repo": "example/repo",
            "pr": 7,
            "governing_issues": [1],
            "source_repo": str(self.clone),
            "worktree_root": "worktrees",
            "state_file": "state.json",
            "lock_file": "run.lock",
            "gates": [{"name": "tests", "argv": ["make", "test"]}],
            "reviewers": [
                self.reviewer("A", "reviewer-a"),
                self.reviewer("B", "reviewer-b"),
                self.reviewer("Auditor", "integration-auditor"),
            ],
            "builder": {
                "argv": ["builder", "{blockers_file}"],
                "signature": "Fixed by: Claude Code",
                "comment_author": BUILDER_LOGIN,
            },
        }
        body.update(overrides)
        return body

    @staticmethod
    def reviewer(name: str, role: str, **overrides: object) -> dict:
        """One self-publishing reviewer lane, which is the smallest valid shape."""
        lane: dict = {
            "name": name,
            "role": role,
            "argv": [f"reviewer-{name.lower()}", "{head}", "{role}"],
            "artifact_author": "the-reviewer-login",
            "artifact_signature": "Reviewed by: CodexReviewer",
        }
        lane.update(overrides)
        return lane

    def load(self, **overrides: object) -> RunConfig:
        return RunConfig.from_mapping(self.payload(**overrides), base_dir=self.tmp)

    def test_a_valid_config_resolves_relative_paths(self) -> None:
        config = self.load()
        self.assertEqual(config.state_file, self.tmp / "state.json")
        self.assertEqual(config.owner, "example")
        self.assertEqual(config.name, "repo")

    # -- the versioned break --------------------------------------------------
    def test_the_shipped_schema_version_is_two(self) -> None:
        """PAPI90-B-P1-003: the discriminator names the shape it describes.

        This head made the old shape invalid — reviewers gained a required role,
        artifact author, and artifact signature, and the lifecycle became three
        exact ordered roles — while still accepting only version 1. One number
        cannot truthfully denote two incompatible files.
        """
        self.assertEqual(SCHEMA_VERSION, 2)
        self.assertEqual(self.load().source, None)

    def test_a_schema_v1_config_is_refused_with_the_upgrade_steps(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(schema_version=1)

        error = caught.exception
        self.assertEqual(error.reason, "invalid-config")
        self.assertEqual(error.evidence["found"], 1)
        self.assertEqual(error.evidence["expected"], 2)
        self.assertEqual(error.evidence["upgrade"], list(V1_UPGRADE_STEPS))
        self.assertIn("schema_version 1 is no longer supported", error.message)
        self.assertIn("set 'schema_version' to 2", error.message)

    def test_the_v1_refusal_is_deterministic(self) -> None:
        """Same input, same words: this text is read by a builder, not a human."""
        messages = set()
        for _ in range(3):
            with self.assertRaises(ConfigError) as caught:
                self.load(schema_version=1)
            messages.add(json.dumps(caught.exception.as_dict(), sort_keys=True))
        self.assertEqual(len(messages), 1)

    def test_an_unknown_future_version_gets_the_generic_refusal(self) -> None:
        for version in (0, 3, "2", None, True):
            with self.subTest(version=version):
                with self.assertRaises(ConfigError) as caught:
                    self.load(schema_version=version)
                self.assertEqual(caught.exception.reason, "invalid-config")
                self.assertNotIn("upgrade", caught.exception.evidence)

    def test_the_shipped_example_declares_the_supported_version(self) -> None:
        example = Path(__file__).resolve().parents[1] / "examples" / "run.example.json"
        payload = json.loads(example.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)

    def test_the_state_journal_version_is_independent_of_the_config_one(self) -> None:
        """Bumping one must not be read as bumping the other."""
        from pr_prover.state import SCHEMA_VERSION as STATE_SCHEMA_VERSION

        self.assertEqual(STATE_SCHEMA_VERSION, 4)
        self.assertNotEqual(STATE_SCHEMA_VERSION, SCHEMA_VERSION)

    # -- every configured path field, over the whole range of bad values ----
    PATH_FIELDS = ("source_repo", "worktree_root", "state_file", "lock_file")

    def test_a_nul_containing_path_is_a_structured_config_error(self) -> None:
        """RA-P1-003: valid JSON that ``Path.resolve`` refuses is still config.

        ``"bad\\u0000path"`` parses as JSON and reaches ``Path.resolve``, which
        raises a bare ``ValueError`` the CLI does not catch. Every path field is
        checked, because one translated field would only move the traceback.
        """
        for key in self.PATH_FIELDS:
            with self.subTest(field=key):
                with self.assertRaises(ConfigError) as caught:
                    self.load(**{key: "bad\x00path"})
                self.assertEqual(caught.exception.reason, "invalid-config")
                self.assertEqual(caught.exception.evidence, {"key": key})
                self.assertIn(key, caught.exception.message)

    def test_a_rejected_path_is_never_echoed_back(self) -> None:
        """The value is operator text; the field name is what needs fixing."""
        hostile = "/tmp/ghp_0123456789abcdefghijABCDEFGHIJ0123\x00/x"
        for key in self.PATH_FIELDS:
            with self.subTest(field=key):
                with self.assertRaises(ConfigError) as caught:
                    self.load(**{key: hostile})
                rendered = json.dumps(caught.exception.as_dict())
                self.assertNotIn("ghp_", rendered)
                self.assertNotIn("\\u0000", rendered)

    def test_every_other_unusable_path_value_is_the_same_structured_stop(self) -> None:
        for key in self.PATH_FIELDS:
            for label, value in (
                ("missing", None),
                ("empty", ""),
                ("wrong type", 7),
                ("a list", ["/tmp"]),
                ("null", None),
            ):
                with self.subTest(field=key, value=label):
                    with self.assertRaises(ConfigError) as caught:
                        self.load(**{key: value})
                    self.assertEqual(caught.exception.reason, "invalid-config")
                    self.assertIn(key, caught.exception.message)

    # -- the task contract ----------------------------------------------------
    def test_the_governing_issues_are_configured_not_parsed_from_the_pr(self) -> None:
        """Which contract a change is measured against is Hermes's call.

        A PR body is untrusted prose — this repository's own PAPI-90 PR says
        ``Refs #1`` and closes nothing — so the reviewer's contract arrives by
        number from this file and cannot be moved by what the PR claims.
        """
        self.assertEqual(self.load().governing_issues, (1,))
        self.assertEqual(self.load(governing_issues=[1, 84]).governing_issues, (1, 84))

    def test_a_run_with_no_governing_issue_fails_closed(self) -> None:
        for label, value in (
            ("null", None),
            ("empty", []),
            ("a bare number", 1),
            ("a string", "1"),
        ):
            with self.subTest(governing_issues=label):
                with self.assertRaises(ConfigError) as caught:
                    self.load(governing_issues=value)
                self.assertIn("governing_issues", caught.exception.message)

    def test_an_unusable_governing_issue_number_fails_closed(self) -> None:
        for label, value in (
            ("a boolean", [True]),
            ("zero", [0]),
            ("negative", [-3]),
            ("text", ["1"]),
            ("a float", [1.5]),
        ):
            with self.subTest(governing_issues=label):
                with self.assertRaises(ConfigError):
                    self.load(governing_issues=value)

    def test_a_repeated_or_unbounded_governing_issue_list_fails_closed(self) -> None:
        with self.assertRaises(ConfigError) as repeated:
            self.load(governing_issues=[1, 1])
        self.assertIn("same issue twice", repeated.exception.message)
        with self.assertRaises(ConfigError) as many:
            self.load(governing_issues=list(range(1, MAX_GOVERNING_ISSUES + 2)))
        self.assertEqual(many.exception.evidence["limit"], MAX_GOVERNING_ISSUES)

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
            self.load(reviewers=[self.reviewer("A", "reviewer-a")])

    def test_duplicate_lane_names_fail_closed(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(
                reviewers=[
                    self.reviewer("A", "reviewer-a"),
                    self.reviewer("A", "reviewer-b"),
                    self.reviewer("Auditor", "integration-auditor"),
                ]
            )

    def test_the_acceptance_lifecycle_must_be_the_three_required_roles_in_order(self) -> None:
        """The auditor reconciles two artifacts, so it cannot be missing or first."""
        for roles in (
            ("reviewer-a", "reviewer-b"),
            ("integration-auditor", "reviewer-a", "reviewer-b"),
            ("reviewer-b", "reviewer-a", "integration-auditor"),
            ("reviewer-a", "reviewer-b", "reviewer-c"),
        ):
            with self.subTest(roles=roles):
                with self.assertRaises(ConfigError) as caught:
                    self.load(
                        reviewers=[
                            self.reviewer(f"L{index}", role)
                            for index, role in enumerate(roles)
                        ]
                    )
                self.assertEqual(
                    caught.exception.evidence["required_roles"],
                    ["reviewer-a", "reviewer-b", "integration-auditor"],
                )

    def test_two_lanes_sharing_a_role_fail_closed(self) -> None:
        """Either lane could satisfy the other's readback, which ends independence."""
        with self.assertRaises(ConfigError):
            self.load(
                reviewers=[
                    self.reviewer("A", "reviewer-a"),
                    self.reviewer("B", "reviewer-a"),
                    self.reviewer("Auditor", "integration-auditor"),
                ]
            )

    def test_a_reviewer_without_a_pinned_artifact_author_fails_closed(self) -> None:
        lane = self.reviewer("A", "reviewer-a")
        del lane["artifact_author"]
        with self.assertRaises(ConfigError) as caught:
            self.load(
                reviewers=[
                    lane,
                    self.reviewer("B", "reviewer-b"),
                    self.reviewer("Auditor", "integration-auditor"),
                ]
            )
        self.assertIn("artifact_author", caught.exception.message)

    def test_a_relay_lane_must_receive_the_artifact_file_on_both_sides(self) -> None:
        """Neither half of the handoff can be left holding nothing."""
        no_write = self.reviewer(
            "A",
            "reviewer-a",
            relay={"argv": ["gh", "pr", "comment", "--body-file", "{artifact_file}"]},
        )
        with self.assertRaises(ConfigError) as caught:
            self.load(
                reviewers=[
                    no_write,
                    self.reviewer("B", "reviewer-b"),
                    self.reviewer("Auditor", "integration-auditor"),
                ]
            )
        self.assertIn("nowhere to prepare", caught.exception.message)

        no_post = self.reviewer(
            "A",
            "reviewer-a",
            argv=["reviewer-a", "{head}", "--artifact-file", "{artifact_file}"],
            relay={"argv": ["gh", "pr", "comment"]},
        )
        with self.assertRaises(ConfigError) as caught:
            self.load(
                reviewers=[
                    no_post,
                    self.reviewer("B", "reviewer-b"),
                    self.reviewer("Auditor", "integration-auditor"),
                ]
            )
        self.assertIn("no prepared artifact to publish", caught.exception.message)

    def test_a_relayed_lane_may_not_be_handed_a_github_credential(self) -> None:
        """The relay publishes; naming a token for the judging lane contradicts that."""
        lane = self.reviewer(
            "A",
            "reviewer-a",
            argv=["reviewer-a", "{head}", "--artifact-file", "{artifact_file}"],
            relay={"argv": ["gh", "pr", "comment", "--body-file", "{artifact_file}"]},
            env={"GH_TOKEN": "provided-elsewhere"},
        )
        with self.assertRaises(ConfigError) as caught:
            self.load(
                reviewers=[
                    lane,
                    self.reviewer("B", "reviewer-b"),
                    self.reviewer("Auditor", "integration-auditor"),
                ]
            )
        self.assertIn("without a GitHub credential", caught.exception.message)

    def test_a_lane_may_not_retarget_the_session_the_agents_authenticate_through(
        self,
    ) -> None:
        """No synthetic HOME: the trusted lanes need the real OAuth/keychain session."""
        for variable in ("HOME", "USER", "LOGNAME", "SHELL"):
            with self.subTest(variable=variable):
                with self.assertRaises(ConfigError) as caught:
                    self.load(
                        builder={
                            "argv": ["builder", "{blockers_file}"],
                            "signature": "Fixed by: Claude Code",
                            "comment_author": BUILDER_LOGIN,
                            "env": {variable: "/tmp/synthetic"},
                        }
                    )
                self.assertIn(variable, caught.exception.message)
                with self.assertRaises(ConfigError):
                    self.load(
                        builder={
                            "argv": ["builder", "{blockers_file}"],
                            "signature": "Fixed by: Claude Code",
                            "comment_author": BUILDER_LOGIN,
                            "env_unset": [variable],
                        }
                    )

    def test_a_credential_shaped_env_value_fails_closed(self) -> None:
        """Tokens live in the keychain and in gh's auth, not in run evidence."""
        with self.assertRaises(ConfigError) as caught:
            self.load(
                builder={
                    "argv": ["builder", "{blockers_file}"],
                    "signature": "Fixed by: Claude Code",
                    "comment_author": BUILDER_LOGIN,
                    "env": {"SOME_TOKEN": "ghp_examplevaluethatlookslikeacredential"},
                }
            )
        self.assertIn("credential", caught.exception.message)

    def test_an_unbounded_or_unrealistic_budget_is_advised_not_refused(self) -> None:
        """Advisories are notes: a repo with a two-minute suite may know better."""
        config = self.load(
            builder={
                "argv": ["builder", "{blockers_file}"],
                "signature": "Fixed by: Claude Code",
                "comment_author": BUILDER_LOGIN,
                "timeout": 60,
            }
        )
        notes = " ".join(config.advisories())
        self.assertIn("builder timeout is 60s", notes)
        self.assertIn("has no timeout", notes)

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

    def test_a_state_file_inside_the_operational_clone_fails_closed(self) -> None:
        """PAPI88-CONTROL-PATHS: the run must not write inside the clone it judges."""
        with self.assertRaises(ConfigError) as caught:
            self.load(state_file=str(self.clone / ".pr-prover-state"))
        self.assertIn("state_file", caught.exception.message)
        self.assertEqual(caught.exception.evidence["source_repo"], str(self.clone))

    def test_a_lock_file_inside_the_operational_clone_fails_closed(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(lock_file=str(self.clone / "control" / "run.lock"))
        self.assertIn("lock_file", caught.exception.message)

    def test_a_control_file_equal_to_the_operational_clone_fails_closed(self) -> None:
        for key in ("state_file", "lock_file"):
            with self.subTest(key=key):
                with self.assertRaises(ConfigError):
                    self.load(**{key: str(self.clone)})

    def test_a_control_file_reaching_into_the_clone_by_relative_path_fails_closed(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(state_file="clone/nested/state.json")

    def test_control_files_outside_the_operational_clone_are_accepted(self) -> None:
        """Sibling and outside paths are exactly what the rule is protecting."""
        config = self.load(
            state_file=str(self.tmp / "control" / "state.json"),
            lock_file=str(self.tmp / "run.lock"),
        )
        self.assertEqual(config.state_file, self.tmp / "control" / "state.json")
        self.assertEqual(config.lock_file, self.tmp / "run.lock")

    def test_a_control_file_beside_the_clone_with_a_shared_prefix_is_accepted(self) -> None:
        """`clone-state` is not inside `clone`, and must not be rejected as if it were."""
        config = self.load(state_file=str(self.tmp / "clone-state" / "state.json"))
        self.assertEqual(config.state_file, self.tmp / "clone-state" / "state.json")

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
                    "schema_version": SCHEMA_VERSION,
                    "repo": "example/repo",
                    "pr": 7,
                    "governing_issues": [1],
                    "source_repo": str(self.clone),
                    "worktree_root": str(self.tmp / "worktrees"),
                    "state_file": str(self.tmp / "state.json"),
                    "lock_file": str(self.tmp / "run.lock"),
                    "gates": [],
                    "reviewers": [
                        {
                            "name": name,
                            "role": role,
                            "argv": [f"reviewer-{role}", "{head}", "{role}"],
                            "artifact_author": "the-reviewer-login",
                            "artifact_signature": "Reviewed by: CodexReviewer",
                        }
                        for name, role in (
                            ("A", "reviewer-a"),
                            ("B", "reviewer-b"),
                            ("Auditor", "integration-auditor"),
                        )
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

    def test_check_config_accepts_the_shipped_example_and_names_the_lifecycle(self) -> None:
        """The repository-required gate, run against the config it is run against.

        ``pr-prover/bin/pr-prover check-config --config
        pr-prover/examples/run.example.json`` is one of the checks every change
        to this tool must pass. This drives the same entry point over the same
        file, so the gate is exercised by the suite rather than only by whoever
        remembers to type it.
        """
        example = Path(__file__).resolve().parents[1] / "examples" / "run.example.json"
        payload = json.loads(example.read_text(encoding="utf-8"))
        # The one field that cannot be checked in place: the example names an
        # absolute clone path that only exists on an operator's machine.
        payload["source_repo"] = str(self.clone)
        local = self.tmp / "example.json"
        local.write_text(json.dumps(payload), encoding="utf-8")

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(["check-config", "--config", str(local)])

        self.assertEqual(code, 0)
        printed = buffer.getvalue()
        self.assertIn("config ok:", printed)
        self.assertIn("reviewer-a, reviewer-b, integration-auditor", printed)
        # The contract the lanes will be held to is part of what was validated.
        self.assertIn("governed by #1", printed)

    def test_check_config_prints_budget_advisories_without_failing(self) -> None:
        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        payload["builder"]["timeout"] = 30
        short = self.tmp / "short.json"
        short.write_text(json.dumps(payload), encoding="utf-8")

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(["check-config", "--config", str(short)])

        self.assertEqual(code, 0, "an advisory is a note, not a rejection")
        self.assertIn("note: builder timeout is 30s", buffer.getvalue())

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

    def test_a_refused_reset_preserves_both_the_lock_and_the_state(self) -> None:
        """PAPI88-RESET-PRESERVE: the refusal must not delete the journal on its way out."""
        lock = self.tmp / "run.lock"
        state = self.tmp / "state.json"
        lock.write_text("held by an active run\n", encoding="utf-8")
        state.write_text('{"attempt": 1}', encoding="utf-8")

        self.assertEqual(self.cli(["reset", "--config", str(self.config_path)]), cli.USAGE_ERROR)

        self.assertTrue(lock.exists(), "the held lock must survive the refusal")
        self.assertTrue(state.exists(), "the active run's state must survive the refusal")
        self.assertEqual(state.read_text(encoding="utf-8"), '{"attempt": 1}')
        self.assertEqual(lock.read_text(encoding="utf-8"), "held by an active run\n")

    def test_reset_force_removes_the_lock(self) -> None:
        lock = self.tmp / "run.lock"
        lock.write_text("held\n", encoding="utf-8")
        self.assertEqual(self.cli(["reset", "--config", str(self.config_path), "--force"]), 0)
        self.assertFalse(lock.exists())

    def test_reset_force_removes_both_the_state_and_the_lock(self) -> None:
        """Forcing stays explicit: it is the only path that discards a held lock."""
        lock = self.tmp / "run.lock"
        state = self.tmp / "state.json"
        lock.write_text("stale\n", encoding="utf-8")
        state.write_text("{}", encoding="utf-8")

        self.assertEqual(self.cli(["reset", "--config", str(self.config_path), "--force"]), 0)

        self.assertFalse(lock.exists())
        self.assertFalse(state.exists())

    def test_reset_without_a_lock_still_removes_the_state(self) -> None:
        state = self.tmp / "state.json"
        state.write_text("{}", encoding="utf-8")
        self.assertEqual(self.cli(["reset", "--config", str(self.config_path)]), 0)
        self.assertFalse(state.exists())

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
