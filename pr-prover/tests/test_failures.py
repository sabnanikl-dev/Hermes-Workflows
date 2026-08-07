"""Failure records: one shape, four answers, two renderings.

A builder handed dead-end error prose fills the intent hole with a confident
guess. Every failure this loop can reach is therefore expressed as one
:class:`~pr_prover.errors.FailureRecord` naming what failed, the exact evidence,
the bounded remediation, and the escalation condition — and the human summary
and the builder's next-instruction block are two renderings of that one record.
"""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from _support import (
    BUILDER_LOGIN,
    HEAD_A,
    HEAD_B,
    builder_output,
    fix_comment,
    make_source_repo,
    reviewer_output,
)
from pr_prover import cli
from pr_prover import report
from pr_prover.config import SCHEMA_VERSION as CONFIG_SCHEMA_VERSION
from pr_prover.errors import (
    CLASSIFICATION_STOP,
    FAILURE_CLASSES,
    GATE_FAILURE,
    AmbiguousPush,
    BuilderRefusal,
    CommandContractError,
    ConfigError,
    EnvironmentEvidenceError,
    EvidencePacketError,
    FailClosed,
    FailureRecord,
    GitHubError,
    HumanFeedbackPresent,
    LaneFailure,
    LockContention,
    MalformedVerdict,
    ReadbackMismatch,
    ReviewerRelayError,
    ScopeContamination,
    StaleHead,
    StateError,
    WorktreeError,
)
from pr_prover.loop import NEEDS_KARAN, RunResult
from pr_prover.state import PHASE_ATTEMPT_IN_FLIGHT, SCHEMA_VERSION
from test_loop import BLOCKER, LoopHarness
from test_provenance import stopped_clock

# The five classes the slice must cover, plus the rest of the taxonomy. Each row
# is (class, an error that produces it or None for the two non-error classes).
ERROR_CLASSES = (
    ("malformed-verdict", MalformedVerdict),
    ("stale-head", StaleHead),
    ("readback-mismatch", ReadbackMismatch),
    ("relay-failure", ReviewerRelayError),
    ("evidence-packet", EvidencePacketError),
    ("environment-evidence", EnvironmentEvidenceError),
    ("human-feedback", HumanFeedbackPresent),
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

    def assert_sole_candidate_failed(self, result: RunResult, failed: list[str]) -> None:
        """PAPI99-RA-P1-003: the record names which condition this candidate missed."""
        observed = result.failures[0].evidence["observed"]
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0]["failed_conditions"], failed)
        self.assertEqual(observed[0]["author_matches"], "author" not in failed)
        self.assertEqual(observed[0]["signature_present"], "signature" not in failed)
        self.assertEqual(observed[0]["head_present"], "head" not in failed)
        self.assertTrue(observed[0]["comment_id"])

    def test_a_readback_record_distinguishes_the_wrong_login(self) -> None:
        result = self.readback_failure(
            lambda self: self.remote.push(HEAD_B, comment=fix_comment(HEAD_B), author="someone-else")
        )
        self.assert_sole_candidate_failed(result, ["author"])

    def test_a_readback_record_distinguishes_a_missing_signature(self) -> None:
        result = self.readback_failure(
            lambda self: self.remote.push(HEAD_B, comment=f"pushed {HEAD_B}\n")
        )
        self.assert_sole_candidate_failed(result, ["signature"])

    def test_a_readback_record_distinguishes_a_comment_about_the_previous_head(self) -> None:
        result = self.readback_failure(
            lambda self: self.remote.push(HEAD_B, comment=fix_comment(HEAD_A))
        )
        self.assert_sole_candidate_failed(result, ["head"])

    def test_a_readback_record_states_what_was_expected(self) -> None:
        result = self.readback_failure(
            lambda self: self.remote.push(HEAD_B, comment=fix_comment(HEAD_B), author="someone-else")
        )
        evidence = result.failures[0].evidence
        self.assertIn(BUILDER_LOGIN, evidence["expected"])
        self.assertIn(HEAD_B, evidence["expected"])
        self.assertIn("1 comment(s) posted since the builder was invoked", evidence["actual"])

    def test_a_readback_with_no_new_comment_says_so(self) -> None:
        result = self.readback_failure(lambda self: self.remote.push(HEAD_B))
        evidence = result.failures[0].evidence
        self.assertEqual(evidence["observed"], [])
        self.assertEqual(evidence["comments_since_builder_invoked"], 0)
        self.assertIn("no comment was posted", evidence["actual"])

    def test_the_observed_evidence_is_bounded(self) -> None:
        """Enough to name the failing condition on each candidate, never the whole PR."""

        def noisy(self) -> None:
            self.remote.push(HEAD_B)
            for index in range(12):
                self.remote.comment(f"unrelated note {index}\n")

        result = self.readback_failure(noisy)
        evidence = result.failures[0].evidence
        self.assertEqual(evidence["comments_since_builder_invoked"], 12)
        self.assertEqual(len(evidence["observed"]), 10)
        self.assertEqual(evidence["observed_not_described"], 2)

    def test_both_renderings_carry_the_observed_evidence(self) -> None:
        result = self.readback_failure(
            lambda self: self.remote.push(HEAD_B, comment=fix_comment(HEAD_B), author="someone-else")
        )

        markdown = report.to_markdown(result)
        self.assertIn("observed", markdown)
        self.assertIn("author_matches", markdown)
        self.assertIn("failed_conditions", markdown)

        rendered = json.loads(report.to_json(result))["failures"][0]
        self.assertEqual(rendered["evidence"]["observed"][0]["failed_conditions"], ["author"])
        self.assertEqual(rendered["evidence"]["observed"][0]["author"], "someone-else")

    def readback_failure(self, push) -> RunResult:
        """One fix cycle whose push lands and whose fix comment does not read back."""
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["null-deref"]),
            after=lambda: push(self),
        )
        result = loop.run()
        self.assertEqual(self.classes(result), ["readback-mismatch"])
        return result

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


