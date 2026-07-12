---
name: github-issue-specs
description: "Spec strong GitHub issues from user intent: repo-grounded, agent-ready, scoped, verifiable issue contracts. Use when drafting, creating, updating, splitting, or grooming GitHub issues."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [github, issues, specifications, planning, agent-ready, verification]
    related_skills: [github-operations, writing-plans, software-development-lifecycle]
---

# GitHub Issue Specs

## Purpose

Use this skill when the user asks for a GitHub issue such as:

- "Create a GitHub issue for X project so we can do Y and Z."
- "Draft an issue for this feature/bug/refactor."
- "Make issue #N clearer / builder-ready."
- "Split this big issue into focused implementation tickets."
- "Turn this plan, friction log, PR review, design, or conversation into GitHub issues."

The goal is to produce **agent-ready issue contracts**, not vague tickets. A great issue should let:

- a builder implement without guessing;
- a reviewer judge pass/fail from observable criteria;
- the operator verify completion without trusting self-reports;
- future agents understand boundaries, risks, and source-of-truth context.

## Core Standard

A strong issue is:

1. **Outcome-first** — starts with the user/operator-visible capability or problem solved, not an implementation label.
2. **Grounded** — based on current repo/project state, existing issues, docs, code, and constraints.
3. **Scoped** — splits the work into focused slices and names what is out of scope.
4. **Executable** — points to relevant files, seams, commands, dependencies, and likely implementation areas.
5. **Verifiable** — acceptance criteria are observable pass/fail checks, including edge cases and failure modes.
6. **Safe** — preserves approval gates, avoids unintended account/deploy/live mutations, and does not broaden authority casually.
7. **Project-agnostic** — adapts to each repo's conventions instead of imposing GodMode-specific structure everywhere.

## Authority and Mutation Rules

- If the user asks to **draft/spec/write** an issue, draft only. Do not create or edit GitHub issues.
- If the user explicitly asks to **create/open/file** a GitHub issue, that is approval to create the issue in the correct repo after prerequisite checks.
- If the target repo is ambiguous, ask before mutating. Never guess a repository for GitHub writes.
- If creating/editing an issue, verify the mutation by re-reading the issue (`gh issue view ... --json title,body,labels,state,url`) before reporting success.
- Search existing issues/PRs before creating to avoid duplicates or stale scope.
- Use labels/assignees/milestones/projects only if they exist or the user explicitly requests creating/configuring them.
- Live external side effects (deploys, DNS/account changes, emails, purchases, credentials) do not become approved just because an issue mentions them. Encode approval gates in the issue.

## When to Ask Clarifying Questions

Default to acting when the answer can be recovered from repo state, docs, previous issues, or the user's wording. Ask only when ambiguity materially changes the issue contract or risks creating the wrong thing.

Ask before proceeding when any of these are unclear and not recoverable:

1. **Target repo/project** — multiple plausible repos and the user wants the issue created.
2. **Desired outcome** — several incompatible goals could fit the prompt.
3. **Authority boundary** — the issue might require live account mutation, deploys, purchases, client-facing messages, credential changes, or data deletion.
4. **Scope split** — the request bundles unrelated work and you need the user's priority/order.
5. **Acceptance bar** — success depends on a business/product decision the repo cannot reveal.
6. **Source of truth conflict** — repo docs, existing issues, and user wording disagree in a way that changes implementation.

Good clarifying questions are narrow and decision-shaped:

- "Should this be a repo implementation issue, or an ops/readiness tracker with no live activation?"
- "Do you want this created now in `owner/repo`, or drafted first for review?"
- "Should mobile responsiveness be part of this issue, or split into a follow-up?"
- "Is the goal to preserve the existing UX and fix reliability, or redesign the flow?"

## Required Workflow

### 1. Identify the issue type

Choose the closest archetype. The body can mix patterns, but the archetype determines section emphasis.

