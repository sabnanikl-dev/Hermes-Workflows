---
name: codex-linear-consulting-operations
description: "Use Codex + Linear (+ optional Notion) as an agency-style operating system for consulting or productized-service businesses. Covers intake, triage, client kanban, Codex execution, GitHub automation, and review/delivery workflows."
version: 1.0.0
author: Hermes Agent
---

# Codex + Linear Consulting Operations

## Umbrella Scope: Papi/Consulting Operating System

This is the class-level skill for using Linear, Codex, Hermes, GitHub, and optional Notion as an agency/productized-service operating system. The narrower `papi-linear-workspace` skill is absorbed here as the Linear workspace architecture subsection: one Papi AI Consulting workspace, client isolation via labels, 7-state workflow, board views, and label taxonomy for multi-client management.

Full workspace-architecture details are preserved in `references/papi-linear-workspace.md`.

## When to Use

Use this skill when Karan (or another operator) wants to run a consulting or productized-service business through:
- **Linear** as the execution queue / client kanban
- **Codex** as the build agent for web, code, automation, and repo work
- **Hermes** as orchestrator / QA / client communication layer
- **Notion** (optional) as the knowledge/deliverables/SOP layer

This is the operations-focused cousin of `multi-agent-dev-workflow`. Use `multi-agent-dev-workflow` for pure GitHub-centric dev loops. Use this skill when the work is client-facing, intake-driven, or consulting-delivery oriented.

## Core Model

- **Linear** = execution brain for intake, status, ownership, delivery queue
- **Codex** = builder for scoped issues, especially browser/preview-heavy or repo tasks
- **GitHub** = execution surface for branches, PRs, reviews, status automation
- **Hermes** = orchestrator, QA gate, client comms, wiki/reporting layer
- **Notion** = knowledge/client OS layer (SOPs, templates, scorecards, playbooks)
- **Obsidian wiki** = durable internal memory / strategy / checklist layer

## Recommended Board Design

For service businesses, do **not** use a pure engineering board.

Recommended columns:
1. Backlog
2. Scoped
3. Ready for Dev
4. In Progress
5. In Review
6. Client Review
7. Done

Recommended swimlanes:
- Client / project
- Offer type
- Risk level
- Assignee
- Revenue impact

## Offer + Intake Design

Translate offers into structured intake fields.

Every issue should capture:
- client
- offer type
- pain point
- desired outcome
- repo
- effort size
- risk level
- approval state
- agent instructions
- acceptance criteria

Best pattern:
1. Intake form
2. Sheet/table mapping
3. Linear issue creation
4. Codex-executable ticket description
5. Hermes QA gate
6. Client delivery

## Codex Usage Rules

Use Codex for:
- website/CSS/HTML fixes
- browser-based QA
- issue-driven repo changes
- automation scripts
- code review / debugging / ETL glue
- repeatable implementation patterns

Do **not** use Codex as the primary decision-maker for:
- scoping client promises
- handling sensitive data writes
- choosing business strategy
- customer-facing messaging without review

## Notion vs Linear Decision

Use **Linear** for execution.
Use **Notion** for knowledge, SOPs, templates, client-facing OS pages, and playbooks.

Linear strengths:
- issue intake/triage
- Codex-first execution flow
- GitHub automation
- operational rigor at scale

Notion strengths:
- wiki/docs/SOPs
- templates and client deliverables
- structured databases for playbooks/requests/scorecards

## Repo Pattern

Use two layers:
- private internal template repo for reusable schemas/prompts/SOPs/agent standards
- private per-client repo for engagement-specific docs/schemas/scripts/workflows/deliverables

Every client repo should include:
- `AGENTS.md`
- `docs/spec.md`
- clean separation of raw vs curated work
- easy archive/handoff path

## Workflow Sequence

1. Create Linear workspace/team/statuses/labels
2. Define intake form + offer templates
3. Create client repo scaffold
4. Map intake to executable issues
5. Pilot with one real client or engagement type
6. Add Notion knowledge layer if needed
7. Promote repeatable modules into templates

## Manual Agent-Delegated Issue Execution Protocol

Before automating Linear triggers with cron/webhooks, validate the workflow manually on real issues.

For any issue labeled `delegate/hermes`, `delegate/codex`, or `delegate/claude-code`:

1. Load the full Linear issue via API, including title, state, labels, project, description, and comments.
2. Parse the Agent Delegated Issue sections:
   - Context
   - Goal
   - Files/Paths
   - Acceptance Criteria
   - Agent Delegate
   - Constraints
   - Verification
   - Definition of done
3. Work directly against the acceptance criteria, not just the title.
4. Respect constraints throughout execution, especially:
   - no client-facing delivery without Karan approval
   - no PII/secrets in commits, prompts, logs, or Linear comments
   - no production/DNS/account changes without explicit approval
5. When finished, post a Linear comment with:
   - AC status
   - DoD status
   - what changed
   - verification performed
   - blockers or follow-ups
6. Update the issue description checklist to mark completed AC/DoD items.
7. Move completed agent work to `In Review`, not `Done`, so Karan remains the approval gate.

### Real Pilot Visibility / Publication Protocol

When running a “real pilot” from Linear issues, do not leave the outcome split-brained between local repos/Kanban and Linear. Karan will naturally check Linear to understand what happened.