class FailClosedLedgerTests(LoopHarness):
    """PAPI99-RB-002: a fail-closed escalation carries the ledger it reached.

    Stopping after classification does not make the classification stop being
    the subject of the escalation. The report hands Karan the frozen blockers,
    their provenance, and the exact head they were produced against — without
    letting evidence from a head that has since moved ride along.
    """

    def refusal(self) -> RunResult:
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder", builder_output(HEAD_B, addressed=["null-deref"], status="failure")
        )
        result = loop.run()
        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "builder-refusal")
        return result

    def test_a_builder_refusal_still_reports_the_current_head_ledger(self) -> None:
        result = self.refusal()
        self.assertIsNotNone(result.classification)
        self.assertEqual(
            [item.finding.id for item in result.classification.blocking], ["null-deref"]
        )
        self.assertEqual(result.classification_head, HEAD_A)

    def test_the_reported_ledger_is_the_one_the_journal_holds(self) -> None:
        result = self.refusal()
        self.assertEqual(
            result.classification.as_dict(), self.state()["classification"]
        )

    def test_the_escalation_renders_the_blocker_and_its_provenance(self) -> None:
        text = report.to_markdown(self.refusal())
        self.assertIn(f"### Classification (exact head `{HEAD_A}`)", text)
        self.assertIn("`null-deref`", text)
        self.assertIn("found by `A` (role `reviewer`)", text)
        self.assertIn(f"on head `{HEAD_A}`", text)
        self.assertIn("ID=null-deref", text)
        self.assertNotIn("historical evidence only", text)

    def test_the_json_escalation_carries_the_ledger_and_its_head(self) -> None:
        payload = json.loads(report.to_json(self.refusal()))
        self.assertEqual(payload["classification_head"], HEAD_A)
        self.assertEqual(
            [item["id"] for item in payload["classification"]["blocking"]], ["null-deref"]
        )
        self.assertEqual(
            payload["classification"]["blocking"][0]["provenance"]["agent_id"], "A"
        )

    def test_a_stop_before_classification_carries_no_ledger(self) -> None:
        """Nothing is invented: a run that never classified reports nothing to classify."""
        loop = self.build()
        self.script.add("lane-reviewer-A", "looks fine to me\n")

        result = loop.run()

        self.assertEqual(
            [record.failure_class for record in result.failures], ["malformed-verdict"]
        )
        self.assertIsNone(result.classification)
        self.assertIsNone(result.classification_head)
        self.assertNotIn("### Classification", report.to_markdown(result))

    def test_a_stop_after_a_push_does_not_carry_the_old_heads_ledger(self) -> None:
        """Invalidation is untouched: the pushed-away head's findings do not ride along."""
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["null-deref"]),
            after=lambda: self.remote.push(HEAD_B, comment=fix_comment(HEAD_B)),
        )
        self.script.add("lane-reviewer-A", "no marker here\n")

        result = loop.run()

        self.assertEqual(
            [record.failure_class for record in result.failures], ["malformed-verdict"]
        )
        self.assertEqual(result.head, HEAD_B)
        self.assertIsNone(result.classification)
        self.assertNotIn("null-deref", report.to_markdown(result))