| Type | Use when | Emphasize |
| --- | --- | --- |
| Feature / implementation | Build a new user-visible capability | Goal, current code state, scope, acceptance criteria, verification |
| Bug / regression | Something is broken or previously worked | Repro, expected vs actual, root-cause clues, regression test |
| Refactor / architecture | Improve internals without major UX change | Invariants, boundaries, migration plan, tests, no behavior drift |
| Test / reliability | Add coverage, smoke tests, CI/checks | Failure being prevented, deterministic fixtures, failure diagnostics |
| Ops / readiness tracker | Repo-side tracking for external/manual work | Gates, approvals, evidence, non-goals, no-live-change boundary |
| Milestone / dogfood run | Prove an end-to-end workflow | Prerequisites, run protocol, rules of engagement, deliverables |
| Follow-up / split | Extract focused work from larger issue/PR | Parent links, reason for split, narrow scope, explicit out-of-scope |
| Issue grooming/update | Clarify or correct existing issue | Read issue first, inspect current state, preserve useful context, verify edit |

### 2. Ground the issue before writing

Use the available tools and repo-local context before drafting. Minimum grounding for code repos:

- Verify repo identity and default branch.
  - `git status --short --branch`
  - `git remote -v`
  - `gh repo view <owner/repo> --json nameWithOwner,url,defaultBranchRef,isPrivate`
- Read project guidance if present:
  - `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.agentic/*`, `README*`, `docs/spec*`, `docs/architecture/*`, `docs/conventions/*`.
- Inspect existing issues and labels:
  - `gh issue list --state open --limit 100 --json number,title,labels,url`
  - `gh label list --limit 100` when labels matter.
- Inspect relevant code/docs/tests before naming implementation seams.
- For stale local checkouts, prefer grounding against remote default branch (`git fetch`, `git show origin/main:<path>`, `git grep` where appropriate) without disturbing WIP.
- For web/design/inspiration issues, inspect both the inspiration source and target implementation; separate "what works there" from "how to adapt here."

If repo access is unavailable, say so clearly and produce a lower-confidence draft labeled with assumptions instead of inventing code facts.

### 3. Search for duplicates and adjacent work

Before creating or recommending creation:

- Search open and recently closed issues for key terms.
- Search PRs if the work may already be in progress or merged.
- Link related issues explicitly and explain boundaries.
- If existing issue is close but vague, prefer updating/grooming it over creating a duplicate.
- If the request bundles unrelated risks, split into multiple focused issues and explain why.

### 4. Write the issue as an executable contract

Use this default body for implementation-style issues.

```markdown
## Goal

<One short paragraph naming the user/operator-visible outcome. Avoid starting with a library, file, or implementation detail unless that is the real deliverable.>

## Context

<Why this matters now. Link incidents, friction logs, parent issues, PRs, docs, customer/user impact, or project milestone. State the guiding product/engineering principle.>

## Current state verified

Verified against `<branch/ref/commit/date>`.

- `<file/module/doc>` — <what exists today and why it matters>.
- `<file/module/doc>` — <relevant seam, behavior, gap, or invariant>.
- Existing issues/PRs checked: <links or "none found">.

## Scope

### 1. <Slice name>

- <Specific work to implement.>
- <Important constraints.>

### 2. <Slice name>

- <Specific work to implement.>

### 3. Docs / config / tests

- <Docs/config/tests that must change.>

## Out of scope

- <Explicit non-goal.>
- <Adjacent issue or future work.>
- <Live/deploy/account mutation if not approved.>

## Acceptance criteria

- [ ] <Observable pass/fail behavior.>
- [ ] <Edge case or failure mode.>
- [ ] <Regression prevention / test coverage.>
- [ ] <Security/safety/approval invariant if relevant.>
- [ ] <Docs/operator-visible behavior if relevant.>

## Suggested implementation notes

- Likely files/modules: `<path>`, `<path>`.
- Suggested tests: `<test file or command>`.
- Reuse existing seams: <existing functions/types/patterns>.
- Avoid: <known trap or overreach>.

## Verification

```bash
<project-specific check command>
<project-specific test command>
<project-specific build/lint command>
```

Manual smoke: <operator-visible validation path, if automated tests are insufficient>.
```

