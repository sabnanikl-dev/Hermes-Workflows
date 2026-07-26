import argparse
import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "linear_work_order.py"
SPEC = importlib.util.spec_from_file_location("linear_work_order", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def state(name, kind):
    return {"id": name.lower().replace(" ", "-"), "name": name, "type": kind}


def issue(identifier, *, issue_state=None, body="Contract", comments=None, blockers=None, children=None):
    return {
        "id": identifier,
        "identifier": identifier,
        "title": f"Work {identifier}",
        "description": body,
        "priority": 2,
        "updatedAt": "2026-07-23T00:00:00.000Z",
        "url": f"https://linear.example/{identifier}",
        "state": issue_state or state("Triage", "unstarted"),
        "children": {"nodes": children or [], "pageInfo": {"hasNextPage": False}},
        "relations": {"nodes": [], "pageInfo": {"hasNextPage": False}},
        "inverseRelations": {"nodes": blockers or [], "pageInfo": {"hasNextPage": False}},
        "comments": {"nodes": comments or [], "pageInfo": {"hasNextPage": False}},
    }


def approval_comment(
    target,
    body,
    *,
    digest=None,
    comment_id="approval-1",
    user_id=None,
    approved_by="Karan",
):
    actual = digest or MODULE.body_sha256(body)
    return {
        "id": comment_id,
        "createdAt": "2026-07-23T01:00:00.000Z",
        "user": {"id": user_id or next(iter(MODULE.PILOT_APPROVER_IDS)), "name": "Karan Sabnani"},
        "body": (
            "WORK_ORDER_APPROVED\n"
            f"Issue: {target}\n"
            f"Body-SHA256: {actual}\n"
            f"Approved-by: {approved_by}"
        ),
    }


def claim_comment(
    target,
    body,
    *,
    digest=None,
    root_id="PAPI-3",
    comment_id="claim-1",
    run_id="run-test-1",
    created_at="2026-07-23T02:00:00.000Z",
    user_id=None,
    include_next_checkpoint=True,
):
    actual = digest or MODULE.body_sha256(body)
    next_checkpoint = "\nNext-checkpoint: evidence review" if include_next_checkpoint else ""
    return {
        "id": comment_id,
        "createdAt": created_at,
        "user": {"id": user_id or next(iter(MODULE.PILOT_CLAIMER_IDS)), "name": "Karan Sabnani"},
        "body": (
            "WORK_ORDER_CLAIM\n"
            f"Run-ID: {run_id}\n"
            f"Root: {root_id}\n"
            f"Issue: {target}\n"
            f"Body-SHA256: {actual}\n"
            "Claimed-by: Default Hermes\n"
            "Execution-lane: default-hermes\n"
            "Allowed-outputs: Linear updates and local artifacts\n"
            "Started-at: 2026-07-23T02:00:00Z"
            f"{next_checkpoint}"
        ),
    }


def root(*children):
    order = "\n".join(
        f"{index}. [{child['identifier']}](https://linear.example/{child['identifier']})"
        for index, child in enumerate(children, 1)
    )
    return {
        "id": "PAPI-3",
        "identifier": "PAPI-3",
        "title": "Root",
        "description": f"## Child issues and intended order\n\n### Core implementation\n\n{order}\n\n## Verification\n",
        "priority": 2,
        "updatedAt": "2026-07-23T00:00:00.000Z",
        "url": "https://linear.example/PAPI-3",
        "state": state("In Progress", "started"),
        "children": {"nodes": list(children), "pageInfo": {"hasNextPage": False}},
    }


class LinearWorkOrderTests(unittest.TestCase):
    def test_selects_one_valid_ready_issue(self):
        body = "Approved contract"
        first = issue(
            "PAPI-76",
            issue_state=state("Ready", "unstarted"),
            body=body,
            comments=[approval_comment("PAPI-76", body)],
        )
        second = issue("PAPI-77")
        report = MODULE.inspect_root(root(first, second))
        self.assertEqual("SELECTED", report["result"])
        self.assertEqual("ready_for_claim", report["lifecycle_diagnostic"]["classification"])
        self.assertEqual("PAPI-76", report["selected"]["identifier"])
        self.assertTrue(report["selected"]["approval"]["valid"])

    def test_active_issue_without_claim_fails_closed(self):
        active = issue("PAPI-82", issue_state=state("In Progress", "started"))
        report = MODULE.inspect_root(root(active))
        self.assertEqual("CONFLICT", report["result"])
        self.assertIsNone(report["selected"])
        self.assertFalse(report["active"][0]["claim"]["valid"])
        self.assertTrue(any("no valid WORK_ORDER_CLAIM marker" in warning for warning in report["warnings"]))

    def test_conflict_human_output_names_active_issue(self):
        active = issue("PAPI-82", issue_state=state("In Progress", "started"))
        report = MODULE.inspect_root(root(active))
        text = MODULE.format_human(report)
        self.assertIn("STATE: CONFLICT", text)
        self.assertIn("PAPI-82", text)
        self.assertIn("no valid WORK_ORDER_CLAIM marker", text)

    def test_resumes_single_validly_claimed_active_issue_before_new_work(self):
        active_body = "Bootstrap contract"
        active = issue(
            "PAPI-82",
            issue_state=state("In Progress", "started"),
            body=active_body,
            comments=[claim_comment("PAPI-82", active_body)],
        )
        ready_body = "Ready later"
        ready = issue(
            "PAPI-76",
            issue_state=state("Ready", "unstarted"),
            body=ready_body,
            comments=[approval_comment("PAPI-76", ready_body)],
        )
        report = MODULE.inspect_root(root(active, ready))
        self.assertEqual("RESUME_ACTIVE", report["result"])
        self.assertEqual("resume_active_claim", report["lifecycle_diagnostic"]["classification"])
        self.assertEqual("PAPI-82", report["selected"]["identifier"])
        self.assertTrue(report["selected"]["claim"]["valid"])

    def test_material_edit_invalidates_active_claim(self):
        old_body = "Bootstrap contract"
        changed_body = old_body + "\n\nChanged scope"
        active = issue(
            "PAPI-82",
            issue_state=state("In Progress", "started"),
            body=changed_body,
            comments=[claim_comment("PAPI-82", changed_body, digest=MODULE.body_sha256(old_body))],
        )
        report = MODULE.inspect_root(root(active))
        self.assertEqual("CONFLICT", report["result"])
        self.assertEqual("digest_revision_mismatch", report["lifecycle_diagnostic"]["classification"])
        self.assertIn("invalidated", report["active"][0]["claim"]["reason"])

    def test_multiple_active_children_fail_closed(self):
        one = issue("PAPI-82", issue_state=state("In Progress", "started"))
        two = issue("PAPI-76", issue_state=state("In Review", "started"))
        report = MODULE.inspect_root(root(one, two))
        self.assertEqual("CONFLICT", report["result"])
        self.assertIsNone(report["selected"])
        self.assertEqual(2, len(report["active"]))

    def test_open_dependency_blocks_ready_issue(self):
        blocker_ref = {
            "id": "PAPI-82",
            "identifier": "PAPI-82",
            "title": "Bootstrap",
            "state": state("In Progress", "started"),
        }
        body = "Approved but blocked"
        blocked = issue(
            "PAPI-76",
            issue_state=state("Ready", "unstarted"),
            body=body,
            comments=[approval_comment("PAPI-76", body)],
            blockers=[{"id": "relation-1", "type": "blocks", "issue": blocker_ref}],
        )
        blocker = issue("PAPI-82", issue_state=state("Triage", "unstarted"))
        report = MODULE.inspect_root(root(blocker, blocked))
        self.assertEqual("NO_ELIGIBLE_WORK", report["result"])
        self.assertEqual("PAPI-76", report["blocked"][0]["identifier"])
        self.assertEqual("open blocking dependency", report["blocked"][0]["reason"])

    def test_marker_prefix_is_not_accepted(self):
        body = "WORK_ORDER_APPROVED_NOT_REALLY\nIssue: PAPI-76\nBody-SHA256: " + ("a" * 64)
        self.assertIsNone(MODULE.parse_marker(body, MODULE.APPROVAL_MARKER))

    def test_material_edit_invalidates_approval(self):
        old_body = "Original contract"
        changed_body = "Original contract\n\nMaterial new requirement"
        stale = issue(
            "PAPI-76",
            issue_state=state("Ready", "unstarted"),
            body=changed_body,
            comments=[
                approval_comment(
                    "PAPI-76",
                    changed_body,
                    digest=MODULE.body_sha256(old_body),
                )
            ],
        )
        report = MODULE.inspect_root(root(stale))
        self.assertEqual("NO_ELIGIBLE_WORK", report["result"])
        self.assertIn("invalidated", report["blocked"][0]["reason"])

    def test_no_ready_issue_returns_no_eligible_work(self):
        triage = issue("PAPI-76", issue_state=state("Triage", "unstarted"))
        report = MODULE.inspect_root(root(triage))
        self.assertEqual("NO_ELIGIBLE_WORK", report["result"])
        self.assertEqual("PAPI-76", report["parked"][0]["identifier"])

    def test_out_of_scope_blocker_is_reported_and_blocks(self):
        body = "Approved contract"
        blocked = issue(
            "PAPI-76",
            issue_state=state("Ready", "unstarted"),
            body=body,
            comments=[approval_comment("PAPI-76", body)],
            blockers=[
                {
                    "id": "relation-outside",
                    "type": "blocks",
                    "issue": {
                        "id": "PAPI-999",
                        "identifier": "PAPI-999",
                        "title": "External blocker",
                        "state": state("In Progress", "started"),
                    },
                }
            ],
        )
        report = MODULE.inspect_root(root(blocked))
        self.assertEqual("NO_ELIGIBLE_WORK", report["result"])
        self.assertFalse(report["blocked"][0]["open_blockers"][0]["in_scope"])
        self.assertTrue(any("outside the root hierarchy" in warning for warning in report["warnings"]))

    def test_prose_cross_reference_does_not_change_order_category(self):
        bootstrap = issue("PAPI-82", issue_state=state("In Progress", "started"))
        first = issue("PAPI-76")
        packet = root(bootstrap, first)
        packet["description"] = (
            "## Child issues and intended order\n\n"
            "### Linear bootstrap\n\n"
            "0. [PAPI-82](https://linear.example/PAPI-82) — finish before PAPI-76.\n\n"
            "### Core implementation\n\n"
            "1. [PAPI-76](https://linear.example/PAPI-76)\n\n"
            "## Verification\n"
        )
        report = MODULE.inspect_root(packet)
        blocked_or_parked = report["blocked"] + report["parked"]
        target = next(item for item in blocked_or_parked if item["identifier"] == "PAPI-76")
        self.assertEqual("Core implementation", target["category"])

    def test_one_missing_direct_child_makes_queue_invalid(self):
        first = issue("PAPI-76")
        omitted = issue("PAPI-77", issue_state=state("In Progress", "started"))
        packet = root(first, omitted)
        packet["description"] = (
            "## Child issues and intended order\n\n"
            "### Core implementation\n\n"
            "1. [PAPI-76](https://linear.example/PAPI-76)\n\n"
            "## Verification\n"
        )
        report = MODULE.inspect_root(packet)
        self.assertEqual("QUEUE_INVALID", report["result"])
        self.assertTrue(any("PAPI-77" in warning for warning in report["warnings"]))

    def test_duplicate_direct_child_makes_queue_invalid(self):
        first = issue("PAPI-76")
        packet = root(first)
        packet["description"] = (
            "## Child issues and intended order\n\n"
            "### Core implementation\n\n"
            "1. [PAPI-76](https://linear.example/PAPI-76)\n"
            "2. [PAPI-76](https://linear.example/PAPI-76)\n\n"
            "## Verification\n"
        )
        report = MODULE.inspect_root(packet)
        self.assertEqual("QUEUE_INVALID", report["result"])
        self.assertTrue(any("duplicated" in warning for warning in report["warnings"]))

    def test_unauthorized_approval_commenter_cannot_select(self):
        body = "Approved contract"
        candidate = issue(
            "PAPI-76",
            issue_state=state("Ready", "unstarted"),
            body=body,
            comments=[approval_comment("PAPI-76", body, user_id="mallory-user-id")],
        )
        report = MODULE.inspect_root(root(candidate))
        self.assertEqual("NO_ELIGIBLE_WORK", report["result"])
        self.assertIn("not authorized", report["blocked"][0]["reason"])

    def test_approved_by_field_must_name_karan(self):
        body = "Approved contract"
        candidate = issue(
            "PAPI-76",
            issue_state=state("Ready", "unstarted"),
            body=body,
            comments=[approval_comment("PAPI-76", body, approved_by="Mallory")],
        )
        report = MODULE.inspect_root(root(candidate))
        self.assertEqual("NO_ELIGIBLE_WORK", report["result"])
        self.assertIn("malformed", report["blocked"][0]["reason"])

    def test_duplicate_current_claims_conflict(self):
        body = "Bootstrap contract"
        claims = [
            claim_comment(
                "PAPI-82",
                body,
                comment_id="claim-1",
                run_id="run-test-1",
                created_at="2026-07-23T02:00:00.000Z",
            ),
            claim_comment(
                "PAPI-82",
                body,
                comment_id="claim-2",
                run_id="run-test-2",
                created_at="2026-07-23T03:00:00.000Z",
            ),
        ]
        active = issue(
            "PAPI-82",
            issue_state=state("In Progress", "started"),
            body=body,
            comments=claims,
        )
        report = MODULE.inspect_root(root(active))
        self.assertEqual("CONFLICT", report["result"])
        self.assertEqual(
            "duplicate_or_already_applied_control_plane_action",
            report["lifecycle_diagnostic"]["classification"],
        )
        self.assertIn("multiple current valid claims", report["active"][0]["claim"]["reason"])

    def test_claim_requires_next_checkpoint(self):
        body = "Bootstrap contract"
        active = issue(
            "PAPI-82",
            issue_state=state("In Progress", "started"),
            body=body,
            comments=[claim_comment("PAPI-82", body, include_next_checkpoint=False)],
        )
        report = MODULE.inspect_root(root(active))
        self.assertEqual("CONFLICT", report["result"])
        self.assertIn("next-checkpoint", report["active"][0]["claim"]["reason"])

    def test_claim_requires_authorized_linear_actor(self):
        body = "Bootstrap contract"
        active = issue(
            "PAPI-82",
            issue_state=state("In Progress", "started"),
            body=body,
            comments=[claim_comment("PAPI-82", body, user_id="mallory-user-id")],
        )
        report = MODULE.inspect_root(root(active))
        self.assertEqual("CONFLICT", report["result"])
        self.assertIn("not authorized", report["active"][0]["claim"]["reason"])

    def test_truncated_root_children_fail_closed(self):
        packet = root(issue("PAPI-76"))
        packet["children"]["pageInfo"]["hasNextPage"] = True
        report = MODULE.inspect_root(packet)
        self.assertEqual("QUEUE_INVALID", report["result"])
        self.assertTrue(any("Root child list is truncated" in warning for warning in report["warnings"]))

    def test_truncated_child_connections_fail_closed(self):
        for connection_name in ("relations", "inverseRelations", "comments", "children"):
            with self.subTest(connection=connection_name):
                child = issue("PAPI-76")
                child[connection_name]["pageInfo"]["hasNextPage"] = True
                report = MODULE.inspect_root(root(child))
                self.assertEqual("QUEUE_INVALID", report["result"])
                self.assertTrue(any(connection_name in warning for warning in report["warnings"]))

    def test_out_of_scope_descendant_fails_closed(self):
        descendant = {
            "id": "PAPI-900",
            "identifier": "PAPI-900",
            "title": "Hidden active descendant",
            "state": state("In Progress", "started"),
        }
        child = issue("PAPI-76", children=[descendant])
        report = MODULE.inspect_root(root(child))
        self.assertEqual("QUEUE_INVALID", report["result"])
        self.assertTrue(any("PAPI-900" in warning for warning in report["warnings"]))

    def test_explicit_order_is_ranking_and_live_relations_define_dependencies(self):
        earlier = issue("PAPI-76", issue_state=state("Triage", "unstarted"))
        body = "Independent approved work"
        later = issue(
            "PAPI-77",
            issue_state=state("Ready", "unstarted"),
            body=body,
            comments=[approval_comment("PAPI-77", body)],
        )
        report = MODULE.inspect_root(root(earlier, later))
        self.assertEqual("SELECTED", report["result"])
        self.assertEqual("PAPI-77", report["selected"]["identifier"])

    def test_duplicate_marker_keys_are_rejected(self):
        marker = (
            "WORK_ORDER_APPROVED\n"
            "Issue: PAPI-76\n"
            "Issue: PAPI-77\n"
            f"Body-SHA256: {'a' * 64}\n"
            "Approved-by: Karan"
        )
        self.assertIsNone(MODULE.parse_marker(marker, MODULE.APPROVAL_MARKER))

    def test_non_pilot_live_root_is_rejected_before_fetch(self):
        args = argparse.Namespace(root="JMD-1", fixture=None, json=True)
        with self.assertRaisesRegex(MODULE.LinearError, "outside the pilot allowlist"):
            MODULE.command_inspect(args)

    def test_missing_child_order_fails_closed(self):
        child = issue("PAPI-76")
        invalid_root = root(child)
        invalid_root["description"] = "No explicit queue here"
        report = MODULE.inspect_root(invalid_root)
        self.assertEqual("QUEUE_INVALID", report["result"])


if __name__ == "__main__":
    unittest.main()
