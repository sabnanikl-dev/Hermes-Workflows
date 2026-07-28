"""Operator-pinned acknowledgement posts, from the config file to the verdict.

The defect these pin down is a live one. On the pilot repository the builder
publishes as ``sabnanikl-dev`` and the reviewers as ``karanagent1``, those two
are the only authenticated identities available, and the acknowledgement
contract refuses every post written under a configured publishing login. The
operator is the human authority on the pull request *and* one of those logins,
so a run that reads a conversation the operator has already reconciled still
answers ``acknowledged: []`` and stops — not because anything is unresolved, but
because nobody left is allowed to say so.

The repair is one optional config field naming *exact immutable post ids*, and
the tests here are written to hold it to being exactly that:

* the strict default is unchanged. Absent, empty, or naming other posts, a
  publisher-authored acknowledgement clears nothing;
* an id authorizes one post, never a login. The same account's next comment is
  refused, and so is the same account's post with one byte changed;
* a pinned post is not exempt from anything else. Grammar, chronology, the one
  unresolved-to-cleared transition, residual prose, and the surfaces GitHub
  resolves natively all still decide;
* nothing a lane published during the run can be reached by a pin at all.

The loop cases drive :meth:`ProverLoop.run` over the real config → loop →
``RunArtifacts`` → feedback path rather than calling the reconciler directly,
because the defect was never in the classifier's logic: it was in what the
shipped loop handed it. The last class does the same thing through a config file
written to disk and read back by :meth:`RunConfig.load`, which is the only path
an operator actually uses.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from _support import (
    BRANCH,
    BUILDER_LOGIN,
    GOVERNING_ISSUE,
    HEAD_A,
    HEAD_B,
    REVIEWER_LANES,
    REVIEWER_LOGIN,
    SIGNATURE,
    builder_output,
    fix_comment,
    make_source_repo,
    reviewer_lane,
    reviewer_output,
)
from pr_prover import cli
from pr_prover.config import MAX_OPERATOR_ACKNOWLEDGEMENTS, RunConfig
from pr_prover.errors import ConfigError
from pr_prover.feedback import ACKNOWLEDGEMENT
from pr_prover.github import Comment
from pr_prover.loop import MERGE_READY, NEEDS_KARAN, ProverLoop
from pr_prover.worktrees import SourceRepo, WorktreeProvider
from test_loop import BLOCKER, LoopHarness

HUMAN = "karan"
FIRST_PROSE = "do not merge; the migration drops data"
SECOND_PROSE = "and the rollback plan is still missing"
# What the operator's mapped reconciliation post says once its bookkeeping lines
# are taken out. It is ordinary prose, so it stays unresolved feedback until a
# later separately pinned post clears that exact id — which is the second half
# of the live shape this issue reproduces.
RESIDUAL_PROSE = "reconciled with Karan; holding for one more read"
EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "run.example.json"


def ack(target: str) -> str:
    """The canonical acknowledgement line for one immutable artifact id."""
    return f"{ACKNOWLEDGEMENT} {target}"


class ConfigSeamTests(unittest.TestCase):
    """The field is a bounded list of exact ids, or it is a config error."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-ack-config-")
        self.tmp = Path(self._tmp.name).resolve()
        self.addCleanup(self._tmp.cleanup)
        self.source_repo = make_source_repo(self.tmp)

    def payload(self, **overrides: object) -> dict[str, object]:
        """One valid v2 config, in the shipped relayed shape."""
        base: dict[str, object] = {
            "schema_version": 2,
            "repo": "example/repo",
            "pr": 7,
            "branch": BRANCH,
            "base": "main",
            "governing_issues": [GOVERNING_ISSUE],
            "source_repo": str(self.source_repo),
            "worktree_root": str(self.tmp / "worktrees"),
            "state_file": str(self.tmp / "state.json"),
            "lock_file": str(self.tmp / "run.lock"),
            "gates": [],
            "reviewers": [
                reviewer_lane(name, role, program) for name, role, program in REVIEWER_LANES
            ],
            "builder": {
                "argv": ["lane-builder", "--blockers", "{blockers_file}"],
                "signature": SIGNATURE,
                "comment_author": BUILDER_LOGIN,
            },
        }
        base.update(overrides)
        return base

    def load(self, **overrides: object) -> RunConfig:
        return RunConfig.from_mapping(self.payload(**overrides), base_dir=self.tmp)

    def refusal(self, value: object) -> ConfigError:
        with self.assertRaises(ConfigError) as caught:
            self.load(operator_acknowledgements=value)
        return caught.exception

    # -- the default is the strict one ------------------------------------
    def test_an_omitted_field_pins_nothing(self) -> None:
        self.assertEqual(self.load().operator_acknowledgements, ())

    def test_an_empty_list_pins_nothing(self) -> None:
        """Empty and absent are one answer; neither relaxes anything."""
        self.assertEqual(self.load(operator_acknowledgements=[]).operator_acknowledgements, ())

    def test_the_shipped_example_pins_nothing(self) -> None:
        """The documented default an operator copies has to be the strict one."""
        payload = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.assertIn(
            "operator_acknowledgements",
            payload,
            "the example no longer documents the seam it is meant to describe",
        )
        self.assertEqual(payload["operator_acknowledgements"], [])

    # -- what it accepts ---------------------------------------------------
    def test_the_id_shapes_this_tool_reads_are_accepted(self) -> None:
        """A REST comment id, a namespaced review id, and a GraphQL node id."""
        pinned = ["5107483039", "review:2938471", "IC_kwDOM7-x1s6h2K_A=="]
        self.assertEqual(
            self.load(operator_acknowledgements=pinned).operator_acknowledgements,
            tuple(pinned),
        )

    def test_the_order_the_operator_wrote_is_preserved(self) -> None:
        pinned = ["c2", "c1"]
        self.assertEqual(
            self.load(operator_acknowledgements=pinned).operator_acknowledgements, ("c2", "c1")
        )

    # -- what it refuses ---------------------------------------------------
    def test_a_bare_string_is_not_a_list_of_ids(self) -> None:
        self.assertIn("must be a list", self.refusal("c1").message)

    def test_a_non_string_entry_is_refused(self) -> None:
        self.assertIn("operator_acknowledgements[0]", self.refusal([5107483039]).message)

    def test_an_empty_entry_is_refused(self) -> None:
        self.assertIn("operator_acknowledgements[0]", self.refusal([""]).message)

    def test_an_entry_carrying_whitespace_is_refused(self) -> None:
        """An id with a space in it can never match one GitHub assigned."""
        for value in ("c1 c2", " c1", "c1\n", "c1\tc2"):
            with self.subTest(value=value):
                self.assertIn("no whitespace", self.refusal([value]).message)

    def test_an_over_long_entry_is_refused(self) -> None:
        self.assertIn("operator_acknowledgements[0]", self.refusal(["c" * 201]).message)

    def test_a_wildcard_or_path_shaped_pattern_is_refused(self) -> None:
        """The field is ids; nothing with pattern syntax in it is an id."""
        for value in ("*", "karanagent1/*", "^karanagent1$", "c1,c2"):
            with self.subTest(value=value):
                self.assertIsInstance(self.refusal([value]), ConfigError)

    def test_the_same_id_twice_is_refused(self) -> None:
        error = self.refusal(["c1", "c1"])
        self.assertIn("same artifact twice", error.message)
        self.assertEqual(error.evidence["artifact_id"], "c1")

    def test_more_than_the_bound_is_refused(self) -> None:
        too_many = [f"c{index}" for index in range(MAX_OPERATOR_ACKNOWLEDGEMENTS + 1)]
        error = self.refusal(too_many)
        self.assertEqual(error.evidence["limit"], MAX_OPERATOR_ACKNOWLEDGEMENTS)

    def test_a_malformed_entry_is_not_echoed_back(self) -> None:
        """Operator-supplied text of unknown provenance; the index names it."""
        error = self.refusal(["ghp_0123456789abcdef ohno"])
        self.assertEqual(error.evidence, {"index": 0})
        self.assertNotIn("ghp_", json.dumps(error.evidence))

    def test_an_unknown_neighbouring_key_is_still_rejected(self) -> None:
        """The new field does not open the top level to typos."""
        with self.assertRaises(ConfigError):
            self.load(operator_acknowledgments=["c1"])

    # -- the seam is auditable before launch -------------------------------
    def test_check_config_names_every_pinned_id(self) -> None:
        path = self.tmp / "pinned.json"
        path.write_text(
            json.dumps(self.payload(operator_acknowledgements=["c1", "review:r9"])),
            encoding="utf-8",
        )

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(["check-config", "--config", str(path)])

        printed = buffer.getvalue()
        self.assertEqual(code, 0, "a pinned id is a note, not a rejection")
        self.assertIn("note: 2 operator-pinned acknowledgement post id(s)", printed)
        self.assertIn("c1, review:r9", printed)

    def test_check_config_says_nothing_when_nothing_is_pinned(self) -> None:
        path = self.tmp / "plain.json"
        path.write_text(json.dumps(self.payload()), encoding="utf-8")

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
            cli.main(["check-config", "--config", str(path)])

        self.assertNotIn("operator-pinned", buffer.getvalue())


