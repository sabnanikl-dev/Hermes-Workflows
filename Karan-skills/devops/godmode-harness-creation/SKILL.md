---
name: godmode-harness-creation
description: Use when creating or upgrading a project harness so GodMode or a GodMode-like multi-agent coding dashboard can open the repo, assign agent roles, run issue-to-PR workflows, review PRs, and generate aligned implementation issues.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [godmode, harness, multi-agent, github, project-kickoff, agents]
    related_skills: [github-operations, software-development-lifecycle, project-kickoff, agent-workflow-orchestration]
---

# GodMode Harness Creation

## Overview

Use this skill to turn a normal project repo into a **GodMode-optimized agent harness**: a local, source-of-truth structure that lets a human operator open the repo in a multi-agent dashboard, select/spec work, assign builder/reviewer roles, and run a disciplined issue → branch → PR → review → fix → merge-ready loop.

The proven workflow is: clarify product direction, write the durable harness docs, scaffold only the smallest useful app/project surface, verify locally, run a review loop, open/merge a scoped PR, then post aligned GitHub issues that continue the build in project-scope order.

This is not just “make an `AGENTS.md`.” The harness must encode role boundaries, source-of-truth rules, workflow contracts, safety gates, verification commands, review standards, and issue drafts that future agents can execute without Hermes over-prompting every step.

## When to Use

Use when the user asks to:

- create a new project repo that will be worked by agents,
- make an existing repo “GodMode ready,”
- build a bring-your-own-agent coding harness,
- define `AGENTS.md`, `docs/spec.md`, reviewer docs, and `.agentic/godmode.yaml`,
- scaffold a local dashboard/app harness for agent workflows,
- draft or post first implementation issues after a project scaffold,
- capture a repeatable agent workflow from planning through GitHub issues.

Do **not** use for:

- a simple one-off code edit with no durable harness needs,
- generic project management plans with no agent execution loop,
- replacing GitHub/Linear with a parallel tracker,
- auto-merging, deployment, credential changes, or client-facing actions without explicit approval.

## Core Harness Artifacts

Minimum useful harness:

```text
AGENTS.md
README.md or docs/spec.md
```

Recommended GodMode harness:

```text
AGENTS.md
docs/
  spec.md
  godmode-v1-product-spec.md or product-spec.md
  review/
    reviewer-a-correctness.md
    reviewer-b-architecture.md
  conventions/
    branch-pr-policy.md
    testing.md
  friction/
    README.md
.agentic/
  godmode.yaml
  commands/
    builder-start.md
    builder-fix.md
    reviewer-codex.md
    reviewer-codex-rereview.md
    hermes-roll-call.md
    verify-pr-ready.md
```

Use `.agentic/commands/` for lifecycle prompt/command templates that the harness executes or previews. These are harness inputs, not general prose docs. Keep them role-first, pointer-first, and referenced from `.agentic/godmode.yaml`; use `docs/` to explain behavior and `.agentic/commands/` to drive behavior.

If the repo is an app, include standard build/test files for the chosen stack. For a local Electron/React/TypeScript dashboard, the proven scaffold used:

```text
package.json
package-lock.json
tsconfig.json
tsconfig.main.json
vite.config.ts
index.html
src/main/
src/preload/
src/renderer/
src/shared/
```

## Workflow: Planning to Issue Posts

### 1. Discover existing state first

Before writing anything:

1. Verify GitHub auth and repo state:
   ```bash
   gh auth status
   git status --short --branch
   git remote -v
   gh issue list --state open --limit 100
   gh label list --limit 100
   ```
2. Read existing source-of-truth docs if present:
   - `README.md`
   - `AGENTS.md`
   - `docs/spec.md`
   - existing project plans/specs
3. Confirm branch/PR policy from the repo or user.
4. Do not push, create issues, merge, or mutate external systems unless the user explicitly approved that step.

### 2. Capture product direction in plain language

Write a concise product/technical direction before scaffolding code. For a GodMode-style harness, capture:

