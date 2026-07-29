"""The reviewer artifact lifecycle: prepare, validate, relay, read back.

Three separable claims, and the tests keep them separable:

* a lane said something (its marker);
* a transport said it published something (its exit status);
* GitHub shows the artifact, under the configured login, bound to this head.

Only the third is evidence, and the loop is required to hold out for it.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from _support import (
    HEAD_A,
    HEAD_B,
    RELAY_PROGRAM,
    REVIEWER_LANES,
    REVIEWER_LOGIN,
    REVIEWER_SIGNATURE,
    builder_output,
    make_finding,
    reviewer_artifact,
    reviewer_output,
    secret_bearing_summary,
)
from pr_prover import reviewers
from pr_prover.errors import ReviewerRelayError
from pr_prover.github import Comment
from pr_prover.loop import MERGE_READY, NEEDS_KARAN
from pr_prover.redaction import PLACEHOLDER, scrub
from pr_prover.reviewers import (
    CREDENTIAL_ENV,
    GH_CONFIG_DIR_ENV,
    MAX_PREPARED_BYTES,
    artifact_disagreement,
    artifact_matches,
    artifact_path,
    credential_free,
    credential_free_config_dir,
    parse_artifact,
    publication_copy,
    publication_path,
    published_findings,
    read_prepared,
    relay_source,
)
from test_loop import BLOCKER, LoopHarness


class ArtifactParsingTests(unittest.TestCase):
    """The one canonical parser both the prepared file and the post go through."""

    def parse(self, **overrides):
        return parse_artifact(reviewer_artifact(role="reviewer-a", head=HEAD_A, **overrides))

    def test_a_complete_block_parses(self) -> None:
        reading = self.parse()
        self.assertTrue(reading.ok)
        self.assertEqual(reading.claim.role, "reviewer-a")
        self.assertEqual(reading.claim.head, HEAD_A)
        self.assertEqual(reading.claim.status, "pass")
        self.assertEqual(reading.claim.blocking, 0)
        self.assertTrue(reading.claim.runtime)

    def test_a_head_mentioned_only_in_prose_is_not_a_binding(self) -> None:
        """Scope paragraphs and transcripts legitimately quote a SHA."""
        body = (
            f"I reviewed the tree as of {HEAD_A}, which supersedes the earlier work.\n"
            "ROLE=reviewer-a\nRUNTIME=codex\nSTATUS=pass\nBLOCKING=0\n"
            "KILL-SWITCH: looked for a weakened test\n"
            f"{REVIEWER_SIGNATURE}\n"
        )
        reading = parse_artifact(body)
        self.assertFalse(reading.ok)
        self.assertEqual(reading.problem, "declaration")
        self.assertIn("HEAD=", reading.note)

    def test_a_second_conflicting_declaration_is_rejected(self) -> None:
        """Two answers is not one answer, whichever one a reader happens to hit."""
        body = reviewer_artifact(role="reviewer-a", head=HEAD_A) + f"HEAD={HEAD_B}\n"
        reading = parse_artifact(body)
        self.assertFalse(reading.ok)
        self.assertEqual(reading.problem, "declaration")

    def test_a_short_or_uppercase_sha_is_malformed(self) -> None:
        for value in (HEAD_A[:12], HEAD_A.upper(), "not-a-sha"):
            with self.subTest(value=value):
                body = (
                    f"ROLE=reviewer-a\nRUNTIME=codex\nHEAD={value}\nSTATUS=pass\n"
                    f"BLOCKING=0\nKILL-SWITCH: tried\n{REVIEWER_SIGNATURE}\n"
                )
                self.assertEqual(parse_artifact(body).problem, "head")

    def test_an_artifact_that_names_no_runtime_is_rejected(self) -> None:
        """"What reviewed this head" is part of what the artifact has to say."""
        body = reviewer_artifact(role="reviewer-a", head=HEAD_A, runtime="")
        reading = parse_artifact(body)
        self.assertFalse(reading.ok)
        self.assertEqual(reading.problem, "runtime")

    def test_a_status_contradicting_its_own_count_is_rejected(self) -> None:
        body = reviewer_artifact(role="reviewer-a", head=HEAD_A, status="pass", blocking=2)
        reading = parse_artifact(body)
        self.assertFalse(reading.ok)
        self.assertEqual(reading.problem, "status-count")

    def test_an_artifact_with_no_attempted_kill_switch_is_rejected(self) -> None:
        """The adversarial mandate, enforced structurally rather than semantically.

        A review that lists nothing it tried is indistinguishable from one that
        looked for nothing, and the whole point of the stance is that "I found
        no problem" has to be a different statement from "I did not look".
        """
        body = reviewer_artifact(role="reviewer-a", head=HEAD_A, kill_switches=())
        reading = parse_artifact(body)
        self.assertFalse(reading.ok)
        self.assertEqual(reading.problem, "kill-switch")
        self.assertIn("kill", reading.note)

    def test_a_role_read_as_a_substring_would_confuse_two_lanes(self) -> None:
        """``ROLE=reviewer-a`` must not be satisfied by ``ROLE=reviewer-auditor``."""
        claim = parse_artifact(
            reviewer_artifact(role="reviewer-auditor", head=HEAD_A)
        ).claim
        self.assertTrue(
            artifact_disagreement(claim, role="reviewer-a", head=HEAD_A, status="pass", blocking=0)
        )


class PreparedArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-artifact-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def prepare(self, body: str | None, **kwargs):
        path = self.tmp / "artifact.md"
        if body is not None:
            path.write_text(body, encoding="utf-8")
        return read_prepared(
            path,
            reviewer="A",
            role="reviewer-a",
            signature=REVIEWER_SIGNATURE,
            head=HEAD_A,
            status=kwargs.pop("status", "pass"),
            blocking=kwargs.pop("blocking", 0),
            findings=kwargs.pop("findings", ()),
        )

    def test_a_conforming_artifact_validates(self) -> None:
        artifact = self.prepare(reviewer_artifact(role="reviewer-a", head=HEAD_A))
        self.assertGreater(artifact.size, 0)
        self.assertEqual(artifact.claim.head, HEAD_A)

    def test_passing_narrative_tokens_are_not_machine_findings(self) -> None:
        """Only complete ``FINDING:`` records may create a finding."""
        for token in ("stale-pr-evidence", "redirect-wiring-substring"):
            with self.subTest(token=token):
                artifact = self.prepare(
                    reviewer_artifact(
                        role="reviewer-a",
                        head=HEAD_A,
                        extra=f"FINDING: {token} (narrative heading; no finding was raised)",
                    )
                )
                self.assertEqual(artifact.claim.status, "pass")
                self.assertEqual(artifact.claim.blocking, 0)
                self.assertEqual(artifact.findings, ())

    def test_a_lane_that_wrote_nothing_stops_the_run(self) -> None:
        """A silently failed lane must not have an empty artifact relayed for it."""
        with self.assertRaises(ReviewerRelayError) as caught:
            self.prepare(None)
        self.assertIn("prepared no artifact", caught.exception.message)
        self.assertEqual(caught.exception.reason, "relay-failure")

    def test_an_empty_artifact_stops_the_run(self) -> None:
        with self.assertRaises(ReviewerRelayError):
            self.prepare("   \n\n")

    def test_an_oversized_artifact_stops_the_run(self) -> None:
        with self.assertRaises(ReviewerRelayError) as caught:
            self.prepare("x" * (MAX_PREPARED_BYTES + 1))
        self.assertEqual(caught.exception.evidence["limit"], MAX_PREPARED_BYTES)

    def test_a_missing_signature_stops_the_run(self) -> None:
        with self.assertRaises(ReviewerRelayError):
            self.prepare(reviewer_artifact(role="reviewer-a", head=HEAD_A, signature="anon"))

    def test_an_artifact_about_another_head_never_reaches_github(self) -> None:
        """Validated before publication, so readback is not what discovers it."""
        with self.assertRaises(ReviewerRelayError) as caught:
            self.prepare(reviewer_artifact(role="reviewer-a", head=HEAD_B))
        self.assertEqual(caught.exception.evidence["declared_head"], HEAD_B)

    def test_an_artifact_disagreeing_with_its_own_lane_verdict_stops_the_run(self) -> None:
        """Two stories about one head: the marker classified, the artifact read."""
        with self.assertRaises(ReviewerRelayError) as caught:
            self.prepare(
                reviewer_artifact(role="reviewer-a", head=HEAD_A, status="pass", blocking=0),
                status="fail",
                blocking=3,
            )
        self.assertEqual(caught.exception.evidence["lane_blocking"], 3)
        self.assertEqual(caught.exception.evidence["declared_blocking"], 0)

    def test_an_artifact_without_records_gets_the_final_verdicts_canonical_block(self) -> None:
        """The final message is structured truth; the prose artifact need not duplicate it."""
        lane = [make_finding("null-deref", summary="crashes on empty input")]
        prepared = self.prepare(
            reviewer_artifact(role="reviewer-a", head=HEAD_A, status="fail", blocking=1),
            status="fail",
            blocking=1,
            findings=lane,
        )

        # The reviewer wrote no structured records, but it still left a valid
        # prose artifact for the parent to normalize rather than reject.
        self.assertEqual(prepared.findings, ())
        published = publication_copy(
            prepared, reviewer="A", signature=REVIEWER_SIGNATURE, findings=lane
        )

        self.assertEqual([record.id for record in published.findings], ["null-deref"])
        self.assertIn(
            "FINDING: SEVERITY=blocking ID=null-deref -- crashes on empty input",
            published.body.splitlines(),
        )
        self.assertTrue(
            artifact_matches(
                Comment(
                    identifier="IC_canonical",
                    author=REVIEWER_LOGIN,
                    body=published.body,
                    kind="comment",
                ),
                author=REVIEWER_LOGIN,
                signature=REVIEWER_SIGNATURE,
                role="reviewer-a",
                head=HEAD_A,
                status="fail",
                blocking=1,
                findings=lane,
            )
        )

    def test_the_same_review_stated_on_both_surfaces_validates(self) -> None:
        """Non-vacuity for every case below: parity is satisfiable, and this is it."""
        artifact = self.prepare(
            reviewer_artifact(
                role="reviewer-a",
                head=HEAD_A,
                status="fail",
                blocking=1,
                findings=[
                    ("blocking", "null-deref", "crashes on empty input"),
                    ("non-blocking", "stale-comment", "the header predates the flag"),
                ],
            ),
            status="fail",
            blocking=1,
            findings=[
                make_finding("null-deref", summary="crashes on empty input"),
                make_finding("stale-comment", "non-blocking", summary="the header predates the flag"),
            ],
        )
        self.assertEqual(
            [record.id for record in artifact.findings], ["null-deref", "stale-comment"]
        )

    def test_every_way_an_artifact_can_disagree_with_its_lane_fails_closed(self) -> None:
        """One table, because they are one predicate read from both sides.

        Each row keeps the declaration block valid and agreeing with the lane, so
        nothing here is caught by a check that already existed: the only thing
        wrong is the relationship between the findings the lane reported and the
        finding lines the artifact carries.
        """
        lane = [
            make_finding("null-deref", summary="crashes on empty input"),
            make_finding("bad-copy", "non-blocking", summary="the copy contradicts the contract"),
        ]
        good = ("blocking", "null-deref", "crashes on empty input")
        other = ("non-blocking", "bad-copy", "the copy contradicts the contract")
        for label, findings, expected in (
            ("a missing record", [good], "carries no FINDING: line"),
            (
                "an extra record",
                [good, other, ("non-blocking", "invented", "nobody reported this")],
                "the lane never reported",
            ),
            (
                "a renamed id",
                [good, ("non-blocking", "renamed", "the copy contradicts the contract")],
                "carries no FINDING: line",
            ),
            (
                "a rewritten summary",
                [good, ("non-blocking", "bad-copy", "a summary the lane never wrote")],
                "summary for bad-copy",
            ),
            (
                "a re-severed finding",
                [good, ("needs-karan", "bad-copy", "the copy contradicts the contract")],
                "as SEVERITY=needs-karan",
            ),
            (
                "a repeated id",
                [good, other, other],
                "repeated finding id",
            ),
            (
                "a malformed record",
                [good, other, ("blocking", "x", "")],
                "the verdict grammar refuses",
            ),
            (
                "the grammar quoted back as an example",
                [good, other, ("<severity>", "<id>", "<summary>")],
                "the verdict grammar refuses",
            ),
        ):
            with self.subTest(artifact=label):
                with self.assertRaises(ReviewerRelayError) as caught:
                    self.prepare(
                        reviewer_artifact(
                            role="reviewer-a",
                            head=HEAD_A,
                            status="fail",
                            blocking=1,
                            findings=findings,
                        ),
                        status="fail",
                        blocking=1,
                        findings=lane,
                    )
                self.assertIn(expected, caught.exception.message)
                self.assertEqual(caught.exception.reason, "relay-failure")

    def test_a_rewritten_summary_that_clipping_used_to_hide_is_still_a_rewrite(self) -> None:
        """Parity is only as exact as the value it compares.

        Both summaries sit exactly at the grammar's limit and differ only inside
        the region a clipped record discarded, so while the parser clipped them
        this artifact restated the lane's finding as a different one and
        reconciled anyway.
        """
        reported = secret_bearing_summary("LEFTLEFTLEFT")
        substituted = secret_bearing_summary("RGHTRGHTRGHT")
        self.assertNotEqual(reported, substituted)
        lane = [make_finding("long-record", summary=scrub(reported))]

        def artifact(summary: str) -> str:
            return reviewer_artifact(
                role="reviewer-a",
                head=HEAD_A,
                status="fail",
                blocking=1,
                findings=[("blocking", "long-record", summary)],
            )

        validated = self.prepare(
            artifact(reported), status="fail", blocking=1, findings=lane
        )
        self.assertEqual([record.id for record in validated.findings], ["long-record"])

        with self.assertRaises(ReviewerRelayError) as caught:
            self.prepare(artifact(substituted), status="fail", blocking=1, findings=lane)
        self.assertIn("summary for long-record", caught.exception.message)

    def test_the_artifact_path_is_cleared_before_a_lane_can_write_to_it(self) -> None:
        """A file an earlier lane left is never mistaken for this lane's work."""
        stale = self.tmp / "reviewer-A-aaaaaaaaaaaa.artifact.md"
        stale.write_text("left over from a previous head\n", encoding="utf-8")
        path = artifact_path(self.tmp, reviewer="A", head=HEAD_A)
        self.assertEqual(path, stale)
        self.assertFalse(path.exists())


class CredentialFreeLaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.config_dir = credential_free_config_dir(self.tmp, reviewer="A")

    def test_every_named_credential_is_dropped(self) -> None:
        base = {name: "secret" for name in CREDENTIAL_ENV}
        base["HOME"] = "/Users/example"
        resolved = credential_free(None, base=base, config_dir=self.config_dir)
        for name in CREDENTIAL_ENV:
            self.assertNotIn(name, resolved)
        self.assertEqual(resolved["HOME"], "/Users/example")

    def test_inheriting_untouched_still_becomes_a_concrete_credential_free_map(self) -> None:
        """``None`` is exactly how the operator's token would otherwise get through."""
        resolved = credential_free(
            None, base={"GH_TOKEN": "ghp_x", "PATH": "/bin"}, config_dir=self.config_dir
        )
        self.assertIsNotNone(resolved)
        self.assertNotIn("GH_TOKEN", resolved)

    def test_a_stored_gh_login_is_out_of_reach_without_retargeting_home(self) -> None:
        """The operator's ordinary logged-in machine, minus the token variables.

        This is the shape the false-pass came in: no ``GH_TOKEN`` anywhere, and
        a perfectly good stored session still reachable through the three paths
        ``gh`` searches. The lane environment must break all three for ``gh``
        while leaving the session variables the trusted agent authenticates
        through exactly where they were.
        """
        base = {
            "HOME": "/Users/example",
            "USER": "example",
            "SHELL": "/bin/zsh",
            "XDG_CONFIG_HOME": "/Users/example/.config",
            "GH_CONFIG_DIR": "/Users/example/.config/gh",
            "PATH": "/usr/bin",
        }
        resolved = credential_free(None, base=base, config_dir=self.config_dir)

        self.assertEqual(resolved["GH_CONFIG_DIR"], str(self.config_dir))
        self.assertEqual(sorted(self.config_dir.iterdir()), [])
        # HOME, XDG_CONFIG_HOME and the rest of the session are untouched: the
        # denial is scoped to gh, and synthesizing a HOME is what the mission
        # forbids and what would take Codex's own OAuth down with it.
        for name in ("HOME", "USER", "SHELL", "XDG_CONFIG_HOME", "PATH"):
            self.assertEqual(resolved[name], base[name])

    def test_each_lane_gets_its_own_empty_directory_even_if_one_is_there(self) -> None:
        """A directory left by an earlier lane is emptied, not reused as-is."""
        (self.config_dir / "hosts.yml").write_text("github.com:\n", encoding="utf-8")
        again = credential_free_config_dir(self.tmp, reviewer="A")
        self.assertEqual(again, self.config_dir)
        self.assertEqual(sorted(again.iterdir()), [])
        other = credential_free_config_dir(self.tmp, reviewer="Integration Auditor")
        self.assertNotEqual(other, self.config_dir)
        self.assertTrue(other.is_dir())