class PinnedShapeHarness(LoopHarness):
    """The PAPI-101 conversation, seeded before any lane can publish.

    Both configured publishing logins are the ones the live pilot uses, and the
    reconciliation posts are written under the builder login exactly as the
    operator's own identity would write them. The ids are the doubles' immutable
    ids, and they are read off the seeded posts rather than typed, because what
    the config pins has to be the post that exists.
    """

    def seed(self, *, mapped_body: str | None = None) -> None:
        self.first = self.remote.comment(FIRST_PROSE, author=HUMAN)
        self.second = self.remote.comment(SECOND_PROSE, author=HUMAN)
        self.mapped = self.remote.comment(
            mapped_body
            if mapped_body is not None
            else f"{ack(self.first.identifier)}\n{ack(self.second.identifier)}\n{RESIDUAL_PROSE}",
            author=BUILDER_LOGIN,
        )
        self.pure = self.remote.comment(ack(self.mapped.identifier), author=BUILDER_LOGIN)

    def unresolved_ids(self, result) -> list[str]:
        return [item["artifact_id"] for item in result.evidence["evidence"]["unresolved"]]

    def acknowledged(self, result) -> list[str]:
        return list(result.evidence["evidence"]["acknowledged"])

    def builder_calls(self) -> list[object]:
        return [call for call in self.runner.calls if call.argv[0] == "lane-builder"]

    def assert_stopped_before_any_fix(self, result) -> None:
        """A stop here spends no attempt and publishes nothing as the builder."""
        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertNotEqual(result.outcome, MERGE_READY)
        self.assertEqual(result.reason, "human-feedback")
        self.assertEqual(result.attempts_used, 0)
        self.assertEqual(self.builder_calls(), [], "the builder lane was launched")
        self.assertEqual(self.remote.head, HEAD_A, "something pushed to the PR")
        # Only the two posts the operator seeded carry the builder login; no fix
        # comment, and nothing else this run wrote, was published as the builder.
        self.assertEqual(
            [item.identifier for item in self.remote.comments if item.author == BUILDER_LOGIN],
            [self.mapped.identifier, self.pure.identifier],
            "a lane published under the builder login",
        )