- one-sentence product definition,
- north star workflow,
- v1 scope and non-goals,
- default roles and responsibilities,
- bring-your-own-agent requirement,
- source-of-truth hierarchy,
- safety/approval policy,
- expected verification commands,
- current build phases.

Example durable direction:

```md
GodMode is a local, tmux-style, bring-your-own-agent coding dashboard where a human operator can command and chat with an agent team, run an automatic build-review-fix PR loop from a project harness, and retain final merge authority.
```

### 3. Write `AGENTS.md` as the operating contract

`AGENTS.md` must be explicit enough that builder/reviewer agents can start fresh sessions and still behave correctly.

Include:

- project direction,
- role map: human/head/builder/reviewer(s),
- source-of-truth order,
- branch and PR rules,
- issue-to-PR workflow,
- completion evidence rules,
- safety rules,
- review standards,
- implementation guidelines,
- verification commands,
- friction log convention.

Important rules to encode:

```md
Agent self-reports are not proof. Verify with tools:
- After push: verify expected commit appears in `gh pr view <PR> --json commits`.
- After PR creation: verify PR exists and branch matches.
- After merge: re-query GitHub and confirm merged/closed.
- For app changes: run the repo's verification commands before reporting success.
```

For fresh-session multi-agent workflows, include:

```md
Builder starts a fresh session for the task, then reads `AGENTS.md`, `docs/spec.md`, the issue, and relevant docs/comments.
Reviewers start fresh review sessions, read `AGENTS.md`, the PR, linked issues, comments, and relevant docs, then review.
Builder starts a fresh fix session before implementing accepted blockers.
```

Prompt/handoff architecture should be **pointer-first by default**. GodMode is an agent harness, not a context-stuffing prompt router: send compact task capsules plus exact source pointers/commands (`gh issue view <N> --comments`, PR URL/number, role docs, `AGENTS.md`, `docs/spec.md`, relevant architecture/convention docs), then require the builder/reviewer to read live canonical sources from the operated project root. Fetch/store/display full issue/PR/review detail for preview/audit and explicit fallback modes, but do not paste full bodies/diffs/threads into agent prompts by default.

Fix-cycle handoffs should normally be **PR-feedback-first**, not blocker-transcript-first. When a reviewer such as CodexReviewer requests changes, the next Claude Code/builder prompt should tell the builder to read the latest GitHub PR reviews, review threads, inline comments, and conversation comments itself, identify unresolved blocking feedback, and fix only those blockers. Hermes/GodMode may keep normalized blocker text for synthesis/audit and fallback, but should not paste blocker summaries as the default source of truth. If the builder cannot access GitHub, treat that as an infrastructure blocker or explicit fallback mode, not the normal path.

### Builder fix handoffs read PR feedback directly

For GitHub-first GodMode loops, the PR should be the coordination bus between reviewers and builders. When CodexReviewer or another reviewer requests changes, the normal builder-fix handoff should point Claude Code to the live PR, not paste Hermes' summarized blocker text:

```md
The PR has blocking review feedback. Read the latest GitHub PR reviews, review threads, inline comments, and conversation comments yourself. Identify unresolved blocking feedback from CodexReviewer, resolve only those blockers, run verification, push a follow-up commit, and comment what changed.
```

Hermes/GodMode may retain normalized blocker findings in the run ledger for state-machine decisions and UI display, but Claude Code's source of truth is the PR. Use a summarized blocker capsule only as a fallback for agents without GitHub access, and label it as fallback data subordinate to the live PR.

### Builder handoff prompts: pointer-first by default

When implementing GodMode builder handoff behavior, preserve the product as an **agent harness**, not a prompt-injection router. The default sent prompt should be **pointer-first + compact task capsule**:

- issue number/title/URL and useful labels;
- a short goal/scope/acceptance capsule when available;
- explicit read-first instructions for `AGENTS.md`, `docs/spec.md`, relevant `docs/architecture/*` / `docs/conventions/*`, and `gh issue view <issueNumber> --comments` from the operated project root;
- implementation/verification/PR-linking instructions.

