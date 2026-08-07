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

Those four say what the run concluded. A fifth block says what the run was in a
position to conclude at all, because the gap between the two is where a reader
supplies the difference themselves. So every report also carries: the UTC moment
the reported head was observed, and no time at all when nothing was observed;
every *configured* gate — not only the ones that ran — with the operator's own
coverage sentence, its sanitized invocation shape, and which of three evidence
modes its result belongs to; which adapter ran each reviewer lane beside the
``RUNTIME=`` its published artifact declared, with whether the lanes share
either; and five claims a green report is easily read as making, each stated
false unless the bounded evidence for it exists.

Coverage is labelled an operator declaration wherever it appears. Nothing here
infers what a gate covers, whether the gate set is sufficient, or what a URL in
an argv array means — and ``head-bound-environment`` is the one evidence mode
that is not configurable at all, because it is what a validated binding envelope
produces rather than what a config file may assert.

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

from .config import (
    GATE_EVIDENCE_HEAD_BOUND,
    GATE_EVIDENCE_LOCAL,
    GATE_EVIDENCE_UNBOUND,
    REQUIRED_REVIEWER_ROLES,
    UNBOUND_STATEMENT,
)
from .findings import provenance_lines
from .loop import GateDisclosure, NEEDS_KARAN, RunResult
from .redaction import sanitize

# Who may merge, stated in every report in both renderings. ``merge-ready`` is
# advice about one exact head; a reader who takes it as approval has read three
# accurate fields and drawn the one conclusion none of them supports.
MERGE_AUTHORITY = (
    "Karan alone decides whether to merge. Every field in this report is "
    "evidence about one exact head, and none of it is merge permission."
)

# What a configured gate's ``coverage`` field is, said where it is rendered.
# The operator wrote that sentence; nothing here checked it, and nothing here
# concluded from the gate set that the gate set is enough.
COVERAGE_DECLARATION = (
    "Gate coverage is the operator's own declaration of what each gate is for. "
    "It is carried verbatim and unverified: pr-prover does not infer gate "
    "sufficiency, coverage quality, or repository risk from a command, an "
    "argument, or a URL, and a configured gate set being complete is not "
    "something this run establishes."
)

# What each evidence mode means, in the words the report says it in. Keyed by
# the mode so the JSON and the Markdown cannot describe one gate two ways, and
# constant for the same reason ``MERGE_AUTHORITY`` is: the unbound sentence is
# the disclosure, and a composed one is a disclosure something could weaken.
EVIDENCE_STATEMENTS = {
    GATE_EVIDENCE_LOCAL: (
        "local or unspecified scope; no external environment was declared for "
        "this gate"
    ),
    GATE_EVIDENCE_UNBOUND: UNBOUND_STATEMENT,
    GATE_EVIDENCE_HEAD_BOUND: (
        "the environment this gate observed reported serving this exact head, "
        "reconciled from the gate's own binding evidence"
    ),
}

# What reviewer topology is, and — more to the point — what it is not. The
# adapter is configuration and the runtime is a line the artifact declares about
# itself; neither is a measurement of what actually executed.
TOPOLOGY_DECLARATION = (
    "Adapter is the configured entrypoint for each lane; runtime is the "
    "RUNTIME= line the lane's own published artifact declares. Neither is a "
    "measurement of what actually executed, and neither establishes that the "
    "lanes are independent of one another."
)

# The five claims a reader may take from a report that this run does not make,
# as ``(key, label, why it is not established, what establishing it means)``.
# Each carries the reason, because "not established" on its own reads like an
# omission somebody could close by looking harder.
#
# Only the first is ever true, and only from bounded evidence: a gate whose
# validated binding envelope reconciled an externally observed revision against
# this run's head. The other four have no proven note at all, because nothing
# this tool does can establish them — it never merges, never deploys, never
# observes production, and is never the human review Karan performs.
PROOF_SCOPE = (
    (
        "environment_revision_binding",
        "environment revision binding",
        "no configured gate produced validated evidence that an external "
        "environment was serving this exact head",
        "at least one configured gate recorded an externally observed revision "
        "equal to this head, reconciled from that gate's own binding evidence; "
        "the environment, URL, and source are listed with the gate below",
    ),
    (
        "heterogeneous_reviewer_independence",
        "heterogeneous reviewer independence",
        "reviewer lanes are separate processes with configured adapters and "
        "self-declared runtimes; this run does not verify what actually "
        "executed, so it cannot establish that the lanes fail independently",
        "",
    ),
    (
        "merged_result_behavior",
        "merged-result behavior",
        "every gate, artifact, and verdict here is about the pull request head, "
        "not about the tree that would exist after a merge",
        "",
    ),
    (
        "deployment_or_production_health",
        "deployment or production health",
        "this tool never deploys, releases, or observes a production system",
        "",
    ),
    (
        "human_final_merge_review",
        "human final merge review and authorization",
        "no automated step here is Karan reading the change and deciding to "
        "merge it",
        "",
    ),
)


