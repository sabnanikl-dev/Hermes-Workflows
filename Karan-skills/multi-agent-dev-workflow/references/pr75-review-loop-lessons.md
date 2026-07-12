# PR #75 review-loop lessons — native deps, fallback builder, and re-review evidence

Use this as a concrete pattern when a reviewer loop hits merge conflicts plus local verification noise.

## Durable lessons

### 1. Rebuild native deps before turning local test failures into blockers

If `npm test` fails in a Node/Electron repo with native modules (`better-sqlite3`, `node-pty`, etc.) and the failure looks unrelated to the PR, check whether the checkout has stale native deps from a different Node version before escalating as a code blocker.

Pattern:

```bash
npm ci --silent
npm test
```

In PR #75, `npm test` initially failed in `test/store.test.js` because SQLite persistence fell back to JSON (`'json' !== 'sqlite'`). After `npm ci --silent`, the same PR passed `npm test` (`305/305`). The durable lesson is not the exact failure text; it is to refresh native deps before classifying local native-backend failures.

### 2. Treat dirty merge state as the primary blocker even when feature behavior looks good

PR #75 visually satisfied the issue and passed smoke locally, but GitHub reported `mergeStateStatus: DIRTY` after `main` moved. The correct blocker was mergeability, not feature behavior.

Required fix pattern:

1. Merge/rebase current base into the PR branch.
2. Resolve conflicts narrowly.
3. Preserve both sides' feature invariants.
4. Push and verify the PR head/merge state on GitHub.

For GodMode renderer conflicts, preserve both the new UI behavior and any concurrent lifecycle/IPC wiring from `main`.

### 3. Re-review must target the new head, not the old review state

After a fix commit lands, reviewers must re-read live PR state and review the current `headRefOid`. Do not count prior approvals/request-changes against an old head as final evidence.

Final closeout should verify:

```bash
gh pr view <PR> --json headRefOid,mergeStateStatus,reviewDecision,statusCheckRollup,commits

gh api repos/<owner>/<repo>/pulls/<PR>/reviews \
  --jq '[.[] | select(.commit_id=="<head sha>") | {user:.user.login,state,submitted_at,body}]'

gh api graphql ... reviewThreads(first:100) ...
```

### 4. Fallback builder lanes must be disclosed

If the intended Claude builder lane is unavailable and another agent performs the fix, the PR comment and final report must say so. This can make the PR code-quality clean while still not being a perfect clean Claude-builder dogfood loop.

Use wording like:

> Claude Code CLI was unavailable in this Hermes terminal, so this fix was performed as a Codex builder fallback.

Do not overstate the loop purity.
