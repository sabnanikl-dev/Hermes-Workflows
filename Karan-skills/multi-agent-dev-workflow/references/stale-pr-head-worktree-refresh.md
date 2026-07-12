# Stale PR head verification — worktree-isolated GitHub refresh pitfall

## When this applies

Use this note when implementing or reviewing GodMode/current-head verification gates, especially issue classes where a PR branch can move after verification and the UI must not keep showing stale green evidence.

## Session-derived lesson

A verification gate that checks only "expected commit exists somewhere in the PR commit list" is unsafe for open PRs. The current remote PR head must also match the verified expected commit. Otherwise reviewer launch, synthesis, merge readiness, or the UI can trust evidence for an old head after a follow-up push.

The first fix for issue #61 added `stale_head`, `currentHeadVerified`, and explicit reviewer/merge gates, but reviewers found two follow-up gaps:

1. **Observed-head reconciliation must update displayed evidence immediately.** If GodMode observes the bound PR head moving via refresh/discovery/watcher, it must record/push stale verification evidence without waiting for the operator to click Re-verify or Start Reviewers.
2. **Worktree-isolated runs cannot rely on the active PR from the primary checkout branch.** In worktree isolation, the bound run branch lives in the run worktree while the primary checkout may remain on a different branch. A GitHub refresh that reconciles only `state.activePr` can miss the bound PR entirely and leave stale green evidence visible.

## Durable implementation pattern

For GodMode-style PR verification:

- Fetch and carry `headRefOid` / `headSha` on both single active-PR reads and repo-wide PR list reads.
- Select the observed bound PR head by `run.prNumber` first, independent of the selected checkout branch.
- Fall back to active-PR head only when the run is unbound or no PR-number match exists.
- Feed that selected head into the same reconciliation path used by explicit verification gates.
- Emit the verification-changed event so the renderer updates `VerificationPane` immediately.
- Keep a guarded adopt-current-head recovery path for `stale_head`, confirming PR number and branch still match before updating the run's expected commit.

## Regression tests to require

Add tests for:

- Expected commit in PR history but not current head => `stale_head`, not `verified`.
- Reviewer/merge gates reject `stale_head` and reject `verified` evidence when `currentHeadVerified=false`.
- Observing a new bound PR head without manual reverify records/pushes stale evidence.
- Worktree-isolated `pr_opened` run where the primary checkout's active PR is different or absent: repo-wide pull list contains the bound PR with a moved head, and refresh updates verification to `stale_head`.
- Adopt-current-head path verifies PR number + branch, updates expected commit, and records a new verification audit trail.

## Review checklist

When reviewing this class of change, check:

- Does every path that observes PR state include current `headRefOid`?
- Is the bound PR matched by PR number/branch, not merely by current checkout branch?
- Does the UI change as soon as observed drift is known?
- Are reviewer launch, synthesis, and merge readiness all gated by current-head evidence?
- Do docs describe the current-head invariant and recovery semantics?
