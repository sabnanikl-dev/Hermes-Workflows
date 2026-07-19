# Long-running workflow status watchdogs

Use this for multi-hour issue-to-PR runs where the builder, evidence producer, or review loop outlives a chat turn and Karan wants periodic Telegram updates.

## Separate the three responsibilities

1. **Worker** — the real bounded task (Claude build, browser evidence producer, tests). Start it as a tracked background process with completion notification.
2. **Recovery supervisor** — waits for worker exit, inspects the authoritative checkpoint, and resumes only pending work after a crash. It must have a no-progress/run limit and must never blanket-rerun terminal evidence merely to improve counts.
3. **Status watchdog** — read-only reporting. Prefer `no_agent=True` with a deterministic script under `~/.hermes/scripts/` so updates cost no model tokens and cannot mutate the repo.

A watchdog is not a substitute for recovery or orchestration. Reporting that a worker died while doing nothing about resumable pending work is not continuity.

## Hermes cron interval semantics

- `schedule="5m"` means **one run five minutes from creation**.
- `schedule="every 5m"` means a recurring five-minute interval.
- A `repeat` count does **not** turn `5m` into a recurring interval; a misconfigured job can finish after run `1/N`.

For temporary recurring status:

```text
schedule="every 5m"
repeat=<finite safety cap>
script="<watchdog>.py"
no_agent=True
deliver="origin"
```

Immediately verify creation shows:

- `schedule: every 5m` (not `once in 5m`)
- `enabled: true`
- `state: scheduled`
- a non-null future `next_run_at`

After the first tick, verify again that the job remains scheduled and has another future `next_run_at`. If it shows `state: completed`, `repeat: 1/N`, and `next_run_at: null`, remove it and recreate it with `every 5m`.

## Source-first status script

Every tick reads live authoritative sources, never session summaries:

- evidence/checkpoint artifact: terminal models, slot outcomes, pending count, eligibility/fail-closed counts;
- process table: worker and recovery-supervisor health;
- GitHub: PR existence/state/head, checks, signed Reviewer A/B state, issue state;
- optional completion sentinel to keep future ticks silent after completion.

A useful update contains:

```text
Stage: browser evidence | finalization | PR verification | review/fix | merge-ready
Models: terminal/total; currently eligible
Slots: complete/total; pending
Fail-closed: grouped reasons
Workers: producer active/inactive; supervisor active/inactive
PR: absent or #N/head/check/reviewer state
```

Do not call the overall task “done” because one subprocess says `complete`. Distinguish explicitly:

- **in progress** — any required worker/evidence/test/reviewer stage remains;
- **merge-ready** — exact current head is remotely verified, required tests/visual QA pass, A+B current-head reviews have no blockers, and only Karan’s human merge gate remains;
- **done** — the user-approved terminal state (usually merged/issue closed) is verified.

## Cleanup

- Keep the watchdog alive through fix/re-review, not only through the long producer.
- When the final handoff is reached, list jobs to resolve the exact job ID, then remove it; never guess IDs.
- Also make the script silent after merged/closed or a completion sentinel so a missed cleanup does not spam.
- Use a finite repeat cap as orphan protection, but do not choose a cap shorter than the plausible workflow.
- Verify removal or completed state before reporting that updates stopped.

## Failure handling

- If Karan reports a missing update, inspect live cron state first. A healthy gateway does not prove a specific job is recurring.
- Compare `last_run_at`, `last_status`, `next_run_at`, `state`, and repeat progress.
- Check the original project/process before answering whether work is complete; cron history is only delivery evidence, not project truth.
- Own configuration mistakes directly, repair them immediately, and provide the current live project status in the same response.