class PublishedArtifactTests(unittest.TestCase):
    def artifact(self, **overrides) -> Comment:
        fields = {
            "identifier": "IC_1",
            "author": REVIEWER_LOGIN,
            "body": reviewer_artifact(role="reviewer-a", head=HEAD_A),
            "kind": "comment",
        }
        fields.update(overrides)
        return Comment(**fields)

    def matches(self, artifact: Comment) -> bool:
        return artifact_matches(
            artifact,
            author=REVIEWER_LOGIN,
            signature=REVIEWER_SIGNATURE,
            role="reviewer-a",
            head=HEAD_A,
            status="pass",
            blocking=0,
            findings=(),
        )

    def test_a_conforming_comment_matches(self) -> None:
        self.assertTrue(self.matches(self.artifact()))

    def test_another_login_copying_the_body_verbatim_does_not_match(self) -> None:
        """The body is public the moment a real artifact is posted; the login is not."""
        self.assertFalse(self.matches(self.artifact(author="someone-else")))

    def test_a_review_whose_commit_id_contradicts_its_body_does_not_match(self) -> None:
        """GitHub's own binding is checked alongside the declaration, not instead of it."""
        self.assertFalse(
            self.matches(self.artifact(kind="review", commit_id=HEAD_B))
        )

    def test_a_review_whose_commit_id_agrees_matches(self) -> None:
        self.assertTrue(self.matches(self.artifact(kind="review", commit_id=HEAD_A)))

    def test_a_review_with_no_commit_id_falls_back_to_the_declaration(self) -> None:
        self.assertTrue(self.matches(self.artifact(kind="review", commit_id="")))


class PublishedFindingReadbackTests(unittest.TestCase):
    """What GitHub actually shows, held to the findings the lane reported.

    Validating the prepared file proves what a relay was handed. Between there
    and the pull request the bytes can still be truncated, substituted, or
    rewritten, and every one of those keeps the declaration block — author,
    signature, role, runtime, head, ``STATUS=fail``, ``BLOCKING=1`` — perfectly
    intact. So the published body is read with the same grammar and reconciled
    against the same findings, and each row below is a body that used to read
    back as this run's own complete transport.
    """

    lane = (
        make_finding("null-deref", summary="crashes on empty input"),
        make_finding("bad-copy", "non-blocking", summary="the copy contradicts the contract"),
    )
    good = ("blocking", "null-deref", "crashes on empty input")
    other = ("non-blocking", "bad-copy", "the copy contradicts the contract")

    def published(self, findings, **overrides) -> Comment:
        fields = {
            "identifier": "IC_1",
            "author": REVIEWER_LOGIN,
            "body": reviewer_artifact(
                role="reviewer-a",
                head=HEAD_A,
                status="fail",
                blocking=1,
                findings=findings,
            ),
            "kind": "comment",
        }
        fields.update(overrides)
        return Comment(**fields)

    def matches(self, findings, **overrides) -> bool:
        return artifact_matches(
            self.published(findings, **overrides),
            author=REVIEWER_LOGIN,
            signature=REVIEWER_SIGNATURE,
            role="reviewer-a",
            head=HEAD_A,
            status="fail",
            blocking=1,
            findings=self.lane,
        )

    def test_the_review_the_lane_reported_reads_back(self) -> None:
        """Non-vacuity for every case below: parity is satisfiable, and this is it."""
        self.assertTrue(self.matches([self.good, self.other]))

    def test_a_published_body_that_declares_a_blocker_and_states_none_is_refused(self) -> None:
        """The exact shape the readback predicate used to credit.

        ``STATUS=fail``, ``BLOCKING=1``, the configured author and signature, the
        exact head — and not one word of what the blocker was. The relay reported
        success, and what is on the pull request is unusable.
        """
        self.assertFalse(self.matches([]))

    def test_every_way_the_published_body_can_lose_the_lanes_findings_is_refused(self) -> None:
        """One table, because the published body is judged by the prepared file's predicate."""
        for label, findings in (
            ("a missing record", [self.good]),
            (
                "an extra record",
                [self.good, self.other, ("non-blocking", "invented", "nobody reported this")],
            ),
            (
                "a renamed id",
                [self.good, ("non-blocking", "renamed", "the copy contradicts the contract")],
            ),
            (
                "a rewritten summary",
                [self.good, ("non-blocking", "bad-copy", "a summary the lane never wrote")],
            ),
            (
                "a re-severed finding",
                [self.good, ("needs-karan", "bad-copy", "the copy contradicts the contract")],
            ),
            ("a duplicated record", [self.good, self.other, self.other]),
            ("a malformed record", [self.good, self.other, ("blocking", "x", "")]),
            (
                "the grammar quoted back as an example",
                [self.good, self.other, ("<severity>", "<id>", "<summary>")],
            ),
        ):
            with self.subTest(published=label):
                self.assertFalse(self.matches(findings))

    def test_a_published_summary_rewritten_where_clipping_hid_it_is_refused(self) -> None:
        """The off-by-one's consequence on the surface that decides transport.

        Both summaries are exactly at the grammar's limit and differ only inside
        the region a clipped record threw away, so while the parser clipped them
        this substitution read back as the lane's own finding. It is a
        substitution, and readback has to see it.
        """
        reported = secret_bearing_summary("LEFTLEFTLEFT")
        substituted = secret_bearing_summary("RGHTRGHTRGHT")
        self.assertNotEqual(reported, substituted)
        lane = (make_finding("long-record", summary=scrub(reported)),)

        def published(summary: str) -> Comment:
            return Comment(
                identifier="IC_1",
                author=REVIEWER_LOGIN,
                body=reviewer_artifact(
                    role="reviewer-a",
                    head=HEAD_A,
                    status="fail",
                    blocking=1,
                    findings=[("blocking", "long-record", summary)],
                ),
                kind="comment",
            )

        def matches(summary: str) -> bool:
            return artifact_matches(
                published(summary),
                author=REVIEWER_LOGIN,
                signature=REVIEWER_SIGNATURE,
                role="reviewer-a",
                head=HEAD_A,
                status="fail",
                blocking=1,
                findings=lane,
            )

        self.assertTrue(matches(reported), "the record the lane reported must still read back")
        self.assertFalse(matches(substituted))


