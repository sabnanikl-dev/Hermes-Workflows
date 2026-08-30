---
name: verified-merge-closeout
description: "Execute an explicitly approved GitHub PR merge and reconcile linked trackers with exact-head, merge-commit, base-ref, comment-ID, and state readback proof."
version: 1.2.0
author: Hermes Agent
metadata:
  hermes:
    tags: [github, pull-requests, merge, verification, linear, closeout]
    related_skills: [autonomous-pr-prover, github-operations, linear, tracker-artifact-closeout]
---

# Verified Merge Closeout

## Purpose

Use this after a PR has already passed its required review/evidence gate and Karan explicitly authorizes the pending merge. This skill owns the last mile:

```text
explicit approval → live preflight → ready-marking if needed → merge → independent GitHub proof → tracker reconciliation → final report
```

It does not own implementation, reviewer-loop execution, deployment, release, or downstream issue selection.

## Triggers

Load this skill when:

- the last report says “remaining action: Karan approve mark-ready/merge” and Karan immediately approves;
- Karan explicitly says to merge a named, already-proven PR;
- a merged PR must be reconciled to Linear or another tracker with durable evidence.

Do not use an old continuation, repair-cycle, or generic workflow approval as merge authority.

## Core invariants

1. **Approval is proximal and scoped.** A short “Approved” counts only when it directly answers a clearly stated pending ready/merge action. It does not authorize branch deletion, deploy/release, account changes, parent-issue edits, or downstream execution.
2. **The reviewed head is immutable.** Re-query immediately before mutation; any head drift invalidates the prior merge-ready certificate.
3. **Repository convention selects merge method.** Inspect allowed methods and recent accepted merges instead of reflexively squashing.
4. **Command exit is not merge proof.** Report success only after direct GitHub readback says `merged: true`.
5. **Base integration is part of proof.** For a merge commit, verify expected parents include the prior base and exact reviewed head. For a squash merge, verify the merge commit's sole parent is the prior base and its tree exactly equals the reviewed PR head's tree; ancestry cannot prove a squash landed unchanged.
6. **Tracker state is re-fetched after merge.** GitHub↔tracker automation may already have transitioned the issue. A completed state is not proof that acceptance checkboxes, completion evidence, or parent train rows were reconciled; verify those surfaces independently.
7. **No duplicate external writes.** A printed URL/ID plus nonzero exit is ambiguous state; read back before retrying.
8. **Close only the authorized scope.** Parent issues, umbrellas, downstream slices, deploys, and releases remain untouched unless the approval explicitly includes them. Interpret cleanup wording precisely:
   - “merge and delete branch” includes the remote/local/remote-tracking feature refs and, when necessary, the clean worktree that has that branch checked out; preserve detached reviewer/evidence worktrees unless the user also asked for cleanup/closeout or repository policy explicitly owns their disposal;
   - “merge, delete branch, and close out/clean up” includes clean task-owned reviewer/evidence worktrees and evidence-backed tracker closeout, but not downstream execution.
   Never infer broad scratch-worktree deletion from branch deletion alone.
9. **Preserve tracker chronology.** If the tracker already records a verified “merge-ready but unmerged” checkpoint, do not rewrite it after merge. Append a later dated merge checkpoint with the merge commit, timestamp, ancestry, branch/worktree cleanup, and new boundary. Historical evidence remains true for the time it described.
10. **Prerequisite completion is not successor adoption.** When a merged repair unblocks another issue only conditionally, update the dependent issue to say that the merge prerequisite is satisfied while preserving its current state and explicit adoption/rerun gate. Never infer downstream execution authority from the prerequisite merge approval.
11. **Ordered multi-PR approval stays conditional at each head.** When Karan authorizes a reviewer to approve an ordered PR chain (for example, merge a baseline repair first and merge the dependent feature only after refresh), treat the instruction as authority for the stated sequence—not as permission to skip the dependency barrier. Merge and prove the prerequisite, update the dependent branch from the new base, rerun full exact-head deterministic gates and environment-specific smoke evidence, obtain the required fresh reviewer verdict on the new head, and only then merge/delete the dependent branch.

## Procedure

### 1. Freeze the live pre-merge state

Query the PR and verify:

- `state == OPEN`;
- `headRefOid` and final PR commit equal the exact reviewed head;
- review artifacts and current-head evidence remain valid;
- no new human feedback, inline comment, review thread, failed check, or head change appeared;
- mechanical state is `MERGEABLE` / `CLEAN` or any deviation is explicitly resolved;
- the intended operator GitHub identity is active.

For draft PRs, GitHub may leave aggregate `reviewDecision` blank even when a formal current-head approval exists. Do not treat that aggregate as either proof of approval or proof of failure. Read the full reviews API and verify the formal review by reviewer login, role signature, state, and exact `commit_id`; verify signed comment-only reviewer lanes from the conversation-comment API. Until ready-marking is explicitly authorized, describe this state as **review-complete / draft-ready for Karan's decision**, not already GitHub merge-ready. See `references/draft-review-artifact-preflight.md` for exact-head filtering, raw artifact readback, stale-metadata handling, and the post-ready recheck barrier.

