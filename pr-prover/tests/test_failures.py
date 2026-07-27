"""Failure records: one shape, four answers, two renderings.

A builder handed dead-end error prose fills the intent hole with a confident
guess. Every failure this loop can reach is therefore expressed as one
:class:`~pr_prover.errors.FailureRecord` naming what failed, the exact evidence,
the bounded remediation, and the escalation condition — and the human summary
and the builder's next-instruction block are two renderings of that one record.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from _support import HEAD_A, HEAD_B, builder_output, fix_comment, reviewer_output
from pr_prover import report
from pr_prover.errors import (
    CLASSIFICATION_STOP,
    FAILURE_CLASSES,
    GATE_FAILURE,
    AmbiguousPush,
    BuilderRefusal,
    CommandContractError,
    ConfigError,
    FailClosed,
    FailureRecord,
    GitHubError,
    LaneFailure,
    LockContention,
    MalformedVerdict,
    ReadbackMismatch,
    ScopeContamination,
    StaleHead,
    StateError,
    WorktreeError,
)
from pr_prover.loop import NEEDS_KARAN, RunResult
from test_loop import BLOCKER, LoopHarness
from test_provenance import stopped_clock

# The five classes the slice must cover, plus the rest of the taxonomy. Each row
# is (class, an error that produces it or None for the two non-error classes).
ERROR_CLASSES = (
    ("malformed-verdict", MalformedVerdict),
    ("stale-head", StaleHead),
    ("readback-mismatch", ReadbackMismatch),
    ("lane-failure", LaneFailure),
    ("ambiguous-push", AmbiguousPush),
    ("scope-contamination", ScopeContamination),
    ("builder-refusal", BuilderRefusal),
    ("github-error", GitHubError),
    ("worktree-error", WorktreeError),
    ("unexpected-state", StateError),
    ("lock-contention", LockContention),
    ("invalid-config", ConfigError),
    ("invalid-command", CommandContractError),
    ("fail-closed", FailClosed),
)

REQUIRED_CLASSES = (
    GATE_FAILURE,
    "readback-mismatch",
    "malformed-verdict",
    "stale-head",
    CLASSIFICATION_STOP,
)


def gate_record() -> FailureRecord:
    return FailureRecord.for_gate(
        name="tests",
        kind="baseline",
        command=["python3", "-m", "unittest", "discover"],
        returncode=1,
        timed_out=False,
        output="1 test failed",
        finding_id="gate-tests",
    )


def classification_record() -> FailureRecord:
    return FailureRecord.for_classification_stop(
        finding={
            "id": "copy-tone",
            "summary": "headline wording is a product call",
            "category": "needs-karan",
            "provenance": {"agent_id": "B", "role": "reviewer", "head": HEAD_A},
        }
    )


class FailureTaxonomyTests(unittest.TestCase):
    """Every class the loop can reach answers all four questions."""

    def test_the_five_required_classes_are_in_the_taxonomy(self) -> None:
        for failure_class in REQUIRED_CLASSES:
            with self.subTest(failure_class=failure_class):
                self.assertIn(failure_class, FAILURE_CLASSES)

    def test_every_fail_closed_reason_has_a_class(self) -> None:
        for failure_class, error in ERROR_CLASSES:
            with self.subTest(failure_class=failure_class):
                self.assertEqual(error.reason, failure_class)
                self.assertIn(failure_class, FAILURE_CLASSES)

    def test_every_error_class_produces_a_complete_record(self) -> None:
        for failure_class, error in ERROR_CLASSES:
            with self.subTest(failure_class=failure_class):
                record = FailureRecord.from_error(
                    error("it broke", evidence={"expected": "a", "actual": "b"})
                )
                self.assertEqual(record.failure_class, failure_class)
                self.assertEqual(record.what_failed, "it broke")
                self.assertEqual(record.evidence["expected"], "a")
                self.assertEqual(record.evidence["actual"], "b")
                self.assertTrue(record.remediation, "a record must bound what may be attempted")
                self.assertTrue(record.escalation, "a record must say when to escalate instead")

    def test_every_class_in_the_taxonomy_is_reachable_as_a_record(self) -> None:
        """No class may exist in the vocabulary with no playbook behind it."""
        built = {record.failure_class for record in (gate_record(), classification_record())}
        built |= {
            FailureRecord.from_error(error("x", evidence={})).failure_class
            for _, error in ERROR_CLASSES
        }
        self.assertEqual(set(FAILURE_CLASSES) - built, set())

    def test_an_unknown_class_cannot_be_recorded(self) -> None:
        with self.assertRaises(StateError):
            FailureRecord(
                failure_class="vibes",
                what_failed="something",
                remediation=("stop",),
                escalation="always",
            )

    INCOMPLETE = (
        ("no summary", {"what_failed": ""}),
        ("no remediation", {"remediation": ()}),
        ("no escalation condition", {"escalation": "  "}),
    )

    def test_an_incomplete_record_fails_closed(self) -> None:
        base = {
            "failure_class": GATE_FAILURE,
            "what_failed": "gate 'tests' exited 1",
            "remediation": ("re-run it",),
            "escalation": "the gate needs unrelated work",
        }
        for case, overrides in self.INCOMPLETE:
            with self.subTest(case=case):
                with self.assertRaises(StateError):
                    FailureRecord(**{**base, **overrides})

    def test_an_unknown_reason_falls_back_to_the_conservative_class(self) -> None:
        class Odd(FailClosed):
            reason = "something-new"

        record = FailureRecord.from_error(Odd("unclassifiable"))
        self.assertEqual(record.failure_class, "fail-closed")
        self.assertTrue(record.escalation)


class FailureEvidenceTests(unittest.TestCase):
    """A record names the command, or expected versus actual, wherever it can."""

    def test_a_gate_record_carries_the_command_and_the_exit_status(self) -> None:
        record = gate_record()
        self.assertEqual(record.failure_class, GATE_FAILURE)
        self.assertEqual(record.finding_id, "gate-tests")
        self.assertEqual(record.evidence["command"], ["python3", "-m", "unittest", "discover"])
        self.assertEqual(record.evidence["expected"], "exit status 0")
        self.assertEqual(record.evidence["actual"], "exit status 1")
        self.assertIn("1 test failed", record.evidence["output"])

    def test_a_timed_out_gate_says_so_rather_than_naming_an_exit(self) -> None:
        record = FailureRecord.for_gate(
            name="visual",
            kind="visual",
            command=["gate-visual"],
            returncode=124,
            timed_out=True,
            output="",
            finding_id="gate-visual",
        )
        self.assertEqual(record.evidence["actual"], "timed out")
        self.assertIn("timed out", record.what_failed)

    def test_a_classification_stop_carries_the_finding_it_stopped_on(self) -> None:
        record = classification_record()
        self.assertEqual(record.failure_class, CLASSIFICATION_STOP)
        self.assertEqual(record.finding_id, "copy-tone")
        self.assertEqual(record.evidence["finding"]["provenance"]["agent_id"], "B")
        self.assertIn("needs-karan", record.evidence["actual"])
        self.assertIn("always", record.escalation)


class DerivedRenderingTests(unittest.TestCase):
    """One record, two audiences, no second bookkeeping."""

    def rendered(self, record: FailureRecord) -> tuple[list[str], dict]:
        payload = record.as_dict()
        return report.failure_markdown(payload), payload

    def test_the_human_summary_answers_all_four_questions(self) -> None:
        lines, _ = self.rendered(gate_record())
        text = "\n".join(lines)
        self.assertIn("`gate-failure` — baseline gate 'tests' exited 1", text)
        self.assertIn("- evidence:", text)
        self.assertIn("command: [\"python3\"", text)
        self.assertIn("- bounded remediation the builder may attempt:", text)
        self.assertIn("  1. re-run the exact command", text)
        self.assertIn("- escalate instead when:", text)

    def test_the_markdown_embeds_the_builder_block_verbatim(self) -> None:
        lines, payload = self.rendered(gate_record())
        text = "\n".join(lines)
        block = text.split("```json\n", 1)[1].split("\n```", 1)[0]
        self.assertEqual(json.loads(block), payload)

    def test_both_renderings_move_together(self) -> None:
        """Change the record and both renderings change; neither has its own copy."""
        record = gate_record()
        lines, payload = self.rendered(record)
        text = "\n".join(lines)
        for step in record.remediation:
            with self.subTest(step=step[:40]):
                self.assertIn(step, text)
                self.assertIn(step, payload["remediation"])
        self.assertIn(record.escalation, text)
        self.assertEqual(payload["escalation"], record.escalation)

    def test_the_record_is_the_next_instruction_block(self) -> None:
        payload = gate_record().as_dict()
        self.assertEqual(
            sorted(payload),
            ["escalation", "evidence", "failure_class", "finding_id", "remediation", "what_failed"],
        )


class ReportFailureTests(unittest.TestCase):
    """The report carries the records, sanitized like everything else."""

    SECRET = "ghp_0123456789abcdefghijABCDEFGHIJ0123"

    def result(self) -> RunResult:
        leaking = FailureRecord.for_gate(
            name="tests",
            kind="baseline",
            command=["gate-tests", "--token", self.SECRET],
            returncode=1,
            timed_out=False,
            output=f"authenticating with {self.SECRET}",
            finding_id="gate-tests",
        )
        return RunResult(
            outcome=NEEDS_KARAN,
            reason="builder-refusal",
            head=HEAD_A,
            failures=(leaking, FailureRecord.from_error(BuilderRefusal("the builder declined"))),
        )

    def test_the_json_report_carries_every_record(self) -> None:
        payload = json.loads(report.to_json(self.result()))
        self.assertEqual(
            [record["failure_class"] for record in payload["failures"]],
            [GATE_FAILURE, "builder-refusal"],
        )
        self.assertTrue(all(record["remediation"] for record in payload["failures"]))

    def test_the_markdown_report_renders_every_record(self) -> None:
        text = report.to_markdown(self.result())
        self.assertIn("### What failed and what to do next", text)
        self.assertIn("`gate-failure`", text)
        self.assertIn("`builder-refusal`", text)

    def test_a_credential_never_reaches_either_rendering(self) -> None:
        for rendered in (report.to_json(self.result()), report.to_markdown(self.result())):
            with self.subTest(form=rendered[:1]):
                self.assertNotIn(self.SECRET, rendered)
                self.assertIn("<redacted>", rendered)

    def test_a_run_with_no_failures_renders_no_section(self) -> None:
        text = report.to_markdown(RunResult(outcome=NEEDS_KARAN, reason="x", head=HEAD_A))
        self.assertNotIn("### What failed and what to do next", text)


class LoopFailureRecordTests(LoopHarness):
    """The shipped path emits records for the classes it can actually reach."""

    def build(self, **kwargs):  # noqa: D102 - the harness builder, with a fixed clock
        loop = super().build(**kwargs)
        loop.clock = stopped_clock()
        return loop

    def classes(self, result) -> list[str]:
        return [record.failure_class for record in result.failures]

    def test_a_failing_gate_emits_a_gate_record_bound_to_its_finding(self) -> None:
        loop = self.build(gates=[{"name": "tests", "argv": ["lane-gate-tests", "--head", "{head}"]}])
        self.script.add("lane-gate-tests", "1 test failed\n", returncode=1)
        self.script.add(
            "lane-builder", builder_output(HEAD_B, addressed=["gate-tests"], status="failure")
        )

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(self.classes(result), [GATE_FAILURE, "builder-refusal"])
        gate = result.failures[0]
        self.assertEqual(gate.finding_id, "gate-tests")
        self.assertEqual(gate.evidence["command"], ["lane-gate-tests", "--head", HEAD_A])

    def test_the_frozen_blocker_set_carries_the_gate_next_instruction(self) -> None:
        loop = self.build(gates=[{"name": "tests", "argv": ["lane-gate-tests", "--head", "{head}"]}])
        self.script.add("lane-gate-tests", "1 test failed\n", returncode=1)
        captured: dict[str, str] = {}

        def capture() -> None:
            call = next(call for call in self.runner.calls if call.argv[0] == "lane-builder")
            captured["path"] = call.argv[call.argv.index("--blockers") + 1]

        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["gate-tests"], status="failure"),
            after=capture,
        )

        loop.run()

        payload = json.loads(Path(captured["path"]).read_text(encoding="utf-8"))
        instruction = payload["next_instructions"][0]
        self.assertEqual(instruction["failure_class"], GATE_FAILURE)
        self.assertEqual(instruction["finding_id"], "gate-tests")
        self.assertEqual(instruction["evidence"]["command"], ["lane-gate-tests", "--head", HEAD_A])
        self.assertTrue(instruction["remediation"])
        self.assertTrue(instruction["escalation"])

    def test_the_frozen_blocker_set_is_scrubbed_like_the_report(self) -> None:
        """The one other file the loop serializes evidence into gets the same boundary."""
        secret = "ghp_0123456789abcdefghijABCDEFGHIJ0123"
        loop = self.build(
            gates=[{"name": "tests", "argv": ["lane-gate-tests", "--token", secret]}]
        )
        self.script.add("lane-gate-tests", f"authenticating with {secret}\n", returncode=1)
        captured: dict[str, str] = {}

        def capture() -> None:
            call = next(call for call in self.runner.calls if call.argv[0] == "lane-builder")
            captured["path"] = call.argv[call.argv.index("--blockers") + 1]

        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["gate-tests"], status="failure"),
            after=capture,
        )

        loop.run()

        written = Path(captured["path"]).read_text(encoding="utf-8")
        self.assertNotIn(secret, written)
        self.assertIn("<redacted>", written)

    def test_a_needs_karan_finding_emits_a_classification_stop(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A, [("needs-karan", "copy-tone", "a product call")])

        result = loop.run()

        self.assertEqual(self.classes(result), [CLASSIFICATION_STOP])
        record = result.failures[0]
        self.assertEqual(record.finding_id, "copy-tone")
        self.assertEqual(record.evidence["finding"]["provenance"]["agent_id"], "A")
        rendered = report.to_markdown(result)
        self.assertIn("`classification-stop`", rendered)

    def test_a_malformed_marker_emits_a_malformed_verdict_record(self) -> None:
        loop = self.build()
        self.script.add("lane-reviewer-A", "looks fine to me\n")

        result = loop.run()

        self.assertEqual(self.classes(result), ["malformed-verdict"])
        self.assertIn("DONE:", result.failures[0].remediation[0])

    def test_a_stale_head_emits_a_stale_head_record(self) -> None:
        loop = self.build()
        self.script.add("lane-reviewer-A", reviewer_output(HEAD_A))
        self.script.add(
            "lane-reviewer-B", reviewer_output(HEAD_A), after=lambda: self.remote.push(HEAD_B)
        )

        result = loop.run()

        self.assertEqual(self.classes(result), ["stale-head"])
        self.assertEqual(result.failures[0].evidence["drift"]["head"]["live"], HEAD_B)

    def test_a_missing_fix_comment_emits_a_readback_record(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["null-deref"]),
            after=lambda: self.remote.push(HEAD_B),
        )

        result = loop.run()

        self.assertEqual(self.classes(result), ["readback-mismatch"])
        self.assertIn("signature", " ".join(result.failures[0].remediation))

    def test_a_clean_run_emits_no_records(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.failures, ())
        self.assertNotIn("### What failed", report.to_markdown(result))

    def test_records_from_an_earlier_head_do_not_survive_a_fix_cycle(self) -> None:
        loop = self.build(gates=[{"name": "tests", "argv": ["lane-gate-tests", "--head", "{head}"]}])
        self.script.add("lane-gate-tests", "1 test failed\n", returncode=1)
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["gate-tests"]),
            after=lambda: self.remote.push(HEAD_B, comment=fix_comment(HEAD_B)),
        )
        self.script.add("lane-gate-tests", "3 tests passed\n")
        self.review_round(HEAD_B)

        result = loop.run()

        self.assertEqual(result.failures, (), "a fixed gate must not still be reported as failing")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