class RelayLifecycleLoopTests(LoopHarness):
    """The lifecycle end to end, through the loop that owns it."""

    def test_a_clean_pass_publishes_and_reads_back_one_artifact_per_lane(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertEqual(len(result.transport), 3)
        self.assertEqual(
            [item.role for item in result.transport],
            ["reviewer-a", "reviewer-b", "integration-auditor"],
        )
        for item in result.transport:
            self.assertTrue(item.prepared, item.lane)
            self.assertTrue(item.published, item.lane)
            self.assertTrue(item.read_back, item.lane)
            self.assertEqual(item.identity, REVIEWER_LOGIN)
            self.assertEqual(item.head, HEAD_A)
            self.assertTrue(item.identifier)

    def test_passing_prose_tokens_relay_without_a_false_finding(self) -> None:
        """The relay path uses structured artifact records, never prose."""
        loop = self.build()
        self.review_round(HEAD_A)
        self.runner.reviewer_artifact = lambda argv, status, blocking: reviewer_artifact(
            role=argv[argv.index("--role") + 1],
            head=HEAD_A,
            status=status,
            blocking=blocking,
            extra=(
                "FINDING: stale-pr-evidence (narrative heading; no finding was raised)\n"
                "FINDING: redirect-wiring-substring (narrative heading; no finding was raised)"
            ),
        )

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertEqual(result.reason, "no-blocking-findings")
        self.assertEqual([verdict.findings for verdict in result.verdicts], [(), (), ()])
        self.assertTrue(all(item.read_back for item in result.transport))

    def test_the_ordered_lifecycle_runs_a_then_b_then_the_auditor(self) -> None:
        """The auditor reconciles two artifacts, so it cannot be the first to run."""
        loop = self.build()
        self.review_round(HEAD_A)
        loop.run()
        lanes = [
            call.argv[0]
            for call in self.runner.calls
            if call.argv[0].startswith("lane-reviewer-")
        ]
        self.assertEqual(
            lanes, ["lane-reviewer-A", "lane-reviewer-B", "lane-reviewer-Auditor"]
        )

    def test_the_judging_lane_runs_with_no_github_credential(self) -> None:
        """It audits and prepares; the relay is what publishes."""
        loop = self.build()
        self.review_round(HEAD_A)
        loop.run()
        lane_envs = [env for program, env in self.runner.lane_env if program.startswith("lane-reviewer-")]
        self.assertEqual(len(lane_envs), 3)
        for env in lane_envs:
            self.assertIsNotNone(env, "a relayed lane must not inherit untouched")
            for name in CREDENTIAL_ENV:
                self.assertNotIn(name, env)
            # The session it authenticates through is left exactly as it was.
            self.assertIn("PATH", env)

    def test_a_relay_that_cannot_publish_stops_the_run(self) -> None:
        """A transport failure is not something readback should have to explain."""
        loop = self.build()
        self.review_round(HEAD_A)
        self.runner.relay_failures = 1

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "relay-failure")
        self.assertEqual(result.transport[0].prepared, True)
        self.assertEqual(result.transport[0].published, False)
        self.assertEqual(result.transport[0].read_back, False)

    def test_a_lane_that_prepared_nothing_stops_before_anything_is_published(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)
        self.runner.reviewer_artifact = lambda **_: None

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "relay-failure")
        self.assertEqual(self.remote.comments, [])
        self.assertFalse(result.transport[0].prepared)

    def test_an_artifact_published_under_the_wrong_login_fails_readback(self) -> None:
        """The relay reported success; GitHub is what decides.

        The body is byte-identical to the one that would have passed, so nothing
        in the artifact itself distinguishes this case — only the login does,
        which is exactly why the login is pinned configuration.
        """
        loop = self.build()
        self.review_round(HEAD_A)
        self.runner.relay_author = "impostor"

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "readback-mismatch")
        self.assertEqual(result.evidence["evidence"]["expected_author"], REVIEWER_LOGIN)

    def test_a_relay_that_publishes_a_body_without_the_lanes_findings_fails_readback(
        self,
    ) -> None:
        """The production path, not the predicate: transport succeeded, the record did not.

        The lane wrote a conforming artifact and the prepared-file check passed
        it, because the file *was* conforming. What the relay put on the pull
        request is that file with its ``FINDING:`` lines removed — declarations
        untouched, ``STATUS=fail`` and ``BLOCKING=1`` still agreeing with the
        marker, and nothing left for the Integration Auditor or Karan to act on.
        Only reading the published body back can tell, and the run must stop
        rather than credit this as its own complete transport.
        """
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.runner.relay_body = lambda body: "".join(
            f"{line}\n"
            for line in body.splitlines()
            if not line.startswith("FINDING:")
        )

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "readback-mismatch")
        self.assertEqual(result.evidence["evidence"]["expected_findings"], ["null-deref"])
        # Prepared and published both happened; only the readback failed. That
        # distinction is the diagnosis.
        self.assertTrue(result.transport[0].prepared)
        self.assertTrue(result.transport[0].published)
        self.assertFalse(result.transport[0].read_back)

    def test_a_relay_that_publishes_a_rewritten_finding_fails_readback(self) -> None:
        """Substitution, not truncation: a blocker the lane never reported."""
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.runner.relay_body = lambda body: body.replace(
            "ID=null-deref -- crashes on empty input",
            "ID=null-deref -- a summary the lane never wrote",
        )

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "readback-mismatch")
        self.assertEqual(len(self.remote.comments), 1)

    def test_a_reviewer_artifact_for_the_previous_head_does_not_count(self) -> None:
        """Stale evidence is the thing a per-head lifecycle exists to refuse."""
        loop = self.build()
        self.review_round(HEAD_A)
        self.runner.reviewer_artifact = lambda argv, status, blocking: reviewer_artifact(
            role=argv[argv.index("--role") + 1], head=HEAD_B, status=status, blocking=blocking
        )

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "relay-failure")

    def test_a_failing_lane_publishes_an_artifact_declaring_that_failure(self) -> None:
        """The artifact reports the review, not a sanitized version of it."""
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_A, addressed=["null-deref"], status="failure"),
            returncode=1,
        )
        loop.run()
        bodies = [comment.body for comment in self.remote.comments]
        self.assertTrue(any("STATUS=fail" in body and "BLOCKING=1" in body for body in bodies))
        self.assertTrue(all("KILL-SWITCH:" in body for body in bodies))

    def test_every_published_artifact_is_retained_as_this_runs_own(self) -> None:
        """Which is what stops the next cycle reading them back as human feedback."""
        loop = self.build()
        self.review_round(HEAD_A)
        result = loop.run()
        self.assertEqual(result.outcome, MERGE_READY)
        owned = self.state()["verified_artifacts"]
        self.assertEqual(len(owned), 3)
        self.assertEqual(
            sorted(owned), sorted(comment.identifier for comment in self.remote.comments)
        )

    def test_the_judging_lane_has_no_route_to_a_stored_gh_login_either(self) -> None:
        """Dropping the token variables is necessary and was never sufficient.

        ``gh`` resolves a stored session through ``GH_CONFIG_DIR``, then
        ``$XDG_CONFIG_HOME/gh``, then ``$HOME/.config/gh``, so a lane that only
        lost ``GH_TOKEN`` could still publish under the operator's login. Each
        lane is therefore pointed at an empty directory it owns — and at its
        own, so one lane cannot be handed whatever another left behind.
        """
        loop = self.build()
        self.review_round(HEAD_A)
        loop.run()

        observed = [
            (path, empty)
            for program, path, empty in self.runner.lane_gh_config
            if program.startswith("lane-reviewer-")
        ]
        self.assertEqual(len(observed), 3)
        self.assertEqual(len({path for path, _ in observed}), 3, "one per lane, not one shared")
        for path, empty in observed:
            self.assertTrue(empty, f"{path} was not an empty directory when the lane launched")

        for program, env in self.runner.lane_env:
            if not program.startswith("lane-reviewer-"):
                continue
            self.assertIn(GH_CONFIG_DIR_ENV, env)
            # HOME and the rest of the session are not retargeted: the mission
            # forbids a synthetic HOME, and it is where the trusted agent's own
            # OAuth session lives. Denying gh must not deny Codex.
            for name in ("HOME", "USER", "SHELL"):
                if name in os.environ:
                    self.assertEqual(env.get(name), os.environ[name])

    def test_the_relay_keeps_its_own_transport_authority(self) -> None:
        """Only the judging half is denied. The relay publishes as it always did."""
        loop = self.build()
        self.review_round(HEAD_A)
        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        relay_envs = [env for program, env in self.runner.lane_env if program == RELAY_PROGRAM]
        self.assertEqual(len(relay_envs), 3)
        for env in relay_envs:
            # No overlay is configured for the relay, so it inherits untouched —
            # including whatever gh session it already holds.
            self.assertIsNone(env)
        self.assertEqual(len(self.remote.comments), 3)
        for item in result.transport:
            self.assertTrue(item.read_back, item.lane)


