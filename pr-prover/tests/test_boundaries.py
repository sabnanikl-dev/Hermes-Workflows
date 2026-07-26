"""Classification, the GitHub boundary, redaction, config, and the CLI."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from _support import BUILDER_LOGIN, HEAD_A, REVIEWER_LOGIN, REVIEWER_SIGNATURE, make_source_repo
from pr_prover import cli, redaction
from pr_prover.commands import CommandResult
from pr_prover.config import REQUIRED_REVIEWER_ROLES, RunConfig
from pr_prover.errors import (
    CommandContractError,
    ConfigError,
    GitHubError,
    ReviewerRelayError,
    StateError,
)
from pr_prover.findings import Finding, classify
from pr_prover.github import _NESTED_PAGE_INFO, _REVIEW_THREADS_QUERY, Comment, GhCliGitHub
from pr_prover.reviewers import (
    artifact_matches,
    binds_head,
    head_binding,
    head_declarations,
    read_prepared,
)


def finding(identifier: str, severity: str = "blocking", source: str = "reviewer:A") -> Finding:
    return Finding(id=identifier, severity=severity, summary="s", source=source, head=HEAD_A)


def reviewer(name: str, *, role: str | None = None, **overrides: object) -> dict:
    """A complete reviewer lane: argv plus the identity its artifact must carry."""
    lane: dict = {
        "name": name,
        "role": role or f"reviewer-{name.lower()}",
        "argv": [f"reviewer-{name.lower()}", "{head}"],
        "artifact_author": REVIEWER_LOGIN,
        "artifact_signature": REVIEWER_SIGNATURE,
    }
    lane.update(overrides)
    return lane


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
                return CommandResult(argv=tuple(argv), returncode=0, stdout=self.payload(), stderr="")

            def payload(self) -> str:
                return json.dumps({"number": 7, "state": "OPEN", "isDraft": True, "title": "t",
                                   "url": "u", "headRefName": "b", "headRefOid": HEAD_A,
                                   "baseRefName": "main"})

        GhCliGitHub(Recorder()).pull_request("example/repo", 7)
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
            [[{"id": 123, "user": {"login": "karanagent1"}, "body": "hi", "html_url": "u"}]]
        )
        comments = self.boundary(payload).comments("example/repo", 7)
        self.assertEqual(comments[0].author, "karanagent1")
        self.assertEqual(comments[0].identifier, "123")
        self.assertEqual(comments[0].url, "u")

    def test_a_comment_without_a_stable_id_fails_closed(self) -> None:
        """Without an id there is no way to tell a comment from a copy of it."""
        payload = json.dumps([[{"user": {"login": "karanagent1"}, "body": "hi"}]])
        with self.assertRaises(GitHubError):
            self.boundary(payload).comments("example/repo", 7)

    def test_a_comment_without_an_author_fails_closed(self) -> None:
        payload = json.dumps([[{"id": 123, "body": "hi"}]])
        with self.assertRaises(GitHubError):
            self.boundary(payload).comments("example/repo", 7)

    def test_a_comment_payload_that_is_not_an_array_fails_closed(self) -> None:
        with self.assertRaises(GitHubError):
            self.boundary(json.dumps({"message": "Not Found"})).comments("example/repo", 7)

    def test_a_comment_with_an_unusable_body_fails_closed(self) -> None:
        payload = json.dumps([[{"id": 1, "user": {"login": "karanagent1"}, "body": {"x": 1}}]])
        with self.assertRaises(GitHubError):
            self.boundary(payload).comments("example/repo", 7)

    def test_reviews_carry_the_commit_they_were_submitted_against(self) -> None:
        payload = json.dumps(
            [[{"id": 42, "user": {"login": "karanagent1"}, "body": "ROLE=reviewer-a", "commit_id": HEAD_A.upper()}]]
        )
        reviews = self.boundary(payload).reviews("example/repo", 7)
        self.assertEqual(reviews[0].identifier, "review:42")
        self.assertEqual(reviews[0].kind, "review")
        self.assertEqual(reviews[0].commit_id, HEAD_A)

    def test_reviews_are_read_through_the_rest_api_across_pages(self) -> None:
        seen: list[tuple[str, ...]] = []

        class Recorder:
            def run(self, argv, *, cwd=None, env=None, timeout=None, progress=None):
                seen.append(tuple(argv))
                return CommandResult(argv=tuple(argv), returncode=0, stdout="[[], []]", stderr="")

        self.assertEqual(GhCliGitHub(Recorder()).reviews("example/repo", 7), ())
        self.assertEqual(seen[0][:4], ("gh", "api", "--paginate", "--slurp"))
        self.assertIn("repos/example/repo/pulls/7/reviews?per_page=100", seen[0])

    def test_a_bodyless_approval_is_data_not_an_error(self) -> None:
        payload = json.dumps([[{"id": 1, "user": {"login": "karanagent1"}, "state": "APPROVED"}]])
        self.assertEqual(self.boundary(payload).reviews("example/repo", 7)[0].body, "")

    def test_a_review_without_an_author_fails_closed(self) -> None:
        payload = json.dumps([[{"id": 1, "body": "ROLE=reviewer-a"}]])
        with self.assertRaises(GitHubError):
            self.boundary(payload).reviews("example/repo", 7)

    def test_a_review_payload_that_is_not_an_array_fails_closed(self) -> None:
        with self.assertRaises(GitHubError):
            self.boundary(json.dumps({"message": "Not Found"})).reviews("example/repo", 7)


def thread_node(
    identifier: str,
    *,
    authors: tuple[str, ...] = (REVIEWER_LOGIN,),
    resolved: bool = False,
    outdated: bool = False,
    has_next: object = False,
    page_info: bool = True,
    comments: bool = True,
) -> dict:
    """One ``reviewThreads`` node, with the nested completeness field the query asks for."""
    connection: dict = {
        "nodes": [
            {"id": f"{identifier}-c{index}", "url": "u", "body": "b", "author": {"login": login}}
            for index, login in enumerate(authors)
        ]
    }
    if page_info:
        connection["threadCommentsPageInfo"] = {"hasNextPage": has_next}
    node: dict = {
        "id": identifier,
        "isResolved": resolved,
        "isOutdated": outdated,
        "path": "src/example.py",
    }
    if comments:
        node["comments"] = connection
    return node


def thread_page(*nodes: dict, has_next: bool = False, end_cursor: str = "CURSOR") -> dict:
    """One slurped GraphQL page, with the top-level completeness signal it must carry."""
    page_info: dict = {"hasNextPage": has_next}
    if has_next:
        page_info["endCursor"] = end_cursor
    connection = {"pageInfo": page_info, "nodes": list(nodes)}
    return {"data": {"repository": {"pullRequest": {"reviewThreads": connection}}}}


class PaginatedFeedbackSurfaceTests(unittest.TestCase):
    """ADAPTER-SMOKE-1: neither human surface may be read as a silent slice.

    The defect these pin down: conversation comments were read with a single
    unpaginated ``gh pr view --json comments`` call, and each review thread asked
    for ``comments(first: 100)`` without ever checking whether that was all of
    them. On a long PR either read returns a slice with no indication of what it
    dropped, so a human reply outside the slice reached nothing that could block
    the run, and ``merge-ready`` was reachable over unresolved human feedback.
    """

    def boundary(self, *pages: object, returncode: int = 0) -> GhCliGitHub:
        stdout = json.dumps(list(pages))

        class OneShot:
            def run(self, argv, *, cwd=None, env=None, timeout=None, progress=None):
                return CommandResult(argv=tuple(argv), returncode=returncode, stdout=stdout, stderr="")

        return GhCliGitHub(OneShot())

    def comment(self, identifier: int, *, login: str, body: str = "b") -> dict:
        return {"id": identifier, "user": {"login": login}, "body": body, "html_url": "u"}

    # -- conversation comments ------------------------------------------------
    def test_comments_are_read_through_the_paginated_rest_endpoint(self) -> None:
        seen: list[tuple[str, ...]] = []

        class Recorder:
            def run(self, argv, *, cwd=None, env=None, timeout=None, progress=None):
                seen.append(tuple(argv))
                return CommandResult(argv=tuple(argv), returncode=0, stdout="[[], []]", stderr="")

        self.assertEqual(GhCliGitHub(Recorder()).comments("example/repo", 7), ())
        self.assertEqual(seen[0][:4], ("gh", "api", "--paginate", "--slurp"))
        self.assertIn("repos/example/repo/issues/7/comments?per_page=100", seen[0])
        self.assertNotIn("view", seen[0], "the unpaginated CLI read is gone")

    def test_a_human_comment_on_a_later_page_is_returned(self) -> None:
        """The frozen probe: old feedback lives on page two of a long PR."""
        pages = [
            [self.comment(index, login=BUILDER_LOGIN) for index in range(100)],
            [self.comment(100, login="human-reviewer", body="do not merge")],
        ]

        comments = self.boundary(*pages).comments("example/repo", 7)

        self.assertEqual(len(comments), 101)
        self.assertEqual(comments[-1].identifier, "100")
        self.assertEqual(comments[-1].author, "human-reviewer")

    def test_pages_flatten_in_a_deterministic_order(self) -> None:
        """Two reads of the same PR must agree, or id snapshots mean nothing."""
        pages = [
            [self.comment(1, login=BUILDER_LOGIN), self.comment(2, login=BUILDER_LOGIN)],
            [self.comment(3, login="human-reviewer")],
        ]

        boundary = self.boundary(*pages)
        first = [item.identifier for item in boundary.comments("example/repo", 7)]

        self.assertEqual(first, ["1", "2", "3"])
        self.assertEqual(
            first, [item.identifier for item in boundary.comments("example/repo", 7)]
        )

    def test_a_single_object_page_is_kept_rather_than_dropped(self) -> None:
        comments = self.boundary(self.comment(9, login="human-reviewer")).comments(
            "example/repo", 7
        )
        self.assertEqual([item.identifier for item in comments], ["9"])

    def test_a_string_comment_id_is_still_accepted(self) -> None:
        payload = [[{"id": "9", "user": {"login": "human-reviewer"}, "body": "b"}]]
        self.assertEqual(
            self.boundary(*payload).comments("example/repo", 7)[0].identifier, "9"
        )

    def test_a_malformed_comment_page_fails_closed(self) -> None:
        for page in ([["not an object"]], [[{"id": 1, "user": "human-reviewer"}]]):
            with self.subTest(page=page):
                with self.assertRaises(GitHubError):
                    self.boundary(*page).comments("example/repo", 7)

    # -- nested review-thread comments ---------------------------------------
    def test_the_query_asks_each_thread_whether_its_comments_are_complete(self) -> None:
        self.assertIn(f"{_NESTED_PAGE_INFO}: pageInfo", _REVIEW_THREADS_QUERY)
        self.assertEqual(
            _REVIEW_THREADS_QUERY.count("pageInfo { hasNextPage endCursor }"),
            1,
            "only the top-level connection carries the cursor gh pages on",
        )

    def test_a_complete_thread_is_read_normally(self) -> None:
        threads = self.boundary(thread_page(thread_node("T1"))).review_threads("example/repo", 7)

        self.assertEqual(len(threads), 1)
        self.assertEqual(threads[0].authors, (REVIEWER_LOGIN,))
        self.assertFalse(threads[0].is_resolved)

    def test_a_thread_with_more_comments_than_one_page_fails_closed(self) -> None:
        """The frozen probe: the returned slice is all agents, the reply is not."""
        page = thread_page(thread_node("T1", authors=(REVIEWER_LOGIN,), has_next=True))

        with self.assertRaises(GitHubError) as caught:
            self.boundary(page).review_threads("example/repo", 7)

        self.assertIn("more comments than one page holds", caught.exception.message)

    def test_an_overflowing_thread_fails_closed_even_when_resolved(self) -> None:
        """Completeness is decided at the boundary, before anything filters threads."""
        page = thread_page(thread_node("T1", resolved=True, has_next=True))

        with self.assertRaises(GitHubError):
            self.boundary(page).review_threads("example/repo", 7)

    def test_a_thread_that_does_not_report_completeness_fails_closed(self) -> None:
        page = thread_page(thread_node("T1", page_info=False))

        with self.assertRaises(GitHubError) as caught:
            self.boundary(page).review_threads("example/repo", 7)

        self.assertIn("did not report whether its comments are complete", caught.exception.message)

    def test_a_non_boolean_completeness_flag_fails_closed(self) -> None:
        for value in ("true", 1, None, {}):
            with self.subTest(value=value):
                page = thread_page(thread_node("T1", has_next=value))
                with self.assertRaises(GitHubError):
                    self.boundary(page).review_threads("example/repo", 7)

    def test_a_thread_with_no_comments_connection_fails_closed(self) -> None:
        page = thread_page(thread_node("T1", comments=False))

        with self.assertRaises(GitHubError) as caught:
            self.boundary(page).review_threads("example/repo", 7)

        self.assertIn("no comments connection", caught.exception.message)

    def test_one_overflowing_thread_fails_the_whole_read(self) -> None:
        """A partial answer is not salvageable by returning the threads that fit."""
        page = thread_page(thread_node("T1"), thread_node("T2", has_next=True))

        with self.assertRaises(GitHubError):
            self.boundary(page).review_threads("example/repo", 7)

    def test_top_level_thread_pagination_is_preserved(self) -> None:
        seen: list[tuple[str, ...]] = []
        pages = [
            thread_page(thread_node("T1"), has_next=True),
            thread_page(thread_node("T2")),
        ]
        stdout = json.dumps(pages)

        class Recorder:
            def run(self, argv, *, cwd=None, env=None, timeout=None, progress=None):
                seen.append(tuple(argv))
                return CommandResult(argv=tuple(argv), returncode=0, stdout=stdout, stderr="")

        threads = GhCliGitHub(Recorder()).review_threads("example/repo", 7)

        self.assertEqual([thread.identifier for thread in threads], ["T1", "T2"])
        self.assertEqual(seen[0][:5], ("gh", "api", "graphql", "--paginate", "--slurp"))


class TopLevelThreadCompletenessTests(unittest.TestCase):
    """REVIEW-A-2 / IA-2: an incomplete thread payload is not an empty PR.

    The defect these pin down: a null ``reviewThreads`` connection, a connection
    with no ``nodes`` member, and a final captured page still reporting
    ``hasNextPage`` were each read as "this PR has no review threads". Every one
    of those is a read that never established how many threads exist, and the
    empty tuple they produced is indistinguishable downstream from a clean PR —
    so an unresolved human thread outside the returned data could reach
    ``merge-ready``. The nested reply-completeness guard cannot help here: it
    never runs when the top-level nodes were lost.
    """

    def boundary(self, *pages: object) -> GhCliGitHub:
        stdout = json.dumps(list(pages))

        class OneShot:
            def run(self, argv, *, cwd=None, env=None, timeout=None, progress=None):
                return CommandResult(argv=tuple(argv), returncode=0, stdout=stdout, stderr="")

        return GhCliGitHub(OneShot())

    def connection(self, value: object) -> dict:
        return {"data": {"repository": {"pullRequest": {"reviewThreads": value}}}}

    def test_a_null_connection_is_not_an_empty_thread_surface(self) -> None:
        """Frozen probe ``THREAD_INCOMPLETE null_connection ACCEPTED 0``."""
        with self.assertRaises(GitHubError) as caught:
            self.boundary(self.connection(None)).review_threads("example/repo", 7)

        self.assertIn("no usable reviewThreads connection", caught.exception.message)

    def test_a_connection_without_nodes_is_not_an_empty_thread_surface(self) -> None:
        """Frozen probe ``THREAD_INCOMPLETE missing_nodes ACCEPTED 0``."""
        with self.assertRaises(GitHubError) as caught:
            self.boundary(
                self.connection({"pageInfo": {"hasNextPage": False}})
            ).review_threads("example/repo", 7)

        self.assertIn("no usable nodes array", caught.exception.message)

    def test_a_null_nodes_member_is_not_an_empty_thread_surface(self) -> None:
        with self.assertRaises(GitHubError):
            self.boundary(
                self.connection({"pageInfo": {"hasNextPage": False}, "nodes": None})
            ).review_threads("example/repo", 7)

    def test_a_final_page_that_still_reports_another_page_fails_closed(self) -> None:
        """Frozen probe ``THREAD_INCOMPLETE truncated_top_page ACCEPTED 0``."""
        with self.assertRaises(GitHubError) as caught:
            self.boundary(thread_page(has_next=True)).review_threads("example/repo", 7)

        self.assertIn("still reports another page", caught.exception.message)

    def test_a_page_promising_more_without_a_cursor_fails_closed(self) -> None:
        page = self.connection({"pageInfo": {"hasNextPage": True}, "nodes": []})

        with self.assertRaises(GitHubError) as caught:
            self.boundary(page, thread_page()).review_threads("example/repo", 7)

        self.assertIn("hands over no cursor", caught.exception.message)

    def test_a_page_sequence_that_stops_reporting_continuation_fails_closed(self) -> None:
        """``--slurp`` concatenates; it does not prove the pages are one read."""
        with self.assertRaises(GitHubError) as caught:
            self.boundary(thread_page(), thread_page()).review_threads("example/repo", 7)

        self.assertIn("not one coherent read", caught.exception.message)

    def test_a_missing_page_info_fails_closed(self) -> None:
        page = self.connection({"nodes": []})

        with self.assertRaises(GitHubError) as caught:
            self.boundary(page).review_threads("example/repo", 7)

        self.assertIn("did not report whether more threads follow", caught.exception.message)

    def test_a_non_boolean_page_flag_fails_closed(self) -> None:
        for value in ("false", 0, None, []):
            with self.subTest(value=value):
                page = self.connection({"pageInfo": {"hasNextPage": value}, "nodes": []})
                with self.assertRaises(GitHubError):
                    self.boundary(page).review_threads("example/repo", 7)

    def test_graphql_errors_are_not_a_successful_read(self) -> None:
        """Partial data with an errors array exits zero and looks like a payload."""
        page = self.connection({"pageInfo": {"hasNextPage": False}, "nodes": []})
        page["errors"] = [{"message": "Something went wrong while executing your query."}]

        with self.assertRaises(GitHubError) as caught:
            self.boundary(page).review_threads("example/repo", 7)

        self.assertIn("GraphQL errors", caught.exception.message)

    def test_a_null_repository_or_pull_request_fails_closed(self) -> None:
        for payload in (
            {"data": {"repository": None}},
            {"data": {"repository": {"pullRequest": None}}},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(GitHubError) as caught:
                    self.boundary(payload).review_threads("example/repo", 7)
                self.assertIn("reviewThreads connection", caught.exception.message)

    def test_no_pages_at_all_fails_closed(self) -> None:
        with self.assertRaises(GitHubError) as caught:
            self.boundary().review_threads("example/repo", 7)

        self.assertIn("no review-thread pages", caught.exception.message)

    def test_a_complete_empty_surface_is_still_accepted(self) -> None:
        """Fail-closed must not mean a PR with genuinely no threads cannot pass."""
        self.assertEqual(self.boundary(thread_page()).review_threads("example/repo", 7), ())


class CanonicalHeadBindingTests(unittest.TestCase):
    """REVIEW-A-4 / IA-1: a body-bound artifact declares its head, it does not mention it.

    The defect these pin down: the expected SHA legitimately appears in scope
    prose, command transcripts, and quoted history, so "the expected SHA is
    somewhere in the body" is satisfied by an artifact that says on its own line
    that it reviewed a different commit.
    """

    OTHER = "d" * 40

    def artifact(self, declared: str, *, prose: str = "") -> str:
        lead = f"Expected launch head: {prose}\n" if prose else ""
        return (
            f"Audited the diff.\n{lead}\n---\n{REVIEWER_SIGNATURE}\n"
            f"ROLE=reviewer-a\nHEAD={declared}\n"
        )

    def test_one_standalone_declaration_of_the_bound_head_is_accepted(self) -> None:
        self.assertTrue(binds_head(self.artifact(HEAD_A), head=HEAD_A))

    def test_the_expected_sha_in_prose_never_counts(self) -> None:
        """The frozen mutation: expected SHA in prose, another SHA declared."""
        body = self.artifact(self.OTHER, prose=HEAD_A)

        binding = head_binding(body, head=HEAD_A)

        self.assertIn(HEAD_A, body, "the expected SHA really is in the body")
        self.assertFalse(binding.ok)
        self.assertEqual(binding.problem, "mismatch")
        self.assertEqual(binding.declared, self.OTHER)

    def test_a_body_with_no_declaration_is_rejected(self) -> None:
        binding = head_binding(f"Reviewed {HEAD_A} carefully.\n", head=HEAD_A)
        self.assertFalse(binding.ok)
        self.assertEqual(binding.problem, "missing")

    def test_two_declarations_are_rejected_even_when_they_agree(self) -> None:
        binding = head_binding(f"HEAD={HEAD_A}\ntext\nHEAD={HEAD_A}\n", head=HEAD_A)
        self.assertFalse(binding.ok)
        self.assertEqual(binding.problem, "duplicate")
        self.assertEqual(binding.count, 2)

    def test_conflicting_declarations_are_rejected(self) -> None:
        binding = head_binding(f"HEAD={HEAD_A}\nHEAD={self.OTHER}\n", head=HEAD_A)
        self.assertFalse(binding.ok)
        self.assertEqual(binding.problem, "duplicate")

    def test_a_malformed_declaration_is_rejected(self) -> None:
        for value in ("", HEAD_A[:39], HEAD_A.upper(), f"{HEAD_A} (reviewed)", "not-a-sha"):
            with self.subTest(value=value):
                binding = head_binding(f"HEAD={value}\n", head=HEAD_A)
                self.assertFalse(binding.ok)
                self.assertIn(binding.problem, {"malformed", "missing"})

    def test_a_declaration_is_read_as_a_whole_line(self) -> None:
        """An inline mention is prose, however it is punctuated."""
        for body in (f"reviewed HEAD={HEAD_A} today\n", f"`HEAD={HEAD_A}`\n"):
            with self.subTest(body=body):
                self.assertEqual(head_declarations(body), ())

    def test_surrounding_whitespace_does_not_break_a_real_declaration(self) -> None:
        self.assertTrue(binds_head(f"  HEAD={HEAD_A}  \r\n", head=HEAD_A))

    def test_a_review_keeps_its_authoritative_commit_id_binding(self) -> None:
        """GitHub's own commit_id is stronger than anything in a body."""
        review = Comment(
            identifier="review:1",
            author=REVIEWER_LOGIN,
            body=f"Audited.\n{REVIEWER_SIGNATURE}\nROLE=reviewer-a\n",
            kind="review",
            commit_id=HEAD_A,
        )

        self.assertTrue(
            artifact_matches(
                review,
                author=REVIEWER_LOGIN,
                signature=REVIEWER_SIGNATURE,
                role="reviewer-a",
                head=HEAD_A,
            )
        )

    def test_a_comment_falls_to_the_canonical_declaration(self) -> None:
        stale = Comment(
            identifier="IC_1",
            author=REVIEWER_LOGIN,
            body=self.artifact(self.OTHER, prose=HEAD_A),
        )

        self.assertFalse(
            artifact_matches(
                stale,
                author=REVIEWER_LOGIN,
                signature=REVIEWER_SIGNATURE,
                role="reviewer-a",
                head=HEAD_A,
            )
        )

    def test_a_prepared_artifact_is_held_to_the_same_predicate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pr-prover-artifact-") as tmp:
            path = Path(tmp) / "prepared.md"
            path.write_text(self.artifact(self.OTHER, prose=HEAD_A), encoding="utf-8")

            with self.assertRaises(ReviewerRelayError) as caught:
                read_prepared(
                    path,
                    reviewer="A",
                    role="reviewer-a",
                    signature=REVIEWER_SIGNATURE,
                    head=HEAD_A,
                )

        self.assertIn("not bound to this exact head", caught.exception.message)
        self.assertEqual(caught.exception.evidence["declared_head"], self.OTHER)


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
            "reviewers": [reviewer("A"), reviewer("B"), reviewer("IA", role="integration-auditor")],
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
            self.load(reviewers=[reviewer("A")])

    def test_duplicate_lane_names_fail_closed(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(reviewers=[reviewer("A"), reviewer("A", role="reviewer-b")])

    # -- REVIEWER-B-2 / IA-4: the acceptance lifecycle is configuration ------
    #
    # The defect these pin down: configuration required only two lanes with
    # unique roles, and the loop ran whatever array order it was given. Both
    # ``check-config`` and the public loop therefore accepted a run with no
    # Integration Auditor at all, or with the auditor running before the
    # Reviewer A/B artifacts it exists to reconcile.
    def test_a_run_without_the_integration_auditor_fails_closed(self) -> None:
        """Frozen probe ``TWO_REVIEWER_CONFIG accepted=True``."""
        with self.assertRaises(ConfigError) as caught:
            self.load(reviewers=[reviewer("A"), reviewer("B")])

        self.assertEqual(
            caught.exception.evidence["configured_roles"], ["reviewer-a", "reviewer-b"]
        )
        self.assertEqual(
            caught.exception.evidence["required_roles"], list(REQUIRED_REVIEWER_ROLES)
        )

    def test_an_auditor_first_lifecycle_fails_closed(self) -> None:
        """Frozen probe ``AUDITOR_FIRST_CONFIG accepted=True``."""
        with self.assertRaises(ConfigError) as caught:
            self.load(
                reviewers=[
                    reviewer("IA", role="integration-auditor"),
                    reviewer("A"),
                    reviewer("B"),
                ]
            )

        self.assertEqual(
            caught.exception.evidence["configured_roles"],
            ["integration-auditor", "reviewer-a", "reviewer-b"],
        )

    def test_reviewer_a_and_b_out_of_order_fails_closed(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(
                reviewers=[
                    reviewer("B"),
                    reviewer("A"),
                    reviewer("IA", role="integration-auditor"),
                ]
            )

    def test_a_duplicated_required_role_fails_closed(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(
                reviewers=[
                    reviewer("A"),
                    reviewer("A2", role="reviewer-a"),
                    reviewer("IA", role="integration-auditor"),
                ]
            )

    def test_a_fourth_lane_is_not_part_of_the_required_lifecycle(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(
                reviewers=[
                    reviewer("A"),
                    reviewer("B"),
                    reviewer("IA", role="integration-auditor"),
                    reviewer("C", role="reviewer-c"),
                ]
            )

    def test_the_required_lifecycle_is_accepted(self) -> None:
        self.assertEqual(
            [lane.role for lane in self.load().reviewers], list(REQUIRED_REVIEWER_ROLES)
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
                        reviewer("A"),
                        reviewer("B"),
                        reviewer("IA", role="integration-auditor"),
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
