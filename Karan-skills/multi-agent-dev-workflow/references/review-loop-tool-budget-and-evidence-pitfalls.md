# Review-loop tool budget and evidence pitfalls

Session-derived pattern from a PR review/fix loop that hit the tool-call ceiling mid-fix.

## Durable lessons

### 1. Do not start a new fix loop unless there is enough budget to verify it

A fix loop is not complete when the builder starts editing. It is only complete after:

1. Builder process exits with a clear marker.
2. Worktree diff is inspected.
3. Tests/checks/build are rerun.
4. Follow-up commit is pushed.
5. Push is verified against the live PR commit list/head SHA.
6. Builder fix comment is posted/read back.
7. Required reviewers re-review current head.
8. GitHub review surfaces are re-read and blockers are closed.

If the session is near tool-call or context limits, stop at the verified checkpoint and report exact next commands instead of launching the fix. Starting a fix that may finish after the operator loses tool access leaves the PR in an unknown state.

### 2. Treat reviewer processes as incomplete until the process exits

A reviewer may submit an early approval or comment, then continue running and later submit a stronger/final review (including `REQUEST_CHANGES`). Do not infer the lane’s final result from an intermediate `gh pr view` while the Codex/Claude reviewer process is still running.

Required closeout:

- Wait for the reviewer process to exit or explicitly kill/cancel it.
- Read the process final marker (`DONE: REVIEWER=...`).
- Re-query all GitHub review surfaces after process exit.
- Prefer the role-signed latest review on the current `headRefOid`, but also inspect same-account multiple reviews because GitHub `latestReviews` may collapse or obscure role history.

### 3. Screenshot evidence must show the changed component state

For frontend PRs, screenshots filed as responsive/component evidence must actually show the changed component, not only the page hero/top fold. If the changed area is lower on the page:

- Scroll the component into view before capture.
- Capture the default committed state and, when the feature is data-gated, a clearly labeled injected/demo state for geometry only.
- Record viewport dimensions and what state is shown (blocked/single/multi-photo, empty/loading/error, etc.).
- Pair visual screenshots with a geometry/overflow check when the acceptance criteria include “no clipping” or “no horizontal scroll.”

Do not claim responsive component QA from screenshots that do not contain the component.

### 4. Data-gated UI needs synthetic geometry QA

When the committed public state is intentionally empty/blocked until a later asset/CMS gate, still test the future populated state without mutating live data:

- Inject local in-memory fixture data in the browser/page context.
- Verify single-item behavior hides inactive controls.
- Verify multi-item carousel/card geometry at required breakpoints.
- Keep fixture screenshots/evidence labeled as temporary QA, not production content.

This is especially important when the acceptance criteria concern layout behavior that only appears after future data ingestion.