Never use the earlier merge-ready snapshot as the mutation preflight.

### 2. Select the merge method

Inspect repository settings for merge, squash, and rebase support. Inspect recent accepted merges when policy allows multiple methods. Preserve the established convention and auditability of the reviewed head.

Do not delete the feature branch unless the approval or repository policy explicitly includes deletion.

### 3. Mark ready, then re-check

If the PR is draft:

1. mark it ready;
2. re-read `isDraft`, `state`, `headRefOid`, `mergeable`, and `mergeStateStatus`;
3. stop if the head changed, the PR stopped being clean, or new feedback appeared.

Ready-marking is a distinct external mutation; do not assume it implies successful merge.

### 4. Merge and independently prove it

Execute the approved merge, then require all of the following:

- REST pull readback: `merged: true`, `state: closed`, `merged_at`, `merge_commit_sha`;
- `gh pr view`: `state: MERGED`, non-null merge time, same merge commit;
- fetched `origin/<base>` equals the remote base ref and both equal the merge commit;
- for a normal merge commit, parents include the prior base and exact reviewed PR head;
- for a squash merge, the sole parent equals the prior base and the merge tree equals the exact reviewed PR head tree;
- closing-reference behavior matches the contract (`Refs #N` should not silently close umbrella issue `#N`).

If these disagree, report an ambiguous or failed closeout—never “merged” from CLI exit alone.

When tracker closeout depends on live behavior produced by an automatic post-merge deployment, add a runtime barrier before closing the tracker. Deployment success and public reachability prove publication, not feature behavior. For consent-gated analytics or similar integrations, require the feature's positive control as well as its negative controls: a stored choice, mounted provider, iframe, queue, or DOM marker does not prove external delivery.

1. verify the exact merge commit's deployment/status is successful;
2. probe the live source surface without following redirects first, recording status and exact `Location` for root, a nested path with query parameters, and any ordering-sensitive legacy path;
3. prove path/query preservation and rule precedence from those first-hop headers;
4. keep target reachability as a separate claim—an environment that cannot follow the canonical target does not erase valid first-hop redirect proof, but it also must not be reported as a fresh target-health pass;
5. update durable knowledge only after the live behavior is observed, then check the final tracker gate and read back the completed state/comment.

If branch/worktree cleanup is explicitly authorized, perform it only after the merge and base proof. Freeze the exact cleanup set first: branch-only deletion does not silently expand to detached reviewer/evidence worktrees.

1. fetch the verified remote base. Prefer fast-forwarding a clean default-branch worktree. If no clean default worktree exists, no post-merge tests require a checkout, and the local default ref is not checked out anywhere, an inactive-ref update is acceptable only after proving `local-default` is an ancestor of `origin/default`; update that ref without checking out or touching an unrelated dirty control worktree, then verify its status is byte-for-byte unchanged;
2. prove every worktree selected for removal is clean and unambiguously task-owned;
3. remove the branch-holding feature worktree; remove detached reviewer/evidence worktrees only when cleanup/closeout scope explicitly includes them;
4. delete the local feature branch with `git branch -d` after a normal merge whose updated default branch contains the reviewed head;
5. for a verified squash merge, `git branch -d` will correctly refuse because the reviewed commit is not an ancestor: only after REST merge proof, prior-base parent proof, merge-tree equality, a clean task-owned feature worktree, and remote branch deletion may cleanup use `git branch -D`;
6. delete the remote feature branch when not already deleted;
7. fetch with `--prune` and verify all three refs are absent: remote branch via `git ls-remote`, local branch, and stale `refs/remotes/origin/...` tracking ref;
8. verify each requested worktree path is absent. Require a clean default worktree only when one was actually used; otherwise prove the inactive default ref equals the remote merge commit and the unrelated control worktree's pre-existing status is unchanged.

Use explicit `if ...; then exit 1; fi` checks for expected-absent refs in compound shell commands. This keeps the final command status unambiguous while still failing closed.

See `references/branch-and-worktree-cleanup.md` for safe ordering and readback shapes.

### 5. Reconcile the linked tracker

Only after GitHub proof:

1. re-fetch the tracker issue and any authorized parent train/roll-up issue;
2. detect whether integration automation already moved the child to `Done` / `completed`;
3. treat workflow state and body contract as independent: even an auto-completed child may still have unchecked acceptance boxes or missing completion evidence;
4. omit `stateId` when it is already completed; do not make an idempotent status write merely to satisfy a stale precondition;
5. check only evidence-backed acceptance lines and append a concise dated merge checkpoint; preserve any earlier “merge-ready but unmerged” checkpoint as historical evidence rather than rewriting it;
6. when closeout explicitly includes the train/roll-up, update only that child’s parent sequence/acceptance row while leaving the parent state unchanged;
7. if another issue depended on this merge, record only that the merge prerequisite is satisfied; leave the dependent issue state, candidate-adoption gate, and downstream execution authority unchanged unless separately approved;
8. add one durable child closeout comment, one narrowly scoped dependent-disposition comment when step 7 applies, and—if the parent body changed—one parent checkpoint comment;
9. capture immutable comment IDs and verify each directly;
10. re-fetch and verify final child state name/type, semantic description content, dependent state/boundary, authorized parent-row transition, and unchanged parent state.

