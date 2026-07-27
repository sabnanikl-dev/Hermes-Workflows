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

The reported head is the head the live PR was *observed* on, and it is absent
when the run stopped before reading GitHub at all. Both renderings keep that
distinction: an unknown head is printed as unknown, and a classification carried
into the report is marked historical or unverified unless the head it was
produced against is the head that was observed.

Four claims are kept apart rather than blended into one impression of health.
**Transport** says an artifact reached GitHub under the configured identity and
can be read back — it says nothing about what the review concluded. The
**implementation verdict** is the reviewer statuses and the classification
buckets. **Exact-head readiness** is the outcome at the top, tied to the head
the live PR was observed on. A run can have complete transport, a failing
verdict, and no readiness at all, and the report has to be able to say so.

**Human merge authority** is the fourth, and it is written down rather than left
to be inferred from the other three: ``merge_authority`` says in every report,
in both renderings, that Karan alone decides and that nothing here is
permission. It is a module constant, not a computed field, because a value
something could set is a value something could set to the wrong thing.

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

from .config import REQUIRED_REVIEWER_ROLES
from .findings import provenance_lines
from .loop import NEEDS_KARAN, RunResult
from .redaction import sanitize

# Who may merge, stated in every report in both renderings. ``merge-ready`` is
# advice about one exact head; a reader who takes it as approval has read three
# accurate fields and drawn the one conclusion none of them supports.
MERGE_AUTHORITY = (
    "Karan alone decides whether to merge. Every field in this report is "
    "evidence about one exact head, and none of it is merge permission."
)


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
        # How each lane's process ended. Separate from the verdicts on purpose:
        # "the lane ran for 40 minutes and exited 0" and "the reviewer passed"
        # are two different facts, and a quiet stretch belongs to the first.
        "lanes": [
            {
                "lane": lane.lane,
                "state": lane.state,
                "returncode": lane.returncode,
                "duration_seconds": round(lane.duration, 1),
                "quiet_seconds": round(lane.quiet_seconds, 1),
            }
            for lane in result.lanes
        ],
        # Whether each artifact actually reached GitHub, step by step, under the
        # identity it was supposed to. This is transport, not judgement: a
        # complete transport says the evidence is on the PR and readable, and
        # says nothing at all about whether the review passed.
        "transport": [
            {
                "lane": item.lane,
                "role": item.role,
                "head": item.head,
                "identity": item.identity,
                "prepared": item.prepared,
                "published": item.published,
                "read_back": item.read_back,
                "artifact_id": item.identifier,
                "complete": item.complete,
            }
            for item in result.transport
        ],
        "transport_complete": _transport_is_complete(result),
        # The fourth claim, said rather than implied. Everything above is
        # evidence; none of it is permission, and ``merge-ready`` is the outcome
        # most easily misread as one. It is a constant on purpose: a field whose
        # value could vary is a field something could be made to set.
        "merge_authority": MERGE_AUTHORITY,
        "classification": result.classification.as_dict() if result.classification else None,
        "classification_head": result.classification_head,
        # Whether the ledger above is evidence about the head the live PR was
        # actually observed on. It is false both when the PR moved underneath
        # the run and when the run stopped before reading the PR at all, so a
        # machine reader is told the ledger is historical or unverified instead
        # of having to infer it from two nullable heads — and ``head: null``
        # can never be read as agreeing with a recorded classification head.
        "classification_head_current": _classification_head_is_current(result),
        "failures": [record.as_dict() for record in result.failures],
        "events": list(result.events),
        "retained_paths": list(result.retained_paths),
    }
    if result.evidence:
        payload["fail_closed"] = result.evidence
    return sanitize(payload)


def _transport_is_complete(result: RunResult) -> bool:
    """Did the whole required artifact lifecycle reach GitHub on one exact head?

    ``all(item.complete for item in result.transport)`` was vacuously true for an
    empty ledger, so a gate that blocked before any reviewer launched, and a stop
    before transport began, both published a positive claim that zero of the
    three required artifacts had landed. A truncated-but-complete prefix — one
    finished Reviewer A record and nothing else — said the same thing.

    The field is a claim about the lifecycle, not about whichever records happen
    to exist, so it is measured against the lifecycle: the required three roles,
    in the required order, each read back on GitHub, and all of them bound to the
    one head the ledger they support was produced against. Anything short of that
    is incomplete, and the per-record list above is where a reader sees exactly
    how far each one got.

    This says nothing about the verdicts. Three failing reviews whose artifacts
    all landed are complete transport and a blocked head, which is the separation
    the field exists to preserve.
    """
    transport = result.transport
    if len(transport) != len(REQUIRED_REVIEWER_ROLES):
        return False
    if tuple(item.role for item in transport) != REQUIRED_REVIEWER_ROLES:
        return False
    if not all(item.complete for item in transport):
        return False
    heads = {item.head for item in transport}
    if len(heads) != 1 or not heads.pop():
        return False
    # The lanes ran against the head the classification is bound to; a ledger
    # with no head at all cannot have a complete exact-head transport behind it.
    return result.classification_head is not None and all(
        item.head == result.classification_head for item in transport
    )


