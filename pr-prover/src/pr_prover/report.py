"""Render a run into machine-readable JSON or a human report.

Both forms carry the same facts: the terminal outcome tied to the exact final
head, how many of the two attempts were used, the four classification buckets,
gate results, reviewer verdicts, and — when the run stopped and asked — the
fail-closed reason with its preserved evidence.

Child output is scrubbed where it is captured, but that only covers the strings
a call site remembered to pass through :mod:`pr_prover.redaction`. Serialization
is the last place a value can leak, so both renderers here are built from one
:func:`pr_prover.redaction.sanitize` pass over the assembled payload: every
string in it, however deeply nested, is scrubbed, and the structure and scalar
types survive so the report stays readable and machine-usable.

Two things are rendered rather than summarized. A ``needs-Karan`` escalation
prints each finding's provenance inline — who found it, on which head, at which
surface, and the verbatim excerpt — so the decision does not require re-reading
raw lane output. And every failure is printed from its
:class:`~pr_prover.errors.FailureRecord`: :func:`failure_markdown` is the human
summary and the fenced JSON block beside it is the builder's next instruction.
Both come from the same sanitized record, so the two audiences can never be
told two different stories about one failure.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .findings import provenance_lines
from .loop import NEEDS_KARAN, RunResult
from .redaction import sanitize


def as_dict(result: RunResult) -> dict[str, Any]:
    """The machine-readable report, sanitized as a whole before it is returned."""
    payload: dict[str, Any] = {
        "outcome": result.outcome,
        "reason": result.reason,
        "head": result.head,
        "branch": result.branch,
        "pr_url": result.pr_url,
        "attempts_used": result.attempts_used,
        "attempt_cap": 2,
        "corrective_reruns": list(result.corrective_reruns),
        "gates": [
            {
                "name": gate.name,
                "kind": gate.kind,
                "passed": gate.passed,
                "returncode": gate.returncode,
                "output": gate.output,
            }
            for gate in result.gates
        ],
        "reviewers": [
            {
                "reviewer": verdict.reviewer,
                "status": verdict.status,
                "head": verdict.head,
                "blocking": len(verdict.blocking),
                "findings": [finding.as_dict() for finding in verdict.findings],
            }
            for verdict in result.verdicts
        ],
        "classification": result.classification.as_dict() if result.classification else None,
        "classification_head": result.classification_head,
        "failures": [record.as_dict() for record in result.failures],
        "events": list(result.events),
        "retained_paths": list(result.retained_paths),
    }
    if result.evidence:
        payload["fail_closed"] = result.evidence
    return sanitize(payload)


def to_json(result: RunResult) -> str:
    return json.dumps(as_dict(result), indent=2, sort_keys=True)


def to_markdown(result: RunResult) -> str:
    """The human report, rendered from the same sanitized payload as the JSON."""
    payload = as_dict(result)
    lines: list[str] = [
        f"## pr-prover — {payload['outcome']}",
        "",
        f"**Reason:** {payload['reason']}",
        f"**Head:** `{payload['head'] or 'unknown'}`",
        f"**Branch:** {payload['branch'] or 'unknown'}",
        f"**Attempts used:** {payload['attempts_used']}/{payload['attempt_cap']}",
    ]
    if payload["corrective_reruns"]:
        lines.append(
            "**Corrective reruns:** attempt(s) "
            + ", ".join(str(attempt) for attempt in payload["corrective_reruns"])
        )
    if payload["pr_url"]:
        lines.append(f"**PR:** {payload['pr_url']}")

    if payload["gates"]:
        lines += ["", "### Gates"]
        for gate in payload["gates"]:
            status = "pass" if gate["passed"] else f"FAIL (exit {gate['returncode']})"
            lines.append(f"- `{gate['name']}` ({gate['kind']}): {status}")

    if payload["reviewers"]:
        lines += ["", "### Reviewers"]
        for verdict in payload["reviewers"]:
            lines.append(
                f"- Reviewer {verdict['reviewer']}: {verdict['status']}, "
                f"{verdict['blocking']} blocking on `{verdict['head']}`"
            )

    if payload["classification"] is not None:
        bound = payload.get("classification_head")
        # The findings are evidence about one exact commit, so the report says
        # which one rather than letting a reader infer it from the outcome.
        heading = f"### Classification (exact head `{bound}`)" if bound else "### Classification"
        lines += ["", heading]
        if bound and payload["head"] and bound != payload["head"]:
            lines.append(
                f"- historical evidence only: these findings were produced against `{bound}`, "
                "not the head reported above"
            )
        # A needs-Karan report is the one a human has to act on without the
        # run's context — including a fail-closed stop, where the ledger it
        # reached is the whole subject of the escalation — so every finding it
        # carries prints its provenance rather than sending Karan back to the
        # raw lane output.
        escalating = payload["outcome"] == NEEDS_KARAN
        for label, items in payload["classification"].items():
            if not items:
                continue
            lines.append(f"- **{label}** ({len(items)})")
            for item in items:
                lines.append(f"  - `{item['id']}` — {item['summary']} [{', '.join(item['sources'])}]")
                if escalating or label == "needs-karan":
                    lines += provenance_lines(item, indent="    ")

    if payload["failures"]:
        lines += ["", "### What failed and what to do next"]
        for record in payload["failures"]:
            lines += failure_markdown(record)

    fail_closed = payload.get("fail_closed")
    if fail_closed:
        lines += [
            "",
            "### Stopped and asking Karan",
            f"- reason: `{fail_closed.get('reason')}`",
            f"- detail: {fail_closed.get('message')}",
        ]
        for key, value in sorted((fail_closed.get("evidence") or {}).items()):
            lines.append(f"- {key}: {_inline(value)}")

    if payload["retained_paths"]:
        lines += ["", "### Retained evidence"]
        lines += [f"- `{path}`" for path in payload["retained_paths"]]

    if payload["events"]:
        lines += ["", "### Run log"]
        lines += [f"- {event}" for event in payload["events"]]

    return "\n".join(lines) + "\n"


def failure_markdown(record: Mapping[str, Any]) -> list[str]:
    """Render one already-sanitized failure record as Markdown plus its JSON block.

    The prose above the fence is for the human reading the report; the fence
    below it is the block the trusted builder consumes as its next instruction.
    Both are this one ``record`` — there is no second description of the failure
    to keep in step with it.
    """
    lines = [
        "",
        f"#### `{record.get('failure_class')}` — {record.get('what_failed')}",
    ]
    if record.get("finding_id"):
        lines.append(f"- finding: `{record['finding_id']}`")
    evidence = record.get("evidence") or {}
    if evidence:
        lines.append("- evidence:")
        lines += [f"  - {key}: {_inline(value)}" for key, value in sorted(evidence.items())]
    remediation = record.get("remediation") or []
    if remediation:
        lines.append("- bounded remediation the builder may attempt:")
        lines += [f"  {index}. {step}" for index, step in enumerate(remediation, start=1)]
    lines.append(f"- escalate instead when: {record.get('escalation')}")
    lines += [
        "",
        "```json",
        json.dumps(record, indent=2, sort_keys=True, default=str),
        "```",
    ]
    return lines


def _inline(value: Any) -> str:
    """Render one already-sanitized evidence value on a single Markdown line."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return str(value)
    return json.dumps(value, sort_keys=True, default=str)


__all__ = ["as_dict", "failure_markdown", "to_json", "to_markdown"]