### Bug / regression variant

Add or substitute:

```markdown
## Reproduction

1. <Step>
2. <Step>

## Expected behavior

<What should happen.>

## Actual behavior

<What happens now, including error text/logs/screenshots if available.>

## Regression guard

<The specific test/smoke/check that must fail before the fix and pass after.>
```

### Milestone / dogfood / end-to-end run variant

Use when the issue is a tracked run or milestone rather than one implementation PR:

```markdown
## Goal

<The end-to-end milestone outcome.>

## Why a tracked issue

<Why this deserves an issue and what evidence closes it.>

## Prerequisites

Hard blockers:
- <#issue / condition>

Recommended but not blocking:
- <#issue / condition>

## The run

### Setup

1. <Step>

### Loop / execution protocol

1. <Step>

### Rules of engagement

- <What must go through the product/tool.>
- <What counts as a finding vs shortcut.>
- <Human approval gates.>

## Deliverables

- [ ] <Evidence artifact/link/comment/doc.>
- [ ] <Friction/follow-up issues.>
- [ ] <Spec/docs update.>

## Out of scope

- <Non-goals.>

## Verification

<Checklist and commands.>
```

### Ops / readiness tracker variant

Use when GitHub should track repo-visible readiness, not directly perform external live operations:

```markdown
## Goal

<Readiness or artifact outcome, not unapproved live activation.>

## Context / authority boundary

<Source of truth, approvals required, and explicit statement that this issue does not authorize live mutation.>

## Scope

- <Repo-side artifact/checklist/config/documentation work.>
- <Read-only validation/evidence gathering.>

## Approval gates

- [ ] <Human approval required before live action.>
- [ ] <Credential/account owner approval if relevant.>

## Out of scope

- <Deploy/DNS/account/message mutation unless separately approved.>

## Acceptance criteria

- [ ] <Evidence exists and is linked.>
- [ ] <Dry-run/readiness check passes.>
- [ ] <No live changes occurred without approval.>
```

## Quality Bar for Acceptance Criteria

Acceptance criteria must be concrete enough that a reviewer can mark each checkbox pass/fail.

Prefer:

- "With `gh` unavailable on PATH, the pane shows `gh_missing` guidance and does not crash."
- "Cleanup refuses a dirty worktree and states the reason."
- "The command exits non-zero if the preload bridge is absent."
- "The PR body includes `Closes #N` and verification output for `npm test`."

Avoid:

- "Works well."
- "Improve reliability."
- "Handle edge cases."
- "Make the UI better."

For each issue, include at least one criterion for:

- primary happy path;
- relevant edge/failure path;
- regression/test coverage;
- verification command or manual smoke;
- safety/authority invariant if external effects are possible.

## Scope-Splitting Rules

Split into separate issues when:

- the work touches unrelated risk surfaces (e.g. UI redesign + auth + deployment);
- one slice is needed now and another is speculative/future;
- one slice can merge independently and produce a reviewable artifact;
- mobile/responsive/accessibility work would balloon a general feature issue;
- live ops/account changes should be gated separately from repo implementation;
- milestone evidence/follow-ups are different from the implementation PRs.

When splitting, write each issue with:

- parent/related issue links;
- what was intentionally excluded;
- dependency order, if any;
- acceptance criteria independent enough to close separately.

## Labels and Metadata

- Use existing labels only unless the user asks to create labels.
- If no label system is obvious, prefer no labels over hallucinated labels.
- Suggested common mapping when labels exist:
  - feature → `enhancement`
  - bug/regression → `bug`
  - documentation-only → `documentation`
  - tests/smoke/CI → `testing`, `ci`, or `enhancement` depending on repo labels
  - ops/readiness → `ops`, `tracking`, or no label if unavailable
