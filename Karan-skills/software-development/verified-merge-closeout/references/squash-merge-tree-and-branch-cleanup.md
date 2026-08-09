# Squash merge proof and branch cleanup

Use this when the repository convention is squash merge and the user explicitly authorizes branch deletion.

## Why ancestry is insufficient

A squash commit has the prior base as its sole parent. The reviewed feature-head commit is intentionally not an ancestor, so `merge-base --is-ancestor <reviewed-head> <merge-commit>` and `git branch -d` are the wrong proof/cleanup mechanisms.

## Proof sequence

1. Freeze `reviewed_head`, `prior_base`, and the PR head immediately before merging.
2. Execute the approved squash merge without combining branch cleanup into the merge command.
3. REST-read the PR and require `merged: true`, `state: closed`, a non-null merge time, and a merge commit SHA.
4. Independently require `gh pr view` to report `MERGED` with the same merge commit.
5. Fetch the base branch and require the remote base and fetched tracking ref to equal the merge commit.
6. Require the squash commit's sole parent to equal `prior_base`.
7. Compare Git trees, not ancestry:
   - `git rev-parse "$merge^{tree}"`
   - `git rev-parse "$reviewed_head^{tree}"`
   - require equality.
8. Re-read linked issue closure semantics.

Tree equality proves the reviewed repository snapshot landed byte-for-byte even though commit history was rewritten into one squash commit.

## Cleanup sequence

Only when branch deletion was explicitly authorized:

1. Prove the feature worktree is clean and task-owned.
2. Delete the remote branch and verify the API/git operation succeeded.
3. Remove the clean feature worktree.
4. Because squash ancestry makes `git branch -d` refuse, use `git branch -D` only after the full merge/tree proof above and remote deletion.
5. Fetch with `--prune`.
6. Fail if any remains:
   - `git ls-remote --heads origin <branch>` returns a ref;
   - `refs/heads/<branch>` exists;
   - `refs/remotes/origin/<branch>` exists;
   - the removed worktree path exists.

Do not delete unrelated retained reviewer worktrees merely because the feature branch was deleted; preserve audit evidence unless cleanup scope explicitly includes them.