It is useful to fetch full issue detail for the UI preview, audit log, and optional fallback modes, but do **not** paste full issue bodies/comments into the builder PTY prompt by default. Full-context handoff should be explicit/operator-selected or reserved for builders without repo/GitHub access, one-shot remote agents, or frozen audit snapshots. If any issue/comment excerpt is sent, label it as task data beneath the authority of `AGENTS.md` and repo docs.

### 4. Write `docs/spec.md` as the living product/technical spec

`docs/spec.md` should be shorter than the full product spec and directly actionable for implementation agents.

Recommended sections:

- What This Is
- Default Workflow
- Bring Your Own Agent Requirement
- V1 Tech Stack
- Architecture Overview
- V1 UX Shape
- V1 Workflow
- Current Build Phases
- Open Questions / Decisions
- Spec Drift Convention
- Links

Keep open questions current. When the user resolves questions in a PR comment or chat, patch `docs/spec.md`, `AGENTS.md`, and config so the harness—not one-off conversation context—carries the decision.

### 5. Add role docs for reviewers

Create focused reviewer docs so the head agent does not need to over-prompt.

`docs/review/reviewer-a-correctness.md`:

- correctness,
- tests,
- security,
- runtime behavior,
- regressions,
- unsafe shell/process behavior.

`docs/review/reviewer-b-architecture.md`:

- architecture,
- maintainability,
- spec drift,
- harness compliance,
- role/agent separation,
- source-of-truth discipline.

Require concise output and a completion marker such as:

```text
DONE: ROLE=reviewer STATUS=pass|fail BLOCKING=<count>
```

### 6. Add `.agentic/godmode.yaml`

The config should map **roles** to **agents/adapters**. Do not model vendors as core abstractions.

#### CodeGraph enforcement for builder/reviewer agents

When a GodMode-operated repo expects agents to use CodeGraph, do not rely only on a buried `AGENTS.md` paragraph. Put the requirement directly in the sent lifecycle prompts and in PR acceptance:

- `commands.builder_start`: require `npx -y @colbymchenry/codegraph@<version> sync .` plus at least one concrete `query`/`impact`/`callers`/`callees` check before implementation on non-trivial code changes.
- `commands.builder_fix`: require CodeGraph re-orientation around the touched blocker symbols before patching.
- Reviewer prompts/role docs: require CodeGraph triage for changed exported functions/components/IPC/config boundaries, followed by source/diff verification.
- PR bodies should include `CodeGraph context used:` with queries/symbols checked and limitations; absence is a review finding for substantive implementation PRs.
- MCP setup helps tool discoverability, but prompt wording still matters: agents often skip optional tooling unless the handoff says it is required evidence.

### Operator Core and CLI control-plane issues

When Karan asks how the GodMode head agent should operate the app, preserve this architecture split:

- **Operator Core first**: a transport-neutral semantic app-control boundary inside the Electron main/app layer. It wraps existing project/config/GitHub/run/handoff/reviewer/fix/loop/PTY behavior without creating a second workflow engine.
- **CLI second**: a local `godmode` CLI that calls the Operator Core and returns stable JSON for head agents/Hermes. It is the first external operator surface because it is scriptable, inspectable, and easy to dogfood.
- **MCP later**: expose the same Operator Core/CLI semantics as native tools; do not invent a parallel MCP workflow.
- **ACP belongs primarily to agent adapters**: use ACP/PTY/CLI/custom adapters for how GodMode controls builder/reviewer/head role sessions, not as the first app-control surface for the head agent.

For issue specs in this area, split the work into at least two focused issues:

1. **Internal Operator Core** — add `src/main/operator.ts` or `src/main/operator/index.ts`, typed `OperatorActor` / `OperatorResult` / action metadata, and refactor Electron IPC handlers to thin adapters while preserving renderer events (`runChanged`, `githubChanged`, `runVerificationChanged`, `runLoopChanged`, `ptyStarted`, `ptyExit`). Require docs such as `docs/architecture/operator-core.md` and a spec/AGENTS update stating that structured operator actions are the head-control path; PTY is an agent-session transport/fallback.
2. **GodMode CLI** — add a `godmode` package CLI with JSON-first commands (`project inspect`, `state`, `run status/start/dispatch/verify`, PR discovery/confirm, handoff/fix/reviewer/PTY controls), explicit live-app vs offline-inspection behavior, typed errors such as `app_unavailable`, and clear exit codes. The CLI must call Operator Core and must not mutate `.godmode/godmode.db` as a second conflicting brain for live-run actions.

Acceptance criteria should explicitly preserve existing gates: run transitions through the state machine, handoff/fix sendability checks, live PTY/worktree/isolation checks, GitHub evidence verification, manual merge authority, no auto-merge, and role-generic names (`head`, `builder`, `reviewer_a`, `reviewer_b`). Before creating issues, check duplicate issue titles for `Operator Core`, `GodMode CLI`, `control plane`, `head agent`, and related wording; after creation, re-read each issue and verify structural markers plus cross-issue dependencies (e.g. CLI depends on Operator Core).

### Repo-local Hermes orchestration templates

When a repo needs durable templates for the Hermes → Claude Code → CodexReviewer dogfooding loop, avoid a generic `.agentic/commands/` folder. That name is too easy for agents to confuse with GodMode product runtime commands. Prefer an explicit Hermes-owned namespace:

```text
.agentic/
  hermes-orchestration/
    README.md
    templates/
      claude-builder-start.md
      claude-builder-fix.md
      codex-reviewer-start.md
      codex-reviewer-rereview.md
      hermes-roll-call.md
      verify-pr-ready.md
```

The folder README must say this is **not GodMode product runtime code**, that it contains repo-local operational templates used by Hermes while working on the repo, and that agents should not implement product features from those templates unless a GitHub Issue explicitly asks for that work. If product code later loads these templates, use an explicit config namespace such as `orchestration.owner: hermes`, not a vague top-level `commands:` block. For the first PR, safest path is to add README/templates as Hermes dogfooding assets only and leave product loading out of scope.

Example:

```yaml
project:
  name: ExampleProject
  default_branch: main

harness:
  agents_file: AGENTS.md
  spec_file: docs/spec.md
  product_spec_file: docs/product-spec.md

roles:
  head:
    agent: hermes
    pane: head
    display_name: Hermes
  builder:
    agent: claude-code
    pane: builder
    display_name: Claude Code
  reviewers:
    - id: reviewer-a
      agent: codex
      pane: reviewer_a
      display_name: Codex A
      role_doc: docs/review/reviewer-a-correctness.md
    - id: reviewer-b
      agent: codex
      pane: reviewer_b
      display_name: Codex B
      role_doc: docs/review/reviewer-b-architecture.md

workflow:
  auto_start_reviewers_after_pr: true
  auto_send_blockers_to_builder: true
  max_fix_cycles: 3
  auto_merge: false

agents:
  hermes:
    adapter: cli
    command: hermes
    mode: interactive
  claude-code:
    adapter: cli
    command: claude
    mode: interactive
  codex:
    adapter: cli
    command: codex
    mode: oneshot
```

### 7. Scaffold the smallest useful implementation surface

If building a dashboard app, start with a thin but real artifact:

- a visible tmux-style UI,
- panes for head/builder/reviewers/PR state,
- safe PTY/session lifecycle if in scope,
- shared TypeScript types,
- build/typecheck scripts.

For GodMode UI identity, see `references/godmode-hermes-ui-direction.md`: preserve the split-pane cockpit layout while steering visual identity toward Hermes (cobalt/ultramarine, wing-like linework, cyber-classical command cockpit) rather than a QuadWork clone or generic neon terminal.

Do not overbuild SaaS, marketplace, deployment, or auto-merge features in v1.

For a local Electron + React + Vite scaffold, verify with:

```bash
npm install
npm run typecheck
npm run build
```

A Vite chunk-size warning is acceptable if the build exits 0 and the project has not yet added code splitting.

