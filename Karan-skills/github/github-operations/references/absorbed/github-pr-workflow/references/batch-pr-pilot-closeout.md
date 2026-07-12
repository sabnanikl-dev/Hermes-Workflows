# Batch PR Pilot Closeout

Use this for multi-repo pilots where the user approves merging several PRs and wrapping associated tracker issues.

## Sequence

1. Precheck each PR independently:
   - `gh pr view <N> -R OWNER/REPO --json state,mergeStateStatus,headRefName,baseRefName,title,url,headRefOid`
   - `gh pr checks <N> -R OWNER/REPO --watch=false`
2. Merge one PR at a time, preferably squash + delete branch:
   - `gh pr merge <N> -R OWNER/REPO --squash --delete-branch`
3. Immediately verify merge via REST API boolean:
   - `gh api repos/OWNER/REPO/pulls/<N> --jq '{state, merged, merged_at, merge_commit_sha, head_ref: .head.ref}'`
   - Required before reporting success: `merged: true`.
4. Verify deleted branch:
   - `git ls-remote --heads https://github.com/OWNER/REPO.git HEAD_BRANCH`
   - Empty output means gone.
5. Sync local checkouts:
   - `git fetch origin main --prune`
   - `git checkout main`
   - `git pull --ff-only origin main`
   - delete local feature branch if still present.
6. If local `main` tracks an old/template remote after repo repointing, fix tracking:
   - `git branch --set-upstream-to=origin/main main`
7. If local `main` diverged only because the same branch commit was also present locally before squash merge, reset local copy to remote after merge verification:
   - `git reset --hard origin/main`
8. Close tracker issues only after all relevant PRs are verified merged.

## Pitfalls

- `gh pr checks` may exit non-zero when no checks exist; treat the output (`no checks reported`) as informational, not a merge blocker unless branch protection requires checks.
- When merging several PRs back-to-back, GitHub may temporarily report `mergeable: UNKNOWN` / `mergeStateStatus: UNKNOWN` for the next PR right after `main` advances. Do not merge from the stale/unknown state. Wait a few seconds, re-query `gh pr view <N> --json mergeable,mergeStateStatus`, and require `MERGEABLE`/`CLEAN` before proceeding.
- Squash merging creates a new merge commit on `main`; local branches that contain pre-squash commits can diverge from `origin/main`. After merge is verified, local reset/cleanup is appropriate for disposable pilot branches.
- For batch closeout, never generalize one verified merge to the whole batch; verify every PR and every tracker issue independently.
