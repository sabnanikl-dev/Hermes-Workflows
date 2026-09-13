# Harness Process Audit Reference

Use after a client/project harness pilot or when Karan asks what worked, what did not, and what should change in the reusable harness template.

## Trigger

- Repo has accumulated issues/PRs/reviews and Karan asks for first-principles process findings.
- A task-specific harness exposed reusable template gaps.
- Karan explicitly says not to overengineer the workflow.

## Audit Inputs

1. GitHub issues: open/closed, state reasons, labels, bodies, closure timing.
2. GitHub PRs: merged/closed/open, base/head, commits, files, PR bodies.
3. PR issue comments, reviews, and review comments.
4. Local clone of the task repo: `AGENTS.md`, `docs/spec.md`, build plan, friction logs, outputs/evidence.
5. Local clone of the reusable template repo for comparison.

Prefer the REST-based audit pattern in `github-pr-workflow` to avoid GraphQL traversal limits from deeply nested `gh pr list --json ...` queries.

## Synthesis Shape

Write a plan/audit doc that covers:

- Executive take: one clear verdict.
- Current repo state and whether its role changed.
- Issues created/closed/open and what each means.
- PRs made, comments/reviews, and how review changed the work.
- What got done.
- What did not get done.
- First-principles read: what the workflow is actually trying to protect.
- What could go right.
- What could go wrong.
- Recommended next work in the task repo.
- Minimal changes for the reusable template.
- Explicit “what not to add” section to prevent overengineering.

## Template Change Guidance

Keep reusable template updates class-level and role-based:

- Use `Builder`, `Evaluator`, `Orchestrator`, not task-specific tool names unless the template is explicitly tool-specific.
- Keep local/private agent skills optional unless the repo docs make them project requirements.
- Required constraints must live in repo docs and issues, not only in one agent’s memory or local skill library.
- Add tiny scaffolds that reduce repeated mistakes; avoid full PM systems.

Good minimal template fixes discovered in the JMD pilot:

- Correct post-merge verification to use REST `merged: true` boolean.
- Add generic harness stewardship: docs are part of the deliverable when implementation changes scope, setup, paths, conventions, verification, approval gates, or known friction.
- Add a tiny `docs/build-plan.md` scaffold for phase sequencing, gates, and PR handoff.
- Make friction logging practical: log reusable lessons only, not routine progress.
- Keep skills/capabilities agent-agnostic and optional by default.

## Storage

For durable process audits, save a curated wiki page under Hermes Brain, index it, and log it. Do not copy GitHub’s full tracker state into the wiki; preserve the synthesized lessons and link/source the repo.
