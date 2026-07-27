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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from _support import (
    HEAD_A,
    HEAD_B,
    RELAY_PROGRAM,
    REVIEWER_LANES,
    REVIEWER_LOGIN,
    REVIEWER_SIGNATURE,
    builder_output,
    reviewer_artifact,
    reviewer_output,
)
from pr_prover.errors import ReviewerRelayError
from pr_prover.github import Comment
from pr_prover.loop import MERGE_READY, NEEDS_KARAN
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
    read_prepared,
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
        )

    def test_a_conforming_artifact_validates(self) -> None:
        artifact = self.prepare(reviewer_artifact(role="reviewer-a", head=HEAD_A))
        self.assertGreater(artifact.size, 0)
        self.assertEqual(artifact.claim.head, HEAD_A)

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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
