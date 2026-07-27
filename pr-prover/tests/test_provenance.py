"""Finding provenance: complete at creation, fail-closed, and durable.

Four questions have to survive from the moment a lane prints a finding to the
moment Karan reads the escalation: who found it, on which exact head, at which
surface, and what did they actually say. These tests hold that end to end —
construction, classification lineage, the ``needs-Karan`` rendering, and a
restart that reads the journal back off disk.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import (
    HEAD_A,
    HEAD_B,
    builder_output,
    fix_comment,
    make_finding,
    make_provenance,
    reviewer_output,
)
from pr_prover import report
from pr_prover.errors import StateError
from pr_prover.findings import (
    Classification,
    ClassificationEvent,
    ClassifiedFinding,
    Finding,
    FindingLocation,
    FindingProvenance,
    classify,
)
from pr_prover.loop import MERGE_READY, NEEDS_KARAN, RunResult
from pr_prover.state import RunState
from pr_prover.verdicts import parse_reviewer_verdict
from test_loop import BLOCKER, LoopHarness

COMPLETE = {
    "agent_id": "A",
    "role": "reviewer",
    "head": HEAD_A,
    "location": FindingLocation(kind="lane-output", reference="reviewer:A", line=3),
    "evidence_excerpt": "FINDING: SEVERITY=blocking ID=x -- boom",
}


def stopped_clock(stamps=("2026-07-26T09:00:00Z",)):
    """A deterministic clock: each call returns the next stamp, then repeats the last."""
    remaining = list(stamps)

    def tick() -> str:
        return remaining.pop(0) if len(remaining) > 1 else remaining[0]

    return tick


class ProvenanceCompletenessTests(unittest.TestCase):
    """Every field is load-bearing, so every field is required at construction."""

    # (case, overrides, the field the failure must name)
    INCOMPLETE = (
        ("an empty agent id", {"agent_id": ""}, "agent_id"),
        ("a whitespace agent id", {"agent_id": "   "}, "agent_id"),
        ("a non-string agent id", {"agent_id": None}, "agent_id"),
        ("a short head", {"head": HEAD_A[:7]}, "head"),
        ("an absent head", {"head": None}, "head"),
        ("an uppercase head", {"head": HEAD_A.upper()}, "head"),
        ("no location", {"location": None}, "location"),
        ("an untyped location", {"location": "somewhere in the diff"}, "location"),
        ("an empty evidence excerpt", {"evidence_excerpt": ""}, "evidence_excerpt"),
        ("a whitespace evidence excerpt", {"evidence_excerpt": "\n  "}, "evidence_excerpt"),
    )

    def test_incomplete_provenance_cannot_be_constructed(self) -> None:
        for case, overrides, field in self.INCOMPLETE:
            with self.subTest(case=case):
                with self.assertRaises(StateError) as caught:
                    FindingProvenance(**{**COMPLETE, **overrides})
                self.assertEqual(caught.exception.evidence["incomplete_field"], field)
                self.assertEqual(caught.exception.reason, "unexpected-state")

    def test_an_unknown_role_fails_closed(self) -> None:
        with self.assertRaises(StateError) as caught:
            FindingProvenance(**{**COMPLETE, "role": "integration-auditor-lane"})
        self.assertEqual(caught.exception.evidence["role"], "integration-auditor-lane")

    def test_complete_provenance_is_accepted(self) -> None:
        provenance = FindingProvenance(**COMPLETE)
        self.assertEqual(provenance.source_label, "reviewer:A")
        self.assertEqual(provenance.head, HEAD_A)

    def test_an_unknown_location_kind_fails_closed(self) -> None:
        with self.assertRaises(StateError) as caught:
            FindingLocation(kind="vibes", reference="somewhere")
        self.assertEqual(caught.exception.evidence["kind"], "vibes")

    LOCATIONS = (
        ("an empty reference", {"reference": ""}, "reference"),
        ("a file location with no line", {"kind": "file-line", "line": None}, "line"),
        ("a zero line", {"line": 0}, "line"),
        ("a negative line", {"line": -3}, "line"),
        ("a string line", {"line": "3"}, "line"),
        ("a boolean line", {"line": True}, "line"),
    )

    def test_an_unusable_location_fails_closed(self) -> None:
        base = {"kind": "lane-output", "reference": "reviewer:A", "line": 3}
        for case, overrides, field in self.LOCATIONS:
            with self.subTest(case=case):
                with self.assertRaises(StateError) as caught:
                    FindingLocation(**{**base, **overrides})
                self.assertEqual(caught.exception.evidence["incomplete_field"], field)

    def test_every_location_kind_describes_itself(self) -> None:
        cases = (
            (FindingLocation(kind="file-line", reference="src/app.py", line=42), "src/app.py:42"),
            (FindingLocation(kind="review", reference="PRR_1"), "review PRR_1"),
            (FindingLocation(kind="thread", reference="PRRT_9"), "thread PRRT_9"),
            (FindingLocation(kind="comment", reference="IC_5"), "comment IC_5"),
            (
                FindingLocation(kind="gate-command", reference="python3 -m unittest"),
                "gate-command python3 -m unittest",
            ),
            (
                FindingLocation(kind="lane-output", reference="reviewer:A", line=3),
                "lane-output reviewer:A line 3",
            ),
        )
        for location, expected in cases:
            with self.subTest(kind=location.kind):
                self.assertEqual(location.describe(), expected)

    def test_a_finding_without_provenance_cannot_be_constructed(self) -> None:
        for case, provenance in (("none", None), ("a display string", "reviewer:A")):
            with self.subTest(case=case):
                with self.assertRaises(StateError) as caught:
                    Finding(id="a", severity="blocking", summary="s", provenance=provenance)
                self.assertEqual(caught.exception.evidence["incomplete_field"], "provenance")

    def test_head_and_source_are_read_off_the_provenance(self) -> None:
        finding = make_finding("a", "blocking", "gate:lint", head=HEAD_B)
        self.assertEqual(finding.head, HEAD_B)
        self.assertEqual(finding.source, "gate:lint")
        self.assertEqual(finding.as_dict()["provenance"]["head"], HEAD_B)

    def test_a_rendered_source_is_never_read_back_as_authority(self) -> None:
        """Provenance is recorded, not reconstructed from the strings it renders."""
        payload = make_finding("a").as_dict()
        payload["source"] = "reviewer:B"
        with self.assertRaises(StateError) as caught:
            Finding.from_dict(payload)
        self.assertEqual(caught.exception.evidence["field"], "source")

    def test_a_finding_round_trips_through_its_own_mapping(self) -> None:
        original = make_finding("a", "blocking", "reviewer:B", head=HEAD_B, detail="log")
        self.assertEqual(Finding.from_dict(original.as_dict()), original)


class ReviewerProvenanceTests(unittest.TestCase):
    """The reviewer parser is one of the two places provenance is created."""

    def verdict(self):
        return parse_reviewer_verdict(
            "A",
            reviewer_output(HEAD_A, [("blocking", "null-deref", "crashes on empty input")]),
            expected_head=HEAD_A,
        )

    def test_a_parsed_finding_names_its_lane_role_and_head(self) -> None:
        finding = self.verdict().findings[0]
        self.assertEqual(finding.provenance.agent_id, "A")
        self.assertEqual(finding.provenance.role, "reviewer")
        self.assertEqual(finding.provenance.head, HEAD_A)
        self.assertEqual(finding.source, "reviewer:A")

    def test_a_parsed_finding_points_at_the_line_that_produced_it(self) -> None:
        location = self.verdict().findings[0].provenance.location
        self.assertEqual(location.kind, "lane-output")
        self.assertEqual(location.reference, "reviewer:A")
        self.assertEqual(location.line, 1)

    def test_a_parsed_finding_keeps_the_verbatim_excerpt(self) -> None:
        finding = self.verdict().findings[0]
        self.assertEqual(
            finding.provenance.evidence_excerpt,
            "FINDING: SEVERITY=blocking ID=null-deref -- crashes on empty input",
        )

    def test_each_finding_points_at_its_own_line(self) -> None:
        output = reviewer_output(
            HEAD_A,
            [
                ("blocking", "first", "one"),
                ("non-blocking", "second", "two"),
                ("needs-karan", "third", "three"),
            ],
        )
        verdict = parse_reviewer_verdict("B", output, expected_head=HEAD_A)
        self.assertEqual(
            [item.provenance.location.line for item in verdict.findings], [1, 2, 3]
        )
        for item in verdict.findings:
            with self.subTest(finding=item.id):
                self.assertIn(f"ID={item.id}", item.provenance.evidence_excerpt)

    def test_a_credential_in_a_finding_line_is_scrubbed_in_the_excerpt(self) -> None:
        output = (
            "FINDING: SEVERITY=blocking ID=leak -- the log printed "
            "ghp_0123456789abcdefghijABCDEFGHIJ0123\n"
            f"DONE: STATUS=fail BLOCKING=1 HEAD={HEAD_A}\n"
        )
        verdict = parse_reviewer_verdict("A", output, expected_head=HEAD_A)
        excerpt = verdict.findings[0].provenance.evidence_excerpt
        self.assertNotIn("ghp_0123456789abcdefghijABCDEFGHIJ0123", excerpt)
        self.assertIn("<redacted>", excerpt)


class ClassificationLineageTests(unittest.TestCase):
    """Who classified what, when — recorded as a decision, not inferred later."""

    def test_an_accepted_claim_records_one_classified_event(self) -> None:
        result = classify([make_finding("a", "blocking")], clock=stopped_clock())
        lineage = result.blocking[0].lineage
        self.assertEqual(len(lineage), 1)
        self.assertEqual(lineage[0].action, "classified")
        self.assertEqual(lineage[0].finding_id, "a")
        self.assertEqual(lineage[0].actor, "hermes")
        self.assertEqual(lineage[0].from_category, "blocking")
        self.assertEqual(lineage[0].to_category, "blocking")
        self.assertEqual(lineage[0].at, "2026-07-26T09:00:00Z")

    def test_an_adjudicated_downgrade_records_a_reclassification(self) -> None:
        result = classify(
            [make_finding("a", "blocking")],
            adjudicator=lambda finding: "false-positive",
            actor="karan",
            clock=stopped_clock(),
        )
        event = result.false_positive[0].lineage[0]
        self.assertEqual(event.action, "reclassified")
        self.assertEqual(event.actor, "karan")
        self.assertEqual(event.from_category, "blocking")
        self.assertEqual(event.to_category, "false-positive")

    def test_a_second_lane_raising_the_same_id_extends_the_lineage(self) -> None:
        result = classify(
            [
                make_finding("a", "non-blocking", "reviewer:A"),
                make_finding("a", "blocking", "reviewer:B"),
            ],
            clock=stopped_clock(("2026-07-26T09:00:00Z", "2026-07-26T09:05:00Z", "2026-07-26T09:06:00Z")),
        )
        item = result.blocking[0]
        self.assertEqual(item.sources, ("reviewer:A", "reviewer:B"))
        self.assertEqual([event.action for event in item.lineage], ["classified", "classified", "reclassified"])
        promotion = item.lineage[-1]
        self.assertEqual(promotion.from_category, "non-blocking")
        self.assertEqual(promotion.to_category, "blocking")
        self.assertIn("reviewer:B", promotion.rationale)
        self.assertEqual(promotion.at, "2026-07-26T09:06:00Z")

    def test_a_milder_second_claim_does_not_move_the_category(self) -> None:
        result = classify(
            [
                make_finding("a", "blocking", "reviewer:A"),
                make_finding("a", "non-blocking", "reviewer:B"),
            ],
            clock=stopped_clock(),
        )
        item = result.blocking[0]
        self.assertEqual(item.category, "blocking")
        self.assertEqual(
            [event.action for event in item.lineage],
            ["classified", "classified", "reclassified"],
        )
        kept = item.lineage[-1]
        self.assertEqual((kept.from_category, kept.to_category), ("non-blocking", "blocking"))
        self.assertIn("reviewer:A already claimed blocking", kept.rationale)

    def test_two_lanes_agreeing_need_no_resolution_event(self) -> None:
        result = classify(
            [
                make_finding("a", "blocking", "reviewer:A"),
                make_finding("a", "blocking", "reviewer:B"),
            ],
            clock=stopped_clock(),
        )
        self.assertEqual(
            [event.action for event in result.blocking[0].lineage], ["classified", "classified"]
        )

    def test_lineage_must_end_at_the_assigned_category(self) -> None:
        event = ClassificationEvent(
            finding_id="a",
            actor="hermes",
            action="classified",
            from_category="blocking",
            to_category="blocking",
            at="2026-07-26T09:00:00Z",
        )
        with self.assertRaises(StateError):
            ClassifiedFinding(
                finding=make_finding("a"), category="non-blocking", sources=("reviewer:A",), lineage=(event,)
            )

    def test_a_classified_finding_without_lineage_fails_closed(self) -> None:
        with self.assertRaises(StateError) as caught:
            ClassifiedFinding(finding=make_finding("a"), category="blocking", sources=("reviewer:A",))
        self.assertEqual(caught.exception.evidence["incomplete_field"], "lineage")

    def test_an_unknown_lineage_action_fails_closed(self) -> None:
        with self.assertRaises(StateError):
            ClassificationEvent(
                finding_id="a",
                actor="hermes",
                action="vibed",
                from_category="blocking",
                to_category="blocking",
                at="2026-07-26T09:00:00Z",
            )


class ClassificationRoundTripTests(unittest.TestCase):
    """The buckets survive serialization with their provenance and lineage intact."""

    def classification(self) -> Classification:
        return classify(
            [
                make_finding("a", "blocking", "reviewer:A"),
                make_finding("b", "non-blocking", "reviewer:B"),
                make_finding("c", "needs-karan", "reviewer:B"),
            ],
            clock=stopped_clock(),
        )

    def test_a_classification_round_trips_through_its_own_mapping(self) -> None:
        original = self.classification()
        self.assertEqual(Classification.from_dict(original.as_dict()), original)

    def test_a_bucket_whose_category_disagrees_fails_closed(self) -> None:
        payload = self.classification().as_dict()
        payload["non-blocking"].append(payload["blocking"].pop())
        with self.assertRaises(StateError) as caught:
            Classification.from_dict(payload)
        self.assertEqual(caught.exception.evidence["bucket"], "non-blocking")

    def test_a_stored_finding_with_no_provenance_fails_closed(self) -> None:
        payload = self.classification().as_dict()
        payload["blocking"][0].pop("provenance")
        with self.assertRaises(StateError) as caught:
            Classification.from_dict(payload)
        self.assertEqual(caught.exception.evidence["incomplete_field"], "provenance")

    def test_a_stored_finding_with_half_a_provenance_fails_closed(self) -> None:
        for field in ("agent_id", "role", "head", "location", "evidence_excerpt"):
            with self.subTest(missing=field):
                payload = self.classification().as_dict()
                payload["blocking"][0]["provenance"].pop(field)
                with self.assertRaises(StateError):
                    Classification.from_dict(payload)

    def test_a_stored_finding_with_no_lineage_fails_closed(self) -> None:
        payload = self.classification().as_dict()
        payload["blocking"][0]["lineage"] = []
        with self.assertRaises(StateError) as caught:
            Classification.from_dict(payload)
        self.assertEqual(caught.exception.evidence["incomplete_field"], "lineage")

    def test_a_missing_bucket_fails_closed(self) -> None:
        payload = self.classification().as_dict()
        payload.pop("false-positive")
        with self.assertRaises(StateError):
            Classification.from_dict(payload)

    def test_a_duplicated_id_across_buckets_fails_closed(self) -> None:
        payload = self.classification().as_dict()
        payload["non-blocking"].append(dict(payload["non-blocking"][0]))
        with self.assertRaises(StateError):
            Classification.from_dict(payload)


class DurableProvenanceTests(unittest.TestCase):
    """The journal is what a restart reads, so provenance has to be in it."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-provenance-")
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "state.json"

    def load(self) -> RunState:
        return RunState.load(self.path, repo="example/repo", pr=7)

    def saved_state(self) -> RunState:
        state = self.load()
        state.bind_head(HEAD_A)
        state.record_classification(
            classify(
                [make_finding("a", "blocking", "reviewer:A"), make_finding("c", "needs-karan", "gate:lint")],
                clock=stopped_clock(),
            )
        )
        state.save()
        return state

    def test_a_classification_survives_a_restart_intact(self) -> None:
        original = self.saved_state()

        reloaded = self.load()

        self.assertEqual(reloaded.classification, original.classification)
        finding = reloaded.classification.blocking[0].finding
        self.assertEqual(finding.provenance.agent_id, "A")
        self.assertEqual(finding.provenance.role, "reviewer")
        self.assertEqual(finding.provenance.head, HEAD_A)
        self.assertEqual(finding.provenance.location.kind, "lane-output")
        self.assertEqual(
            finding.provenance.evidence_excerpt, "FINDING: SEVERITY=blocking ID=x -- s"
        )
        self.assertEqual(reloaded.classification.blocking[0].lineage[0].at, "2026-07-26T09:00:00Z")

    def test_the_journal_holds_the_provenance_on_disk(self) -> None:
        self.saved_state()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        stored = payload["classification"]["blocking"][0]
        self.assertEqual(stored["provenance"]["role"], "reviewer")
        self.assertEqual(stored["provenance"]["location"]["reference"], "reviewer:A")
        self.assertEqual(stored["lineage"][0]["actor"], "hermes")

    def test_a_journal_with_incomplete_provenance_is_unexpected_state(self) -> None:
        self.saved_state()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        payload["classification"]["blocking"][0]["provenance"].pop("evidence_excerpt")
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(StateError) as caught:
            self.load()
        self.assertIn("classification is unusable", caught.exception.message)

    def test_a_journal_binding_findings_to_another_head_is_unexpected_state(self) -> None:
        self.saved_state()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        payload["head"] = HEAD_B
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(StateError) as caught:
            self.load()
        self.assertEqual(caught.exception.evidence["finding_heads"], [HEAD_A])

    def test_a_journal_with_findings_and_no_head_is_unexpected_state(self) -> None:
        self.saved_state()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        payload["head"] = None
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(StateError):
            self.load()

    def test_findings_for_another_head_cannot_be_recorded(self) -> None:
        state = self.load()
        state.bind_head(HEAD_A)
        with self.assertRaises(StateError) as caught:
            state.record_classification(
                classify([make_finding("a", "blocking", head=HEAD_B)], clock=stopped_clock())
            )
        self.assertEqual(caught.exception.evidence["finding_heads"], [HEAD_B])

    def test_rebinding_to_a_new_head_drops_the_old_head_findings(self) -> None:
        """A push invalidates evidence; carrying it forward is what that forbids."""
        state = self.saved_state()
        state.bind_head(HEAD_B)
        self.assertIsNone(state.classification)

    def test_rebinding_to_the_same_head_keeps_them(self) -> None:
        state = self.saved_state()
        state.bind_head(HEAD_A)
        self.assertIsNotNone(state.classification)