class DriftedHeadLedgerTests(LoopHarness):
    """PAPI99-RA2-P1-001 / PAPI99-RB-R1-001 / IA-PAPI99-R1-001.

    Carrying the frozen ledger into a fail-closed report is right only while the
    head it was produced against is still the live one. There are two windows
    where it is not: terminal freshness catching drift, and a push whose head
    agreement succeeded before the fix-comment readback failed. In both, state
    is still bound to the old head because nothing has re-inspected yet, so a
    report that took its head from state alone showed the old ledger under a
    heading naming it the current exact head.

    The reported head is therefore the last head the PR was *observed* on, which
    leaves ``classification_head`` naming the commit the findings came from. The
    two disagreeing is what makes every rendering mark the ledger historical.
    """

    def drift_during_the_last_reviewer(self) -> RunResult:
        """Reviewers classify HEAD_A; the live PR moves to HEAD_B before the attempt."""
        loop = self.build()
        self.script.add("lane-reviewer-A", reviewer_output(HEAD_A, [BLOCKER]))
        self.script.add(
            "lane-reviewer-B", reviewer_output(HEAD_A), after=lambda: self.remote.push(HEAD_B)
        )
        result = loop.run()
        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "stale-head")
        return result

    def readback_failure_after_a_push(self) -> RunResult:
        """The push reaches HEAD_B, then the fix comment is not there to read back."""
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["null-deref"]),
            # Pushed without the signed fix comment: head agreement succeeds and
            # readback is what fails, leaving state bound to HEAD_A.
            after=lambda: self.remote.push(HEAD_B),
        )
        result = loop.run()
        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "readback-mismatch")
        return result

    # -- terminal freshness window ----------------------------------------
    def test_drift_reports_the_head_the_pr_was_last_observed_on(self) -> None:
        result = self.drift_during_the_last_reviewer()
        self.assertEqual(result.head, HEAD_B, "the live PR is on HEAD_B, not the bound head")
        self.assertEqual(result.classification_head, HEAD_A)

    def test_drift_keeps_the_ledger_but_marks_it_historical_in_markdown(self) -> None:
        text = report.to_markdown(self.drift_during_the_last_reviewer())
        self.assertIn(f"### Classification (exact head `{HEAD_A}`)", text)
        self.assertIn("`null-deref`", text)
        self.assertIn("historical evidence only", text)
        self.assertNotIn(f"### Classification (exact head `{HEAD_B}`)", text)

    def test_drift_marks_the_ledger_historical_in_json(self) -> None:
        payload = json.loads(report.to_json(self.drift_during_the_last_reviewer()))
        self.assertEqual(payload["head"], HEAD_B)
        self.assertEqual(payload["classification_head"], HEAD_A)
        self.assertNotEqual(
            payload["head"],
            payload["classification_head"],
            "the JSON reader distinguishes the two heads or it cannot tell the ledger is old",
        )

    # -- post-push / readback window --------------------------------------
    def test_a_readback_failure_reports_the_pushed_head(self) -> None:
        result = self.readback_failure_after_a_push()
        self.assertEqual(result.head, HEAD_B, "push agreement already proved the PR is on HEAD_B")
        self.assertEqual(result.classification_head, HEAD_A)

    def test_a_readback_failure_marks_the_old_ledger_historical(self) -> None:
        result = self.readback_failure_after_a_push()
        self.assertIsNotNone(result.classification)
        self.assertEqual(
            [item.finding.id for item in result.classification.blocking], ["null-deref"]
        )
        text = report.to_markdown(result)
        self.assertIn(f"### Classification (exact head `{HEAD_A}`)", text)
        self.assertIn("historical evidence only", text)

    # -- positive same-head control ---------------------------------------
    def test_a_same_head_stop_still_reports_its_ledger_as_current(self) -> None:
        """Nothing drifted, so the ledger is current and must not be marked historical."""
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["null-deref"], status="failure"),
        )

        result = loop.run()

        self.assertEqual(result.reason, "builder-refusal")
        self.assertEqual(result.head, HEAD_A)
        self.assertEqual(result.classification_head, HEAD_A)
        text = report.to_markdown(result)
        self.assertIn(f"### Classification (exact head `{HEAD_A}`)", text)
        self.assertIn("`null-deref`", text)
        self.assertNotIn("historical evidence only", text)