class TransportAttributionTests(LoopHarness):
    """Which post this run is allowed to call its own transport.

    The pre-launch snapshot answers "did this id exist before the lane started".
    That is not the same question as "did this relay publish it", and the
    difference is the whole defect: a valid artifact posted by the judging lane
    itself — under the configured login, on the right head, with every
    declaration correct — satisfies the first and says nothing about the second.
    So attribution runs off a second snapshot taken after the lane exits and
    immediately before the relay is launched.
    """

    def lane_posts_its_own_artifact(self, program: str, head: str, role: str) -> None:
        """Script one reviewer lane to publish a valid artifact for itself.

        This is what a reachable stored login buys: not a forgery, a genuine
        post under the configured account, indistinguishable from the relay's
        by anything except when it happened.
        """
        self.script.add(
            program,
            reviewer_output(head),
            after=lambda: self.remote.comment(
                reviewer_artifact(role=role, head=head), author=REVIEWER_LOGIN
            ),
        )

    def test_a_lane_side_post_cannot_stand_in_for_a_relay_that_published_nothing(
        self,
    ) -> None:
        """The counterexample, end to end: complete-looking transport, zero relay posts.

        Every relay exits zero and publishes nothing; each lane posts its own
        valid artifact instead. Before the pre-relay snapshot this produced
        ``merge-ready`` with three complete transport records. It must now fail
        closed with neither.
        """
        loop = self.build()
        for program, role in (
            ("lane-reviewer-A", "reviewer-a"),
            ("lane-reviewer-B", "reviewer-b"),
            ("lane-reviewer-Auditor", "integration-auditor"),
        ):
            self.lane_posts_its_own_artifact(program, HEAD_A, role)
        self.runner.relay_noops = 3

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "readback-mismatch")
        self.assertNotEqual(result.outcome, MERGE_READY)
        # The lane-side posts really did land, under the configured login.
        self.assertEqual(len(self.remote.comments), 1)
        self.assertEqual(self.remote.comments[0].author, REVIEWER_LOGIN)
        # ...and none of them was credited as transport.
        self.assertEqual(len(result.transport), 1)
        self.assertTrue(result.transport[0].prepared)
        self.assertFalse(result.transport[0].read_back)
        self.assertFalse(result.transport[0].identifier)
        self.assertEqual(self.state().get("verified_artifacts", {}), {})

    def test_the_evidence_names_the_post_that_arrived_while_the_lane_ran(self) -> None:
        """A missing relay post should not read as an unexplained readback puzzle."""
        loop = self.build()
        self.lane_posts_its_own_artifact("lane-reviewer-A", HEAD_A, "reviewer-a")
        self.runner.relay_noops = 1

        result = loop.run()

        self.assertEqual(result.reason, "readback-mismatch")
        evidence = result.failures[0].evidence
        self.assertEqual(evidence["artifacts_published_before_transport"], 1)
        self.assertEqual(evidence["artifacts_since_transport_began"], 0)

    def test_a_real_relay_post_is_retained_and_the_lane_side_copy_is_not(self) -> None:
        """Both posts are valid and both are under the configured login.

        Only one of them is this run's transport, and the run keeps that one.
        The copy is then exactly what human-feedback reconciliation is for: a
        post on the PR that nothing in this run's evidence accounts for, so the
        run refuses to call the head merge-ready over it.
        """
        loop = self.build()
        self.lane_posts_its_own_artifact("lane-reviewer-A", HEAD_A, "reviewer-a")
        self.script.add("lane-reviewer-B", reviewer_output(HEAD_A))

        result = loop.run()

        # Four comments: A's lane-side copy plus one relay post per lane.
        self.assertEqual(len(self.remote.comments), 4)
        lane_side = self.remote.comments[0].identifier
        owned = self.state()["verified_artifacts"]
        self.assertEqual(len(owned), 3)
        self.assertNotIn(lane_side, owned)
        self.assertNotIn(lane_side, [item.identifier for item in result.transport])
        for item in result.transport:
            self.assertTrue(item.identifier)
            self.assertIn(item.identifier, owned)
        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "human-feedback")
        self.assertEqual(
            [item["artifact_id"] for item in result.evidence["evidence"]["unresolved"]],
            [lane_side],
        )

    def test_a_copied_artifact_that_predates_the_lane_still_never_counts(self) -> None:
        """The pre-launch snapshot keeps doing its own job as well."""
        loop = self.build()
        self.remote.comment(
            reviewer_artifact(role="reviewer-a", head=HEAD_A), author=REVIEWER_LOGIN
        )
        self.review_round(HEAD_A)
        self.runner.relay_noops = 1

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "readback-mismatch")

    def test_a_self_publishing_lane_still_attributes_from_its_launch(self) -> None:
        """No relay means no relay window; the pre-launch snapshot is the newest one."""
        lanes = [
            {
                "name": name,
                "role": role,
                "argv": [program, "--role", "{role}", "--head", "{head}"],
                "artifact_author": REVIEWER_LOGIN,
                "artifact_signature": REVIEWER_SIGNATURE,
            }
            for name, role, program in REVIEWER_LANES
        ]
        loop = self.build(reviewers=lanes)
        for program, role in (
            ("lane-reviewer-A", "reviewer-a"),
            ("lane-reviewer-B", "reviewer-b"),
            ("lane-reviewer-Auditor", "integration-auditor"),
        ):
            self.lane_posts_its_own_artifact(program, HEAD_A, role)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertEqual(len(self.state()["verified_artifacts"]), 3)