class NeedsKaranRenderingTests(unittest.TestCase):
    """The escalation has to be actionable without re-reading the lane output."""

    def result(self) -> RunResult:
        escalation = make_finding(
            "copy-tone",
            "needs-karan",
            "reviewer:B",
            summary="headline wording is a product call",
            provenance=make_provenance(
                "reviewer:B",
                line=4,
                excerpt="FINDING: SEVERITY=needs-karan ID=copy-tone -- headline wording is a product call",
            ),
        )
        return RunResult(
            outcome=NEEDS_KARAN,
            reason="needs-karan-finding",
            head=HEAD_A,
            branch="feat/example",
            classification=classify([escalation], clock=stopped_clock()),
        )

    def test_the_escalation_renders_its_provenance_inline(self) -> None:
        text = report.to_markdown(self.result())
        self.assertIn("`copy-tone` — headline wording is a product call", text)
        self.assertIn("found by `B` (role `reviewer`)", text)
        self.assertIn(f"on head `{HEAD_A}`", text)
        self.assertIn("location: lane-output reviewer:B line 4", text)
        self.assertIn(
            "evidence: `FINDING: SEVERITY=needs-karan ID=copy-tone -- "
            "headline wording is a product call`",
            text,
        )

    def test_the_escalation_renders_its_classification_lineage(self) -> None:
        text = report.to_markdown(self.result())
        self.assertIn("lineage: 2026-07-26T09:00:00Z — hermes classified", text)
        self.assertIn("needs-karan → needs-karan", text)

    def test_the_json_report_carries_the_same_provenance(self) -> None:
        payload = json.loads(report.to_json(self.result()))
        item = payload["classification"]["needs-karan"][0]
        self.assertEqual(item["provenance"]["agent_id"], "B")
        self.assertEqual(item["provenance"]["location"]["line"], 4)
        self.assertEqual(item["lineage"][0]["to_category"], "needs-karan")

    def test_a_non_escalating_bucket_stays_a_one_liner(self) -> None:
        """Provenance is inline where a human must act on it, not everywhere."""
        result = RunResult(
            outcome=MERGE_READY,
            reason="no-blocking-findings",
            head=HEAD_A,
            classification=classify([make_finding("naming", "non-blocking")], clock=stopped_clock()),
        )
        text = report.to_markdown(result)
        self.assertIn("`naming`", text)
        self.assertNotIn("found by", text)