class InterruptedRestartLedgerTests(LoopHarness):
    """PAPI99-RB-R2-001 / PAPI99-IA-R2-001: an unread head is not a current one.

    A restart that finds ``phase: "attempt-in-flight"`` stops before its first
    GitHub read on purpose: the interrupted attempt may already have pushed, so
    re-inspecting would rebind the run to whatever head is live by then and
    erase the evidence of what that attempt owed. The stop is right; taking the
    report's head from the journal afterwards was not. Nothing observed the live
    PR, so the recorded head A is a head this run has no evidence about — and
    reporting it as ``head`` beside ``classification_head`` A put the
    pre-attempt ledger under a heading claiming the PR is still on A.

    The live head is therefore unknown, and the recorded head is rendered as
    what it is: the commit those findings were produced against, unverified.
    """

    def restart_after_an_interrupted_attempt(self) -> RunResult:
        """Run one attempt that pushes HEAD_B and is killed before verification.

        The journal it leaves is the schema-v3 state the blocker names: recorded
        head A, the ledger classified on A, ``attempt=1``, and
        ``phase="attempt-in-flight"``. The remote is modelled on B, the head the
        dead attempt pushed and no run ever verified.
        """
        first = self.build()
        self.review_round(HEAD_A, [BLOCKER])

        def push_then_die() -> None:
            self.remote.push(HEAD_B, comment=fix_comment(HEAD_B))
            raise KeyboardInterrupt("the run was killed mid-attempt")

        self.script.add(
            "lane-builder", builder_output(HEAD_B, addressed=["null-deref"]), after=push_then_die
        )
        with self.assertRaises(KeyboardInterrupt):
            first.run()

        journal = self.state()
        self.assertEqual(journal["schema_version"], SCHEMA_VERSION)
        self.assertEqual(journal["phase"], PHASE_ATTEMPT_IN_FLIGHT)
        self.assertEqual(journal["attempt"], 1)
        self.assertEqual(journal["head"], HEAD_A)
        self.assertEqual(
            [item["id"] for item in journal["classification"]["blocking"]], ["null-deref"]
        )
        self.assertEqual(self.remote.head, HEAD_B, "the interrupted attempt already pushed")

        second = self.build()
        self.review_round(HEAD_B)
        self.github.pull_request_calls = 0
        self.github.comment_calls = 0
        self.github.commit_calls = 0
        result = second.run()
        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "unexpected-state")
        return result

    def test_the_restart_still_stops_before_any_github_read(self) -> None:
        """The intentional zero-read safety stop is unchanged by the reporting fix."""
        result = self.restart_after_an_interrupted_attempt()

        self.assertEqual(self.github.pull_request_calls, 0)
        self.assertEqual(self.github.comment_calls, 0)
        self.assertEqual(self.github.commit_calls, 0)
        self.assertFalse(self.script.exhausted, "no lane may run on a restart that owes work")
        self.assertEqual(result.evidence["evidence"]["recorded_head"], HEAD_A)
        self.assertEqual(self.state()["head"], HEAD_A, "the recorded head is still not rebound")

    def test_the_restart_reports_no_verified_live_head(self) -> None:
        result = self.restart_after_an_interrupted_attempt()

        self.assertIsNone(result.head, "nothing was read live, so there is no current head")
        self.assertEqual(result.classification_head, HEAD_A)
        self.assertEqual(
            [item.finding.id for item in result.classification.blocking], ["null-deref"]
        )

    def test_the_restart_marks_the_recorded_ledger_unverified_in_markdown(self) -> None:
        text = report.to_markdown(self.restart_after_an_interrupted_attempt())

        self.assertIn("**Head:** `unknown`", text)
        self.assertNotIn(f"**Head:** `{HEAD_A}`", text)
        self.assertNotIn(f"### Classification (exact head `{HEAD_A}`)", text)
        self.assertIn(f"### Classification (recorded head `{HEAD_A}`", text)
        self.assertIn("unverified", text)
        self.assertIn("historical evidence only", text)
        self.assertIn("`null-deref`", text, "the ledger itself is still handed to Karan")

    def test_the_restart_marks_the_recorded_ledger_unverified_in_json(self) -> None:
        payload = json.loads(report.to_json(self.restart_after_an_interrupted_attempt()))

        self.assertIsNone(payload["head"])
        self.assertEqual(payload["classification_head"], HEAD_A)
        self.assertIs(
            payload["classification_head_current"],
            False,
            "a JSON reader is told the ledger is unverified, not left to compare nulls",
        )
        self.assertEqual(
            [item["id"] for item in payload["classification"]["blocking"]], ["null-deref"]
        )
        self.assertEqual(payload["fail_closed"]["evidence"]["recorded_head"], HEAD_A)

    def test_the_recorded_head_is_never_the_reported_current_head(self) -> None:
        """The one thing that must not happen, asserted directly."""
        result = self.restart_after_an_interrupted_attempt()
        payload = json.loads(report.to_json(result))

        self.assertNotEqual(payload["head"], payload["classification_head"])
        self.assertNotEqual(payload["head"], HEAD_A)
        self.assertNotEqual(payload["head"], HEAD_B, "the live head was never observed either")

    # -- positive controls -------------------------------------------------
    def test_an_observed_same_head_ledger_is_still_reported_as_current(self) -> None:
        """The unknown-head rule fires only when nothing was observed."""
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder", builder_output(HEAD_B, addressed=["null-deref"], status="failure")
        )

        payload = json.loads(report.to_json(loop.run()))

        self.assertEqual(payload["head"], HEAD_A)
        self.assertEqual(payload["classification_head"], HEAD_A)
        self.assertIs(payload["classification_head_current"], True)

    def test_a_drifted_ledger_is_still_reported_against_the_observed_head(self) -> None:
        """The two windows the previous cycle closed keep their behaviour."""
        loop = self.build()
        self.script.add("lane-reviewer-A", reviewer_output(HEAD_A, [BLOCKER]))
        self.script.add(
            "lane-reviewer-B", reviewer_output(HEAD_A), after=lambda: self.remote.push(HEAD_B)
        )

        payload = json.loads(report.to_json(loop.run()))

        self.assertEqual(payload["head"], HEAD_B)
        self.assertEqual(payload["classification_head"], HEAD_A)
        self.assertIs(payload["classification_head_current"], False)

    def test_a_clean_run_reports_its_head_as_current(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        payload = json.loads(report.to_json(loop.run()))

        self.assertEqual(payload["head"], HEAD_A)
        self.assertIs(payload["classification_head_current"], True)


class CliStructuredFailureTests(unittest.TestCase):
    """IA-PAPI99-002: a declared class does not get prose instead of a record.

    ``invalid-config`` and ``invalid-command`` stop the run before a
    :class:`RunResult` exists. They are in the shipped taxonomy with playbooks,
    so they reach the same record and the same two renderings as every stop the
    loop itself reaches.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-cli-failure-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.bad = self.tmp / "run.json"
        self.bad.write_text("{}", encoding="utf-8")

    def invoke(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(argv)
        return code, out.getvalue(), err.getvalue()

    def valid_payload(self) -> dict:
        """The smallest config the parser accepts, for one field to be broken in."""
        clone = make_source_repo(self.tmp)
        return {
            "schema_version": CONFIG_SCHEMA_VERSION,
            "repo": "example/repo",
            "pr": 7,
            "governing_issues": [1],
            "source_repo": str(clone),
            "worktree_root": str(self.tmp / "worktrees"),
            "state_file": str(self.tmp / "state.json"),
            "lock_file": str(self.tmp / "run.lock"),
            "gates": [],
            "reviewers": [
                {
                    "name": name,
                    "role": role,
                    "argv": [f"reviewer-{role}", "{head}"],
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

    def test_a_schema_v1_config_reaches_the_cli_as_an_upgrade_record(self) -> None:
        """PAPI90-B-P1-003 at the boundary: a versioned break, said out loud."""
        payload = self.valid_payload()
        payload["schema_version"] = 1
        self.bad.write_text(json.dumps(payload), encoding="utf-8")

        code, out, err = self.invoke(["check-config", "--config", str(self.bad)])
        json_code, json_out, _ = self.invoke(["run", "--config", str(self.bad), "--json"])

        self.assertEqual(code, cli.USAGE_ERROR)
        self.assertEqual(json_code, cli.USAGE_ERROR)
        self.assertIn("invalid-config", out)
        self.assertIn("schema_version 1 is no longer supported", out)
        self.assertIn("set 'schema_version' to 2", out)
        self.assertIn("invalid-config", err)
        record = json.loads(json_out)
        self.assertEqual(record["failure_class"], "invalid-config")
        self.assertEqual(record["evidence"]["found"], 1)
        self.assertEqual(record["evidence"]["expected"], CONFIG_SCHEMA_VERSION)
        self.assertTrue(record["evidence"]["upgrade"])

    def test_a_nul_containing_path_reaches_the_public_cli_as_a_record(self) -> None:
        """RA-P1-003 at the boundary an operator actually types.

        The reproducer was ``check-config`` exiting 1 with zero stdout bytes and
        a ``ValueError: embedded null byte`` traceback. Both shipped commands,
        both renderings, every path field: exit 64 and a structured record.
        """
        for key in ("source_repo", "worktree_root", "state_file", "lock_file"):
            payload = self.valid_payload()
            payload[key] = "/tmp/bad\x00path"
            self.bad.write_text(json.dumps(payload), encoding="utf-8")
            for argv in (
                ["check-config", "--config", str(self.bad)],
                ["run", "--config", str(self.bad)],
                ["run", "--config", str(self.bad), "--json"],
            ):
                with self.subTest(field=key, command=argv[0], json="--json" in argv):
                    code, out, err = self.invoke(argv)

                    self.assertEqual(code, cli.USAGE_ERROR)
                    self.assertTrue(out.strip(), "the record is the output, not a traceback")
                    self.assertNotIn("Traceback", out)
                    self.assertNotIn("Traceback", err)
                    self.assertNotIn("embedded null byte", out + err)
                    self.assertIn("invalid-config", out + err)
                    self.assertIn(key, out)

    def test_the_hostile_path_value_is_not_echoed_on_any_channel(self) -> None:
        payload = self.valid_payload()
        payload["state_file"] = "/tmp/ghp_0123456789abcdefghijABCDEFGHIJ0123\x00/state.json"
        self.bad.write_text(json.dumps(payload), encoding="utf-8")

        code, out, err = self.invoke(["run", "--config", str(self.bad), "--json"])

        self.assertEqual(code, cli.USAGE_ERROR)
        record = json.loads(out)
        self.assertEqual(record["failure_class"], "invalid-config")
        self.assertEqual(record["evidence"], {"key": "state_file"})
        for channel in (out, err):
            self.assertNotIn("ghp_", channel)
            self.assertNotIn("\x00", channel)

    def test_an_invalid_config_emits_the_builder_facing_json_block(self) -> None:
        """The auditor's reproducer: exit 64 with a record, not zero stdout bytes."""
        code, out, err = self.invoke(["run", "--config", str(self.bad), "--json"])

        self.assertEqual(code, cli.USAGE_ERROR)
        record = json.loads(out)
        self.assertEqual(record["failure_class"], "invalid-config")
        self.assertIn("schema_version", record["what_failed"])
        self.assertTrue(record["remediation"])
        self.assertTrue(record["escalation"])
        self.assertIn("invalid-config", err)

    def test_an_invalid_config_emits_the_human_summary_and_the_same_record(self) -> None:
        code, out, _ = self.invoke(["run", "--config", str(self.bad)])

        self.assertEqual(code, cli.USAGE_ERROR)
        self.assertIn("stopped before the run started", out)
        self.assertIn("#### `invalid-config`", out)
        self.assertIn("bounded remediation the builder may attempt", out)
        self.assertIn("escalate instead when:", out)
        fenced = json.loads(out.split("```json")[1].split("```")[0])
        self.assertEqual(fenced["failure_class"], "invalid-config")
        self.assertEqual(fenced["remediation"], list(_STOP_ONLY_STEPS))

    def test_check_config_reports_the_same_record(self) -> None:
        code, out, _ = self.invoke(["check-config", "--config", str(self.bad)])
        self.assertEqual(code, cli.USAGE_ERROR)
        self.assertIn("#### `invalid-config`", out)

    def test_an_absent_config_is_still_a_record(self) -> None:
        code, out, _ = self.invoke(["run", "--config", str(self.tmp / "absent.json"), "--json"])
        self.assertEqual(code, cli.USAGE_ERROR)
        self.assertEqual(json.loads(out)["failure_class"], "invalid-config")

    def test_the_record_passes_the_same_redaction_boundary_as_the_report(self) -> None:
        secret = "ghp_0123456789abcdefghijABCDEFGHIJ0123"
        self.bad.write_text(
            json.dumps({"schema_version": CONFIG_SCHEMA_VERSION, "repo": secret}),
            encoding="utf-8",
        )

        code, out, _ = self.invoke(["run", "--config", str(self.bad), "--json"])

        self.assertEqual(code, cli.USAGE_ERROR)
        self.assertNotIn(secret, out)
        self.assertIn("<redacted>", out)

    def test_the_invalid_command_class_renders_through_the_same_path(self) -> None:
        """The other pre-loop class shares one renderer with the config one above."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cli._fail_closed(
                CommandContractError("gate argv is not a list", evidence={"gate": "tests"}),
                as_json=True,
            )

        self.assertEqual(code, cli.USAGE_ERROR)
        record = json.loads(out.getvalue())
        self.assertEqual(record["failure_class"], "invalid-command")
        self.assertEqual(record["evidence"]["gate"], "tests")
        self.assertTrue(record["remediation"])
        self.assertTrue(record["escalation"])


# A credential-shaped value, used below as both a config *path* and a config
# *value* so the boundary is checked on the two ways a secret reaches these
# failures: the argument the operator typed and the file's own contents.
SECRET = "ghp_0123456789abcdefghijABCDEFGHIJ0123"


class CliRedactionBoundaryTests(unittest.TestCase):
    """PAPI99-RA2-P1-002 / IA-PAPI99-R1-002: one boundary for all three channels.

    ``_fail_closed`` sanitizes a record for stdout and then also prints an
    operator summary on stderr. Deriving that summary from the exception instead
    of from the record put one failure through the boundary twice with two
    different answers, and the unscrubbed answer was the one that reached logs
    and CI capture. Every case here asserts on stderr as well as stdout, in both
    renderings, for both pre-loop classes.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-cli-redaction-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()

    def invoke(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(argv)
        return code, out.getvalue(), err.getvalue()

    def fail_closed(self, exc, *, as_json: bool) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli._fail_closed(exc, as_json=as_json)
        return code, out.getvalue(), err.getvalue()

    # -- invalid-config ----------------------------------------------------
    def test_a_credential_shaped_config_path_is_scrubbed_on_every_channel(self) -> None:
        """The auditor's reproducer: the path the operator typed is the secret."""
        for as_json in (True, False):
            with self.subTest(json=as_json):
                argv = ["run", "--config", str(self.tmp / f"{SECRET}.json")]
                code, out, err = self.invoke(argv + ["--json"] if as_json else argv)

                self.assertEqual(code, cli.USAGE_ERROR, "exit semantics are unchanged")
                self.assertNotIn(SECRET, out)
                self.assertNotIn(SECRET, err, "stderr is a terminal too")
                self.assertIn("<redacted>", err)
                self.assertIn("invalid-config", err)

    def test_a_credential_shaped_config_value_is_scrubbed_on_every_channel(self) -> None:
        bad = self.tmp / "run.json"
        bad.write_text(
            json.dumps({"schema_version": CONFIG_SCHEMA_VERSION, "repo": SECRET}),
            encoding="utf-8",
        )

        for as_json in (True, False):
            with self.subTest(json=as_json):
                argv = ["run", "--config", str(bad)]
                code, out, err = self.invoke(argv + ["--json"] if as_json else argv)

                self.assertEqual(code, cli.USAGE_ERROR)
                self.assertNotIn(SECRET, out)
                self.assertNotIn(SECRET, err)

    # -- invalid-command ---------------------------------------------------
    def test_an_invalid_command_message_is_scrubbed_on_every_channel(self) -> None:
        """The other pre-loop class: the secret is inside the failure message."""
        for as_json in (True, False):
            with self.subTest(json=as_json):
                code, out, err = self.fail_closed(
                    CommandContractError(
                        f"gate argv template carries a literal token {SECRET}",
                        evidence={"gate": "tests", "argv": ["run", f"--token={SECRET}"]},
                    ),
                    as_json=as_json,
                )

                self.assertEqual(code, cli.USAGE_ERROR)
                self.assertNotIn(SECRET, out)
                self.assertNotIn(SECRET, err)
                self.assertIn("<redacted>", err)
                self.assertIn("invalid-command", err)

    # -- one record behind all three channels ------------------------------
    def test_the_stderr_summary_is_the_record_stdout_printed(self) -> None:
        """Not merely scrubbed: the same sanitized record, so they cannot diverge."""
        code, out, err = self.fail_closed(
            ConfigError(f"cannot read {SECRET}", evidence={"path": SECRET}), as_json=True
        )

        self.assertEqual(code, cli.USAGE_ERROR)
        record = json.loads(out)
        self.assertEqual(
            err.strip(),
            f"pr-prover: {record['failure_class']}: {record['what_failed']}",
        )

    def test_exactly_one_structured_record_is_emitted(self) -> None:
        """The stderr line is a summary of the record, not a second record."""
        _, out, err = self.fail_closed(
            ConfigError("schema_version is missing", evidence={}), as_json=True
        )

        json.loads(out)  # stdout is exactly one JSON document
        self.assertEqual(len(err.strip().splitlines()), 1)


# The stop-only playbook, spelled here so the CLI rendering is checked against
# the shipped steps rather than against itself.
_STOP_ONLY_STEPS = (
    "make no further change and push nothing for this head",
    "report the failure verbatim, including the evidence below",
)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
