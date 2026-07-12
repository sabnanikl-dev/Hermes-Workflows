# Batch PR Review Goal Template

Use this when asking Codex to review several related PRs and keep a persistent objective across checkout, validation, and browser inspection steps.

```text
/goal Thoroughly review <repo> PRs <PR list> for correctness, issue alignment, UX/visual behavior, regressions, and merge readiness, verified by reading each associated GitHub issue before reviewing the PR, checking the PR body/diff/changed files, running applicable local validation, and performing browser/visual inspections where the PR affects UI or runtime behavior. Use repo `<owner>/<repo>`; work from an isolated review worktree or clean checkout so no local work is mutated. For each PR, first read the linked issue and comments (`gh issue view <issue> --comments`) and treat the issue acceptance criteria plus PR claims as the review checklist: <PR → issue mapping>. For each PR, inspect metadata (`gh pr view`), comments/reviews, changed files, and full diff; check out the PR; run applicable validation (`npm ci` if needed, `npm run lint`, `npm run build`, tests); then run targeted browser/Playwright verification where relevant. Do not merge or modify PR branches. Do not approve any PR that has blocking findings, warning-level issues, unverified acceptance criteria, missing necessary visual evidence, or actionable recommendations that should be addressed before merge. If a PR is clean with only non-blocking nits, approval is allowed only if all required evidence is gathered. If recommendations are found, the verdict must be “Not approved / changes recommended” or “Request changes”; include exact file/line references when possible, concrete fix recommendations, and what evidence would make it approvable. If GitHub blocks formal review submission because the same account authored the PR, post a top-level PR comment instead with the same verdict. Final output must include one section per PR with: associated issue read, validation commands and results, browser/visual checks performed, findings grouped as Critical / Warnings / Suggestions / Looks Good, final verdict, and whether a GitHub review/comment was posted with URL. Continue until all PRs have been reviewed or until a real blocker prevents review; if blocked, report the blocker, what was already checked, and the exact next step to unblock.
```

Fill in:
- `<repo>`: human project/repo name.
- `<PR list>`: explicit PR numbers.
- `<owner>/<repo>`: GitHub slug.
- `<PR → issue mapping>`: exact mapping, e.g. `PR #129 → issue #125`.
- UI/browser checks: spell out the route, viewport, interaction, network/console condition, and visual acceptance criteria for each relevant PR.

Review discipline:
- Reading the issue first is mandatory; PR descriptions can omit acceptance criteria or overstate completion.
- Approval requires evidence, not just a clean diff.
- Same-author GitHub review restrictions are not a blocker to review; use a top-level comment fallback.
