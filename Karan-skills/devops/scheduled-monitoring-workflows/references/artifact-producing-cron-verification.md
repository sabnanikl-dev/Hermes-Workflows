# Artifact-Producing Cron Verification and Quiet Projection

Use this reference for scheduled jobs that ingest sources, create durable notes/artifacts, or promote a bounded subset into another knowledge layer.

## Scheduler status is not semantic success

A scheduler-level `ok` proves the execution finished without a framework failure. It does not prove a source was discovered, processed, written, or verified.

Reconcile four evidence layers before claiming success:

1. **Exact run artifact:** read the output for the specific attempt.
2. **Machine state:** confirm source identity and content hash were recorded.
3. **Human provenance:** confirm the ledger/provenance entry names the destination.
4. **Destination readback:** verify the artifact and its required content contract.

When layers disagree, report the narrowest true state: fired, scanned, skipped, blocked, partially written, or fully completed.

## Inbox presence can be intentional

Do not infer that an inbox item is pending merely because it remains visible. Immutable-source designs commonly keep standalone files in `raw/` after successful processing while moving only finalized folder bundles.

Completion is determined by source hash + state + provenance + destination readback—not by source presence or absence alone. If the user wants a clear-inbox UX, change the source-lifecycle contract deliberately rather than silently moving immutable files.

## Bounded projection into an agent-facing knowledge layer

When a human-owned/personal source may contain reusable agent knowledge:

- keep the human-owned layer canonical for full wording and private reasoning;
- evaluate each source hash once and record `projected` or `not_projected`;
- project only the minimum operational statement;
- include canonical source, consumer/purpose, exclusions, and freshness trigger;
- prefer an established destination page and structure;
- exclude verbatim blocks, whole personal notes, secrets, sensitive identity material, emotional/private deliberation, tentative ideas, and live tracker state;
- do not create filler pages for negative decisions;
- commit the projection decision only after destination/index/log readbacks succeed.

## Quiet notification contract

For high-frequency artifact-producing jobs:

- notify only when durable content actually changes;
- include concise changed-layer counts and exact destinations;
- return the scheduler's silent sentinel for no-op/skip-only runs;
- keep diagnostics in local execution output even when delivery is silent;
- set the requested destination explicitly and read the live job back after editing.

Changing delivery without no-op rules creates noise. Changing no-op rules without delivery leaves useful results invisible.

## Verification matrix

| Claim | Required evidence |
|---|---|
| Job fired | Durable execution attempt or exact run artifact |
| Source processed | Matching path/identity and content hash in state |
| Artifact complete | Destination readback plus required content/provenance contract |
| Projection published | Agent-facing destination readback and index/log updates as applicable |
| Notification configured | Live delivery target plus changed-only/silent prompt behavior |
