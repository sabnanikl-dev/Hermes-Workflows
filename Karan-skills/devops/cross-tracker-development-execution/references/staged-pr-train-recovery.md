# Staged PR Train Recovery

Use this recovery when a large draft PR has become the unit of repeated review/fix churn even though some child-owned sections are coherent and independently shippable. The goal is to move the merge unit to explicit dependency boundaries while preserving evidence and re-proving every new SHA.

## Decision gate

Prefer a staged train when most are true:

- the Linear parent already has clear child issues or separable acceptance slices;
- accepted foundation/router/docs/core behavior can be extracted without the churn-heavy subsystem;
- each proposed slice has its own tests and a clear dependency order;
- the current PR mixes concerns or repeated fixes obscure independently known behavior;
- one subsystem is causing most churn and deserves its own child contract;
- interim merges can remain fail-closed and do not expose an unsafe incomplete product.

Do not split merely because a PR is long. Keep one PR when behavior is atomic, cross-slice invariants cannot be safely staged, or interim `main` would be broken.

## Recovery sequence

1. **Freeze the mega-PR as evidence.** Stop adding fixes. Snapshot exact head, body, commits, review surfaces, and remote branch. Do not force-push or delete it.
2. **Map the train before mutation.** Assign every code/docs/test surface to one child. Create a new child when a churn-heavy cross-cutting subsystem has no clean owner.
3. **Amend all contracts together.** Update the Linear parent, affected children, and GitHub umbrella issue so they agree on:
   - ordered dependencies;
   - one clean current-`main` PR per child;
   - scope and explicit exclusions for each slice;
   - Karan's separate approval for every merge;
   - interim PRs use `Refs #<umbrella>`;
   - only the final integration PR uses `Closes #<umbrella>`.
4. **Extract from current `main`, not the moving mega-PR.** Create a new worktree/branch at `origin/main`. Cherry-pick only accepted commits, or reconstruct accepted files when commits mix scopes.
5. **Prove provenance.** For cherry-picks, compare stable patch IDs:

   ```bash
   git show <old-sha> --pretty=format: | git patch-id --stable
   git show <new-sha> --pretty=format: | git patch-id --stable
   ```

   Also inspect `git log --reverse origin/main..HEAD`, complete changed-file scope, and `git diff --check`.
6. **Run complete slice gates.** Include every supported runtime, compile/build/lint/config checks, and a clean worktree. Green gates prove mechanics, not semantic readiness.
7. **Publish a dedicated draft PR.** Name the child, source commits, new exact head, scope/exclusions, verification, and the no-transfer rule for old approvals. Verify local HEAD = remote branch = PR `headRefOid` = final PR commit, and `closingIssuesReferences` is empty for interim slices.
8. **Supersede the mega-PR only after the first replacement PR is live.** Replace its body with a concise evidence notice, close it unmerged, verify `mergedAt` is null, and preserve its remote branch until the train completes.
9. **Run a fresh exact-head triad.** Historical approval, patch equivalence, and green tests are context only; none transfers to the extracted SHA.
10. **Stop the train on a blocked foundation.** Keep it draft, record the decision packet on GitHub and Linear, and do not begin dependent extraction. If the authorized boundary was “open/review/pause,” do not silently launch a repair; request a tightly bounded fix/re-review authorization.

## Reviewer packet scoping

Name later-train features that are explicitly out of scope. This prevents a foundation from being blocked for behavior assigned to a later child while preserving every invariant promised by the foundation itself.

A useful orchestration-tool split is:

- foundation: state, locks, exact-head inspection, gates, worktrees, bounded attempts, direct push/comment readback, fail-closed outcomes;
- router/contract: slim skill surface and conditional references;
- trusted execution: builder/reviewer launch, progress, relay, and complete head/commit readback;
- human-feedback reconciliation: complete feedback surfaces, positive artifact ownership, native resolution, stable reads, and finite acknowledgement semantics;
- final integration: accumulated-main proof only, no feature invention.

## Adversarial probes for an executable foundation

A clean extraction can reveal old semantic gaps missed by the historical suite. Probe at least:

1. **Interrupted-attempt resume:** persist an opened attempt on A, advance remote/PR to B without completing push/comment verification, restart, and require fail-closed rather than `merge-ready`.
2. **Builder-worktree agreement:** advance remote/PR to B while the attempt worktree remains at A; require an explicit local `git rev-parse HEAD` read and exact agreement with marker/remote/PR head.
3. **Refused reset ordering:** with state and lock both present, an unforced reset must refuse before deleting either artifact.
4. **Operational-clone control paths:** reject state, lock, worktree, and other writable control paths equal to or nested inside `source_repo`.
5. **State/lock persistence failures:** deterministic filesystem errors must become structured fail-closed results, not raw `OSError` escapes.

These are reusable false-success/recovery seam probes, not implementation-specific trivia.

## Verification/readback checklist

- Parent and affected children describe the same train and dependency order.
- A dedicated child owns any newly separated churn-heavy surface.
- GitHub umbrella issue identifies the sole final closing PR.
- Interim PR uses `Refs`, API reports zero closing references.
- Stable patch IDs or file-level provenance match accepted source.
- New exact head passes complete slice gates.
- Reviewer artifacts bind to the new head and are read back.
- Mega-PR is closed unmerged, branch still exists, evidence remains reachable.
- Mechanical `MERGEABLE/CLEAN` is never reported as semantic readiness while valid blockers remain.
- No dependent slice starts until its prerequisite is zero-blocker and explicitly merged by Karan.

## Pitfalls

- Do not directly merge “known-good parts” from the mega-PR; extract into a clean current-main PR and re-prove.
- Patch equivalence does not transfer old approvals.
- Interim PRs reference the umbrella; only final integration closes it.
- Preserve the superseded branch through extraction.
- Amend the parent, children, and GitHub issue together; dated normative amendments are acceptable when full rewrites are risky.
- Do not start downstream work after a blocked foundation.
- Test success is not semantic proof; adversarial review may still expose false-success paths.