Required sequence:
1. Before execution, state the external-side-effect boundary: local-only vs push/PR vs Linear comments/status movement.
2. If work is intentionally local-only, make that explicit in the final report as **not visible in Linear/GitHub yet** and list the exact pending publication steps.
3. Once Karan approves publication, create/push repos/branches, open PRs, post Linear comments with PR links, and move issues to `In Review`.
4. Verify each surface after publication:
   - GitHub repo/PR exists and is open.
   - Remote PR contains expected commit SHAs (`gh pr view --json commits`).
   - Linear issue has the new comment and expected state.
5. Report using two buckets: **visible in Linear/GitHub now** and **still local/pending**. Avoid summaries that imply Linear was updated when comments/statuses were intentionally withheld.

Reference: `references/real-pilot-publication-checklist.md` captures the JMD/PAPI pilot pattern and verification checklist.

Important Linear behavior discovered during PAPI setup: labels inside the same label group are mutually exclusive. Do not apply multiple labels from the same group (e.g. multiple Domain labels). Use one label per group: Client, Agent/delegation, Domain, Phase, Effort Level, Offer, Risk/blocker, and any client-specific group.

Triggering note: MCP is not the trigger. MCP/API lets an already-running agent read/update Linear. For automatic activation use Linear webhooks into Hermes Gateway, or a polling cron as a safer later step. Validate manual execution before enabling automation.

## Ops Execution Harness V1 (Non-Code Tasks)

For non-coding consulting work (GBP audits, local SEO baselines, content calendars, review response drafting, client research, access checks), do **not** jump straight to a fully automated/headless Hermes orchestration loop. Karan's preferred V1 is a lean manual harness that can be cloned per issue and opened in Codex Desktop or Claude Desktop, where those agents use their own Linear integrations and execute inside the harness boundaries.

First-principles V1:
- Template folder, not an engine.
- Manual launch by Karan in Codex/Claude Desktop.
- Linear remains the live source of truth.
- Harness provides context, constraints, playbook, output format, and evidence folders.
- Agents write deliverables into files; they do not just respond in chat.
- No automated issue routing, webhooks, cron, or headless spawning until the manual pattern proves out.

Lean base harness shape:

```text
<issue>-<task>-harness/
  AGENTS.md
  README.md
  task.md
  context.md
  playbook.md
  constraints.md
  skills/
    manifest.md      # empty until task-specific skills are loaded
  commands/
    run-task.md
    review-output.md
  outputs/
  evidence/
```

Current V1 repos created from this approach:

- Base harness template: `sabnanikl-dev/papi-ops-execution-harness-template`
- Separate empty skill library: `sabnanikl-dev/papi-ops-skill-library`
- Follow-up Linear issue for skill research/loading: `PAPI-27`

Important design decision: keep the base harness skill-light. Do **not** include GBP/SEO/content/etc. skills in the base template. After cloning the harness for a real issue, Karan + Hermes decide which skills are needed and copy/add only those into that task repo. The separate skill library starts empty and only receives curated reusable skills after they are researched, tested against real tasks, and promoted.

For JMD-2-style GBP audit tasks, the cloned task harness should state:
- Read the Linear issue first and treat Acceptance Criteria / Definition of Done as the contract.
- Execute a GBP audit, not live GBP fixes.
- Save screenshots/API exports under `evidence/`.
- Save `gbp-audit.md`, `quick-fixes.md`, `approval-needed.md`, `blocked-items.md`, and `final-linear-comment.md` under `outputs/`.
- Do not change categories, website URL, hours, phone, address, posts, photos, or review responses without explicit approval.

Hermes' V1 role:
1. Help Karan scope/rewrite the Linear issue.
2. Create or populate the lightweight harness folder.
3. Add client/task context from memory/wiki.
4. Karan opens the folder in Codex/Claude Desktop and runs the task manually.
5. Hermes can review outputs, help write the final Linear comment, and capture lessons.

This keeps usage low, avoids premature bloat, and lets the ops harness evolve from actual task runs before being merged into a broader Papi OS structure.

## Proof of Concept: JMD Menswear

JMD Menswear was the first client to run through this model. Key lessons:

- **Client engagement IS the operating model proof.** Every module built for a client (review generation, customer capture, content pipeline, inventory alerts) becomes a reusable Papi AI module.
- **Linear board design for consulting:** Backlog → Scoped → Ready for Dev → In Review → Client Review → Done. Swimlanes by week/component, labels by domain (website, seo, gbp, content, systems, events).
- **Harness template, not scaffold:** Use `sabnanikl-dev/agentic-harness-template` (slim: AGENTS.md + docs/) for client repos, NOT the bloated Agentic-dev scaffold. Populate `docs/spec.md` with client-specific context.
- **Hermes translates attack plan → Linear issues.** The week-by-week plan becomes properly-scoped issues with acceptance criteria that Claude Code and Codex execute from.

## Pitfalls

- **Do not automate intake before the board is clean.** Codex just automates chaos otherwise.
- **Do not confuse knowledge layer with execution layer.** Linear is queue/state/truth-of-work. Notion/wiki is truth-of-process.
- **Client boards should include a real Client Review column.** Engineering-only boards miss the delivery step.
- **Codex/browser work is powerful but must still be QAed.** Visual review does not replace acceptance-criteria review.
- **Intake forms must capture desired outcome, not just request description.** Otherwise agent execution optimizes for the wrong thing.
- **Use Notion for templates and client-facing OS, but avoid making it the primary execution queue.**
- **Slow models will timeout subagents.** If spawning delegate_task on a slower model, use execute_code + write_file as fallback for document generation tasks.
