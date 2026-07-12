# Real Pilot Publication Checklist

Use this when a real Linear-backed pilot produces local repo/Kanban output and then needs to become visible in GitHub/Linear.

## Lesson from JMD/PAPI pilot

A pilot can be technically complete while looking incomplete to Karan if Linear is not updated. In the JMD/PAPI pilot, local Kanban tasks, commits, reviewer verdicts, and profile lock-down were completed first, but only one Linear comment was visible. Karan checked Linear and reasonably asked whether anything else had happened.

## Publication sequence

1. **Confirm scope of external side effects**
   - Local-only
   - Push/open PR
   - Post Linear comments
   - Move Linear statuses
   - Merge/deploy/live client action

2. **Push/open PRs**
   - Create private per-client repo if needed.
   - Preserve template origin as a separate remote if retargeting a cloned harness.
   - Push a clean base/default branch and the feature branch.
   - Open PR with issue IDs, summary, verification, and safety boundaries.

3. **Verify GitHub before reporting**
   - `gh repo view owner/repo --json nameWithOwner,visibility,defaultBranchRef,url`
   - `gh pr view N --repo owner/repo --json url,state,baseRefName,headRefName,commits`
   - Confirm expected commit SHAs are present on the PR; do not rely on local git alone.

4. **Post Linear comments**
   - Include PR link(s), what changed, verification performed, remaining gate, and safety boundaries.
   - If PRs are open but not merged, move issues to `In Review`, not `Done`.
   - Use `Done` only after the human/review gate accepts or explicitly asks.

5. **Verify Linear before reporting**
   - Re-query each issue.
   - Confirm latest comment contains the PR link.
   - Confirm state is the intended state.

## Reporting format

Use concrete buckets:

- **Visible now in Linear/GitHub**: PR links, states, posted comments.
- **Still pending/local**: merges, Done transitions, deployment/client actions.
- **Verification performed**: exact remote commit checks and Linear re-query.

## Pitfalls

- Do not say “pilot completed” without clarifying whether Linear/GitHub surfaces were updated.
- Do not move to `Done` just because the agent work finished; open PRs belong in `In Review`.
- When pushing a branch from a local `main` that is ahead of origin, use `git push origin HEAD:refs/heads/<feature-branch>` for the PR branch, then reset local upstream back to `origin/main` if needed.
- If creating a per-client repo from a harness cloned from a template, rename the original remote to `template` and set the new client repo as `origin`.
