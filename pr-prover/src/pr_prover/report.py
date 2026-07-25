"""Render a run into machine-readable JSON or a human report.

Both forms carry the same facts: the terminal outcome tied to the exact final
head, how many of the two attempts were used, the four classification buckets,
gate results, reviewer verdicts, and — when the run stopped and asked — the
fail-closed reason with its preserved evidence. Everything captured from a
child has already passed through :mod:`pr_prover.redaction`.
"""
from __future__ import annotations

import json
from typing import Any

from .loop import RunResult


def as_dict(result: RunResult) -> dict[str, Any]:
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
                "findings": [finding.as_dict() for finding in verdict.findings],
            }
            for verdict in result.verdicts
        ],
        "classification": result.classification.as_dict() if result.classification else None,
        "events": list(result.events),
        "retained_paths": list(result.retained_paths),
    }
    if result.evidence:
        payload["fail_closed"] = result.evidence
    return payload


def to_json(result: RunResult) -> str:
    return json.dumps(as_dict(result), indent=2, sort_keys=True)


def to_markdown(result: RunResult) -> str:
    lines: list[str] = [
        f"## pr-prover — {result.outcome}",
        "",
        f"**Reason:** {result.reason}",
        f"**Head:** `{result.head or 'unknown'}`",
        f"**Branch:** {result.branch or 'unknown'}",
        f"**Attempts used:** {result.attempts_used}/2",
    ]
    if result.corrective_reruns:
        lines.append(
            "**Corrective reruns:** attempt(s) "
            + ", ".join(str(attempt) for attempt in result.corrective_reruns)
        )
    if result.pr_url:
        lines.append(f"**PR:** {result.pr_url}")

    if result.gates:
        lines += ["", "### Gates"]
        for gate in result.gates:
            status = "pass" if gate.passed else f"FAIL (exit {gate.returncode})"
            lines.append(f"- `{gate.name}` ({gate.kind}): {status}")

    if result.verdicts:
        lines += ["", "### Reviewers"]
        for verdict in result.verdicts:
            lines.append(
                f"- Reviewer {verdict.reviewer}: {verdict.status}, "
                f"{len(verdict.blocking)} blocking on `{verdict.head}`"
            )

    if result.classification is not None:
        lines += ["", "### Classification"]
        for label, items in result.classification.as_dict().items():
            if not items:
                continue
            lines.append(f"- **{label}** ({len(items)})")
            for item in items:
                lines.append(f"  - `{item['id']}` — {item['summary']} [{', '.join(item['sources'])}]")

    if result.evidence:
        lines += [
            "",
            "### Stopped and asking Karan",
            f"- reason: `{result.evidence.get('reason')}`",
            f"- detail: {result.evidence.get('message')}",
        ]
        for key, value in sorted((result.evidence.get("evidence") or {}).items()):
            lines.append(f"- {key}: {value}")

    if result.retained_paths:
        lines += ["", "### Retained evidence"]
        lines += [f"- `{path}`" for path in result.retained_paths]

    if result.events:
        lines += ["", "### Run log"]
        lines += [f"- {event}" for event in result.events]

    return "\n".join(lines) + "\n"


__all__ = ["as_dict", "to_json", "to_markdown"]