# -- publication redaction -------------------------------------------------
# One synthetic credential-shaped value, assembled rather than written down, and
# never printed. It is not a real token; it is the shape the sanitizer
# recognizes, which is all these tests need in order to watch it not reach a
# pull request.
SYNTHETIC_TOKEN = "ghp_" + "Ab3" * 8


def assert_no_secret(case: unittest.TestCase, haystack: str, what: str) -> None:
    """Assert :data:`SYNTHETIC_TOKEN` is absent, without printing the surface.

    ``assertNotIn`` would put the whole body in the failure message, and the
    body is the thing suspected of carrying the value — so a failing leak test
    would leak. The message names the surface instead, which is what a reader
    needs, and the assertion is the same one.
    """
    case.assertTrue(SYNTHETIC_TOKEN not in haystack, f"{what} still carries the value")


def assert_holds_secret(case: unittest.TestCase, haystack: str, what: str) -> None:
    """The mirror of :func:`assert_no_secret`, for the copy that legitimately does."""
    case.assertTrue(SYNTHETIC_TOKEN in haystack, f"{what} no longer carries the value")


def assert_carries(case: unittest.TestCase, haystack: str, needle: str, what: str) -> None:
    """``needle in haystack``, without ``assertIn`` printing the haystack.

    Every body in these tests is one a credential was pasted into, so the
    container is exactly what must not reach a failure message.
    """
    case.assertTrue(needle in haystack, f"{what} does not carry {needle!r}")


def assert_same_text(case: unittest.TestCase, actual: str, expected: str, what: str) -> None:
    """Assert two bodies are identical without printing either one.

    ``assertEqual`` puts both sides in the failure message, and the failure this
    is most likely to report is redaction not having happened — so the plain
    assertion would print the very value the suite exists to keep off every
    surface. Where they diverge is what a reader needs, and that is what this
    says.
    """
    if actual == expected:
        return
    actual_lines, expected_lines = actual.splitlines(), expected.splitlines()
    for number, (left, right) in enumerate(zip(actual_lines, expected_lines), start=1):
        if left != right:
            case.fail(
                f"{what} first differs on line {number}: {len(left)} characters "
                f"where {len(right)} were expected"
            )
    case.fail(
        f"{what} differs in length: {len(actual_lines)} lines against "
        f"{len(expected_lines)} expected"
    )


