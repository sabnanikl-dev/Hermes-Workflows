# Long-running resumable external-QA orchestration

Use this pattern when an issue requires hundreds or thousands of real-browser/API observations whose wall time can exceed the builder agent's session budget.

## Separate the control planes

Treat these as three distinct processes:

1. **Evidence producer** — performs the bounded observation and atomically checkpoints each slot.
2. **Batch driver** — selects explicit IDs, skips terminal slots, records batch commands/timestamps/exit codes, and resumes safely.
3. **Builder agent** — implements/generates artifacts, starts or supervises the driver, then continues after evidence collection.

Do not make the LLM process itself the only durable owner of a multi-hour run. Launch the bounded producer/driver through Hermes `terminal(background=true, notify_on_complete=true)` when practical, or attach a tracked watcher plus a durable run ledger if the builder launched it.

## Monitor evidence, not silence

Useful health signals:

- evidence `updatedAt` advances;
- terminal-slot/model counts increase;
- pending count decreases;
- the current producer child exists and has plausible CPU/runtime;
- batch/run-log size or latest record advances;
- the full candidate universe remains represented.

Buffered builder stdout is not a hang. Do not kill a quiet builder while these signals move.

## Do not bind orchestration to one PID

A fixed-PID watcher can exit when a failed batch driver is replaced even though the logical rollout continues under a new PID. Prefer one of:

- Hermes-managed background session IDs for the actual bounded driver;
- a semantic run ledger/state file with an explicit terminal status;
- a watcher that verifies both process absence **and** ledger/evidence terminal state before declaring completion.

After any watcher fires, re-check live evidence and process state before announcing that the rollout ended. A process exit is only a state transition, not proof that the logical job completed.

### Recovery supervisor

A watcher tied to one PID observes only that process; it does not guarantee that pending work resumes. For crash-prone rollouts, add a tracked supervisor that:

1. Waits for the current driver to exit before launching anything else.
2. Reads the authoritative evidence and counts pending work.
3. Relaunches the committed resumable driver only when pending work remains.
4. Requires the pending count to decrease across attempts.
5. Stops loudly after a bounded no-progress threshold.
6. Emits a structured terminal summary when pending reaches zero.

Never run two producers concurrently against the same evidence artifact.

## Temporary human-facing status watchdog

When the human asks for updates during a multi-hour producer, use a **script-only Hermes cron job** rather than spending an LLM call every tick:

- Schedule every 5–10 minutes and deliver to the origin conversation.
- Set `no_agent=true`; the script should read evidence, producer/supervisor state, PR state, checks, and current-head Reviewer A/B signatures.
- Print a concise stage plus terminal/eligible/pending/failure counts on every active tick.
- Execute the script once directly before scheduling, then verify the live job with `cronjob(action='list')`.
- Add a finite repeat cap so the watchdog cannot become a permanent orphan.
- Remove the cron and helper script/sentinel at final merge-ready handoff. Optionally make the script go silent after issue closure or verified merge.
- Keep the watchdog read-only: the recovery supervisor advances the producer, while Hermes/builder owns finalization.

Suggested message shape:

```text
Issue #N watchdog — <UTC timestamp>
Stage: <producer | finalization | PR review>
Items: <terminal>/<total>; <eligible> eligible
Slots: <done>/<total>; <pending> pending
Fail-closed: <count> (<grouped reasons>)
Workers: producer=<active|inactive>, supervisor=<active|inactive>
PR: <not opened | #N state>; Reviewer A/B=<present|pending>; checks=<summary>
```

## Producer crash classification

Distinguish destination evidence from harness infrastructure failures.

- A model-specific visible error, permanent loader, identity mismatch, or bounded readiness timeout is terminal evidence and may fail that slot closed.
- A Playwright/browser-context crash such as `browserContext.newPage: Target page, context or browser has been closed` is an infrastructure failure. Do not convert untouched slots into destination failures. Preserve completed checkpoints, leave unattempted slots pending, and resume them.

The producer should catch failures around page/context creation as well as navigation/classification. One worker rejection must not close the shared browser/context while sibling workers are still active. Prefer all-settled worker coordination or per-task containment, followed by a clean non-zero batch exit if infrastructure integrity is uncertain.

## Resume procedure

1. Read the checkpoint and prove the full universe/count is intact.
2. Count terminal, failed, passing, and pending slots/models.
3. Inspect the producer/driver error and classify it as destination vs infrastructure.
4. Fix producer robustness when the crash path is reproducible; otherwise restart conservatively.
5. Relaunch the driver with explicit batch size/concurrency/retries. It must skip terminal slots by default.
6. Record the restart and prior non-zero exit in the durable run log; do not overwrite history.
7. At the end, require zero pending slots unless the issue explicitly permits a documented external-outage checkpoint.
8. Regenerate authority/browser artifacts only from the final committed evidence, then run validators and current-head A/B review.

## Builder-budget rollover

If evidence collection will outlive the builder model session:

- let the tracked producer continue independently;
- stop at a verified checkpoint rather than pretending the builder completed;
- after producer completion, start a fresh builder/fix session on the same isolated branch to generate artifacts, reconcile docs, test, commit, push, and open/update the PR;
- disclose any fallback or builder-session rollover honestly, but do not treat it as evidence loss when the producer and checkpoint remained authoritative.