### 8. Run a review loop before pushing

Before committing/pushing:

1. Inspect `git diff` yourself.
2. Run the repo verification commands.
3. Send the diff/spec to a reviewer agent if requested or warranted.
4. Treat reviewer self-report as advisory until verified.
5. Fix blockers, rerun verification, and only then commit.

A clean review loop should have an unambiguous pass marker, e.g.:

```text
DONE: STATUS=pass BLOCKING=0
```

### 9. Commit, push, open PR, and verify remote state

Only after explicit approval for GitHub mutation. If a named builder agent (Claude Code, Codex, etc.) is already assigned and is explicitly waiting for approval to push/open the PR, prefer steering that same agent to perform the push/PR handoff instead of bypassing it from Hermes. This preserves the GodMode dogfood loop and keeps builder ownership intact; Hermes should still independently verify the resulting PR, branch, linked issue, and remote commit. If direct steering of the existing terminal is not possible, use the agent's resume/remote-control mechanism when available, or clearly explain why Hermes is taking over before doing so.

```bash
git status --short --branch
git add <intended files>
git commit -m "chore: scaffold GodMode harness"
git push -u origin <branch>
gh pr create --title "..." --body "..."
LOCAL=$(git rev-parse HEAD)
REMOTE=$(gh pr view <PR> --json commits --jq '.commits[-1].oid')
test "$LOCAL" = "$REMOTE"
```

GodMode harness rule: every implementation PR must be tied to a GitHub issue. Prefer `Closes #N` / `Fixes #N` in the PR body when merge should close it; otherwise explicitly link the governing issue. Do not open free-floating implementation PRs. If no suitable issue exists, create or ask for a focused issue first.

Report the PR only after verifying:

- PR exists,
- branch/base are correct,
- PR body links/closes the intended issue,
- remote PR latest commit matches local HEAD,
- working tree is clean or intentionally dirty,
- verification commands passed.

After any merge, re-query:

```bash
gh pr view <PR> --json state,mergedAt,mergeCommit
```

Do not claim merged unless GitHub says `MERGED` / merged timestamp exists.

### 10. Convert build order into aligned issues

Before creating issues:

1. Re-read `AGENTS.md`, `docs/spec.md`, and the full product spec.
2. Check existing issues and labels.
3. Audit the draft issues against scope and non-goals.
4. Reorder issues to match the practical dependency chain.
5. Create only after explicit user approval.

A strong first-ten sequence for a GodMode-style dashboard is:

1. Project selector and harness detection.
2. Parse `.agentic/godmode.yaml` into role/agent config.
3. GitHub read-only issue/PR pane.
4. Agent adapter registry and command templates.
5. Configured role sessions through safe PTY controls.
6. Run state machine and operator controls.
7. Builder issue handoff prompt flow.
8. Builder branch/push/PR detection and commit verification.
9. Reviewer A/B launch flow and PR comment posting.
10. Reviewer blocker parsing and first fix loop.

When asked for the **work order** of existing GodMode issues, ground the answer in live issue state plus `AGENTS.md` / `docs/spec.md`, then separate the critical self-dogfood path from the broader product/UX lane. For the current self-dogfood dependency shape, prefer:

1. Live Electron dogfood smoke test / `npm run smoke` — prove the cockpit launches and preload/project/config/GitHub/PTY wiring works before trusting it.
2. Builder PR discovery from GitHub evidence — close the gap between handoff sent and verified PR bound to the run.
3. Per-run builder worktree isolation — treat as practically pre-dogfood when the app is operating on its own repo, because shared checkout collisions have already happened.
4. Automatic review/fix loop controller — chain verified PR → reviewers → synthesis → fix cycle → merge-ready without bypassing state-machine guards.
5. Run persistence/resume — not always a hard blocker, but strongly recommended before serious dogfooding because app restarts mid-run are likely.
6. Real end-to-end dogfood milestone — only after the hard blockers are merged; product/UX items like multi-project rail switching and first-run setup can follow unless the user explicitly prioritizes onboarding.

