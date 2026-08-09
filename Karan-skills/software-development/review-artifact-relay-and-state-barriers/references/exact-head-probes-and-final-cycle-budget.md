# Exact-head probes and final-cycle budget barriers

Use this reference when an adversarial PR loop relies on temporary deterministic reproducers, multiple detached worktrees, or a long final review chain.

## Probe provenance

A temporary probe is executable evidence, not timeless truth. Before every run:

1. Read it and identify its source/worktree binding (`ROOT`, `PYTHONPATH`, imported module path, config path, or embedded SHA).
2. Verify the bound checkout's `HEAD` equals the exact PR head under review.
3. If rebinding is required, create a copy and diff it against the authoritative probe. The exact-head copy should differ only in the declared root/SHA unless an observation wrapper is explicitly needed.
4. Print interpreter version and imported module path when practical.
5. Never cite output from an old detached worktree as evidence about a newer PR head.

A green suite cannot repair stale probe provenance. When output is surprising, inspect the bound root before diagnosing product code.

## When green means an expected exception

Some former-red probes encode a defect as unexpected success—for example, a third lock acquisition that should become `LockContention`. After the fix, the unchanged script may stop early with a non-zero exit because it did not catch the newly correct exception.

Use two complementary executions:

- **Exact probe:** run the authoritative probe with only its root rebound. Confirm it stops at the expected exception and imports current exact-head source.
- **Observation wrapper:** make a separate copy that differs only by the minimal expected-exception catch required to print later observables. Diff this wrapper against the exact probe before execution.

Require shipped assertion-based regressions for durable proof. Report the exact probe's non-zero exit honestly; do not call it green without explaining that the expected fail-closed exception is the corrected behavior.

## Resource-ownership follow-up

When code creates a resource at a pathname and later removes it, review beyond ordinary cleanup:

- retain identity for the resource actually created (for files, device/inode from the owned descriptor);
- use one ownership-aware deletion path for normal release and partial-initialization cleanup;
- preserve absent or replaced paths rather than deleting by pathname alone;
- close the identity-check-to-delete race for conforming processes with proportional cross-process serialization or an atomic primitive;
- verify normal release, failed initialization, replacement preservation, third-party contention, cleanup dispositions, primary-cause preservation, and descriptor closure;
- distinguish removed, already absent, replacement preserved, and cleanup not confirmed.

Use a real cross-process probe in addition to same-process mocks when the contract claims cross-process mutual exclusion. A timing-only thread test is weak unless a negative control proves it fails when the serialization mechanism is removed.

## Final-cycle execution budget barrier

Before launching a final fix or re-review cycle, reserve enough execution budget for the entire remaining chain:

1. builder completion and exact remote/PR-head readback;
2. independent full verification and former-red probes;
3. PR-body/evidence refresh;
4. Reviewer A and B completion;
5. exact-head artifact relay and GitHub readback;
6. refreshed post-A/B packet;
7. Integration Auditor completion;
8. auditor relay/readback;
9. live mergeability/thread/check/draft verification;
10. authorized issue/PR state closeout.

If remaining tool/context budget cannot cover the chain, stop at a stable checkpoint **before** launching the next expensive lane. Record process/session IDs, exact SHA, artifact paths, live URLs, completed gates, and the next single action.

Reduce call overhead by batching independent reads/tests, using one exact-head capture packet per review stage, and avoiding repetitive polls when a background process already has completion notification.

## Reviewer-process retry

If a reviewer process fails while preparing its artifact after code evidence was gathered:

- treat it as an incomplete lane, not a product pass or blocker;
- preserve the exact code head and read-only worktree;
- inspect any durable probe/artifact already written;
- retry with a narrower technical prompt focused on the same frozen question;
- do not change code, reviewer identity, model pin, or acceptance contract merely to obtain a verdict;
- require a complete signed artifact before advancing.

## Corrective-cycle classification

A same-cycle corrective rerun is valid only when the builder omitted or incompletely implemented an already-frozen blocker before that cycle's re-review completed. A new blocker discovered by a fresh exact-head reviewer is a new blocker class. After the configured final cycle, obtain an explicit scope-bound exception before launching another fix/re-review chain; do not relabel the new class as an old-cycle omission.

## Ready-without-merge and tracker closeout barrier

When the user asks for a PR to become mergeable/ready but does **not** authorize merge, keep four claims separate: mechanical mergeability, semantic zero-blocker readiness, draft/ready state, and merge authorization.

Use this order:

1. Require current-head Reviewer A, Reviewer B, and Integration artifacts with zero blockers; relay and directly read back immutable artifact IDs.
2. Re-query the live head, formal reviews, conversation comments, inline comments, review threads, checks, closing references, draft state, and merge state. Do not rely on a capture prepared before the final auditor exited.
3. Re-read the PR body. Replace stale head SHAs, test counts, artifact links, and “review pending” language before changing draft state.
4. Mark the PR ready only when the task authorizes that transition. Do not merge.
5. Re-query and require: exact current head; `state=OPEN`; `isDraft=false`; `mergedAt=null`; expected `MERGEABLE/CLEAN`; current-head approval; zero unresolved current threads; zero inline comments; expected check state; and expected closing-reference count.
6. Only after GitHub passes that barrier, append tracker closeout evidence and transition the tracker issue to its completed state.
7. Capture the tracker evidence-comment ID and read that exact comment back. Re-query the issue and verify both the completed state **name and type**; mutation responses may omit fields needed for final proof.

A successful status mutation is not sufficient evidence by itself. Likewise, `MERGEABLE/CLEAN` does not prove semantic readiness, `isDraft=false` does not authorize merge, and a zero-blocker auditor artifact does not prove the draft transition occurred.
