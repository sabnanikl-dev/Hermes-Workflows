# Visibility coding tasks: Claude/Codex GitHub PR lane

Use this when turning local SEO / visibility plans into website implementation tasks such as technical SEO foundations, service landing pages, schema/metadata updates, internal links, or route/page builds.

## Durable lesson

For Karan's website coding tasks, do **not** write vague handoffs like “builder implements the page.” Karan expects coding work to consume available Claude Code and Codex capacity through the standard GitHub PR workflow.

Correct lane:

```text
web-marketer / PM-spec brief
→ Claude Code and/or Codex CLI implementation in an isolated branch/worktree
→ focused GitHub PR linked to the tracker issue
→ reviewer checks code/content/SEO/accessibility
→ Hermes verifies PR head/checks/deploy state
→ Karan approval before merge/deploy/public mutation
```

## What to put in Linear/GitHub issues

For every visibility issue that touches website code, include an explicit execution-lane section:

```md
## Execution lane — coding tasks

This is a standard multi-agent GitHub PR workflow task, not a simple "builder manually implements" task.

Expected lane:
1. web-marketer / PM-spec confirms the brief, route, files, SEO intent, copy constraints, and acceptance criteria.
2. Claude Code and/or Codex CLI performs the coding in an isolated branch/worktree in the website repo.
3. The coding agent opens a focused GitHub PR linked to this issue, with changed files, validation commands, and screenshots/browser evidence when visual UI is affected.
4. reviewer checks code/content/SEO/accessibility. Claude/Codex may be used again for targeted fixes or a second-pass review.
5. Hermes verifies remote PR head, checks, review state, and deployment status after merge approval.

Karan approval is still required before merge/deploy/public-facing mutations.
```

## Applies to examples

- Technical SEO foundation: robots, sitemap, metadata, OG image, schema.
- Atlanta service pages: `/atlanta-wedding-coordinator`, `/day-of-wedding-coordinator-atlanta`, `/partial-wedding-planning-atlanta`.
- Website copy/schema alignment from approved source-of-truth docs.

## PR opening gates and Kanban unblock pattern

When the repo requires PRs to link a GitHub issue, do not treat a pushed branch as enough. Create or identify the repo issue first, include the closing keyword in the PR body (for example `Closes #148`), then verify:

1. the remote branch contains the expected commit (`gh pr view --json commits` or equivalent),
2. the PR is open and points at the expected head SHA,
3. the PR body links/closes the issue,
4. required checks are passing or explicitly pending/failing.

If a Kanban task blocked itself on an approval gate, a user comment such as “open pr in github repo” is approval context, not automatic execution. The responsible Hermes/orchestrator must actively resume the workflow: unblock or complete the blocked implementation task as appropriate, comment with the PR/issue/verification evidence, promote any child review task, and dispatch it. Do not assume a blocked worker is still listening to comments after it exited.

## Pitfalls

- “Builder” can remain a profile/orchestration label if the system uses it that way, but the actual coding executor should be named as Claude Code/Codex via PR workflow. Otherwise the issue reads like a manual handoff and loses the resource-allocation decision Karan already made.
- Do not report a visibility coding PR as opened/pushed from local state alone. Verify the remote branch, PR head, issue linkage, and checks before summarizing.