If the user asks for the shortest possible route, name the lean path separately (smoke → PR discovery → loop controller → dogfood milestone) and call out the accepted risk of skipping worktree isolation/persistence.

The important alignment checks:

- local/macOS-first,
- BYOA role separation,
- harness-driven source of truth,
- GitHub-first PR visibility,
- reviewer comments on PRs if that is the v1 decision,
- max fix cycles from config/spec,
- manual merge only,
- no SaaS/multi-tenant/deploy/client-message scope,
- no parallel tracker in Obsidian/wiki.

Issue bodies should include:

- Goal,
- Context,
- Scope,
- Out of scope,
- Acceptance criteria,
- Verification.

### 11. Verify created issues

After issue creation or batch issue-body edits, do not trust CLI mutation output alone. Re-query GitHub:

```bash
gh issue list --state open --limit 20 --json number,title,body,labels,url \
  --jq '[.[] | {number,title,url,labels:[.labels[].name], hasGoal:(.body|contains("### Goal")), hasAcceptance:(.body|contains("### Acceptance criteria")), hasVerification:(.body|contains("### Verification"))}]'
```

For design-direction or harness-rule issue updates, verify the exact marker/section landed on every intended issue, e.g.:

```bash
gh issue list --state open --limit 100 --json number,title,body,url \
  --jq 'sort_by(.number) | .[] | {number,title,has_ui_direction:(.body|contains("### UI direction from PR #12")),url}'
```

Report issue URLs only after verification.

## Antigravity / Claude Status Checks

When Karan asks what Claude was doing in Antigravity on a GodMode issue, treat it as a status-verification task, not a PR mutation task. First identify the Claude process whose cwd is the GodMode repo, then verify local branch/commit state, remote branch/PR state, issue state, and cheap repo checks before summarizing. See `references/antigravity-claude-status-check.md` for the exact command sequence and pitfalls.

## GodMode PR Review / Harness Alignment Comments

Use this when reviewing an open GodMode PR for alignment with the harness goals, especially UI/dashboard PRs.

1. Inspect live repo and PR state before judging:
   ```bash
   gh auth status
   git status --short --branch
   gh pr view <PR> --repo <owner/repo> --json number,title,headRefName,baseRefName,state,isDraft,body,comments,reviews,commits,files,mergeable,statusCheckRollup
   gh pr diff <PR> --repo <owner/repo> > /tmp/godmode-pr.diff
   ```
2. Re-read the local harness source of truth before commenting:
   - `AGENTS.md`
   - `docs/spec.md`
   - relevant role/review docs if the PR touches workflow/review behavior.
3. Review the actual changed files, not the PR summary. For renderer/dashboard PRs, explicitly check:
   - tmux/QuadWork-style operator workflow remains visible and dense,
   - local-first/manual-merge framing is preserved,
   - core code stays role-first (`head`, `builder`, `reviewer_a`, `reviewer_b`) instead of vendor-first,
   - Hermes/Claude/Codex appear only as defaults/display labels unless config-backed,
   - static/mock GitHub or run-state facts are either clearly demo-only or planned to become data-backed,
   - no hardcoded user-specific project paths are introduced into durable UI/state,
   - small viewport/layout clipping does not hide critical controls,
   - visual identity does not become an obvious QuadWork clone. For GodMode, keep the split-pane cockpit layout but steer the aesthetic toward Hermes: cobalt/ultramarine + ink/white, green as status-only, subtle magenta/cyan accents, angular/wing-like linework, and cyber-classical “Hermes command cockpit” cues.
4. For GodMode UI aesthetics, separate **layout inspiration** from **visual identity**. QuadWork/tmux can inspire the split-pane/operator workflow, but the surface should not look like a QuadWork clone. Steer toward a Hermes identity: electric cobalt/ultramarine + white/ink as the primary palette, green as status-only, small cyan/magenta glitch accents, wing-like/messenger linework, angular motion trails, and a cyber-classical “Hermes command cockpit” mood. See `references/godmode-hermes-identity-pr-review.md` for detailed cues and review phrasing.
5. Run the repo verification command before commenting:
   ```bash
   npm run build
   ```
   A Vite chunk-size warning is non-blocking when the build exits 0 and no code-splitting goal is in scope.