class PublicationCopyTests(unittest.TestCase):
    """What a relay is handed: the redacted copy, never the reviewer's own bytes.

    A reviewer artifact is child output like any other, except that it is the
    one surface this tool *publishes*, under a name that is not the lane's. The
    parser scrubs the records it extracts and leaves the body alone, so before
    this step a credential a lane pasted into its own artifact reached GitHub
    and then read back clean, because readback re-parsed and re-scrubbed it the
    same way.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-publication-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def prepared(self, body: str, **kwargs):
        """What the lane wrote, validated exactly as the shipped path validates it."""
        path = self.tmp / "reviewer-A-aaaaaaaaaaaa.artifact.md"
        path.write_text(body, encoding="utf-8")
        return read_prepared(
            path,
            reviewer="A",
            role="reviewer-a",
            signature=kwargs.pop("signature", REVIEWER_SIGNATURE),
            head=HEAD_A,
            status=kwargs.pop("status", "pass"),
            blocking=kwargs.pop("blocking", 0),
            findings=kwargs.pop("findings", ()),
        )

    def copy(self, prepared, *, findings=(), signature=REVIEWER_SIGNATURE):
        return publication_copy(
            prepared, reviewer="A", signature=signature, findings=findings
        )

    def leaky(self, **overrides) -> str:
        """A conforming artifact whose prose quotes a credential, as lanes do."""
        fields = {
            "role": "reviewer-a",
            "head": HEAD_A,
            "kill_switches": (
                f"replayed the token {SYNTHETIC_TOKEN} the diff pastes; it was rejected",
            ),
            "extra": (
                f"transcript: curl -H 'Authorization: bearer {SYNTHETIC_TOKEN}' /repos"
            ),
        }
        fields.update(overrides)
        return reviewer_artifact(**fields)

    def test_the_copy_is_its_own_file_and_the_lanes_bytes_are_left_where_they_are(
        self,
    ) -> None:
        """The reviewer's own artifact stays readable local input; it is not the path."""
        prepared = self.prepared(self.leaky())
        published = self.copy(prepared)

        self.assertNotEqual(published.path, prepared.path)
        self.assertEqual(published.path, publication_path(prepared.path))
        self.assertTrue(published.path.is_file())
        assert_same_text(
            self,
            published.path.read_text(encoding="utf-8"),
            published.body,
            "the publication file",
        )
        # Untouched, and still the untrusted input it always was.
        self.assertTrue(prepared.path.is_file())
        assert_same_text(
            self,
            prepared.path.read_text(encoding="utf-8"),
            prepared.body,
            "the lane's own file",
        )
        assert_holds_secret(self, prepared.body, "the lane's own file")

    def test_a_credential_a_lane_pasted_into_its_artifact_is_redacted(self) -> None:
        published = self.copy(self.prepared(self.leaky()))

        assert_no_secret(self, published.body, "the redacted artifact")
        assert_no_secret(
            self, published.path.read_text(encoding="utf-8"), "the publication file"
        )
        assert_carries(self, published.body, PLACEHOLDER, "the redacted artifact")

    def test_every_non_secret_character_survives(self) -> None:
        """Redaction, not truncation.

        The whole body is compared, not sampled: the published bytes are the
        lane's bytes with the credential-shaped runs replaced and nothing else
        touched. ``scrub`` is used rather than ``sanitize``/``evidence`` for
        exactly this reason — those clip, and a review clipped to an evidence
        budget loses the argument it exists to make.
        """
        raw = self.leaky()
        published = self.copy(self.prepared(raw))

        assert_same_text(self, published.body, scrub(raw), "the redacted artifact")
        self.assertTrue(published.body != raw, "nothing was redacted at all")
        # Every line that never held the value is byte-identical, in order.
        for number, (original, kept) in enumerate(
            zip(raw.splitlines(), published.body.splitlines()), start=1
        ):
            if SYNTHETIC_TOKEN not in original:
                assert_same_text(self, kept, original, f"line {number}")
        self.assertEqual(len(raw.splitlines()), len(published.body.splitlines()))

    def test_the_declarations_signature_and_findings_are_revalidated(self) -> None:
        """The copy is held to everything the original was, on its own bytes."""
        note = ("non-blocking", "pasted-header", f"a fixture holds {SYNTHETIC_TOKEN}")
        lane = [make_finding("pasted-header", severity="non-blocking", summary=scrub(note[2]))]
        published = self.copy(
            self.prepared(self.leaky(findings=[note]), findings=lane), findings=lane
        )

        self.assertTrue(published.sanitized)
        self.assertEqual(published.claim.role, "reviewer-a")
        self.assertEqual(published.claim.head, HEAD_A)
        self.assertEqual(published.claim.status, "pass")
        self.assertEqual(published.claim.blocking, 0)
        self.assertTrue(published.claim.kill_switches)
        assert_carries(self, published.body, REVIEWER_SIGNATURE, "the redacted artifact")
        self.assertEqual([record.id for record in published.findings], ["pasted-header"])
        assert_same_text(
            self, published.findings[0].summary, scrub(note[2]), "the published summary"
        )
        assert_no_secret(self, published.findings[0].summary, "the published finding")

    def test_the_redaction_is_idempotent_which_is_what_keeps_parity_exact(self) -> None:
        """Parity compares a scrubbed record against a scrubbed record.

        The lane's finding summaries were scrubbed when its final message was
        parsed; the published body is scrubbed whole and then parsed, which
        scrubs the summaries again. The two are only the same claim if a second
        pass over already-redacted text changes nothing, so that is asserted
        rather than assumed.
        """
        for original in (
            f"a fixture holds {SYNTHETIC_TOKEN}",
            f"curl -H 'Authorization: bearer {SYNTHETIC_TOKEN}'",
            "API_KEY=abcdefghijklmnop",
            "https://user:password@example.test/x",
        ):
            with self.subTest(original=original[:24]):
                once = scrub(original)
                self.assertEqual(scrub(once), once)

    def test_a_signature_consumed_by_redaction_stops_the_run(self) -> None:
        """Redaction is a text substitution, so it can change what a body says."""
        signature = f"Reviewed by: bearer {SYNTHETIC_TOKEN}"
        prepared = self.prepared(
            self.leaky(signature=signature, extra=""), signature=signature
        )
        with self.assertRaises(ReviewerRelayError) as caught:
            self.copy(prepared, signature=signature)
        self.assertIn("redacted artifact", caught.exception.message)
        self.assertIn("configured signature", caught.exception.message)
        self.assertEqual(caught.exception.reason, "relay-failure")
        self.assertFalse(publication_path(prepared.path).exists())

    def test_a_finding_line_redaction_pushes_past_the_grammar_stops_the_run(self) -> None:
        """The placeholder is longer than a short secret, and lines have a limit.

        A summary already at the grammar's maximum grows past it once the
        credential inside it is replaced. Publishing that would put a
        ``FINDING:`` line on the pull request that the readback parser refuses,
        which is the one thing preparing an artifact is checked in order to
        prevent — so the run stops here, before anything is published, rather
        than after.
        """
        summary = secret_bearing_summary("LEFTLEFTLEFT")
        lane = [make_finding("long-record", summary=scrub(summary))]
        prepared = self.prepared(
            reviewer_artifact(
                role="reviewer-a",
                head=HEAD_A,
                status="fail",
                blocking=1,
                findings=[("blocking", "long-record", summary)],
            ),
            status="fail",
            blocking=1,
            findings=lane,
        )
        # The lane's own file is fine: at the limit, and the parser reads it.
        self.assertEqual([record.id for record in prepared.findings], ["long-record"])

        with self.assertRaises(ReviewerRelayError) as caught:
            self.copy(prepared, findings=lane)

        self.assertIn("redacted artifact", caught.exception.message)
        self.assertIn("verdict grammar refuses", caught.exception.message)
        self.assertFalse(publication_path(prepared.path).exists())

    def test_a_body_redaction_grows_past_the_size_limit_stops_the_run(self) -> None:
        """The same growth, measured against the artifact size bound."""
        head = reviewer_artifact(role="reviewer-a", head=HEAD_A, extra="TOKEN=a TOKEN=b ")
        padding = MAX_PREPARED_BYTES - 8 - len(head)
        prepared = self.prepared(head + "z" * padding)
        self.assertLessEqual(prepared.size, MAX_PREPARED_BYTES)

        with self.assertRaises(ReviewerRelayError) as caught:
            self.copy(prepared)

        self.assertIn("larger than an artifact can be", caught.exception.message)
        self.assertEqual(caught.exception.evidence["limit"], MAX_PREPARED_BYTES)
        self.assertFalse(publication_path(prepared.path).exists())

    def test_a_publication_path_that_cannot_be_cleared_stops_the_run(self) -> None:
        prepared = self.prepared(self.leaky())
        publication_path(prepared.path).mkdir()

        with self.assertRaises(ReviewerRelayError) as caught:
            self.copy(prepared)

        self.assertIn("could not be cleared", caught.exception.message)
        self.assertEqual(caught.exception.reason, "relay-failure")

    def test_a_publication_path_that_cannot_be_written_stops_the_run(self) -> None:
        prepared = self.prepared(self.leaky())
        missing = replace(prepared, path=self.tmp / "gone" / "reviewer-A.artifact.md")

        with self.assertRaises(ReviewerRelayError) as caught:
            self.copy(missing)

        self.assertIn("could not be written for publication", caught.exception.message)
        self.assertEqual(caught.exception.evidence["error"], "FileNotFoundError")

    def test_a_symlink_at_the_publication_path_is_removed_not_written_through(self) -> None:
        """Exclusive creation, so the redacted body lands where it was addressed."""
        prepared = self.prepared(self.leaky())
        elsewhere = self.tmp / "elsewhere.md"
        elsewhere.write_text("not this file\n", encoding="utf-8")
        publication_path(prepared.path).symlink_to(elsewhere)

        published = self.copy(prepared)

        self.assertFalse(published.path.is_symlink())
        self.assertTrue(published.path.is_file())
        self.assertEqual(elsewhere.read_text(encoding="utf-8"), "not this file\n")
        assert_no_secret(self, published.path.read_text(encoding="utf-8"), "the publication file")

    def test_only_the_redacted_copy_can_be_handed_to_a_relay(self) -> None:
        """The invariant checked where a path becomes a transport's argument."""
        prepared = self.prepared(self.leaky())
        with self.assertRaises(ReviewerRelayError) as caught:
            relay_source(prepared, reviewer="A")
        self.assertIn("only the redacted publication copy", caught.exception.message)
        self.assertEqual(caught.exception.reason, "relay-failure")

        published = self.copy(prepared)
        self.assertEqual(relay_source(published, reviewer="A"), published.path)


