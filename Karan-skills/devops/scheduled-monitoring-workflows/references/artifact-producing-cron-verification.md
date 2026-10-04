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

## Finite evidence checkpoints

Use explicit one-shots for a small set of milestone reports rather than installing an indefinite recurrence and relying on a future agent to remember to stop it.

1. Define the observation dates, reporting timezone, inclusive data cutoff and final processing-lag capture. A boundary-day run usually cannot contain that day's complete provider data; label it intermediate and disclose why a later review is needed.
2. Enforce `requested_through = min(yesterday_in_reporting_timezone, approved_data_cutoff)` in the collector before network requests, including daily probes and cumulative windows. Determine each provider's available end date separately. Test on-time boundary-day, delayed final review and late-execution cases. A missing date is not automatically zero activity or proven processing lag.
3. Define a hard execution expiry and bounded read retries. If final data remains unavailable, return an incomplete-evidence report and stop; do not self-schedule an open-ended extension or close the owning issue.
4. Keep scheduled-slot identity separate from actual capture time. Verify prior output and hashes before treating a slot as complete; an earlier scheduled job may have failed. Suppress only verified duplicate completions, never missing-data or failure outcomes for a requested report.
5. Bind each fresh-session prompt to an exact local run contract and accepted baseline. Verify the contract digest before execution. Copy collectors into new run directories; never execute producers in frozen evidence directories. Inspect copied builders for stale dates and hard-coded narrative metrics before reuse.
6. Require raw evidence, derived comparisons, scoped validation, a frozen manifest and bounded independent acceptance when the report contract calls for them. Deliver a concise decision summary and usable report attachment, not merely a reminder or local path.
7. Preserve publication gates explicitly. Scheduling a read-only report does not automatically authorize tracker comments, canonical promotion, client sends or issue closure; return review-ready evidence for the next authorized handoff.

### Per-job inference preflight and activation

Before creating agent-backed jobs, inspect only the relevant configured model/provider fields and existing job definitions; do not dump credentials or full secret-bearing configuration. Probe the intended unattended route with a bounded tool-free invocation:

```bash
hermes chat --provider <provider> --model <model> --toolsets '' \
  --max-turns 1 --run-budget 90 --oneshot --quiet \
  -q 'Authentication smoke test only. Do not use tools. Reply exactly: CRON_AUTH_OK'
```

Require the expected response, not just a stored login or healthy gateway. This tests inference authentication only, not Google/API access, report generation or eventual delivery.

If the user explicitly approves a different model for only the new jobs:

1. Create those jobs paused through `cronjob_manage` with their exact one-shot schedules, finite repeat count, workdir and success/failure destination.
2. Check the installed CLI's edit syntax, then apply the user-selected route without changing global configuration:

   ```bash
   hermes cron edit <returned-job-id> --model <approved-model> --provider <approved-provider>
   ```

3. Verify the stored model/provider, then resume the exact returned IDs with `hermes cron resume <job-id>`.
4. Re-read enabled state, one-shot kind/count, timezone-aware `next_run_at`, prompt/contract binding and delivery. Compare protected global configuration and unrelated jobs against the pre-change snapshot; exclude naturally changing execution timestamps/status from that comparison.
5. Record live-auth success and schedule readback separately from future execution acceptance. Do not fire the actual reporting jobs just to prove their model can answer.

Use the supported CLI for an explicitly approved arbitrary model pin when the cron tool only exposes pinning the current model. Do not silently switch the global model as an intermediate step, because that can redirect unrelated unattended work.

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