5. If a dev server is already available or easy to start, open the UI and visually inspect it. Use browser/DOM checks for overflow or clipped controls before making layout claims.
7. Leave the review as a PR comment only after verification. Format:
   ```md
   ## PR #N Review: <title>

   **Verifier: APPROVED|NOT Approved|APPROVED with follow-ups** — <one-line harness-alignment verdict>

   ### Verified
   - Diff/files inspected
   - Harness docs checked
   - Build/test command result
   - Visual/dev-server check if applicable

   ### Harness alignment notes
   - Good / blocking findings tied to AGENTS.md and docs/spec.md

   ### Follow-up / polish
   - Non-blocking issues, clearly labeled
   ```
8. Verify the comment posted by re-querying `gh pr view <PR> --json comments` and report the comment URL.
9. When the builder pushes follow-up commits in response to design/harness feedback, perform a true re-review rather than assuming the response is sufficient: confirm the new commits are on the PR, inspect the updated files, rerun `npm run build`, reload the local UI when possible, and post a new comment with `What improved` plus any remaining non-blocking follow-ups.

## PR Comment Decision Handling

When the user leaves clarifying comments on a scaffold PR:

1. Fetch PR comments:
   ```bash
   gh pr view <PR> --comments --json comments,reviews,commits,state,headRefName,url
   ```
2. Extract decisions, not every phrase.
3. Patch the durable files that should guide future agents:
   - `AGENTS.md` for operating rules,
   - `docs/spec.md` for product/workflow decisions,
   - `.agentic/godmode.yaml` for config changes.
4. Rerun verification.
5. Commit and push to the PR branch.
6. Verify the PR latest commit matches local HEAD.

Typical PR-comment decisions worth encoding:

- default integration mode,
- default reviewer mode,
- whether reviewer findings go to dashboard or GitHub comments,
- default max fix cycles,
- manual merge vs approved merge button,
- fresh-session requirements for builders/reviewers/fixes.

## Setup / Onboarding Issue Drafting

When Karan asks for a GodMode onboarding, config, setup, or settings screen/overlay, treat it as a **first-run operator setup issue** that bridges project selection, BYOA role binding, command validation, GitHub `gh` connection state, and safe `.agentic/godmode.yaml` creation. See `references/setup-onboarding-issue-template.md` for a reusable issue template and scope checklist.

Key points to preserve:

- Settings/setup should configure generic roles (`head`, `builder`, `reviewer_a`, `reviewer_b`) without vendor-specific core abstractions.
- Built-in Hermes/Claude/Codex suggestions are defaults/display labels only; custom CLI agents must be supported.
- GitHub connection should be `gh`-first for v1, with clear states for missing CLI, unauthenticated, no repo, and connected/readable.
- Never store GitHub tokens in `.agentic/godmode.yaml`, logs, or UI state; show account-only or redacted auth info.
- Config writes must target the selected **operated project** root, preview YAML before writing, require explicit confirmation, back up existing config, then reload through the canonical main-process loader.
- If the user asks to create the issue after a draft, re-query existing issues/labels first, create with a body file, then verify the live issue has title/label/structural markers before reporting.

## Current-State Issue Grooming

When Karan asks to review the GodMode codebase and update open issues, treat it as a **GitHub issue mutation task grounded in current `origin/main`**, not a planning-only pass.

Recommended workflow:

1. Verify repo/auth state and create a clean temporary worktree from `origin/main` so local WIP branches do not contaminate the audit:
   ```bash
   gh auth status
   git fetch origin --prune
   git worktree add --detach /tmp/godmode-issue-audit origin/main
   ```
2. Read all open issue bodies before editing:
   ```bash
   gh issue list --state open --limit 100 --json number,title,body,labels,url,comments
   ```