class PublicationRedactionLoopTests(LoopHarness):
    """The normal loop, end to end, with a credential in what a reviewer prepared.

    Production path throughout: the shipped loop, the shipped relay contract,
    the shipped readback. Nothing is patched except in the probe at the bottom,
    which is there to prove these assertions can fail.
    """

    NOTE = (
        "non-blocking",
        "pasted-header",
        f"the fixture under test pastes {SYNTHETIC_TOKEN} into a request header",
    )

    def body(self, role: str, head: str = HEAD_A) -> str:
        """The artifact a lane writes: conforming, and carrying a credential."""
        return reviewer_artifact(
            role=role,
            head=head,
            status="pass",
            blocking=0,
            findings=[self.NOTE] if role == "reviewer-a" else (),
            kill_switches=(
                f"replayed {SYNTHETIC_TOKEN} from the fixture against the API; rejected",
            ),
            extra=f"transcript: curl -H 'Authorization: bearer {SYNTHETIC_TOKEN}' /repos",
        )

    def arrange(self) -> list:
        """One clean review round in which every lane pastes the value."""
        self.script.add("lane-reviewer-A", reviewer_output(HEAD_A, [self.NOTE]))
        self.script.add("lane-reviewer-B", reviewer_output(HEAD_A))
        self.runner.reviewer_artifact = lambda argv, status, blocking: self.body(
            argv[argv.index("--role") + 1], argv[argv.index("--head") + 1]
        )
        handed: list[str] = []

        def record(body: str) -> str:
            handed.append(body)
            return body

        self.runner.relay_body = record
        return handed

    def test_a_credential_in_a_prepared_artifact_never_reaches_the_pull_request(
        self,
    ) -> None:
        """The defect, end to end, on the loop that owns the lifecycle."""
        loop = self.build()
        handed = self.arrange()

        result = loop.run()

        # The run is still an honest clean pass: transport is credited, and the
        # redacted body is what readback accepted.
        self.assertEqual(result.outcome, MERGE_READY, result.reason)
        self.assertEqual(len(result.transport), 3)
        for item in result.transport:
            self.assertTrue(item.prepared, item.lane)
            self.assertTrue(item.published, item.lane)
            self.assertTrue(item.read_back, item.lane)

        # Nothing the transport was handed carried the value...
        self.assertEqual(len(handed), 3)
        for body in handed:
            assert_no_secret(self, body, "a body handed to the relay")
        # ...and nothing on the pull request does, placeholder in its place.
        self.assertEqual(len(self.remote.comments), 3)
        for comment in self.remote.comments:
            assert_no_secret(self, comment.body, f"published artifact {comment.identifier}")
            assert_carries(
                self, comment.body, PLACEHOLDER, f"published artifact {comment.identifier}"
            )

    def test_the_published_artifact_preserves_prose_and_renders_the_final_verdict(
        self,
    ) -> None:
        """Reviewer prose survives; structured records come from the final verdict once."""
        loop = self.build()
        self.arrange()

        result = loop.run()
        self.assertEqual(result.outcome, MERGE_READY, result.reason)
        published = self.remote.comments[0].body

        # The artifact's narrative/declaration surface remains intact after
        # redaction, but any model-written FINDING line is replaced by the
        # canonical record parsed from the final verdict.
        assert_carries(self, published, "KILL-SWITCH:", "the published artifact")
        assert_carries(self, published, REVIEWER_SIGNATURE, "the published artifact")
        claim = parse_artifact(published).claim
        self.assertEqual(claim.role, "reviewer-a")
        self.assertEqual(claim.head, HEAD_A)
        self.assertEqual(claim.status, "pass")
        self.assertEqual(claim.blocking, 0)
        self.assertTrue(claim.kill_switches)
        # The finding survives as one canonical record, redacted and still the
        # exact finding the lane's final verdict carried.
        records = published_findings(published)
        self.assertEqual([record.id for record in records], ["pasted-header"])
        assert_same_text(
            self, records[0].summary, scrub(self.NOTE[2]), "the published summary"
        )
        self.assertEqual(published.count("FINDING: SEVERITY="), 1)
        # And the shipped readback predicate accepts that body for this lane.
        self.assertTrue(
            artifact_matches(
                self.remote.comments[0],
                author=REVIEWER_LOGIN,
                signature=REVIEWER_SIGNATURE,
                role="reviewer-a",
                head=HEAD_A,
                status="pass",
                blocking=0,
                findings=result.verdicts[0].findings,
            )
        )

    def test_the_relay_is_pointed_at_the_redacted_copy_not_the_lanes_file(self) -> None:
        """Structural, not textual: the raw path is never the published path."""
        loop = self.build()
        self.arrange()

        self.assertEqual(loop.run().outcome, MERGE_READY)

        lane_files = [
            call.argv[call.argv.index("--artifact-file") + 1]
            for call in self.runner.calls
            if call.argv[0].startswith("lane-reviewer-")
        ]
        self.assertEqual(len(lane_files), 3)
        self.assertEqual(len(self.runner.relayed_files), 3)
        for lane_file, relayed in zip(lane_files, self.runner.relayed_files):
            self.assertNotEqual(relayed, lane_file)
            self.assertEqual(relayed, str(publication_path(Path(lane_file))))

    def test_disabling_the_publication_redaction_puts_the_credential_on_the_pr(
        self,
    ) -> None:
        """The probe that keeps the three tests above from proving nothing.

        One substitution is neutered — the one :func:`publication_copy` applies,
        and nothing else, so the parser still scrubs the records it extracts
        exactly as it always did. The same run then reaches the same
        ``merge-ready`` verdict with the value on the pull request, which is
        precisely the defect: readback re-parses and re-scrubs, so it never saw
        anything wrong. A regression that could not tell these two runs apart
        would be measuring the parser, not the publication path.
        """
        loop = self.build()
        self.arrange()

        with mock.patch.object(reviewers, "scrub", lambda text: text):
            result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY, result.reason)
        self.assertEqual(len(self.remote.comments), 3)
        leaked = sum(
            1 for comment in self.remote.comments if SYNTHETIC_TOKEN in comment.body
        )
        self.assertEqual(leaked, 3, "the probe did not reproduce the defect")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
