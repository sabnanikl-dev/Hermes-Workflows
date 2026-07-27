"""Fix cycles, and what does and does not travel between them.

Each cycle launches the builder as a new process with a new prompt and a new
blocker file. There is no resume path, so "fresh context" is a property of the
launch rather than a flag somewhere — and what has to survive between cycles
travels through the run state file, which is the thing these tests pin down.

Also here: the report fields that keep transport, verdict, and readiness apart,
because a run that blurs them is one where "the artifact landed" can be read as
"the head is ready".
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from _support import (
    HEAD_A,
    HEAD_B,
    HEAD_C,
    builder_output,
    fix_comment,
    reviewer_output,
)
from pr_prover.commands import RUNNER_DEFAULT
from pr_prover.loop import BLOCKED, MERGE_READY, NEEDS_KARAN
from pr_prover.report import as_dict, to_markdown
from test_loop import BLOCKER, SECOND_BLOCKER, LoopHarness


class FreshBuilderContextTests(LoopHarness):
    def two_cycles(self) -> None:
        """Blocked on A, fixed to B, still blocked on B, fixed to C, clean."""
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["null-deref"]),
            after=lambda: self.remote.push(HEAD_B, comment=fix_comment(HEAD_B)),
        )
        self.review_round(HEAD_B, [SECOND_BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_C, addressed=["bad-copy"]),
            after=lambda: self.remote.push(HEAD_C, comment=fix_comment(HEAD_C)),
        )
        self.review_round(HEAD_C)

    def builder_calls(self) -> list[tuple[str, ...]]:
        return [call.argv for call in self.runner.calls if call.argv[0] == "lane-builder"]

    def test_each_cycle_is_a_separate_launch_with_its_own_blocker_file(self) -> None:
        """No resume flag, no session id, no shared file: two independent launches."""
        loop = self.build()
        self.two_cycles()

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertEqual(result.attempts_used, 2)
        calls = self.builder_calls()
        self.assertEqual(len(calls), 2)
        first = calls[0][calls[0].index("--blockers") + 1]
        second = calls[1][calls[1].index("--blockers") + 1]
        self.assertNotEqual(first, second)
        self.assertIn("attempt1", Path(first).name)
        self.assertIn("attempt2", Path(second).name)

    def test_cycle_two_is_grounded_on_its_own_head_and_its_own_ledger(self) -> None:
        """Re-grounding is the point: nothing about cycle 1 is carried forward."""
        loop = self.build()
        self.two_cycles()
        loop.run()

        calls = self.builder_calls()
        self.assertEqual(calls[0][calls[0].index("--head") + 1], HEAD_A)
        self.assertEqual(calls[1][calls[1].index("--head") + 1], HEAD_B)

        second = self.runner.blocker_files[1]
        self.assertEqual(second["head"], HEAD_B)
        self.assertEqual(second["attempt"], 2)
        self.assertEqual([item["id"] for item in second["blockers"]], ["bad-copy"])
        # Cycle 1's blocker is gone, not carried forward as context.
        self.assertNotIn("null-deref", json.dumps(second))

    def test_the_blocker_file_carries_the_structured_failure_records(self) -> None:
        """The builder's next instructions are data, not prose it has to parse."""
        loop = self.build(gates=[{"name": "tests", "argv": ["lane-gate"]}])
        self.script.add("lane-gate", "boom\n", returncode=1)
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["gate-tests"]),
            after=lambda: self.remote.push(HEAD_B, comment=fix_comment(HEAD_B)),
        )
        self.script.add("lane-gate", "", returncode=0)
        self.review_round(HEAD_B)

        loop.run()

        records = self.runner.blocker_files[0]["next_instructions"]
        self.assertEqual([record["finding_id"] for record in records], ["gate-tests"])
        record = records[0]
        self.assertTrue(record["what_failed"])
        self.assertTrue(record["evidence"]["command"])
        self.assertTrue(record["remediation"])
        self.assertTrue(record["escalation"])

    def test_continuity_between_cycles_lives_only_in_the_state_file(self) -> None:
        """Attempt number, spent reruns, bound head, owned artifacts — all journalled."""
        loop = self.build()
        self.two_cycles()
        loop.run()

        journal = self.state()
        self.assertEqual(journal["attempt"], 2)
        self.assertEqual(journal["head"], HEAD_C)
        self.assertEqual(journal["phase"], "idle")
        self.assertEqual(journal["outcome"], MERGE_READY)
        self.assertTrue(journal["verified_artifacts"])

    def test_a_third_cycle_is_unreachable(self) -> None:
        """The cap is structural: no third attempt can open, whatever is still open."""
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["null-deref"]),
            after=lambda: self.remote.push(HEAD_B, comment=fix_comment(HEAD_B)),
        )
        self.review_round(HEAD_B, [BLOCKER])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_C, addressed=["null-deref"]),
            after=lambda: self.remote.push(HEAD_C, comment=fix_comment(HEAD_C)),
        )
        self.review_round(HEAD_C, [BLOCKER])

        result = loop.run()

        self.assertEqual(result.outcome, BLOCKED)
        self.assertEqual(result.reason, "attempt-cap-reached")
        self.assertEqual(result.attempts_used, 2)
        self.assertEqual(len(self.builder_calls()), 2)