def as_dict(result: RunResult) -> dict[str, Any]:
    """The machine-readable report, sanitized as a whole before it is returned."""
    # One list, read twice: what each gate discloses, and what the run therefore
    # established. Deriving the second from the first is what keeps a gate line
    # and the proof-scope boolean above it from ever disagreeing.
    gates = [_gate_disclosure(gate, result.head) for gate in result.configured_gates]
    scope = _proof_scope(gates)
    payload: dict[str, Any] = {
        "outcome": result.outcome,
        "reason": result.reason,
        "head": result.head,
        # When the live PR was observed on that head, and ``null`` whenever the
        # head is. The two are one fact: a head with no observation time is a
        # SHA with no "as of", and an observation time with no head would be a
        # timestamp for a read that never happened. Read off the head rather
        # than trusted from the result, so the pair cannot come apart here.
        "observed_at": result.observed_at if result.head else None,
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
        # Every gate this run was *configured* with, whether or not it ran, and
        # what each one's result is evidence about. The list above is execution;
        # this one is proof scope, and a skipped visual gate belongs to exactly
        # one of them.
        "configured_gates": gates,
        "gate_coverage_declaration": COVERAGE_DECLARATION,
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
        # Which adapter ran each reviewer lane, and what its published artifact
        # declared it ran as. Rendered beside the two shared-ness answers,
        # because "three roles" and "three independent judgements" are different
        # claims and a list of three lanes reads as the second one.
        "reviewer_topology": [
            {
                "lane": entry.lane,
                "role": entry.role,
                "adapter": entry.adapter,
                "runtime": entry.runtime,
            }
            for entry in result.reviewer_topology
        ],
        "reviewer_adapters_shared": _all_alike(
            [entry.adapter for entry in result.reviewer_topology]
        ),
        "reviewer_runtimes_shared": _all_alike(
            [entry.runtime for entry in result.reviewer_topology]
        ),
        "reviewer_topology_declaration": TOPOLOGY_DECLARATION,
        # What this run did and did not establish, one boolean per claim, each
        # false unless the bounded evidence for it exists.
        "proof_scope": scope,
        # The same sentence the Markdown prints for each claim, in the same
        # state: a machine reader that only reads the booleans is not the only
        # reader, and a note that stayed on "not established" while the boolean
        # said otherwise would be the two renderings disagreeing.
        "proof_scope_notes": _proof_scope_notes(scope),
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


def _all_alike(values: list[str]) -> bool:
    """Do two or more lanes report the same non-empty value?

    False for one lane, because a single lane shares nothing, and false for a
    value no lane stated: an empty runtime is a lane that never published a
    readable artifact, and reading three unknowns as "all the same" would turn
    missing evidence into a finding about the run's topology.
    """
    return len(values) > 1 and all(values) and len(set(values)) == 1


def _gate_disclosure(gate: GateDisclosure, head: str | None) -> dict[str, Any]:
    """One configured gate as this report states it, for the head it is about.

    A binding is evidence about the head whose revision the envelope named. If
    that is not the head being reported — a stop that observed a newer head
    before this run measured anything on it — then nothing here is bound, and
    the gate reads as the live endpoint it currently is rather than carrying a
    revision a reader has to notice is some other commit. Downgrading is the
    only direction available: no head makes a gate stronger.
    """
    bound = (
        gate.evidence_mode == GATE_EVIDENCE_HEAD_BOUND
        and bool(head)
        and gate.revision == head
    )
    mode = gate.evidence_mode
    if not bound:
        mode = GATE_EVIDENCE_UNBOUND if gate.environment else GATE_EVIDENCE_LOCAL
    return {
        "name": gate.name,
        "kind": gate.kind,
        "invocation": gate.invocation,
        "coverage": gate.coverage,
        "evidence_mode": mode,
        "evidence_statement": EVIDENCE_STATEMENTS[mode],
        "environment": gate.environment,
        "url": gate.url if bound else "",
        "revision": gate.revision if bound else "",
        "binding_source": gate.binding_source if bound else "",
        "observed_at": gate.observed_at if bound else "",
    }


def _proof_scope(gates: list[dict[str, Any]]) -> dict[str, bool]:
    """Which of the five claims this run established, each defaulting to false.

    Only the first can be true, and only from evidence: one configured gate this
    report is disclosing as ``head-bound-environment``. It is read off the
    rendered gates rather than recomputed, so the boolean and the gate line it
    summarizes cannot answer differently. The other four are false by
    construction — they are the claims a reader most easily takes from a green
    report, and nothing this tool does supports any of them, so they are stated
    rather than computed.
    """
    scope = {key: False for key, _, _, _ in PROOF_SCOPE}
    scope["environment_revision_binding"] = any(
        gate["evidence_mode"] == GATE_EVIDENCE_HEAD_BOUND for gate in gates
    )
    return scope


def _proof_scope_notes(scope: Mapping[str, bool]) -> dict[str, str]:
    """The sentence each claim is rendered with, in the state it is actually in."""
    return {
        key: (proven if scope[key] else unproven)
        for key, _, unproven, proven in PROOF_SCOPE
    }


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
        _observed_line(payload["head"], payload["observed_at"]),
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

    # Before the evidence rather than after it, because these are the claims a
    # reader most easily takes *from* the evidence, and a disclosure printed
    # under the run log is one somebody has already stopped reading.
    lines += ["", "### What this run established, and what it did not"]
    for key, label, unproven, proven in PROOF_SCOPE:
        established = payload["proof_scope"][key]
        lines.append(
            f"- {label}: **{'established' if established else 'not established'}** — "
            + (proven if established else unproven)
        )

    if payload["gates"]:
        lines += ["", "### Gates"]
        for gate in payload["gates"]:
            status = "pass" if gate["passed"] else f"FAIL (exit {gate['returncode']})"
            lines.append(f"- `{gate['name']}` ({gate['kind']}): {status}")

    if payload["configured_gates"]:
        lines += ["", "### Configured gates and what their results are evidence about"]
        for gate in payload["configured_gates"]:
            lines.append(
                f"- `{gate['name']}` ({gate['kind']}): {gate['evidence_mode']} — "
                f"{gate['evidence_statement']}"
            )
            lines.append(
                "  - operator-declared coverage: "
                + (
                    f"{gate['coverage']}"
                    if gate["coverage"]
                    else "none declared for this gate"
                )
            )
            lines.append(f"  - invocation: `{gate['invocation']}`")
            if gate["environment"]:
                lines.append(f"  - declared environment: `{gate['environment']}`")
            if gate["evidence_mode"] == GATE_EVIDENCE_HEAD_BOUND:
                lines += [
                    f"  - observed at `{gate['url']}`: revision `{gate['revision']}` "
                    f"via {gate['binding_source']}, at {gate['observed_at']}",
                ]
        lines.append(f"- {payload['gate_coverage_declaration']}")

    if payload["reviewer_topology"]:
        lines += ["", "### Reviewer topology (configuration and artifact claims)"]
        for entry in payload["reviewer_topology"]:
            lines.append(
                f"- `{entry['lane']}` (ROLE={entry['role']}): adapter "
                f"`{entry['adapter']}`, RUNTIME= "
                + (f"`{entry['runtime']}`" if entry["runtime"] else "not read back")
            )
        lines.append(f"- {_topology_summary(payload)}")
        lines.append(f"- {payload['reviewer_topology_declaration']}")

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


def _observed_line(head: Any, observed_at: Any) -> str:
    """When the reported head was seen, or say there was no observation.

    Printed even when there is nothing to print, because the absence is the
    information: a run that read nothing live has a head it cannot date, and a
    report that simply omitted the line would leave a reader to assume the SHA
    above it was current as of now.
    """
    if head and observed_at:
        return f"**Head observed at:** {observed_at} (UTC)"
    return (
        "**Head observed at:** never — this run completed no live read of the "
        "pull request, so nothing here is dated against GitHub"
    )


def _topology_summary(payload: Mapping[str, Any]) -> str:
    """One sentence on whether the reviewer lanes share a family, and what that means.

    The independence half of the sentence does not vary with the answer, and
    that is deliberate: distinct adapters and distinct declared runtimes are
    still configuration and self-description, so a run with three different ones
    has not established independence either — it has only stopped having the
    most obvious reason it could not.
    """
    shared_adapter = payload["reviewer_adapters_shared"]
    shared_runtime = payload["reviewer_runtimes_shared"]
    if shared_adapter and shared_runtime:
        observed = "every reviewer lane ran the same configured adapter and declared the same runtime"
    elif shared_adapter:
        observed = "every reviewer lane ran the same configured adapter"
    elif shared_runtime:
        observed = "every reviewer lane declared the same runtime"
    else:
        observed = (
            "the reviewer lanes do not all share one configured adapter and one "
            "declared runtime"
        )
    return f"{observed}; heterogeneous reviewer independence was not established"


def _inline(value: Any) -> str:
    """Render one already-sanitized evidence value on a single Markdown line."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return str(value)
    return json.dumps(value, sort_keys=True, default=str)


__all__ = ["as_dict", "failure_markdown", "to_json", "to_markdown"]
