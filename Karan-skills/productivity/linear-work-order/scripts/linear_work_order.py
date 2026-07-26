#!/usr/bin/env python3
"""Read-only Linear hierarchy inspector and deterministic work selector."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable

ENDPOINT = "https://api.linear.app/graphql"
APPROVAL_MARKER = "WORK_ORDER_APPROVED"
CLAIM_MARKER = "WORK_ORDER_CLAIM"
READY_STATE = "Ready"
PILOT_ROOTS = {"PAPI-3"}
PILOT_APPROVER_IDS = {"7499695b-ecce-444b-af2a-96d9a71618c9"}
PILOT_CLAIMER_IDS = {"7499695b-ecce-444b-af2a-96d9a71618c9"}
TERMINAL_TYPES = {"completed", "canceled", "duplicate"}
STARTED_TYPE = "started"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_CHECKPOINTS = {
    "clean_idle": "No active claimed child is present; Default Hermes may select the first eligible approved issue and create one revision-bound claim.",
    "active_worker_lock": "A local launcher reports active ownership; wait and rerun local launcher diagnostics before cleanup or relaunch.",
    "stale_consumed_grant": "Use launcher residue diagnostics/recovery for the exact grant/run; the hierarchy inspector remains read-only.",
    "stale_task_skill_residue": "Use launcher residue diagnostics/recovery for the exact grant/run; the hierarchy inspector remains read-only.",
    "digest_revision_mismatch": "Stop and request fresh human approval/claim for the current issue body digest before execution.",
    "duplicate_or_already_applied_control_plane_action": "Do not create another claim/action; return to Default Hermes to review the existing current marker.",
    "ready_for_claim": "Default Hermes may create exactly one revision-bound claim for the selected issue if still current.",
    "resume_active_claim": "Resume or review the active claimed child; do not select new work.",
    "queue_invalid": "Stop and repair the parent hierarchy/order before selecting or launching work.",
}

ISSUE_QUERY = r"""
query($id: String!) {
  issue(id: $id) {
    id identifier title description priority createdAt updatedAt url
    state { id name type }
    assignee { id name }
    parent { id identifier title }
    children(first: 100) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id identifier title description priority createdAt updatedAt url
        state { id name type }
        assignee { id name }
        children(first: 100) {
          pageInfo { hasNextPage endCursor }
          nodes { id identifier title state { id name type } }
        }
        relations(first: 100) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id type
            relatedIssue { id identifier title state { id name type } }
          }
        }
        inverseRelations(first: 100) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id type
            issue { id identifier title state { id name type } }
          }
        }
        comments(first: 100) {
          pageInfo { hasNextPage endCursor }
          nodes { id body createdAt user { id name } }
        }
      }
    }
  }
}
"""


class LinearError(RuntimeError):
    pass


@dataclass(frozen=True)
class Approval:
    valid: bool
    reason: str
    comment_id: str | None = None
    approved_by: str | None = None
    digest: str | None = None


@dataclass(frozen=True)
class Claim:
    valid: bool
    reason: str
    comment_id: str | None = None
    run_id: str | None = None
    claimed_by: str | None = None
    digest: str | None = None
    fields: dict[str, str] | None = None


def normalize_body(body: str | None) -> str:
    """Normalize inconsequential line-ending/trailing-space drift before hashing."""
    text = (body or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip() + "\n"


def body_sha256(body: str | None) -> str:
    return hashlib.sha256(normalize_body(body).encode("utf-8")).hexdigest()


def graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    key = os.environ.get("LINEAR_API_KEY")
    if not key:
        raise LinearError("LINEAR_API_KEY is not set")
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Authorization": key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LinearError(f"Linear HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LinearError(f"Linear request failed: {exc}") from exc
    if result.get("errors"):
        raise LinearError(json.dumps(result["errors"], indent=2))
    return result["data"]


def fetch_root(identifier: str) -> dict[str, Any]:
    data = graphql(ISSUE_QUERY, {"id": identifier})
    root = data.get("issue")
    if not root:
        raise LinearError(f"Linear issue not found: {identifier}")
    return root


def parse_marker(body: str | None, marker: str) -> dict[str, str] | None:
    if not body:
        return None
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if not lines or lines[0] != marker:
        return None
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if ":" not in line:
            return None
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if not key or not value or key in fields:
            return None
        fields[key] = value
    return fields


def approval_for(issue: dict[str, Any]) -> Approval:
    expected = body_sha256(issue.get("description"))
    approvals: list[tuple[str, dict[str, str], dict[str, Any]]] = []
    for comment in issue.get("comments", {}).get("nodes", []):
        fields = parse_marker(comment.get("body"), APPROVAL_MARKER)
        if fields is not None:
            approvals.append((comment.get("createdAt") or "", fields, comment))
    if not approvals:
        return Approval(False, "missing digest-bound approval comment", digest=expected)
    approvals.sort(key=lambda item: item[0], reverse=True)
    stale: list[str] = []
    malformed: list[str] = []
    unauthorized: list[str] = []
    for _, fields, comment in approvals:
        issue_ref = fields.get("issue")
        digest = fields.get("body-sha256", "").lower()
        approved_by = fields.get("approved-by")
        commenter_id = (comment.get("user") or {}).get("id")
        if issue_ref != issue.get("identifier") or not HEX64.fullmatch(digest) or approved_by != "Karan":
            malformed.append(comment.get("id") or "unknown")
            continue
        if commenter_id not in PILOT_APPROVER_IDS:
            unauthorized.append(comment.get("id") or "unknown")
            continue
        if digest == expected:
            return Approval(
                True,
                "approval digest matches current issue body and authorized Linear commenter",
                comment_id=comment.get("id"),
                approved_by=approved_by,
                digest=digest,
            )
        stale.append(comment.get("id") or "unknown")
    if stale:
        return Approval(
            False,
            "material issue edit invalidated the latest authorized approval",
            comment_id=stale[0],
            digest=expected,
        )
    if unauthorized:
        return Approval(
            False,
            "approval commenter is not authorized for the PAPI-3 pilot",
            comment_id=unauthorized[0],
            digest=expected,
        )
    return Approval(
        False,
        "approval comment is malformed",
        comment_id=malformed[0] if malformed else None,
        digest=expected,
    )


def claim_for(issue: dict[str, Any], root_identifier: str) -> Claim:
    expected = body_sha256(issue.get("description"))
    claims: list[tuple[str, dict[str, str], dict[str, Any]]] = []
    for comment in issue.get("comments", {}).get("nodes", []):
        fields = parse_marker(comment.get("body"), CLAIM_MARKER)
        if fields is not None:
            claims.append((comment.get("createdAt") or "", fields, comment))
    if not claims:
        return Claim(False, "active issue has no valid WORK_ORDER_CLAIM marker", digest=expected)

    claims.sort(key=lambda item: item[0], reverse=True)
    evaluated: list[Claim] = []
    required = (
        "run-id",
        "claimed-by",
        "execution-lane",
        "allowed-outputs",
        "started-at",
        "next-checkpoint",
    )
    for _, fields, comment in claims:
        issue_ref = fields.get("issue")
        root_ref = fields.get("root")
        digest = fields.get("body-sha256", "").lower()
        missing = [key for key in required if not fields.get(key)]
        base = {
            "comment_id": comment.get("id"),
            "run_id": fields.get("run-id"),
            "claimed_by": fields.get("claimed-by"),
            "digest": expected,
            "fields": fields,
        }
        if issue_ref != issue.get("identifier"):
            evaluated.append(Claim(False, "claim issue identifier does not match active issue", **base))
        elif root_ref != root_identifier:
            evaluated.append(Claim(False, "claim root does not match inspected hierarchy", **base))
        elif (comment.get("user") or {}).get("id") not in PILOT_CLAIMER_IDS:
            evaluated.append(Claim(False, "claim commenter is not authorized for the PAPI-3 pilot", **base))
        elif not HEX64.fullmatch(digest):
            evaluated.append(Claim(False, "claim body digest is malformed", **base))
        elif digest != expected:
            evaluated.append(Claim(False, "material issue edit invalidated the active claim", **base))
        elif missing:
            evaluated.append(
                Claim(False, "claim marker is missing required fields: " + ", ".join(missing), **base)
            )
        else:
            evaluated.append(Claim(True, "claim digest, scope, actor, and required fields match", **base))

    current_valid = [claim for claim in evaluated if claim.valid]
    if len(current_valid) > 1:
        latest = current_valid[0]
        run_ids = sorted({claim.run_id or "missing" for claim in current_valid})
        conflict_fields = dict(latest.fields or {})
        conflict_fields["conflicting-run-ids"] = ", ".join(run_ids)
        return Claim(
            False,
            "multiple current valid claims conflict for the active issue",
            comment_id=latest.comment_id,
            run_id=latest.run_id,
            claimed_by=latest.claimed_by,
            digest=expected,
            fields=conflict_fields,
        )
    if len(current_valid) == 1:
        return current_valid[0]
    return evaluated[0]


def unique_in_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def parse_order(root: dict[str, Any], child_ids: set[str]) -> tuple[list[str], dict[str, str], list[str]]:
    body = root.get("description") or ""
    match = re.search(
        r"^## Child issues and intended order\s*$([\s\S]*?)(?=^##\s|\Z)",
        body,
        flags=re.MULTILINE,
    )
    if not match:
        return [], {}, ["Root is missing a 'Child issues and intended order' section"]
    section = match.group(1)
    prefix = root.get("identifier", "").split("-", 1)[0]
    link_pattern = re.compile(rf"\[({re.escape(prefix)}-\d+)\]")
    linked = [value for value in link_pattern.findall(section) if value in child_ids]
    order = unique_in_order(linked)
    categories: dict[str, str] = {}
    current = "uncategorized"
    for line in section.splitlines():
        heading = re.match(r"^###\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip()
        for identifier in link_pattern.findall(line):
            if identifier in child_ids and identifier not in categories:
                categories[identifier] = current
    warnings: list[str] = []
    missing = sorted(child_ids - set(order))
    if missing:
        warnings.append("Direct children missing from explicit order: " + ", ".join(missing))
    duplicates = sorted({identifier for identifier in linked if linked.count(identifier) > 1})
    if duplicates:
        warnings.append("Direct children duplicated in explicit order: " + ", ".join(duplicates))
    return order, categories, warnings


def open_blockers(issue: dict[str, Any], child_ids: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[dict[str, Any]] = []
    warnings: list[str] = []
    for relation in issue.get("inverseRelations", {}).get("nodes", []):
        if relation.get("type") != "blocks":
            continue
        blocker = relation.get("issue") or {}
        state_type = (blocker.get("state") or {}).get("type")
        if state_type not in TERMINAL_TYPES:
            entry = {
                "identifier": blocker.get("identifier"),
                "title": blocker.get("title"),
                "state": (blocker.get("state") or {}).get("name"),
                "in_scope": blocker.get("identifier") in child_ids,
            }
            blockers.append(entry)
            if not entry["in_scope"]:
                warnings.append(
                    f"{issue.get('identifier')} has an open blocker outside the root hierarchy: "
                    f"{blocker.get('identifier')}"
                )
    return blockers, warnings


def issue_summary(issue: dict[str, Any], category: str) -> dict[str, Any]:
    return {
        "identifier": issue.get("identifier"),
        "title": issue.get("title"),
        "state": (issue.get("state") or {}).get("name"),
        "state_type": (issue.get("state") or {}).get("type"),
        "priority": issue.get("priority"),
        "updated_at": issue.get("updatedAt"),
        "category": category,
        "url": issue.get("url"),
    }


def hierarchy_completeness_errors(root: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    children_connection = root.get("children", {})
    if (children_connection.get("pageInfo") or {}).get("hasNextPage"):
        errors.append("Root child list is truncated; pagination is required before selection")
    for child in children_connection.get("nodes", []):
        identifier = child.get("identifier") or "unknown"
        for connection_name in ("relations", "inverseRelations", "comments", "children"):
            connection = child.get(connection_name, {})
            if (connection.get("pageInfo") or {}).get("hasNextPage"):
                errors.append(
                    f"{identifier} {connection_name} list is truncated; pagination is required before selection"
                )
        descendants = child.get("children", {}).get("nodes", [])
        if descendants:
            descendant_ids = ", ".join(
                sorted(descendant.get("identifier") or "unknown" for descendant in descendants)
            )
            errors.append(
                f"{identifier} has out-of-scope descendants under the direct-child pilot: {descendant_ids}"
            )
    return errors


def invalid_report(root: dict[str, Any], reason: str, warnings: list[str]) -> dict[str, Any]:
    return finalize_report({
        "schema_version": 1,
        "root": issue_summary(root, "root"),
        "result": "QUEUE_INVALID",
        "reason": reason,
        "active": [],
        "selected": None,
        "ready": [],
        "blocked": [],
        "conditional": [],
        "parked": [],
        "completed": [],
        "warnings": unique_in_order(warnings),
    })


def lifecycle_classification(report: dict[str, Any]) -> str:
    text = "\n".join([report.get("reason") or "", *report.get("warnings", [])]).lower()
    if "invalidated" in text or "digest" in text and "malformed" not in text:
        return "digest_revision_mismatch"
    if "multiple current valid claims" in text:
        return "duplicate_or_already_applied_control_plane_action"
    if report.get("result") == "QUEUE_INVALID":
        return "queue_invalid"
    if report.get("result") == "RESUME_ACTIVE":
        return "resume_active_claim"
    if report.get("result") == "SELECTED":
        return "ready_for_claim"
    return "clean_idle"


def finalize_report(report: dict[str, Any]) -> dict[str, Any]:
    classification = lifecycle_classification(report)
    report["lifecycle_diagnostic"] = {
        "classification": classification,
        "safe_next_checkpoint": SAFE_CHECKPOINTS[classification],
        "read_only": True,
    }
    return report


def inspect_root(root: dict[str, Any]) -> dict[str, Any]:
    completeness_errors = hierarchy_completeness_errors(root)
    if completeness_errors:
        return invalid_report(
            root,
            "The Linear hierarchy read is truncated or contains out-of-scope descendants",
            completeness_errors,
        )
    children = root.get("children", {}).get("nodes", [])
    by_id = {child["identifier"]: child for child in children}
    child_ids = set(by_id)
    order, categories, order_warnings = parse_order(root, child_ids)
    warnings = list(order_warnings)
    if not order or order_warnings:
        return finalize_report({
            "schema_version": 1,
            "root": issue_summary(root, "root"),
            "result": "QUEUE_INVALID",
            "reason": "The explicit child order is missing or inconsistent",
            "active": [],
            "selected": None,
            "ready": [],
            "blocked": [],
            "conditional": [],
            "parked": [],
            "completed": [],
            "warnings": warnings,
        })

    active: list[dict[str, Any]] = []
    ready: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    conditional: list[dict[str, Any]] = []
    parked: list[dict[str, Any]] = []
    completed: list[dict[str, Any]] = []

    for identifier in order:
        issue = by_id[identifier]
        category = categories.get(identifier, "uncategorized")
        summary = issue_summary(issue, category)
        state = issue.get("state") or {}
        state_type = state.get("type")
        state_name = state.get("name")
        blockers, blocker_warnings = open_blockers(issue, child_ids)
        warnings.extend(blocker_warnings)
        summary["open_blockers"] = blockers

        if state_type == STARTED_TYPE:
            claim = claim_for(issue, root.get("identifier", ""))
            summary["body_sha256"] = claim.digest
            summary["claim"] = {
                "valid": claim.valid,
                "reason": claim.reason,
                "comment_id": claim.comment_id,
                "run_id": claim.run_id,
                "claimed_by": claim.claimed_by,
                "fields": claim.fields,
            }
            if not claim.valid:
                summary["warning"] = claim.reason
                warnings.append(f"{identifier}: {claim.reason}")
            active.append(summary)
            continue
        if state_type in TERMINAL_TYPES:
            completed.append(summary)
            continue
        if blockers:
            summary["reason"] = "open blocking dependency"
            blocked.append(summary)
            continue
        if state_name != READY_STATE:
            summary["reason"] = f"state is {state_name!r}, not {READY_STATE!r}"
            if any(word in category.lower() for word in ("later", "conditional", "optional", "visibility")):
                conditional.append(summary)
            else:
                parked.append(summary)
            continue
        approval = approval_for(issue)
        summary["body_sha256"] = approval.digest
        summary["approval"] = {
            "valid": approval.valid,
            "reason": approval.reason,
            "comment_id": approval.comment_id,
            "approved_by": approval.approved_by,
        }
        if not approval.valid:
            summary["reason"] = approval.reason
            blocked.append(summary)
            continue
        ready.append(summary)

    missing_ids = sorted(child_ids - set(order))
    for identifier in missing_ids:
        summary = issue_summary(by_id[identifier], "out-of-order")
        summary["reason"] = "direct child is absent from the explicit root order"
        parked.append(summary)

    if len(active) > 1:
        result = "CONFLICT"
        reason = "Multiple active direct children violate the one-lane pilot policy"
        selected = None
    elif len(active) == 1 and not active[0].get("claim", {}).get("valid"):
        result = "CONFLICT"
        reason = "The active child has no valid revision-bound claim"
        selected = None
    elif len(active) == 1:
        result = "RESUME_ACTIVE"
        reason = "Resume or review the validly claimed active child before selecting new work"
        selected = active[0]
    elif ready:
        result = "SELECTED"
        reason = "Selected the first eligible issue in the explicit parent order"
        selected = ready[0]
    else:
        result = "NO_ELIGIBLE_WORK"
        reason = "No direct child is both Ready, unblocked, and digest-approved"
        selected = None

    return finalize_report({
        "schema_version": 1,
        "root": issue_summary(root, "root"),
        "result": result,
        "reason": reason,
        "active": active,
        "selected": selected,
        "ready": ready,
        "blocked": blocked,
        "conditional": conditional,
        "parked": parked,
        "completed": completed,
        "warnings": unique_in_order(warnings),
    })


def format_human(report: dict[str, Any]) -> str:
    root = report["root"]
    diagnostic = report.get("lifecycle_diagnostic") or {}
    lines = [
        f"ROOT: {root['identifier']} — {root['title']}",
        f"STATE: {report['result']}",
        f"WHY: {report['reason']}",
        f"LIFECYCLE: {diagnostic.get('classification', 'unknown')}",
        f"SAFE NEXT: {diagnostic.get('safe_next_checkpoint', 'Return to Default Hermes for review.')}",
    ]
    selected = report.get("selected")
    if selected:
        label = "ACTIVE" if report["result"] == "RESUME_ACTIVE" else "SELECTED"
        lines.append(f"{label}: {selected['identifier']} — {selected['title']} [{selected['state']}]")
    elif report.get("active"):
        lines.append("ACTIVE:")
        for item in report["active"]:
            warning = item.get("warning")
            suffix = f" — {warning}" if warning else ""
            lines.append(f"- {item['identifier']} — {item['title']} [{item['state']}]{suffix}")
    sections = (
        ("BLOCKED", report.get("blocked", [])),
        ("CONDITIONAL", report.get("conditional", [])),
        ("PARKED", report.get("parked", [])),
        ("COMPLETED", report.get("completed", [])),
    )
    for heading, items in sections:
        if not items:
            continue
        lines.append(heading + ":")
        for item in items:
            reason = item.get("reason")
            suffix = f" — {reason}" if reason else ""
            lines.append(f"- {item['identifier']} — {item['title']} [{item['state']}]{suffix}")
    if report.get("warnings"):
        lines.append("WARNINGS:")
        lines.extend(f"- {warning}" for warning in report["warnings"])
    return "\n".join(lines)


def load_fixture(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("issue", data)


def command_inspect(args: argparse.Namespace) -> int:
    if not args.fixture and args.root not in PILOT_ROOTS:
        allowed = ", ".join(sorted(PILOT_ROOTS))
        raise LinearError(f"Root {args.root} is outside the pilot allowlist ({allowed})")
    root = load_fixture(args.fixture) if args.fixture else fetch_root(args.root)
    report = inspect_root(root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_human(report))
    return 2 if report["result"] in {"CONFLICT", "QUEUE_INVALID"} else 0


def command_digest(args: argparse.Namespace) -> int:
    root = fetch_root(args.issue)
    target = root
    if root.get("identifier") != args.issue:
        raise LinearError(f"Unexpected issue readback for {args.issue}")
    print(body_sha256(target.get("description")))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect = subparsers.add_parser("inspect", help="Inspect one Linear parent hierarchy")
    inspect.add_argument("root", help="Root issue identifier, e.g. PAPI-3")
    inspect.add_argument("--fixture", help="Read fixture JSON instead of Linear")
    inspect.add_argument("--json", action="store_true", help="Emit structured JSON")
    inspect.set_defaults(func=command_inspect)
    digest = subparsers.add_parser("digest", help="Print normalized description SHA-256")
    digest.add_argument("issue", help="Issue identifier")
    digest.set_defaults(func=command_digest)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (LinearError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