class PinnedAcknowledgementLoopTests(PinnedShapeHarness):
    """The live two-publisher shape, proved through the shipped loop."""

    def test_both_pinned_posts_reconcile_the_conversation(self) -> None:
        """The positive case: the mapped post clears the prose, then is cleared."""
        self.seed()
        loop = self.build(
            operator_acknowledgements=[self.mapped.identifier, self.pure.identifier]
        )
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertEqual(result.head, HEAD_A)
        self.assertEqual(
            sorted(self.config.operator_acknowledgements),
            sorted([self.mapped.identifier, self.pure.identifier]),
        )

    def test_the_unpinned_default_still_deadlocks_rather_than_clearing(self) -> None:
        """PAPI-101 itself: every publisher-authored post is refused authority."""
        self.seed()
        loop = self.build()
        self.review_round(HEAD_A)

        result = loop.run()

        self.assert_stopped_before_any_fix(result)
        self.assertEqual(self.acknowledged(result), [])
        self.assertEqual(
            self.unresolved_ids(result),
            [
                self.first.identifier,
                self.second.identifier,
                self.mapped.identifier,
                self.pure.identifier,
            ],
        )
        self.assertEqual(result.evidence["evidence"]["operator_pinned_acknowledgements"], [])

    def test_omitting_the_later_pure_acknowledgement_stops_the_run(self) -> None:
        """Its prose is cleared, but the mapped post's own residual is not."""
        self.seed()
        loop = self.build(operator_acknowledgements=[self.mapped.identifier])
        self.review_round(HEAD_A)

        result = loop.run()

        self.assert_stopped_before_any_fix(result)
        self.assertEqual(
            self.acknowledged(result), [self.first.identifier, self.second.identifier]
        )
        self.assertEqual(
            self.unresolved_ids(result), [self.mapped.identifier, self.pure.identifier]
        )
        self.assertIn(
            RESIDUAL_PROSE, result.evidence["evidence"]["unresolved"][0]["excerpt"]
        )

    def test_omitting_the_mapped_post_leaves_the_original_prose_unresolved(self) -> None:
        self.seed()
        loop = self.build(operator_acknowledgements=[self.pure.identifier])
        self.review_round(HEAD_A)

        result = loop.run()

        self.assert_stopped_before_any_fix(result)
        self.assertEqual(
            self.unresolved_ids(result), [self.first.identifier, self.second.identifier]
        )
        self.assertEqual(self.acknowledged(result), [self.mapped.identifier])

    def test_changing_the_pinned_body_clears_only_what_still_parses(self) -> None:
        """A pin authorizes a post to be read, never a line to be forgiven."""
        self.seed()
        # The same post, with one acknowledgement line mistyped as the double
        # space a human actually produces.
        self.remote.comments[2] = Comment(
            identifier=self.mapped.identifier,
            author=BUILDER_LOGIN,
            body=(
                f"{ACKNOWLEDGEMENT}  {self.first.identifier}\n"
                f"{ack(self.second.identifier)}\n{RESIDUAL_PROSE}"
            ),
            url=self.mapped.url,
            created_at=self.mapped.created_at,
        )
        loop = self.build(
            operator_acknowledgements=[self.mapped.identifier, self.pure.identifier]
        )
        self.review_round(HEAD_A)

        result = loop.run()

        self.assert_stopped_before_any_fix(result)
        self.assertEqual(self.unresolved_ids(result), [self.first.identifier])
        self.assertNotIn(self.first.identifier, self.acknowledged(result))

    def test_an_unpinned_publisher_acknowledgement_clears_nothing(self) -> None:
        """One more human comment, answered by the reviewer login nobody pinned."""
        self.seed()
        stray = self.remote.comment("and one more thing", author=HUMAN)
        rogue = self.remote.comment(ack(stray.identifier), author=REVIEWER_LOGIN)
        loop = self.build(
            operator_acknowledgements=[self.mapped.identifier, self.pure.identifier]
        )
        self.review_round(HEAD_A)

        result = loop.run()

        self.assert_stopped_before_any_fix(result)
        self.assertEqual(
            self.unresolved_ids(result), [stray.identifier, rogue.identifier]
        )
        self.assertNotIn(stray.identifier, self.acknowledged(result))

    def test_a_pinned_id_that_names_no_post_authorizes_nothing(self) -> None:
        self.seed()
        loop = self.build(operator_acknowledgements=["IC_comment404", "review:r404"])
        self.review_round(HEAD_A)

        result = loop.run()

        self.assert_stopped_before_any_fix(result)
        self.assertEqual(self.acknowledged(result), [])
        self.assertEqual(
            result.evidence["evidence"]["operator_pinned_acknowledgements"],
            ["IC_comment404", "review:r404"],
        )

    def test_a_pin_that_reads_like_an_author_rule_is_matched_as_an_id(self) -> None:
        """Nothing in the field is ever interpreted; it is compared to ids.

        ``author:karanagent1`` is a string the id grammar admits, and that is
        deliberately not a way to spell "trust this login": it is compared to the
        immutable ids on the PR, matches none of them, and authorizes nothing.
        """
        self.seed()
        loop = self.build(operator_acknowledgements=[f"author:{REVIEWER_LOGIN}", BUILDER_LOGIN])
        self.review_round(HEAD_A)

        result = loop.run()

        self.assert_stopped_before_any_fix(result)
        self.assertEqual(self.acknowledged(result), [])
        self.assertEqual(
            self.unresolved_ids(result),
            [
                self.first.identifier,
                self.second.identifier,
                self.mapped.identifier,
                self.pure.identifier,
            ],
        )

    def test_a_publishing_lane_cannot_self_clear_during_the_run(self) -> None:
        """A lane posting its own acknowledgement while it runs is still refused.

        The pinned ids are the two posts that existed before launch. Reviewer A
        then publishes an extra comment under the reviewer login acknowledging
        the one piece of feedback nothing else answers — the shape a lane would
        use to clear the objection aimed at it — and the run still stops.
        """
        self.seed()
        stray = self.remote.comment("this one is for the lane", author=HUMAN)
        loop = self.build(
            operator_acknowledgements=[self.mapped.identifier, self.pure.identifier]
        )
        self.script.add(
            "lane-reviewer-A",
            reviewer_output(HEAD_A),
            after=lambda: self.remote.comment(
                ack(stray.identifier), author=REVIEWER_LOGIN
            ),
        )
        self.script.add("lane-reviewer-B", reviewer_output(HEAD_A))

        result = loop.run()

        self.assert_stopped_before_any_fix(result)
        self.assertIn(stray.identifier, self.unresolved_ids(result))
        self.assertNotIn(stray.identifier, self.acknowledged(result))

    def test_no_lane_publication_of_this_run_acknowledges_anything(self) -> None:
        """What the lanes publish is evidence, never authorization.

        The three reviewer artifacts this run relays are the only things it
        publishes on an unpinned stop, and none of them can clear feedback: they
        are run-owned, so the pin cannot reach them and the login cannot either.
        The count is asserted too, because "one artifact per lane, once" is what
        makes "nothing else was published" a fact rather than an impression.
        """
        self.seed()
        loop = self.build()
        self.review_round(HEAD_A)

        result = loop.run()

        self.assert_stopped_before_any_fix(result)
        published = [
            item.identifier
            for item in self.remote.comments
            if item.author == REVIEWER_LOGIN
        ]
        self.assertEqual(len(published), len(REVIEWER_LANES))
        for identifier in published:
            self.assertNotIn(identifier, self.acknowledged(result))
            self.assertNotIn(identifier, self.unresolved_ids(result))

    def test_no_pinned_conversation_reaches_a_lane_as_text(self) -> None:
        """Pinned or not, the conversation is evidence and never lane input."""
        self.seed()
        loop = self.build(operator_acknowledgements=[self.mapped.identifier])
        self.review_round(HEAD_A)

        loop.run()

        for call in self.runner.calls:
            joined = " ".join(call.argv)
            self.assertNotIn(RESIDUAL_PROSE, joined)
            self.assertNotIn(FIRST_PROSE, joined)


