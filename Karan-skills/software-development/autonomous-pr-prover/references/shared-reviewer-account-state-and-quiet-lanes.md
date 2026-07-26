# Shared reviewer-account state and quiet reviewer lanes

Use this when two independent review lanes share one GitHub reviewer account, or when a lane has finished reasoning but has not exited.

Artifact publication, transport, and readback belong to `pr-prover`; hardened reviewer publication and credential scoping are owed by PAPI-90 (see the proof map in `pr-prover/MISSION.md`). Do not recover tokens or post artifacts by hand from this reference. What follows are the durable risk lessons only.

## One account collapses two roles

GitHub collapses effective review state by account. A later approval from one lane can neutralize another lane's live change-request state before the blocker is fixed. So:

- an account-level review decision is not per-role evidence;
- role separation has to be carried inside the artifact — explicit role, verdict, and exact head — never inferred from the account;
- an artifact tied to an older head is audit history, never a current-head pass.

When both lanes must be proven, read the full artifact set and filter by role signature *and* head, rather than trusting a single collapsed summary field.

## A quiet lane is not a finished lane, and a finished lane is not a dead one

A reviewer process can complete its audit yet stay alive because long-lived MCP/CodeGraph children do not exit. Before concluding anything about such a lane:

- inspect the process tree and CPU instead of trusting silence;
- inspect the lane's own worktree status;
- check whether a result file or a complete review body exists;
- check the live GitHub surface directly, because stale subprocess output can hide an artifact that did post.

If the lane is idle and only MCP/CodeGraph children remain, terminate the child first and let the parent exit. Do not kill an active reviewer merely because stdout is quiet.

## Transient failures are not durable beliefs

A single transient API failure inside a lane is not evidence that an identity or surface is unavailable. Re-verify before it becomes a verdict, and prefer a fail-closed stop over a guess.

A lane that completed a full independent audit but could not publish is a degraded *transport* result, not a degraded review — and the two must never be reported as the same thing.
