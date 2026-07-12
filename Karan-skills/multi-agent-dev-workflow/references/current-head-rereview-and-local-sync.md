# Current-Head Re-review + Local Sync Lessons

Session-derived pattern from a multi-agent GitHub issue-to-PR loop where the builder profile opened a PR, Codex A/B requested changes, several small fix commits landed, and Hermes had to prove the final PR head was actually merge-ready.

## Durable lessons

### 1. Treat builder push reports as claims until the local worktree is synced

A builder/fix lane may commit and push successfully while the orchestrator's local worktree remains behind `origin/<branch>`. Before running local grep/tests/validators to verify a reported fix, sync the worktree to the PR head:

```bash
git fetch origin <branch>
git status --short --branch
git merge --ff-only origin/<branch>
git rev-parse HEAD
gh pr view <PR> --json headRefOid,commits --jq '{headRefOid,lastCommit:.commits[-1].oid}'
```

Only then inspect files and rerun verification. Otherwise you can falsely think a stale issue remains because you are reading the previous local commit.

### 2. Review approvals are head-specific; rerun both lanes after every follow-up commit

If a follow-up commit lands after Reviewer A approves but Reviewer B still blocks, A's approval may no longer count for the new head. Do not declare merge-ready until both role-signed reviewers have clean outcomes on the current `headRefOid`.

Required readback:

```bash
gh pr view <PR> --json headRefOid,reviewDecision,mergeStateStatus,statusCheckRollup

gh api repos/<owner>/<repo>/pulls/<PR>/reviews --paginate \
  --jq '[.[] | select(.commit_id=="<current-head>") | {user:.user.login,state,body,submitted_at,commit_id}]'
```

Check for the role signatures in bodies:

- `Reviewed by: Codex Reviewer A via Hermes orchestration`
- `Reviewed by: Codex Reviewer B via Hermes orchestration`

### 3. `reviewDecision: CHANGES_REQUESTED` can persist until current-head approvals land

After blocker fix comments are posted, GitHub can still report `CHANGES_REQUESTED` until reviewers submit new reviews on the current head. Fix comments alone are not re-review evidence.

### 4. Search for stale docs/comments after doc-blocker fixes, but after syncing

When a reviewer flags stale docs such as old load-order comments, use targeted searches on the synced head:

```bash
rg -n 'empty until #41|intentionally empty until #41|../assets/jmd-owner-about' \
  docs/ site/ scripts/
```

This catches contradictory examples that validators may not cover, such as a sample path in component docs that differs from runtime data.

### 5. Final closeout gate

Before telling Karan a PR is merge-ready, verify all of the following from live GitHub, not local assumptions:

- PR `headRefOid` equals local `HEAD` and the last PR commit.
- `mergeStateStatus` is clean/mergeable.
- Required status checks are success.
- Current-head A and B role-signed reviews are pass/approved or explicitly non-blocking.
- GraphQL review threads are empty or resolved/outdated.
- Any fix comments are present and signed if the builder/fix lane posted them.

This is especially important after several small doc-only fix commits: they are easy to dismiss as harmless, but they still change the reviewed head.