class LoopProvenanceTests(LoopHarness):
    """Provenance from the shipped path: real lanes, real gates, real journal."""

    def gate(self, name: str = "lint", argv=("gate-lint", "--head", "{head}")):
        return [{"name": name, "argv": list(argv)}]

    def failed_gate_run(self, *, stdout: str, returncode: int) -> dict:
        """Run one failing gate and return the blocker as the journal stored it.

        The builder refuses, so the run stops before any terminal report — which
        is exactly the case provenance exists for: the journal written before the
        builder was invoked still says who found what, where.
        """
        loop = self.build(gates=self.gate())
        self.script.add("gate-lint", stdout, returncode=returncode)
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["gate-lint"], status="failure"),
        )

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        return self.state()["classification"]["blocking"][0]

    def test_a_gate_failure_carries_the_command_it_ran(self) -> None:
        stored = self.failed_gate_run(stdout="boom\n", returncode=1)
        provenance = stored["provenance"]
        self.assertEqual(provenance["role"], "gate")
        self.assertEqual(provenance["agent_id"], "lint")
        self.assertEqual(provenance["head"], HEAD_A)
        self.assertEqual(provenance["location"]["kind"], "gate-command")
        self.assertEqual(provenance["location"]["reference"], f"gate-lint --head {HEAD_A}")
        self.assertIn("boom", provenance["evidence_excerpt"])
        self.assertEqual(stored["source"], "gate:lint")

    def test_a_quiet_gate_failure_still_carries_an_excerpt(self) -> None:
        stored = self.failed_gate_run(stdout="", returncode=3)
        self.assertEqual(
            stored["provenance"]["evidence_excerpt"], "<gate captured no output; exit 3>"
        )

    def test_a_reviewer_blocker_reaches_the_frozen_set_with_its_provenance(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        captured: dict[str, str] = {}

        def capture() -> None:
            call = next(call for call in self.runner.calls if call.argv[0] == "lane-builder")
            captured["path"] = call.argv[call.argv.index("--blockers") + 1]

        self.script.add("lane-builder", "", returncode=1, after=capture)

        loop.run()

        payload = json.loads(Path(captured["path"]).read_text(encoding="utf-8"))
        provenance = payload["blockers"][0]["provenance"]
        self.assertEqual(provenance["role"], "reviewer")
        self.assertEqual(provenance["agent_id"], "A")
        self.assertEqual(provenance["head"], HEAD_A)
        self.assertIn("ID=null-deref", provenance["evidence_excerpt"])
        self.assertEqual(payload["blockers"][0]["lineage"][0]["to_category"], "blocking")

    def test_the_run_journal_holds_the_classification_it_reported(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A, [("needs-karan", "copy-tone", "a product call")])

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        stored = self.state()["classification"]["needs-karan"][0]
        self.assertEqual(stored["id"], "copy-tone")
        self.assertEqual(stored["provenance"]["agent_id"], "A")
        self.assertEqual(stored["provenance"]["head"], HEAD_A)
        self.assertIn("ID=copy-tone", stored["provenance"]["evidence_excerpt"])

    def test_a_fix_cycle_journals_the_new_head_findings_only(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["null-deref"]),
            after=lambda: self.remote.push(HEAD_B, comment=fix_comment(HEAD_B)),
        )
        self.review_round(HEAD_B, [("non-blocking", "naming", "rename the helper")])

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        stored = self.state()["classification"]
        self.assertEqual(stored["blocking"], [])
        self.assertEqual(stored["non-blocking"][0]["provenance"]["head"], HEAD_B)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
