# Multi-worktree squash-merge closeout

Use this when a repository has many worktrees, the accepted merge method is squash, and the user authorizes merging plus deletion of the feature branch.

## Validated sequence

1. **Freeze live authority before mutation**
   - Re-read PR state, exact reviewed head, final PR commit, checks, latest conversation artifact, and unresolved review threads.
   - Record the remote base SHA and verify GitHub recognizes any intended closing issue through `closingIssuesReferences`.

2. **Prove repository convention**
   - Inspect recent accepted merge commits. A one-parent commit whose subject ends in `(#PR)` is strong evidence of squash convention, but still verify repository settings allow it.

3. **Merge without combined cleanup**
   - Use the exact-head guard when supported, e.g. `gh pr merge N --squash --match-head-commit <reviewed-head>`.
   - Do not combine branch deletion with this command; a cleanup failure must not obscure merge success.

4. **Independently prove the squash**
   - REST: `merged: true`, `state: closed`, non-null merge time, merge SHA, preserved head SHA, and prior base SHA.
   - `gh pr view`: `state: MERGED` with the same merge SHA.
   - Fetch `main`; require remote and tracking refs equal the merge SHA.
   - Require the merge commit's sole parent equals the prior base.
   - Require `merge^{tree} == reviewed-head^{tree}`.
   - Re-read the linked issue and confirm the expected `CLOSED` / `COMPLETED` state.

5. **Synchronize local default branch safely**
   - Preferred: create a temporary task-owned worktree for `main` if no clean default-branch worktree exists. After `git fetch origin main --prune`, prove local `main` is an ancestor of `origin/main`, then run `git merge --ff-only refs/remotes/origin/main` there.
   - Metadata-only alternative: when no post-merge test requires a checked-out `main`, `main` is not checked out in any worktree, and an unrelated control worktree may be dirty, snapshot that control worktree's status, prove local `main` is an ancestor of `origin/main`, and advance only the inactive ref (`git branch -f main refs/remotes/origin/main`). Re-read the control status exactly afterward. This manages repository metadata without granting authority over unrelated WIP.
   - If performing post-merge tests in a fresh worktree, run the repository's declared bootstrap/install command first; classify a missing-dependency failure as setup evidence, not a product regression, and rerun the canonical suite after bootstrap.

6. **Delete only the authorized branch surfaces**
   - Re-check the feature worktree is clean and task-owned.
   - Verify the remote feature ref still equals the reviewed head. The local feature branch may legitimately be stale if later commits were pushed from isolated builder/prover worktrees; do not use the stale local ref as merge evidence.
   - Delete the remote branch, remove the attached clean feature worktree, and only then delete the local branch.
   - For squash merges, `git branch -D` is permitted only after prior-base/tree-equality proof and remote deletion.
   - Preserve detached reviewer/evidence worktrees when the user asked only to “merge and delete branch.” Remove those only when cleanup/closeout scope explicitly includes them.

7. **Final absence and state readback**
   - Remote branch absent via `git ls-remote`.
   - Local and remote-tracking refs absent via `git show-ref`.
   - Feature and temporary closeout worktree paths absent and no longer registered.
   - Local, tracking, and remote `main` equal the verified merge SHA.
   - A temporary default worktree is clean and removed, or—when the inactive-ref alternative was used—the unrelated control worktree's status exactly matches its pre-closeout snapshot.
   - REST PR still says merged and the closing issue still says completed.

## Common ambiguity to avoid

A successful merge CLI exit is not proof. Conversely, a post-merge cleanup or fresh-worktree setup failure does not undo an already verified merge. Preserve these as separate phases and report each from direct readback.