When the PR does not directly link a Linear issue but the user asks to “update Linear if necessary,” do not assume either “no update” or broad tracker mirroring. Inspect the live rollout hierarchy and find the **narrowest issue whose contract explicitly names the repository, PR, GitHub issue, or merge prerequisite**. If that issue is an unstarted pilot/dependent milestone and a separate predecessor still blocks it:

- append one prerequisite-satisfied evidence comment to that narrow issue only;
- include PR URL, exact reviewed head, merge commit/method/time, linked GitHub issue disposition, and requested branch/worktree cleanup proof;
- preserve its workflow state, description checkboxes, blocking relations, approval digest, and downstream execution gate;
- do not also comment on the parent/umbrella unless its body or state was explicitly authorized to change;
- verify the comment by immutable ID and re-read the dependent issue plus the blocking predecessor relation.

This is milestone reconciliation, not mirroring GitHub coding status into Linear. It records that a named historical prerequisite became true without implying pilot adoption, queue approval, successor selection, or execution authority.

Linear may normalize Markdown bullets, naked URLs, and trailing newlines. Compare unique checkpoint headings, checkbox transitions, SHAs, and evidence links rather than byte equality. Direct comment bodies can still be compared exactly when preserved by the API.

### 6. Final report

Report only directly verified facts:

- PR URL and final `MERGED` state;
- reviewed head;
- merge commit, timestamp, and method;
- base-ref and parent proof;
- tracker final state and verified closeout-comment ID;
- umbrella issues, branches, deploys, and downstream work intentionally left unchanged.

## Pitfalls

- “Merge-ready” is not merge authorization.
- A continuation approval for reviewer/fix work is not merge approval.
- Do not choose squash merely because it is common; inspect repository convention.
- Do not combine `--delete-branch` with the merge unless deletion is explicitly in scope.
- Do not treat a dirty unrelated control worktree as unusable metadata control or as permission to alter it. When using it only to manage refs/worktrees, snapshot its status and require the same status after closeout.
- Do not remove detached reviewer/evidence worktrees from a branch-only deletion request; require explicit cleanup/closeout scope.
- Do not update Linear from a pre-merge snapshot; integrations can race or auto-complete it.
- Do not re-post a GitHub/Linear comment after a wrapper error until the returned URL/ID is read back.
- Do not mark the parent/umbrella Done merely because one child PR merged.
- Do not claim the reviewed head landed without verifying ancestry or merge parents.

## Verification checklist

- [ ] Approval directly names or immediately follows the pending merge action.
- [ ] Live PR head equals reviewed head immediately before mutation.
- [ ] PR was re-checked after ready-marking.
- [ ] REST says `merged: true`.
- [ ] `gh pr view` says `MERGED` with the same commit.
- [ ] Remote and fetched base refs equal the merge commit.
- [ ] Normal merge parents include the prior base and exact reviewed head, or squash proof shows prior-base sole parent plus exact reviewed-tree equality.
- [ ] Closing references and umbrella issue state are verified.
- [ ] Tracker was fetched after merge before any status mutation.
- [ ] Auto-completed tracker state was not mistaken for completed checkbox/evidence reconciliation.
- [ ] Final tracker state, semantic body, authorized parent row/state, and closeout comment IDs were read back directly.
- [ ] When deletion was authorized: the default branch/ref was synchronized without touching unrelated WIP; the branch-holding worktree, local branch, remote branch, and remote-tracking ref were each verified absent; detached review/evidence worktrees were removed only if cleanup/closeout scope included them.
- [ ] Branch deletion/downstream/deploy authority was not inferred.

## References

- `references/github-linear-merge-closeout.md` — concrete readback matrix, ambiguity handling, and GitHub→Linear sequencing.
- `references/branch-and-worktree-cleanup.md` — post-merge cleanup ordering, task-owned reviewer-worktree scope, non-force local deletion, prune barriers, and absence verification.
- `references/squash-merge-tree-and-branch-cleanup.md` — squash-specific prior-base/tree proof and the narrowly gated local `-D` cleanup path when normal ancestry is intentionally absent.
- `references/multi-worktree-squash-closeout.md` — validated squash closeout for stale local feature refs, temporary default-branch worktrees, deterministic fast-forward sync, dependency bootstrap before post-merge tests, and branch-only cleanup boundaries.
- `references/draft-review-artifact-preflight.md` — draft PR aggregate-state trap, exact-head multi-surface review proof, byte-exact reviewer-body readback, stale-metadata classification, and the post-ready recheck barrier.
