# Runtime Coverage and NotebookLM Alignment

Use this reference when a client ontology appears rich in YAML/SQLite but a user experiences it as a narrow checker or context dump, or when NotebookLM is used to critique the ontology roadmap.

## Audit Three Separate Layers

Never conflate these:

1. **Model representation** — can the schema express the concept (entity, relationship, metric, approval, action, state machine)?
2. **Client coverage** — has the relevant business/technical knowledge actually been modeled for this client with evidence and honest status?
3. **Runtime queryability** — can a consumer retrieve and traverse that knowledge through the supported service/CLI without reading raw YAML or inventing SQL?

A passing validator proves representation integrity, not coverage or consumer usefulness. An SQLite table proves exportability, not runtime accessibility.

## Avoid the “Copy Checker” False Impression

When demonstrating the CLI, do not lead only with `check-copy`. Show:

- client and projection discovery;
- entity/system lookup;
- relationship traversal;
- status/confidence/evidence preservation;
- action/approval/state-machine queries when available;
- one guardrail check as an enforcement example.

If relationships, actions, approvals, or state machines exist canonically but are absent from the service/CLI, report that as a consumer-surface gap rather than implying the ontology is complete.

## Competency Questions Drive Scope

Use deterministic, projection-scoped competency questions as the coverage contract. Include business and technical questions such as:

- Who owns the system that hosts a client website?
- Which system is authoritative for a content type?
- What data flows between intake, CMS, and public surfaces?
- Which approval gate governs a public transition?
- What metric defines an outcome, and where is it observed?

Add multi-hop relationship questions before considering GraphRAG/vector retrieval. Expand the competency runner’s query vocabulary when a required question cannot be expressed; do not substitute model grading for deterministic assertions when the answer is structured.

## Canonical vs Source-System Boundary

Canonical ontology stores durable meaning: definitions, ownership, systems of record, relationships, policies, metric semantics, approval boundaries, lifecycle, evidence, and confidence. Source systems retain raw instances: CRM rows, individual inventory records, analytics events, CMS bodies, tracker state, private exports, and secrets.

Rule of thumb: “What does this event/system/metric mean?” belongs in the ontology; “Record 123 happened today” stays in the source system.

## Intake Conflict Reconciliation

A production intake path should be:

```text
collect -> normalize -> sanitize -> extract candidates -> compare with canonical
-> classify matching/new/changed/conflicting/stale -> human reconcile
-> proposed patch -> validate -> review
```

Represent unresolved conflicts in candidate/review staging first. Do not immediately add a canonical `conflicted` status or generic contradiction detector: differences may be temporal, field semantics may be incomparable, and free-form values cannot be safely contradicted by a generic validator. Promote a canonical conflict model only after repeated real cases prove it is durable ontology truth.

## NotebookLM Cross-Check Pattern

NotebookLM knows its sources, not live repo state. Provide a verified digest with:

- current ref and resource counts;
- live schema/runtime operations;
- open issues and dependencies;
- explicit gaps and non-goals;
- recommendations labeled for evaluation.

Ask for `ALIGN`, `MODIFY`, or `REJECT`, source titles, over-engineering risks, missing recommendations, and a minimal sequence. Then adjudicate outside NotebookLM.

If NotebookLM recommends work already delivered, correct it with exact live evidence and ask for a replacement recommendation. Treat its issue mapping and implementation details as hypotheses. Source-backed principles may be right while repo-state conclusions are wrong.

## Roadmap Checks

Before claiming a clear path:

- verify every live open issue appears in the roadmap;
- distinguish schema/export acceptance from service/CLI acceptance;
- ensure dependencies remain explicit (for example approvals before gated actions/transitions);
- keep semantic retrieval gated behind a measured deterministic-query failure;
- add a tracked owner for any “next PR” named in docs.
