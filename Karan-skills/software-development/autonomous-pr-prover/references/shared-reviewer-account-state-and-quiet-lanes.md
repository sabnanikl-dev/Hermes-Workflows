# Shared reviewer-account state and quiet reviewer lanes

Use this when two independent review lanes share one GitHub reviewer account, or when a lane has finished reasoning but has not exited.

Artifact publication, transport, and readback belong to `pr-prover`; hardened reviewer publication and credential scoping are owed by PAPI-90 (see the proof map in `pr-prover/MISSION.md`). Do not recover tokens or post artifacts by hand from this reference. What follows are the durable risk lessons only.

## One account collapses two roles

GitHub collapses effective review state by account. A later approval from one lane can neutralize another lane's live change-request state before the blocker is fixed. So:

- an account-level review decision is not per-role evidence;
- role separation has to be carried inside the artifact — explicit role, verdict, and exact head — never inferred from the account;
- an artifact tied to an older head is audit history, never a current-head pass.

A single collapsed account-level summary field therefore cannot prove two lanes. Proving both is a property of per-role, head-bound artifact evidence — invariant M4 in `pr-prover/MISSION.md` — and producing and reading that evidence is `pr-prover`'s work, with its GitHub-published reviewer half owed by PAPI-90.

## A quiet lane is not a finished lane, and a finished lane is not a dead one

A reviewer process can complete its audit yet stay alive because long-lived MCP/CodeGraph children do not exit. Silence is therefore ambiguous in both directions:

- quiet output is not evidence of a hang, and it is not evidence of completion;
- an unexited lane is not a failed lane — a lane whose children outlive its audit still produced a result;
- no locally visible result is not the same fact as no posted artifact, because stale subprocess output can hide an artifact that did post.

Resolving that ambiguity is lane lifecycle work `pr-prover` owns: bounded runtimes and fail-closed timeouts, run-owned worktrees at a verified head, and direct GitHub readback (M9, M10, M13). Per-lane elapsed/quiet progress reporting and a report field separating transport success from readback are the parts PAPI-90 still owes. Long-lived MCP/CodeGraph children are why an exit signal alone under-determines a lane's state; reconciling them belongs to that owned lifecycle rather than to hand-run process control driven from this reference.

## Transient failures are not durable beliefs

A single transient API failure inside a lane is not evidence that an identity or surface is unavailable. Re-verify before it becomes a verdict, and prefer a fail-closed stop over a guess.

A lane that completed a full independent audit but could not publish is a degraded *transport* result, not a degraded review — and the two must never be reported as the same thing.