3. For 3+ issues, spawn focused subagents in parallel by issue clusters (for example #8/#9, #10/#11, repo-wide synthesis). Give each subagent:
   - the clean worktree path,
   - current issue bodies,
   - instruction not to mutate GitHub,
   - desired output: existing seams/files, already done, remaining scope, stale acceptance criteria, proposed issue body sections.
4. Synthesize into full issue bodies that include:
   - `### Current code state verified` with the inspected commit,
   - `### Scope`,
   - `### Out of scope`,
   - `### Acceptance criteria`,
   - `### Verification`,
   - concrete file/symbol seams from current code.
5. Write proposed bodies to temporary markdown files first, then use `gh issue edit --body-file` so quoting/newlines do not corrupt long issue bodies.
6. Immediately re-query the edited issues and verify titles plus structural markers landed before reporting success:
   ```bash
   gh issue list --state open --limit 20 --json number,title,body,url \
     --jq 'sort_by(.number) | [.[] | {number,title,url,has_current_state:(.body|contains("### Current code state verified")),has_scope:(.body|contains("### Scope")),has_acceptance:(.body|contains("### Acceptance criteria")),has_verification:(.body|contains("### Verification"))}]'
   ```
7. If issue grooming was based on code state, run the cheap repo verification commands from the issue bodies or package scripts where practical (`npm test`, `npm run typecheck`, `npm run build`) so the reported baseline is real.
8. Clean up the temporary worktree after verification.

- `references/hermes-claude-codex-orchestration.md` — Hermes-as-orchestrator, Claude Code builder, CodexReviewer reviewer workflow notes: manual → roll-call → webhook infrastructure, PR-feedback-first fix cycles, and `.agentic/hermes-orchestration/` namespace guardrails.

## Common Pitfalls

1. **Drafting or updating issues before reading the merged scaffold.** Re-check current `main`, `docs/spec.md`, and existing implementation before posting issues. A merged scaffold may already include static panes, GitHub panes, PTY support, config loaders, or run state machines, changing the right next issue.

2. **Letting issue order follow the old draft instead of current product scope.** If the old draft puts persistence too early, move it later unless the current build needs it immediately. Prefer visible harness/GitHub/adapter/run-loop foundations first.

3. **Hardcoding Hermes/Claude/Codex into core abstractions.** They can be defaults and display labels. Core code should model `head`, `builder`, `reviewer_a`, `reviewer_b`, adapters, and capabilities.

4. **Storing durable rules only in chat or PR comments.** If future agents need it, patch `AGENTS.md`, `docs/spec.md`, role docs, or `.agentic/godmode.yaml`.

5. **Creating GitHub issues without checking labels/existing issues.** Always check first; use only labels that exist unless the user approved label creation.

6. **Claiming push/merge success from local git.** Always verify PR commits after push and PR merged state after merge.

7. **Auto-merging or deploying in v1.** Manual merge remains the safe default unless the user explicitly changes policy.

8. **Overscoping the harness into a SaaS product.** A GodMode harness is local, visible, and governable first. Avoid marketplace, multi-tenant, deployment, or autonomous overnight runner scope unless specifically requested.

## Verification Checklist

- [ ] `gh auth status`, `git status`, remotes, labels, and existing issues/PRs checked.
- [ ] `AGENTS.md` includes roles, source-of-truth rules, safety, PR policy, verification, review standards, and friction logging.
- [ ] `docs/spec.md` includes current workflow decisions and build phases.
- [ ] `.agentic/godmode.yaml` maps roles to configurable agents/adapters and keeps auto-merge false by default.
- [ ] Reviewer docs exist for each configured reviewer role.
- [ ] Scaffold builds/typechecks successfully if code was added.
- [ ] PR push was verified with PR commit list before reporting.
- [ ] Merge was verified with `gh pr view --json state,mergedAt,mergeCommit` before reporting.
- [ ] Issues were audited against project scope before creation.
- [ ] Created issues were re-queried and verified to contain goal, acceptance criteria, verification, labels, and URLs.