class LaneBudgetTests(LoopHarness):
    def test_each_lane_is_handed_its_own_configured_budget(self) -> None:
        """One configured value, enforced and reported — no hidden cap underneath."""
        loop = self.build(
            gates=[{"name": "tests", "argv": ["lane-gate"], "timeout": 30}],
            reviewers=None,
        )
        self.script.add("lane-gate", "", returncode=0)
        self.review_round(HEAD_A)

        loop.run()

        budgets = dict(self.runner.lane_budgets)
        self.assertEqual(budgets["lane-gate"], 30.0)
        # Lanes with no configured timeout are handed None — "no deadline" —
        # rather than falling through to the runner's own default.
        self.assertIsNone(budgets["lane-reviewer-A"])
        self.assertIsNot(budgets["lane-reviewer-A"], RUNNER_DEFAULT)

    def test_the_run_log_says_a_lane_ran_and_how_it_ended(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertTrue(any("launched" in event for event in result.events))
        self.assertTrue(any("exited after" in event for event in result.events))
        self.assertTrue(any("budget unbounded" in event for event in result.events))
        self.assertEqual(
            [lane.lane for lane in result.lanes],
            [
                "reviewer A",
                "relay A",
                "reviewer B",
                "relay B",
                "reviewer Auditor",
                "relay Auditor",
            ],
        )
        self.assertTrue(all(lane.state == "exited" for lane in result.lanes))


class ReportSeparationTests(LoopHarness):
    """Transport, implementation verdict, and exact-head readiness stay apart."""

    def test_a_clean_run_reports_all_three_separately(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        payload = as_dict(loop.run())

        # Transport: the artifacts reached GitHub under the configured identity.
        self.assertTrue(payload["transport_complete"])
        self.assertEqual(len(payload["transport"]), 3)
        # Implementation verdict: what the reviews concluded.
        self.assertEqual([item["status"] for item in payload["reviewers"]], ["pass"] * 3)
        # Exact-head readiness: the outcome, tied to the observed head.
        self.assertEqual(payload["outcome"], MERGE_READY)
        self.assertEqual(payload["head"], HEAD_A)
        self.assertTrue(payload["classification_head_current"])

    def test_complete_transport_does_not_imply_a_passing_verdict(self) -> None:
        """The case the separation exists for: everything landed, nothing passed."""
        loop = self.build()
        self.review_round(HEAD_A, [BLOCKER])
        self.remote.comment("please hold", author="karan")

        payload = as_dict(loop.run())

        self.assertTrue(payload["transport_complete"], "all three artifacts landed")
        self.assertEqual([item["status"] for item in payload["reviewers"]], ["fail", "pass", "pass"])
        self.assertEqual(payload["outcome"], NEEDS_KARAN)
        self.assertEqual(len(payload["classification"]["blocking"]), 1)

    def test_the_markdown_says_transport_is_not_a_verdict(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        rendered = to_markdown(loop.run())

        self.assertIn("### Artifact transport (not a verdict)", rendered)
        self.assertIn("ROLE=integration-auditor", rendered)
        self.assertIn("### Lanes", rendered)

    def test_an_incomplete_transport_says_exactly_how_far_it_got(self) -> None:
        """"Prepared but never published" and "never prepared" are different bugs."""
        loop = self.build()
        self.review_round(HEAD_A)
        self.runner.relay_failures = 1

        result = loop.run()
        payload = as_dict(result)

        self.assertFalse(payload["transport_complete"])
        self.assertTrue(payload["transport"][0]["prepared"])
        self.assertFalse(payload["transport"][0]["published"])
        self.assertIn("prepared, not published", to_markdown(result))

    def test_the_report_never_claims_merge_authority(self) -> None:
        """Merge stays Karan's; no field here is permission, and none says approved."""
        loop = self.build()
        self.review_round(HEAD_A)
        rendered = to_markdown(loop.run()).lower()
        for forbidden in ("approved to merge", "merging now", "you may merge"):
            self.assertNotIn(forbidden, rendered)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