def _classification_head_is_current(result: RunResult) -> bool:
    """Is the classification's head the head the live PR was observed on?

    Both heads have to exist and agree. An absent observed head is the case that
    matters: a run that stopped before its first GitHub read has no evidence
    about the live PR at all, so its recorded ledger is unverified rather than
    current, and ``None == None`` must never make it look otherwise.
    """
    return (
        result.head is not None
        and result.classification_head is not None
        and result.head == result.classification_head
    )


def to_json(result: RunResult) -> str:
    return json.dumps(as_dict(result), indent=2, sort_keys=True)


def to_markdown(result: RunResult) -> str:
    """The human report, rendered from the same sanitized payload as the JSON."""
    payload = as_dict(result)
    lines: list[str] = [
        f"## pr-prover — {payload['outcome']}",
        "",
        f"**Reason:** {payload['reason']}",
        _head_line(payload["head"]),
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
    lines.append(f"**Merge authority:** {payload['merge_authority']}")

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

    if payload["transport"]:
        lines += ["", "### Artifact transport (not a verdict)"]
        for item in payload["transport"]:
            reached = (
                f"read back on GitHub as `{item['artifact_id']}`"
                if item["read_back"]
                else "published, not read back"
                if item["published"]
                else "prepared, not published"
                if item["prepared"]
                else "not prepared"
            )
            lines.append(
                f"- `{item['lane']}` (ROLE={item['role']}) as `{item['identity']}`: "
                f"{reached}, on `{item['head']}`"
            )
        lines.append(
            "- transport says the evidence reached the PR under the configured identity; "
            "what the review concluded is in the verdicts and the classification above, "
            "and whether this head is merge-ready is the outcome at the top"
        )

    if payload["lanes"]:
        lines += ["", "### Lanes"]
        for lane in payload["lanes"]:
            lines.append(
                f"- `{lane['lane']}`: {lane['state']} after {lane['duration_seconds']}s "
                f"(exit {lane['returncode']}, quiet {lane['quiet_seconds']}s)"
            )

    if payload["classification"] is not None:
        bound = payload.get("classification_head")
        current = payload.get("classification_head_current")
        # The findings are evidence about one exact commit, so the report says
        # which one rather than letting a reader infer it from the outcome. It
        # calls that commit the exact head only when the live PR was read: with
        # no observation, the same SHA is a recorded head this run could not
        # hold against GitHub, and the heading has to say so.
        if not bound:
            heading = "### Classification"
        elif payload["head"]:
            heading = f"### Classification (exact head `{bound}`)"
        else:
            heading = (
                f"### Classification (recorded head `{bound}` — "
                "unverified against the live pull request)"
            )
        lines += ["", heading]
        if bound and not current:
            lines.append(
                f"- historical evidence only: these findings were produced against `{bound}`, "
                + (
                    "not the head reported above"
                    if payload["head"]
                    else "and this run read nothing live, so whether that is still the "
                    "PR's head is unverified"
                )
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


def _head_line(head: Any) -> str:
    """Render the head the live PR was observed on, or say there is none.

    A missing head is not a formatting gap to fill from somewhere else: it means
    this run never read the live PR, so it has no current head to report. Saying
    that is the whole point — the alternative is printing a head out of local
    state under a label a reader takes as verified.
    """
    if head:
        return f"**Head:** `{head}`"
    return (
        "**Head:** `unknown` — this run read nothing live, "
        "so the pull request's current head is unverified"
    )


def _inline(value: Any) -> str:
    """Render one already-sanitized evidence value on a single Markdown line."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return str(value)
    return json.dumps(value, sort_keys=True, default=str)


__all__ = ["as_dict", "failure_markdown", "to_json", "to_markdown"]
