# Cross-session pause and resume for active development work

Use this when a Linear-governed coding issue and its GitHub branch/PR must pause with uncommitted work or an incomplete migration. The goal is fresh-session reconstruction from live systems without resetting coherent work or treating stale green evidence as current.

## Pause packet

Before ending the session:

1. Stop the task-scoped builder/reviewer processes and confirm no relevant child remains. Bind cleanup to the recorded worker session/PID/worktree command; do not kill unrelated desktop application helpers merely because their command contains `claude` or `codex`.
2. Re-read and record:
   - Linear issue, state, parent, dependencies, and active claim;
   - repository, GitHub issue/PR, branch, worktree, and exact local HEAD;
   - remote branch and PR head when readback is in scope;
   - modified/untracked path counts, `git diff --stat`, `git diff --check`, and whether anything was committed or pushed.
3. Separate **last proven evidence** from **current WIP**. If edits happened after a passing suite, say explicitly that those results predate the current delta and do not count as acceptance.
4. Freeze the remaining blocker ledger: exact blocker classes, prohibited scope, downstream-owned limits, expected checks, and ordered resume steps. Avoid vague “continue where we left off” prose.
5. Keep task-local prompt/ledger files only as convenience pointers. Linear and GitHub plus the live repository remain authoritative.
6. Add a concise `PAUSED_HANDOFF` Linear comment, capture the returned comment ID, then verify that comment directly by ID and confirm the issue state.

Recommended fields:

```text
PAUSED_HANDOFF — <date>
Issue/state and active claim:
Repo / PR / branch / worktree / exact HEAD:
Committed or pushed:
Dirty paths and diff hygiene:
Last proven gates (and why stale, if applicable):
Open blocker ledger:
Worker/process cleanup:
Authority exclusions:
Ordered resume steps:
Downstream boundary:
```

## Resume packet

When the user asks to resume:

1. Read the paused Linear comment directly by ID when available, then re-read the live issue, PR, and repository/worktree. Session history is secondary context, not execution authority.
2. Confirm that the issue is still active, the branch/worktree/HEAD still match, the dirty delta remains, no unexpected commit/push appeared, and no old task worker is still running.
3. Inspect the partial delta before changing anything. **Do not reset blindly.** An interrupted migration can temporarily fail many tests because code and fixtures stopped mid-conversion.
4. Run a diagnostic baseline before relaunching. Record the real failure count/shape as the resume checkpoint. Treat expected interrupted-state failures as unfinished work—not as a newly introduced blocker and not as waived evidence.
5. Resume the same frozen blocker ledger and authority envelope. Preserve the fix-cycle count when no new reviewer pass or blocker set occurred.
6. Continue an existing Claude conversation only when its identity is deterministic and no later persistent Claude session displaced it. `--continue` means “most recent,” not “the task named in the handoff.” If identity is uncertain, start a fresh worker using the pause packet, current diff, exact paths, and blocker ledger.
7. Run long repairs in the background with completion notification and a real budget. During quiet periods inspect process liveness/tree/activity, HEAD, dirty paths, diff stat, and diff hygiene; buffered stdout alone is not a hang signal.
8. Add a concise `RESUMED_HANDOFF` Linear comment linking the paused comment ID, current live state, diagnostic baseline, new worker handle, unchanged authority exclusions, and next checkpoint. Capture and directly verify the comment ID.

## Acceptance after resume

Any passing evidence that predates current WIP is historical only. Before commit/push or re-review:

- rerun full required suites on every supported runtime;
- rerun compile/build/config examples and deterministic former-red probes;
- run live boundary probes required by the blocker class;
- run `git diff --check` and inspect status;
- independently inspect the builder’s final delta and completion marker.

Only after the resumed WIP is green may Default Hermes commit/push if the active contract authorizes it. Then verify local HEAD = remote branch HEAD = PR `headRefOid`, create a fresh detached exact-head review worktree, and run the required reviewer lanes. A resumed worker’s success marker is never current-head review approval.

## Pitfalls

- “WIP preserved” alone is not reconstructable.
- A temporary prompt file is not durable tracker evidence.
- A test count without saying whether later edits made it stale is misleading.
- `--continue` after unrelated persistent Claude activity can attach to the wrong task.
- Broad process-name searches can confuse desktop helpers with task workers.
- Do not advance Linear to review or post completion while the resumed worker is still running.
