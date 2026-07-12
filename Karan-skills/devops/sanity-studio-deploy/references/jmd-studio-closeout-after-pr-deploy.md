# JMD Studio issue closeout after PR/deploy already happened

Use this when a JMD Sanity Studio issue is still open, but prior repo-side PR and hosted Studio deploy evidence already exist in GitHub comments or merged PR history.

## Pattern

1. **Verify the existing merge/deploy before doing new work.**
   - Read the issue comments for prior deploy evidence.
   - Re-query the merged PR with REST, not just `gh pr view`, and confirm `merged: true`, `merged_at`, and `merge_commit_sha`.
   - Fetch `origin/main` and use a clean detached worktree at current `origin/main` for verification.

2. **Re-run deterministic repo-side evidence from current `origin/main`.**
   - Render or serialize the Studio desk structure if the repo has a script for it.
   - Run the relevant Studio gates (`npm --prefix studio run validate`, `npm --prefix studio run build`) and any issue-specific root validators.
   - Run `npm test` when the issue touches a repo-wide contract or if closeout will claim the current branch is healthy.

3. **Verify hosted/deployed evidence without making account changes.**
   - Check `https://jmd-studio.sanity.studio/` headers/redirects.
   - Run `npx sanity schema list` from the verified worktree when authenticated CLI access exists.
   - If an unauthenticated/local browser shows Sanity's “Connect this studio to your project” / “Add development host” gate, do **not** click through without explicit approval. Registering the Studio or adding a development host is a Sanity project/account mutation.

4. **Close the issue only with a clear closeout comment.**
   Include:
   - PR merge evidence and current `origin/main` head.
   - Current desk/navigation evidence.
   - Commands re-run and pass/fail results.
   - Hosted URL/schema evidence.
   - Any browser/auth limitation, clearly labeled as not a blocker if deterministic deploy evidence is sufficient.

## Why this matters

Approval-gated Studio issues can remain open after the repo PR merges because hosted deploy or authenticated UI evidence was intentionally separated from repo-side work. Before launching a new builder/reviewer loop, check whether the approval-gated step was already completed and only the issue state is stale. Closeout work should be verification-first, not a duplicate implementation.