class UnpinnedFixCycleTests(PinnedShapeHarness):
    """The other guard point: an unanswered conversation before a fix attempt."""

    def test_a_blocking_head_with_unpinned_feedback_launches_no_builder(self) -> None:
        """The stop lands before the attempt opens, with the builder unscripted.

        The reviewer lanes have already run and published by then — they are what
        produced the blocking verdict, and the mission fixes the two guard points
        this check runs at — so what is proved here is the boundary that matters:
        no attempt is spent, no builder process starts, its scripted output is
        never consumed, and nothing reaches the PR under the builder login.
        """
        self.seed()
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["null-deref"]),
            after=lambda: self.remote.push(HEAD_B, comment=fix_comment(HEAD_B)),
        )

        result = loop.run()

        self.assert_stopped_before_any_fix(result)
        self.assertFalse(self.script.exhausted, "the builder script was consumed")

    def test_pinning_both_posts_lets_the_same_head_open_its_fix_attempt(self) -> None:
        """The control: the only thing that changed is the two authorized ids."""
        self.seed()
        loop = self.build(
            operator_acknowledgements=[self.mapped.identifier, self.pure.identifier]
        )
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["null-deref"]),
            after=lambda: self.remote.push(HEAD_B, comment=fix_comment(HEAD_B)),
        )
        self.review_round(HEAD_B)

        result = loop.run()

        self.assertEqual(result.attempts_used, 1)
        self.assertEqual(result.head, HEAD_B)
        self.assertEqual(len(self.builder_calls()), 1)


