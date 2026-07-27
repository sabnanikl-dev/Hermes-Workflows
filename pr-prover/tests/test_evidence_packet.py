"""The frozen evidence a credential-free reviewer judges from.

The lane cannot reach GitHub, so the packet is the only thing standing between
"this reviewer read the PR" and "this reviewer reviewed nothing and said so
confidently". Three separable claims, kept separable here:

* the packet says what this run actually read (its surfaces and their counts);
* it says how completely it read each one, rather than presenting a first page
  as a whole PR;
* it is bound to one repository, PR, base, head, and lane, and a packet bound
  to anything else stops the lane instead of being reviewed.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from _support import (
    GOVERNING_ISSUE,
    GOVERNING_ISSUE_BODY,
    HEAD_A,
    HEAD_B,
    PR_BODY,
    REVIEWER_LOGIN,
    reviewer_output,
)
from pr_prover.errors import EvidencePacketError
from pr_prover.github import (
    CheckRun,
    Comment,
    GoverningIssue,
    InlineComment,
    LinkedIssue,
    PullRequest,
    ReviewEvidence,
)
from pr_prover.loop import MERGE_READY, NEEDS_KARAN
from pr_prover.packet import (
    MAX_BODY_BYTES,
    MAX_PACKET_BYTES,
    PACKET_SCHEMA_VERSION,
    REQUIRED_SURFACES,
    build_packet,
    packet_binding,
    read_packet,
    write_packet,
)
from test_loop import LoopHarness

REPO = "example/repo"


def pull_request(
    *, number: int = 7, head: str = HEAD_A, base: str = "main", body: str = PR_BODY
) -> PullRequest:
    return PullRequest(
        number=number,
        state="OPEN",
        is_draft=True,
        title="example",
        url="https://example.invalid/pull/7",
        head_ref_name="feat/example",
        head_ref_oid=head,
        base_ref_name=base,
        body=body,
    )


def governing(body: str = GOVERNING_ISSUE_BODY) -> ReviewEvidence:
    """The ordinary shipped case: one configured contract, read whole."""
    return ReviewEvidence(
        governing_issues=(
            GoverningIssue(number=1, title="mission", state="OPEN", body=body),
        ),
        governing_issues_complete=True,
    )


class PacketContentTests(unittest.TestCase):
    def build(self, **overrides):
        fields = {
            "pull": pull_request(),
            "repo": REPO,
            "head": HEAD_A,
            "sequence": 1,
            "reviewer": "A",
            "role": "reviewer-a",
            "comments": (),
            "reviews": (),
            "evidence": ReviewEvidence(),
        }
        fields.update(overrides)
        return build_packet(**fields)

    def test_the_binding_names_repo_pr_base_head_and_sequence(self) -> None:
        self.assertEqual(
            packet_binding(repo=REPO, pr=7, base="main", head=HEAD_A, sequence=3),
            f"REPO={REPO} PR=7 BASE=main HEAD={HEAD_A} SEQUENCE=3",
        )

    def test_a_packet_carries_every_surface_a_reviewer_needs(self) -> None:
        payload = self.build(
            comments=(Comment(identifier="IC_1", author="someone", body="a note"),),
            reviews=(
                Comment(
                    identifier="review:1",
                    author=REVIEWER_LOGIN,
                    body="a review",
                    kind="review",
                    commit_id=HEAD_A,
                    state="CHANGES_REQUESTED",
                ),
            ),
            evidence=ReviewEvidence(
                inline_comments=(
                    InlineComment(
                        identifier="inline:1",
                        author="someone",
                        body="this line",
                        path="src/thing.py",
                        line=12,
                    ),
                ),
                check_runs=(CheckRun(name="tests", status="completed", conclusion="success"),),
                linked_issues=(LinkedIssue(number=1, title="mission", state="OPEN"),),
                governing_issues=(
                    GoverningIssue(
                        number=GOVERNING_ISSUE,
                        title="mission",
                        state="OPEN",
                        body=GOVERNING_ISSUE_BODY,
                    ),
                ),
                inline_comments_complete=True,
                check_runs_complete=True,
                linked_issues_complete=True,
                governing_issues_complete=True,
                reviews_complete=True,
            ),
        )
        surfaces = payload["surfaces"]
        self.assertEqual(
            sorted(surfaces),
            [
                "check_runs",
                "conversation_comments",
                "governing_issues",
                "inline_comments",
                "linked_issues",
                "pull_request_body",
                "reviews",
            ],
        )
        self.assertEqual(set(surfaces), set(REQUIRED_SURFACES))
        for name, surface in surfaces.items():
            with self.subTest(surface=name):
                self.assertEqual(surface["count"], len(surface["items"]))
                self.assertEqual(surface["count"], 1)
                self.assertTrue(surface["read_as"])
        self.assertEqual(surfaces["reviews"]["items"][0]["commit_id"], HEAD_A)
        self.assertEqual(surfaces["inline_comments"]["items"][0]["path"], "src/thing.py")
        self.assertEqual(surfaces["check_runs"]["items"][0]["conclusion"], "success")
        self.assertEqual(surfaces["linked_issues"]["items"][0]["number"], 1)

    def test_the_packet_carries_the_pr_body_and_the_governing_contract(self) -> None:
        """PAPI90-FINAL-P1-002: the two documents the prompt says to read.

        The lane is told to check the PR body for stale claims and to judge
        scope against the issue's acceptance criteria. Before this it was handed
        neither: the PR metadata had no body, and a PR using ``Refs #1`` closes
        nothing, so ``linked_issues`` supplied no contract either.
        """
        payload = self.build(evidence=governing())
        surfaces = payload["surfaces"]

        stated = surfaces["pull_request_body"]
        self.assertEqual(stated["count"], 1)
        self.assertEqual(stated["items"][0]["body"], PR_BODY)
        self.assertEqual(stated["items"][0]["number"], 7)
        self.assertTrue(stated["complete"])

        contract = surfaces["governing_issues"]
        self.assertEqual(contract["count"], 1)
        self.assertEqual(contract["items"][0]["number"], GOVERNING_ISSUE)
        self.assertEqual(contract["items"][0]["body"], GOVERNING_ISSUE_BODY)
        self.assertTrue(contract["complete"])
        # ...and the contract is not the PR's claim about itself. Both are
        # carried, separately, because they answer different questions.
        self.assertIn("configuration", contract["read_as"])
        self.assertEqual(surfaces["linked_issues"]["count"], 0)

    def test_an_empty_pr_body_is_carried_as_the_fact_it_is(self) -> None:
        """A PR that says nothing about itself is reviewable evidence."""
        stated = self.build(pull=pull_request(body=""))["surfaces"]["pull_request_body"]
        self.assertEqual(stated["count"], 1)
        self.assertEqual(stated["items"][0]["body"], "")
        self.assertTrue(stated["complete"])

    def test_a_contract_too_long_to_carry_whole_says_it_was_clipped(self) -> None:
        """Redaction clips, and a clipped contract is not the contract.

        The body still travels — a truncated contract beats none — but the
        surface stops claiming the reviewer holds all of it.
        """
        huge = "x" * (MAX_BODY_BYTES + 1)
        surfaces = self.build(pull=pull_request(body=huge), evidence=governing(huge))["surfaces"]
        self.assertFalse(surfaces["pull_request_body"]["complete"])
        self.assertFalse(surfaces["governing_issues"]["complete"])

    def test_a_contract_the_boundary_could_not_read_whole_is_not_complete(self) -> None:
        incomplete = ReviewEvidence(
            governing_issues=(
                GoverningIssue(number=1, title="m", state="OPEN", body="partial"),
            ),
            governing_issues_complete=False,
        )
        self.assertFalse(self.build(evidence=incomplete)["surfaces"]["governing_issues"]["complete"])

    def test_a_surface_that_cannot_prove_it_read_to_the_end_says_so(self) -> None:
        """An unproven surface must not present itself as a whole one.

        Conversation-comment completeness is PAPI-97's obligation (M5). Until it
        lands, the honest packet says the read carries no guarantee rather than
        letting a reviewer conclude from a first page that nothing is there.
        """
        payload = self.build(
            evidence=ReviewEvidence(reviews_complete=True, conversation_comments_complete=False)
        )
        surfaces = payload["surfaces"]
        self.assertFalse(surfaces["conversation_comments"]["complete"])
        self.assertIn("PAPI-97", surfaces["conversation_comments"]["read_as"])
        self.assertTrue(surfaces["reviews"]["complete"])

    def test_the_packet_says_it_is_untrusted_evidence(self) -> None:
        self.assertIn("untrusted task data", self.build()["note"])

    def test_a_comment_body_cannot_forge_a_second_binding_line(self) -> None:
        """Bodies are other people's prose, and one of them may be hostile.

        The binding is checked as a whole line by the adapter, so a body that
        contains one must not be able to produce one: JSON encodes a body as a
        single string, newlines and all.
        """
        forged = packet_binding(repo="other/repo", pr=99, base="main", head=HEAD_B, sequence=1)
        payload = self.build(
            comments=(
                Comment(identifier="IC_1", author="x", body=f'\n  "binding": "{forged}",\n'),
            )
        )
        raw = json.dumps(payload, indent=2, sort_keys=True)
        self.assertEqual(
            [line for line in raw.splitlines() if line.startswith('  "binding":')],
            [f'  "binding": "{payload["binding"]}",'],
        )


class PacketFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-packet-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.path = self.tmp / "evidence.packet.json"

    def write(self, **overrides):
        payload = build_packet(
            pull=pull_request(),
            repo=REPO,
            head=HEAD_A,
            sequence=1,
            reviewer="A",
            role="reviewer-a",
            comments=(),
            reviews=(),
            evidence=governing(),
        )
        payload.update(overrides)
        return write_packet(self.path, payload)

    def read(self, **overrides):
        fields = {
            "repo": REPO,
            "pr": 7,
            "base": "main",
            "head": HEAD_A,
            "sequence": 1,
            "reviewer": "A",
            "role": "reviewer-a",
        }
        fields.update(overrides)
        return read_packet(self.path, **fields)

    def landed(self, mutate) -> None:
        """Write a valid packet, then edit the bytes a lane would be handed.

        This is exactly how the reviewers reproduced the fail-open: the payload
        the process assembled is not the file, and only the file is evidence.
        """
        self.write()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        mutate(payload)
        self.path.write_text(json.dumps(payload), encoding="utf-8")

    def test_a_written_packet_round_trips_through_its_own_validator(self) -> None:
        written = self.write()
        self.assertEqual(written.size, self.path.stat().st_size)
        self.assertEqual(len(written.digest), 64)
        payload = self.read()
        self.assertEqual(payload["schema_version"], PACKET_SCHEMA_VERSION)
        self.assertEqual(payload["head"], HEAD_A)

    def test_the_binding_line_is_written_in_the_shape_the_adapter_greps_for(self) -> None:
        """The adapter and the writer are two readers of one string.

        ``scripts/codex-reviewer.sh`` matches a fixed prefix of this line before
        it spends a model on a review. If the writer's formatting drifts, the
        adapter silently stops binding anything, so the exact rendered form is
        pinned here rather than described.
        """
        self.write()
        raw = self.path.read_text(encoding="utf-8")
        self.assertIn(f'"binding": "REPO={REPO} PR=7 BASE=main HEAD={HEAD_A} ', raw)

    def test_a_secret_that_reached_a_body_is_redacted_before_it_is_written(self) -> None:
        """The packet gets the same recursive scrub the report and blockers do."""
        self.write(
            surfaces={
                "conversation_comments": {
                    "complete": False,
                    "read_as": "test",
                    "count": 1,
                    "items": [{"body": "token ghp_0123456789abcdefghijklmnopqrstuvwxyz"}],
                }
            }
        )
        self.assertNotIn("ghp_0123456789abcdefghijklmnopqrstuvwxyz", self.path.read_text())

    def test_a_packet_that_never_landed_stops_the_lane(self) -> None:
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertIn("no frozen evidence packet", caught.exception.message)
        self.assertEqual(caught.exception.reason, "evidence-packet")

    def test_an_empty_packet_is_not_a_pull_request_with_nothing_on_it(self) -> None:
        self.path.write_text("   \n", encoding="utf-8")
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertIn("empty", caught.exception.message)

    def test_a_truncated_or_unparsable_packet_stops_the_lane(self) -> None:
        self.write()
        self.path.write_text(self.path.read_text(encoding="utf-8")[:80], encoding="utf-8")
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertIn("not readable JSON", caught.exception.message)

    def test_a_json_document_that_is_not_an_object_stops_the_lane(self) -> None:
        self.path.write_text("[]\n", encoding="utf-8")
        with self.assertRaises(EvidencePacketError):
            self.read()

    def test_another_tools_json_at_this_path_stops_the_lane(self) -> None:
        self.write()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        payload["schema_version"] = 99
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertIn("packet schema", caught.exception.message)

    def test_a_packet_bound_to_another_repo_pr_base_head_or_lane_stops_the_lane(self) -> None:
        """A packet an earlier cycle left behind is the one that would slip through."""
        self.write()
        for label, overrides in (
            ("head", {"head": HEAD_B}),
            ("pr", {"pr": 8}),
            ("repo", {"repo": "someone/else"}),
            ("base", {"base": "develop"}),
            ("sequence", {"sequence": 2}),
        ):
            with self.subTest(bound_to=label):
                with self.assertRaises(EvidencePacketError) as caught:
                    self.read(**overrides)
                self.assertIn("not bound to", caught.exception.message)

    def test_a_binding_line_that_disagrees_with_its_own_fields_stops_the_lane(self) -> None:
        """The adapter greps one line; anything structural reads the fields.

        A packet that satisfies one and not the other is two documents, and the
        reviewer would be handed whichever its reader happened to trust.
        """
        self.write()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        payload["head"] = HEAD_B
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertIn("disagrees with its own binding", caught.exception.message)
        self.assertEqual(caught.exception.evidence["field"], "head")

    def test_a_packet_with_no_surfaces_is_not_evidence(self) -> None:
        self.write(surfaces={})
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertIn("no GitHub surfaces", caught.exception.message)

    # -- former red: bound, parseable, and still not evidence ------------------
    #
    # Every case below is one the reviewers wrote by hand: a file that keeps the
    # canonical binding the adapter greps for, and the fields a structural
    # reader indexes, while removing or corrupting the evidence itself. Each one
    # used to be accepted, and two of them reached `merge-ready`.

    def test_a_boolean_where_an_integer_belongs_is_not_that_integer(self) -> None:
        """``True == 1`` in Python, and JSON ``true`` is not schema version 1."""
        for field in ("schema_version", "sequence"):
            with self.subTest(field=field):
                self.landed(lambda payload, key=field: payload.__setitem__(key, True))
                with self.assertRaises(EvidencePacketError):
                    self.read()

    def test_a_sequence_that_is_not_a_positive_integer_stops_the_lane(self) -> None:
        for label, value in (("zero", 0), ("negative", -1), ("text", "1"), ("float", 1.0)):
            with self.subTest(sequence=label):
                self.landed(lambda payload, item=value: payload.__setitem__("sequence", item))
                with self.assertRaises(EvidencePacketError):
                    self.read(sequence=value if isinstance(value, int) else 1)

    def test_a_packet_missing_a_required_surface_stops_the_lane(self) -> None:
        """A surface a reviewer is told it has, and does not, reads as silence."""
        for name in sorted(REQUIRED_SURFACES):
            with self.subTest(surface=name):
                self.landed(lambda payload, key=name: payload["surfaces"].pop(key))
                with self.assertRaises(EvidencePacketError) as caught:
                    self.read()
                self.assertEqual(caught.exception.evidence["missing_surfaces"], [name])

    def test_a_surface_this_tool_does_not_write_stops_the_lane(self) -> None:
        self.landed(lambda payload: payload["surfaces"].update({"telegrams": {}}))
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertEqual(caught.exception.evidence["unknown_surfaces"], ["telegrams"])

    def test_a_surface_that_does_not_declare_its_own_shape_stops_the_lane(self) -> None:
        cases = (
            ("missing complete", lambda surface: surface.pop("complete")),
            ("boolean-shaped complete", lambda surface: surface.update({"complete": "yes"})),
            ("numeric complete", lambda surface: surface.update({"complete": 1})),
            ("missing read_as", lambda surface: surface.pop("read_as")),
            ("empty read_as", lambda surface: surface.update({"read_as": "   "})),
            ("non-text read_as", lambda surface: surface.update({"read_as": 7})),
            ("missing count", lambda surface: surface.pop("count")),
            ("boolean count", lambda surface: surface.update({"count": True})),
            ("negative count", lambda surface: surface.update({"count": -1})),
            ("text count", lambda surface: surface.update({"count": "0"})),
            ("missing items", lambda surface: surface.pop("items")),
            ("items that are not a list", lambda surface: surface.update({"items": {}})),
        )
        for label, mutate in cases:
            with self.subTest(surface=label):
                self.landed(lambda payload, edit=mutate: edit(payload["surfaces"]["reviews"]))
                with self.assertRaises(EvidencePacketError) as caught:
                    self.read()
                self.assertEqual(caught.exception.evidence["surface"], "reviews")

    def test_a_count_that_disagrees_with_its_own_items_stops_the_lane(self) -> None:
        """One of the two numbers is wrong and the file cannot say which."""
        self.landed(
            lambda payload: payload["surfaces"]["conversation_comments"].update({"count": 4})
        )
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertIn("counts items it does not carry", caught.exception.message)
        self.assertEqual(caught.exception.evidence["items"], 0)

    def test_a_packet_frozen_for_another_lane_stops_this_one(self) -> None:
        """The sequence binds a lane; the packet also says which lane in words."""
        for field, value in (("reviewer", "B"), ("role", "reviewer-b")):
            with self.subTest(frozen_for=field):
                self.landed(
                    lambda payload, key=field, item=value: payload["frozen_for"].update({key: item})
                )
                with self.assertRaises(EvidencePacketError) as caught:
                    self.read()
                self.assertIn("frozen for another lane", caught.exception.message)
                self.assertEqual(caught.exception.evidence["field"], f"frozen_for.{field}")

    def test_a_packet_that_does_not_say_which_lane_it_is_for_stops_the_lane(self) -> None:
        for label, value in (("missing", None), ("not an object", "reviewer-a")):
            with self.subTest(frozen_for=label):
                self.landed(
                    lambda payload, item=value: (
                        payload.pop("frozen_for")
                        if item is None
                        else payload.__setitem__("frozen_for", item)
                    )
                )
                with self.assertRaises(EvidencePacketError) as caught:
                    self.read()
                self.assertIn("which lane", caught.exception.message)

    def test_a_field_of_the_wrong_type_cannot_satisfy_the_binding(self) -> None:
        """The adapter greps a string; a structural reader indexes fields."""
        for field, value in (("repo", 7), ("head", None), ("base", ["main"]), ("pr", "7")):
            with self.subTest(field=field):
                self.landed(lambda payload, key=field, item=value: payload.__setitem__(key, item))
                with self.assertRaises(EvidencePacketError) as caught:
                    self.read()
                self.assertEqual(caught.exception.evidence["field"], field)

    # -- former red: the envelope is right and the contract inside it is not ---
    #
    # Everything above proves the surfaces are shaped like surfaces. These prove
    # the two contract surfaces carry the documents the reviewer prompt names.
    # Each case keeps the binding, the required surfaces, the completeness flags
    # and the counts — and hands the lane a PR body it does not have, a contract
    # body that is missing or ``null``, or a contract for another issue entirely.

    def test_a_pull_request_body_record_without_body_text_stops_the_lane(self) -> None:
        """The prompt tells the lane to check this document for stale claims."""
        cases = (
            ("missing body field", lambda record: record.pop("body")),
            ("null body", lambda record: record.update({"body": None})),
            ("non-text body", lambda record: record.update({"body": 7})),
            ("body that is a list", lambda record: record.update({"body": ["text"]})),
        )
        for label, mutate in cases:
            with self.subTest(pull_request_body=label):
                self.landed(
                    lambda payload, edit=mutate: edit(
                        payload["surfaces"]["pull_request_body"]["items"][0]
                    )
                )
                with self.assertRaises(EvidencePacketError) as caught:
                    self.read()
                self.assertIn("carries no description text", caught.exception.message)
                self.assertEqual(caught.exception.evidence["surface"], "pull_request_body")

    def test_a_pull_request_body_belonging_to_another_pr_stops_the_lane(self) -> None:
        """A body is only the change's stated contract if it is this change's."""
        for label, value in (("another PR", 8), ("boolean", True), ("text", "7"), ("absent", None)):
            with self.subTest(number=label):
                self.landed(
                    lambda payload, item=value: payload["surfaces"]["pull_request_body"]["items"][
                        0
                    ].update({"number": item})
                )
                with self.assertRaises(EvidencePacketError) as caught:
                    self.read()
                self.assertIn("not this pull request's", caught.exception.message)
                self.assertEqual(caught.exception.evidence["expected"], 7)

    def test_more_than_one_pull_request_body_is_not_the_pull_request_body(self) -> None:
        """Two descriptions is one of them being the wrong one, silently."""
        self.landed(
            lambda payload: payload["surfaces"]["pull_request_body"].update(
                {
                    "count": 2,
                    "items": [
                        {"number": 7, "title": "example", "body": PR_BODY},
                        {"number": 7, "title": "example", "body": "and also this"},
                    ],
                }
            )
        )
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertIn("exactly one pull request body", caught.exception.message)

    def test_a_pull_request_body_record_that_is_not_an_object_stops_the_lane(self) -> None:
        self.landed(
            lambda payload: payload["surfaces"]["pull_request_body"].update({"items": [PR_BODY]})
        )
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertIn("is not a record", caught.exception.message)

    def test_a_governing_issue_without_a_contract_body_stops_the_lane(self) -> None:
        """A contract with no text is not a shorter contract; it is none."""
        cases = (
            ("missing body field", lambda record: record.pop("body")),
            ("null body", lambda record: record.update({"body": None})),
            ("non-text body", lambda record: record.update({"body": 1})),
        )
        for label, mutate in cases:
            with self.subTest(governing_issue=label):
                self.landed(
                    lambda payload, edit=mutate: edit(
                        payload["surfaces"]["governing_issues"]["items"][0]
                    )
                )
                with self.assertRaises(EvidencePacketError) as caught:
                    self.read()
                self.assertIn("carries no contract body", caught.exception.message)
                self.assertEqual(caught.exception.evidence["issue"], GOVERNING_ISSUE)

    def test_a_contract_for_an_issue_this_run_does_not_name_stops_the_lane(self) -> None:
        """Substitution is the case a well-formed envelope cannot show.

        The packet declares the issues the run configured. A record for #999
        keeps every count and flag intact while measuring the change against a
        document nobody chose, so the records are held to the declared numbers.
        """
        self.landed(
            lambda payload: payload["surfaces"]["governing_issues"]["items"][0].update(
                {"number": 999}
            )
        )
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertIn("does not carry the governing issues", caught.exception.message)
        self.assertEqual(caught.exception.evidence["expected"], [GOVERNING_ISSUE])
        self.assertEqual(caught.exception.evidence["found"], [999])

    def test_a_governing_issue_number_that_is_not_one_stops_the_lane(self) -> None:
        for label, value in (("boolean", True), ("zero", 0), ("negative", -1), ("text", "1")):
            with self.subTest(number=label):
                self.landed(
                    lambda payload, item=value: payload["surfaces"]["governing_issues"]["items"][
                        0
                    ].update({"number": item})
                )
                with self.assertRaises(EvidencePacketError) as caught:
                    self.read()
                self.assertIn("no usable issue number", caught.exception.message)

    def test_a_governing_record_that_is_not_an_object_stops_the_lane(self) -> None:
        self.landed(
            lambda payload: payload["surfaces"]["governing_issues"].update(
                {"items": [GOVERNING_ISSUE_BODY]}
            )
        )
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertIn("governing issue is not a record", caught.exception.message)

    def test_a_duplicated_or_reordered_contract_is_not_the_configured_one(self) -> None:
        """Order and multiplicity are part of what the configuration said."""
        both = [
            {"number": 1, "title": "mission", "state": "OPEN", "body": GOVERNING_ISSUE_BODY},
            {"number": 1, "title": "mission", "state": "OPEN", "body": GOVERNING_ISSUE_BODY},
        ]
        self.landed(
            lambda payload: payload["surfaces"]["governing_issues"].update(
                {"count": 2, "items": both}
            )
        )
        with self.assertRaises(EvidencePacketError) as caught:
            self.read()
        self.assertIn("does not carry the governing issues", caught.exception.message)

    def test_the_reader_holds_the_contract_to_the_numbers_the_caller_configured(self) -> None:
        """The loop passes the same tuple it handed GitHub; both must agree.

        Without this the packet is only self-consistent: a writer that named
        #999 in both places would be believed. The run's configuration is the
        authority, so it is what the records are measured against.
        """
        self.write()
        self.assertEqual(
            self.read(governing_issues=(GOVERNING_ISSUE,))["surfaces"]["governing_issues"][
                "items"
            ][0]["number"],
            GOVERNING_ISSUE,
        )
        for label, configured in (("another issue", (2,)), ("one too many", (1, 2))):
            with self.subTest(configured=label):
                with self.assertRaises(EvidencePacketError) as caught:
                    self.read(governing_issues=configured)
                self.assertIn("this run did not configure", caught.exception.message)
                self.assertEqual(caught.exception.evidence["configured"], list(configured))

    def test_a_packet_that_does_not_name_its_governing_issues_stops_the_lane(self) -> None:
        cases = (
            ("missing", lambda payload: payload.pop("governing_issue_numbers")),
            ("empty", lambda payload: payload.__setitem__("governing_issue_numbers", [])),
            ("not a list", lambda payload: payload.__setitem__("governing_issue_numbers", 1)),
            ("boolean", lambda payload: payload.__setitem__("governing_issue_numbers", [True])),
            ("zero", lambda payload: payload.__setitem__("governing_issue_numbers", [0])),
            ("text", lambda payload: payload.__setitem__("governing_issue_numbers", ["1"])),
            ("duplicated", lambda payload: payload.__setitem__("governing_issue_numbers", [1, 1])),
        )
        for label, mutate in cases:
            with self.subTest(governing_issue_numbers=label):
                self.landed(mutate)
                with self.assertRaises(EvidencePacketError) as caught:
                    self.read()
                self.assertIn("does not name the governing issues", caught.exception.message)

    def test_a_pr_that_says_nothing_about_itself_still_reaches_the_lane(self) -> None:
        """The strictness must not turn an honest empty description into a stop."""
        write_packet(
            self.path,
            build_packet(
                pull=pull_request(body=""),
                repo=REPO,
                head=HEAD_A,
                sequence=1,
                reviewer="A",
                role="reviewer-a",
                comments=(),
                reviews=(),
                evidence=governing(),
                governing_issues=(GOVERNING_ISSUE,),
            ),
        )
        payload = self.read(governing_issues=(GOVERNING_ISSUE,))
        self.assertEqual(payload["surfaces"]["pull_request_body"]["items"][0]["body"], "")

    def test_a_valid_packet_still_round_trips_after_all_of_that(self) -> None:
        """The strictness has to admit the packet this tool actually writes."""
        self.write()
        payload = self.read()
        self.assertEqual(set(payload["surfaces"]), set(REQUIRED_SURFACES))
        self.assertEqual(
            payload["surfaces"]["governing_issues"]["items"][0]["body"], GOVERNING_ISSUE_BODY
        )
        self.assertEqual(payload["surfaces"]["pull_request_body"]["items"][0]["body"], PR_BODY)

    def test_a_full_size_artifact_reaches_the_packet_intact(self) -> None:
        """The auditor reconciles A's and B's artifacts and cannot fetch them.

        Redaction clips as well as scrubs, and its default clip is sized for an
        evidence excerpt. A packet that truncated the artifacts it exists to
        carry would hand the auditor a different document from the one on the
        PR, so the clip is the largest artifact this tool will relay.
        """
        body = "ROLE=reviewer-a\n" + ("filler line\n" * 3000)
        self.assertGreater(len(body), 4000)
        write_packet(
            self.path,
            build_packet(
                pull=pull_request(),
                repo=REPO,
                head=HEAD_A,
                sequence=1,
                reviewer="Auditor",
                role="integration-auditor",
                comments=(Comment(identifier="IC_1", author=REVIEWER_LOGIN, body=body),),
                reviews=(),
                evidence=governing(),
            ),
        )
        landed = self.read(reviewer="Auditor", role="integration-auditor")["surfaces"][
            "conversation_comments"
        ]["items"][0]["body"]
        self.assertEqual(landed, body)
        self.assertNotIn("characters elided", landed)

    def test_an_oversized_packet_stops_rather_than_being_written(self) -> None:
        """A runaway surface is a stop, not a scratch directory nobody looks at."""
        huge = [
            {"id": f"IC_{index}", "author": "someone", "body": "x" * 4096}
            for index in range(1200)
        ]
        with self.assertRaises(EvidencePacketError) as caught:
            self.write(
                surfaces={
                    "conversation_comments": {
                        "complete": False,
                        "read_as": "test",
                        "count": len(huge),
                        "items": huge,
                    }
                }
            )
        self.assertEqual(caught.exception.evidence["limit"], MAX_PACKET_BYTES)


class PacketInTheLoopTests(LoopHarness):
    def test_every_reviewer_lane_is_handed_a_packet_bound_to_it_and_this_head(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        packets = self.runner.evidence_packets
        self.assertEqual(len(packets), 3)
        for packet, role in zip(
            packets, ["reviewer-a", "reviewer-b", "integration-auditor"], strict=True
        ):
            with self.subTest(role=role):
                self.assertEqual(packet["head"], HEAD_A)
                self.assertEqual(packet["repo"], self.config.repo)
                self.assertEqual(packet["pr"], self.remote.number)
                self.assertEqual(packet["frozen_for"]["role"], role)
                self.assertTrue(packet["generated_at"])
        # One packet per lane, never one lane's handed to another.
        self.assertEqual([packet["sequence"] for packet in packets], [1, 2, 3])

    def test_the_auditor_is_handed_the_artifacts_a_and_b_already_published(self) -> None:
        """Its whole job is reconciling two artifacts, and it cannot fetch them."""
        loop = self.build()
        self.review_round(HEAD_A)

        loop.run()

        auditor = self.runner.evidence_packets[2]["surfaces"]["conversation_comments"]
        self.assertEqual(auditor["count"], 2)
        for item in auditor["items"]:
            self.assertEqual(item["author"], REVIEWER_LOGIN)
            self.assertIn(HEAD_A, item["body"])

    def test_a_packet_that_did_not_land_bound_stops_before_the_lane_runs(self) -> None:
        """Written and then re-read, for the same reason artifacts are.

        What a lane is handed is the file on disk, not the payload this process
        assembled. Here the write lands a packet for another head — a stale one
        at the same path is the realistic version — and the lane must never be
        launched against it.
        """
        loop = self.build()
        self.review_round(HEAD_A)

        def stale(path, payload):
            payload["head"] = HEAD_B
            payload["binding"] = packet_binding(
                repo=payload["repo"],
                pr=payload["pr"],
                base=payload["base"],
                head=HEAD_B,
                sequence=payload["sequence"],
            )
            return write_packet(path, payload)

        with patch("pr_prover.loop.write_packet", stale):
            result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "evidence-packet")
        self.assertEqual(
            [call.argv[0] for call in self.runner.calls if call.argv[0].startswith("lane-")],
            [],
            "no lane may run against a packet that is not bound to this head",
        )

    def test_every_lane_is_handed_the_pr_body_and_the_governing_contract(self) -> None:
        """PAPI90-FINAL-P1-002, at the loop seam the reviewers measured.

        The lane's own prompt tells it to check the PR body for stale claims and
        to judge scope against the issue. Both documents have to arrive through
        the shipped path, for all three lanes, not just through ``build_packet``.
        """
        loop = self.build()
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        for packet, role in zip(
            self.runner.evidence_packets,
            ["reviewer-a", "reviewer-b", "integration-auditor"],
            strict=True,
        ):
            with self.subTest(role=role):
                stated = packet["surfaces"]["pull_request_body"]
                self.assertEqual(stated["items"][0]["body"], PR_BODY)
                self.assertTrue(stated["complete"])
                contract = packet["surfaces"]["governing_issues"]
                self.assertEqual(contract["items"][0]["number"], GOVERNING_ISSUE)
                self.assertEqual(contract["items"][0]["body"], GOVERNING_ISSUE_BODY)
                self.assertTrue(contract["complete"])
        # ...and the numbers came from the configuration, not from the PR prose.
        self.assertEqual(
            self.github.governing_issues_asked_for, [(GOVERNING_ISSUE,)] * 3
        )

    def test_a_packet_with_no_governing_contract_cannot_earn_merge_ready(self) -> None:
        """Former red at the loop level: no contract, and still a green run."""
        loop = self.build()
        self.review_round(HEAD_A)
        self.remote.governing_issues = []

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "evidence-packet")
        self.assertEqual(
            [call.argv[0] for call in self.runner.calls if call.argv[0].startswith("lane-")],
            [],
            "no lane may judge a change against a contract it was never handed",
        )

    def test_a_malformed_landed_packet_cannot_earn_merge_ready(self) -> None:
        """Former red at the loop level, exactly as the reviewers reproduced it.

        The packet writer's payload keeps the canonical repo/PR/base/head/lane
        binding and loses the evidence schema. Every one of these returned
        ``merge-ready`` with three transported review lanes.
        """
        cases = {
            "missing-surfaces": lambda payload: payload["surfaces"].pop("reviews"),
            "missing-completeness": lambda payload: payload["surfaces"]["reviews"].pop("complete"),
            "count-mismatch": lambda payload: payload["surfaces"]["reviews"].update({"count": 9}),
            "boolean-schema": lambda payload: payload.__setitem__("schema_version", True),
            "no-contract": lambda payload: payload["surfaces"]["governing_issues"].update(
                {"count": 0, "items": []}
            ),
        }
        for label, mutate in cases.items():
            with self.subTest(packet=label):
                self.setUp()
                loop = self.build()
                self.review_round(HEAD_A)

                def landed(path, payload, edit=mutate):
                    edit(payload)
                    return write_packet(path, payload)

                with patch("pr_prover.loop.write_packet", landed):
                    result = loop.run()

                self.assertEqual(result.outcome, NEEDS_KARAN)
                self.assertEqual(result.reason, "evidence-packet")
                self.assertEqual(
                    [
                        call.argv[0]
                        for call in self.runner.calls
                        if call.argv[0].startswith("lane-")
                    ],
                    [],
                )

    def test_a_landed_packet_with_a_hollow_contract_cannot_earn_merge_ready(self) -> None:
        """Former red at the loop level: the envelope held and the contract did not.

        These are the four the reviewer reproduced by hand. Every surface keeps
        its completeness flag, its count, and a matching list of items — and the
        lane would have been handed a PR body with no text, a governing issue
        with no contract body or a ``null`` one, or the contract for issue #999
        while this run is measured against #1. All four reached ``merge-ready``
        with three review lanes launched.
        """
        cases = {
            "missing-pr-body-field": lambda payload: payload["surfaces"]["pull_request_body"][
                "items"
            ][0].pop("body"),
            "missing-governing-body-field": lambda payload: payload["surfaces"][
                "governing_issues"
            ]["items"][0].pop("body"),
            "null-governing-body": lambda payload: payload["surfaces"]["governing_issues"][
                "items"
            ][0].update({"body": None}),
            "substituted-governing-number": lambda payload: payload["surfaces"][
                "governing_issues"
            ]["items"][0].update({"number": 999}),
        }
        for label, mutate in cases.items():
            with self.subTest(packet=label):
                self.setUp()
                loop = self.build()
                self.review_round(HEAD_A)

                def landed(path, payload, edit=mutate):
                    edit(payload)
                    return write_packet(path, payload)

                with patch("pr_prover.loop.write_packet", landed):
                    result = loop.run()

                self.assertEqual(result.outcome, NEEDS_KARAN)
                self.assertEqual(result.reason, "evidence-packet")
                self.assertEqual(
                    [
                        call.argv[0]
                        for call in self.runner.calls
                        if call.argv[0].startswith("lane-")
                    ],
                    [],
                    "no lane may judge a change against a contract it was not handed",
                )
                self.assertEqual(result.transport, ())

    def test_a_contract_read_for_an_issue_this_run_did_not_configure_stops_it(self) -> None:
        """The substitution case through the shipped value flow, unpatched.

        The configuration names issue #1; the boundary comes back describing
        #999. Nothing about that packet is malformed — it is simply a contract
        this run did not choose, which is exactly what a lane cannot detect from
        the inside, so the configured numbers travel into the readback and the
        run stops before any lane is launched.
        """
        loop = self.build()
        self.review_round(HEAD_A)
        self.remote.governing_issues = [
            GoverningIssue(
                number=999, title="someone else's mission", state="OPEN", body="ACCEPTANCE: other"
            )
        ]

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "evidence-packet")
        self.assertEqual(self.github.governing_issues_asked_for, [(GOVERNING_ISSUE,)])
        self.assertEqual(
            [call.argv[0] for call in self.runner.calls if call.argv[0].startswith("lane-")],
            [],
        )

    def test_a_packet_that_could_not_be_written_stops_the_run(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        def refuse(path, payload):
            raise EvidencePacketError(
                "the frozen evidence packet could not be written: no space left",
                evidence={"packet_file": str(path)},
            )

        with patch("pr_prover.loop.write_packet", refuse):
            result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "evidence-packet")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