- Milestones/projects/assignees require extra care; only set if requested or repo convention is clear.

## Creating the Issue with `gh`

Only after target repo is verified and duplicate search is done:

```bash
gh issue create \
  --repo <owner/repo> \
  --title '<title>' \
  --body-file <tmp-body-file> \
  --label '<existing-label>'
```

Then verify:

```bash
gh issue view <number-or-url> \
  --repo <owner/repo> \
  --json number,title,body,labels,state,url
```

Report:

- issue URL;
- labels applied;
- duplicate/adjacent issues checked;
- any assumptions or deferred clarifications.

## Updating Existing Issues

When grooming/updating:

1. Read the issue first:
   ```bash
   gh issue view <N> --json number,title,body,comments,labels,state,url
   ```
2. If the user says they just edited or clarified the issue manually, re-read the live issue immediately before applying another edit. Treat the user's live edit as source-of-truth context, patch around it, and verify you did not overwrite or drop their wording.
3. Inspect current repo/default branch state, not only a local WIP branch.
4. Check adjacent open/closed issues and PRs.
5. Rewrite for executability while preserving valid context and comments.
6. Prefer narrowing over expanding. If necessary, split follow-up work into a new issue.
7. After editing, re-read the issue and verify the live title/body/labels before reporting success.

## Output Format to the User

When drafting only, provide:

```markdown
## Proposed GitHub issue

**Title:** <title>
**Repo:** <owner/repo or assumed repo>
**Labels:** <existing labels or suggestions>

<full issue body>

## Notes

- Existing related issues checked: ...
- Assumptions: ...
- Recommended split/follow-up: ...
```

When created, provide:

```markdown
Created and verified: <issue URL>

- Repo: <owner/repo>
- Labels: <labels>
- Related issues checked: <summary>
- Verification: re-read issue via `gh issue view`
```

## Stakeholder approval comments as issue sources

When a Linear/GitHub approval-gate comment contains a stakeholder note that needs repo follow-up (for example “approved except please also mention X anywhere Y is named”), turn it into a focused implementation issue rather than burying it in the approval tracker:

1. Re-read the source approval issue/comment and quote the stakeholder note in context.
2. Ground against the target repo/default branch (`origin/main` when appropriate), not only the current feature branch; search for every current occurrence of the affected names/phrases.
3. Check adjacent open issues so the new issue is not a duplicate and so related gates remain separate.
4. Preserve role accuracy in the issue body. If the note says to add a person/name, do not assign titles, ownership, tenure, or responsibilities that the source did not approve; explicitly call out wording that must avoid implying an unapproved role.
5. Keep approval/live-change boundaries explicit: a repo issue does not authorize deploy, client-facing publication, account changes, or new business facts.
6. After creating the issue, re-read it and, if the source was Linear, comment back with the GitHub URL and verify the Linear comment by ID.

## Common Pitfalls

- Writing a task title as the goal instead of the user-visible outcome.
- Skipping current-state inspection and inventing file paths or implementation seams.
- Creating duplicate issues because existing work was not searched.
- Leaving out out-of-scope boundaries, causing agents to overbuild.
- Acceptance criteria that require subjective judgment instead of observable evidence.
- Encoding live account/deploy/client-facing actions without explicit approval gates.
- Treating agent self-reports as proof instead of requiring tool-verifiable evidence.
- Making a milestone issue look like an implementation issue; milestones need deliverables and rules of engagement.
- Over-specifying exact code when the real need is preserving invariants and verification.
- For source-grounded audit issues, opening implementation tickets for intentionally absent facts that are waiting on approval. If the repo deliberately omits a fact (for example visible author/date metadata), create or defer to a source-of-truth approval step before an implementation/schema issue.
- Letting a broad source-backed audit issue say “verification-only” when the title promises a concrete artifact. Keep the title, scope, and acceptance criteria aligned: if the issue says “static/no-JS projection,” require that projection rather than only a rendered-DOM check.