class RealConfigFileTests(PinnedShapeHarness):
    """The same proof, through a config file on disk and ``RunConfig.load``.

    Everything above builds its config in memory. An operator does not: they
    write JSON, run ``check-config``, and then run the loop over that file. This
    class exercises that path end to end, so a field that parses in a mapping but
    never survives a real load — or never reaches the reconciler — is caught
    where it would actually be met.
    """

    def written_config(self, pinned: list[str]) -> Path:
        payload = {
            "schema_version": 2,
            "repo": "example/repo",
            "pr": 7,
            "branch": BRANCH,
            "base": "main",
            "governing_issues": [GOVERNING_ISSUE],
            "source_repo": str(self.source_repo),
            "worktree_root": str(self.tmp / "worktrees"),
            "state_file": str(self.tmp / "state.json"),
            "lock_file": str(self.tmp / "run.lock"),
            "gates": [],
            "operator_acknowledgements": pinned,
            "reviewers": [
                reviewer_lane(name, role, program) for name, role, program in REVIEWER_LANES
            ],
            "builder": {
                "argv": [
                    "lane-builder",
                    "--blockers",
                    "{blockers_file}",
                    "--mode",
                    "{mode}",
                    "--head",
                    "{head}",
                ],
                "signature": SIGNATURE,
                "comment_author": BUILDER_LOGIN,
            },
        }
        path = self.tmp / "run.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def loop_from(self, path: Path) -> ProverLoop:
        """The loop the CLI builds, over a config it really loaded from disk."""
        config = RunConfig.load(path)
        self.config = config
        source = SourceRepo(runner=self.runner, path=config.source_repo)
        return ProverLoop(
            config,
            runner=self.runner,
            github=self.github,
            worktrees=WorktreeProvider(source, config.worktree_root),
            scratch_root=self.tmp / "scratch",
        )

    def test_a_loaded_file_carries_its_pinned_ids_into_reconciliation(self) -> None:
        self.seed()
        path = self.written_config([self.mapped.identifier, self.pure.identifier])

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(["check-config", "--config", str(path)])
        self.assertEqual(code, 0)
        self.assertIn("operator-pinned acknowledgement", buffer.getvalue())

        loop = self.loop_from(path)
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)

    def test_the_same_file_without_the_ids_stops_the_run(self) -> None:
        self.seed()
        loop = self.loop_from(self.written_config([]))
        self.review_round(HEAD_A)

        result = loop.run()

        self.assert_stopped_before_any_fix(result)
        self.assertEqual(self.acknowledged(result), [])


if __name__ == "__main__":  # pragma: no cover - parity with the other modules
    unittest.main()
