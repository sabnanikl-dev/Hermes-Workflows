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

from _support import BUILDER_LOGIN, HEAD_A, HEAD_B, builder_output, fix_comment, reviewer_output
from pr_prover import cli
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
            json.dumps({"schema_version": 1, "repo": secret}), encoding="utf-8"
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


# The stop-only playbook, spelled here so the CLI rendering is checked against
# the shipped steps rather than against itself.
_STOP_ONLY_STEPS = (
    "make no further change and push nothing for this head",
    "report the failure verbatim, including the evidence below",
)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
