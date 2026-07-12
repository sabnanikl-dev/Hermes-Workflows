# Stale Merged Branch Cleanup

Use this when an `fe/*`, `hotfix/*`, or `preview/*` branch appears ahead of `main`, but the associated PR may already have been merged and the branch is just stale.

## Remote branch cleanup after a merged PR

1. Identify the PR for the branch:

```bash
BRANCH=fe/example-branch
gh pr list --state all --head "$BRANCH" --json number,title,state,baseRefName,headRefName,url,mergeable,mergeStateStatus,reviewDecision
```

2. Verify the PR really merged using the REST boolean, not local history:

```bash
gh api repos/OWNER/REPO/pulls/PR_NUMBER \
  --jq '{state, merged, merged_at, merge_commit_sha, head_ref:.head.ref, base_ref:.base.ref}'
```

Required before cleanup: `merged: true`.

3. If the branch still exists remotely, check whether merging it now would reintroduce conflicts or rollback newer work:

```bash
git fetch origin --prune
git merge-tree --write-tree origin/main origin/$BRANCH
# exit 1 + conflict messages means do not merge the stale branch as-is

git diff --stat origin/main...origin/$BRANCH
git diff --name-status origin/main...origin/$BRANCH
```

If the PR is already merged and the current branch conflicts or contains stale versions of files, do not open/merge another PR. Delete the stale remote branch instead:

```bash
git ls-remote --heads origin "$BRANCH"
git push origin --delete "$BRANCH"
git ls-remote --heads origin "$BRANCH"   # empty output verifies deletion
```

## Local branch cleanup after squash/rebase merge

A local branch can show commits ahead of `origin/main` after a squash/rebase merge even when the final file tree is already identical to `main`. Do not rely on ahead count alone.

Verify all of these before force-deleting the local branch:

```bash
BRANCH=fe/example-branch

# PR merge verification
gh api repos/OWNER/REPO/pulls/PR_NUMBER \
  --jq '{state, merged, merged_at, merge_commit_sha, head_ref:.head.ref, base_ref:.base.ref}'

# Remote branch is already absent or intentionally deleted
git ls-remote --heads origin "$BRANCH"

# Actual content diff is empty
git diff --stat origin/main.."$BRANCH"
git diff --name-status origin/main.."$BRANCH"

# Strongest check: tree hashes match
main_tree=$(git rev-parse origin/main^{tree})
branch_tree=$(git rev-parse "$BRANCH"^{tree})
echo "origin/main tree=$main_tree"
echo "$BRANCH tree=$branch_tree"
test "$main_tree" = "$branch_tree"
```

If trees match and PR is verified merged, it is safe to delete the local branch:

```bash
if [ "$(git branch --show-current)" = "$BRANCH" ]; then git checkout main; fi
git branch -D "$BRANCH"
git show-ref --verify --quiet "refs/heads/$BRANCH" || echo "removed"
```

## Pitfall

`git cherry -v origin/main BRANCH` may still show `+` commits after a squash/rebase merge because patch identity changes as later commits land. Treat it as a clue, not a blocker. The decisive checks are the PR REST `merged: true`, remote branch absence, empty two-dot content diff, and matching tree hash.