# Branch and Worktree Cleanup After a Verified Merge

Use this only when branch/worktree cleanup is explicitly authorized and GitHub has already been independently read back as merged.

## Why the order matters

A local feature branch can be fully merged on GitHub while the local default branch still points at the pre-merge base. Deleting the local feature branch before syncing the default branch can produce a misleading “not yet merged to HEAD” warning or tempt an unsafe `-D`. Sync the clean default branch first, then use ordinary `git branch -d` as an extra ancestry guard.

Deleting the remote branch is also not the end of cleanup: a stale `refs/remotes/origin/<branch>` remains until fetch/prune. Verify remote, local, remote-tracking, and worktree state separately.

## Safe sequence

1. **Prove the merge first**
   - REST PR: `merged: true` and merge SHA.
   - PR view: `MERGED` with the same SHA.
   - Remote default ref equals the merge SHA.
   - For merge commits, parents include the pre-merge base and exact reviewed head.

2. **Select and sync the canonical clean default-branch worktree**
   - A machine may contain multiple independent clones of the same remote in addition to linked worktrees. Prefer the checkout named by the live tracker/repository mapping or current task contract; otherwise prove the intended canonical checkout from remote identity and active worktree ownership.
   - Do not fast-forward, prune, or “tidy” unrelated stale clones merely because they share the remote. Record them as intentionally untouched if their state matters to the final report.
   - Require the selected default-branch worktree to be clean.
   - `git fetch origin <default> --prune`
   - `git pull --ff-only origin <default>`
   - Verify local default and `origin/<default>` equal the merge SHA.

3. **Inventory removal scope**
   - Feature worktree checked out on the merged branch.
   - Disposable detached reviewer worktrees created solely for this PR/head sequence, including older-head reviewer worktrees retained across fix cycles.
   - Exclude shared, dirty, ambiguous, differently owned worktrees, and detached reviewer/evidence worktrees when the user asked only to delete the branch.
   - Require `git status --porcelain` empty for each selected path.
   - For multi-cycle closeouts, freeze the selected absolute paths in a `/tmp` manifest before removal and read it back. Record the expected count so a partial cleanup cannot look complete.

4. **Remove the branch-holding worktree, then delete the local branch safely**
   - Remove the clean worktree that has the feature branch checked out with `git worktree remove <clean-task-path>`.
   - After a normal merge whose synchronized default branch contains the reviewed head, use `git branch -d <feature-branch>` as an ancestry guard.
   - After a squash merge, ordinary `-d` correctly refuses because the reviewed head is not an ancestor of the squash commit. Use `git branch -D` only after all squash-specific gates pass: REST merge proof, prior-base sole-parent proof, merge-tree equality with the exact reviewed head, clean branch-holding worktree removal, and verified remote branch deletion.
   - Any refusal or mismatch outside that exact squash case is a stop requiring investigation.

5. **Delete and prune the remote branch**
   - Delete through the intended authenticated GitHub/git path. For a squash closeout, verify this deletion before the narrowly gated local `-D` step above.
   - `git fetch --prune origin`.

6. **Verify independent absence surfaces**
   - Remote source of truth: `git ls-remote --heads origin refs/heads/<branch>` is empty.
   - Local branch: `refs/heads/<branch>` absent.
   - Remote-tracking cache: `refs/remotes/origin/<branch>` absent.
   - Every requested worktree path is absent and no longer appears in `git worktree list --porcelain`.
   - Default worktree remains clean at the verified merge SHA.

## Manifest-driven batch cleanup

Long review/fix loops can leave many clean detached worktrees on older heads. Treat them as one explicit cleanup set rather than removing only the final A/B/Auditor worktrees:

1. Parse `git worktree list --porcelain` with a standalone local script or bounded `python -c` invocation.
2. Select only paths whose ownership is unambiguous for the merged PR/mission.
3. Verify every selected path is clean, write one absolute path per line to a `/tmp` manifest, record the count, and read the manifest back before deletion.
4. During removal, re-check path existence and cleanliness immediately before each `git worktree remove`.
5. Afterward, require every manifest path to be absent from both the filesystem and a fresh `git worktree list --porcelain`; verify the removed count equals the frozen count.

Avoid `producer | python` pipelines for these checks. Apart from triggering security scanners, they blur which stage failed. Save producer output to `/tmp` and parse it in a separate bounded step, or use explicit shell `if` checks.

## Shell verification shape

For expected absence inside a compound command, avoid a bare negated command as the final status signal. Use explicit branches so the command exits cleanly on success and clearly on failure:

```bash
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "local branch still exists" >&2
  exit 1
fi

if git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
  echo "remote-tracking ref still exists" >&2
  exit 1
fi

if test -n "$(git ls-remote --heads origin "refs/heads/$BRANCH")"; then
  echo "remote branch still exists" >&2
  exit 1
fi
```

## Tracker handoff

Only after cleanup verification, write tracker evidence that names:

- reviewed head and merge commit;
- remote/local/remote-tracking branch absence;
- task/reviewer worktree removal count or paths;
- clean reconciled default branch;
- any intentionally preserved shared worktrees or umbrella issues.
