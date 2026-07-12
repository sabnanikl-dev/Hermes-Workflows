<!-- Archived source skill consolidated into `codex-linear-consulting-operations` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: papi-linear-workspace
description: Papi AI Consulting Linear workspace architecture — one workspace, client labels, 7-state workflow, board views, and label taxonomy for multi-client management.
tags: [linear, papi-ai, workspace, multi-client]
triggers:
  - "linear workspace"
  - "papi ai board"
  - "client labels"
  - "linear setup"
---

# Papi AI Consulting — Linear Workspace Architecture

## Core Principle
ONE workspace called **Papi AI Consulting** with team **PAI-Core**.
Client isolation via labels, NOT separate boards/workspaces per client.

## Why Not Per-Client Boards
| Approach | Client 1 | Client 2 | Client 3 |
|----------|----------|----------|----------|
| Separate boards | ✅ Works | ❌ New workspace each | ❌ Doesn't scale |
| **One workspace + labels** | ✅ `label:jmd` filter | ✅ `label:femme` filter | ✅ `label:client3` filter |

## 7-State Workflow
1. **Backlog** — everything from attack plans
2. **Scoped** — has acceptance criteria, ready to build
3. **Ready for Dev** — assigned to Claude Code or Codex
4. **In Progress** — actively being built
5. **In Review** — PR open, Codex reviewing
6. **Client Review** — waiting on Karan's go/no-go
7. **Done** — merged + deployed

## Label Taxonomy

### Client Labels
- `jmd-menswear`
- `femme-events`
- (future: `client-name`)

### Component Labels
- `website` / `seo` / `gbp` / `content` / `reviews` / `systems` / `events` / `partnerships`

### Effort Labels
- `quick-win` (< 30 min)
- `half-day` (2-4 hours)
- `multi-day` (1+ days)

### Offer Type Labels
- `audit` / `buildout` / `content-engine` / `mini-tool` / `managed-os`

## Board Views
- **All Clients** — everything, swimlaned by client label
- **JMD Only** — filtered to `label:jmd-menswear`
- **Femme Events** — filtered to `label:femme-events`
- **Papi Ops** — internal tooling, processes, templates
- **This Week** — filtered to `priority:high` + `state:started|ready`

## Issue Template Strategy

Use **one primary Linear issue template**: `Agent Delegated Issue`.

Avoid separate full templates for Hermes / Claude Code / Codex unless real workflow friction proves they are needed. Instead, use one standard base issue body and add a short agent-specific section when useful:

- **Hermes Research/Docs Instructions** — for research, wiki/docs, planning, Linear organization, Google Workspace work, client-facing drafts, checklists, templates, SOPs, and recommendations.
- **Implementation Agent Instructions** — for Claude Code, Codex, or another implementation agent doing code, scripts, websites, automations, schemas, tests, or repo changes.

Local source-of-truth docs created from PAPI-8:

```text
~/projects/consultancy/papi-internal/templates/linear/
├── README.md
├── agent-delegated-issue.md
├── hermes-research-docs-section.md
└── implementation-agent-section.md
```

Every delegated issue must include: Context, Goal, Files/Paths, Acceptance Criteria, Agent Delegate, Constraints, Verification, and Definition of done.

All client-facing or approval-sensitive issues must include explicit Karan approval language. All client-data issues must include no-secrets/no-PII constraints.

## Headless Flow
```
Karan (Telegram): "work on JMD-7"
↓
Hermes reads Linear issue → checks acceptance criteria + DoD
↓
If issue is vague, Hermes enriches it using Agent Delegated Issue sections before work starts
↓
Hermes uses the appropriate agent-specific section (Hermes research/docs or Implementation Agent)
↓
Builder/reviewer loop runs as needed
↓
Hermes sends Karan one summary → "go" → merge/deliver/update status
```

## Research-Backed Spec Issue Pattern

When Karan asks for a Papi software/product spec issue based on existing Papi context:

1. Review the current Papi business plan first: `~/obsidian-vault/hermes-brain/wiki/consultancy/business-plan.md`.
2. Query Linear projects/issues for the relevant Papi project, especially:
   - `Papi Sales and Delivery Asset Buildout` for sales/delivery asset requirements.
   - `PAPI - Operating System Setup` for internal tooling/spec issues.
3. Use parallel subagents when there are two distinct knowledge streams, e.g. external product research (monday.com) + internal Linear/project issue review.
4. Synthesize into one implementation-ready Linear issue with sections: Context, Goal, Recommended Files/Paths, Product Vision, Required Workflows, IA/UI, Data Model, Boards/Templates, Statuses, Automations, Dashboards, Permissions/Safety, Integrations, V1/V1.5/Later, Non-goals, Acceptance Criteria, Agent Delegate, Verification, Definition of Done.
5. Place internal Papi tooling/spec issues in project `PAPI - Operating System Setup` unless Karan explicitly names another project.
6. Verify created/updated issues by re-querying Linear and checking the description contains key required terms; do not trust mutation success alone.

For the Papi Work OS / monday-style frontend idea, the seed issue created from this pattern is `PAPI-26`.

## PAPI Ops Skill Library Pattern

When working on PAPI ops skill-library issues:

1. Keep broad library/governance issues separate from domain pack implementation issues.
   - Example: `PAPI-27` owns `papi-ops-skill-library` strategy, source research, README conventions, promotion criteria, and first reusable cross-ops skills.
   - Example: `PAPI-30` owns the focused GBP/local SEO domain skill pack from JMD-2 lessons.
2. If a broad issue overlaps with a domain pack, do not combine into one monster issue. Update the broad issue to explicitly link/defer the domain-specific implementation to the focused issue.
3. Include `skills.sh` research in skill-library issues as discovery input, but treat marketplace skills as source references only: inspect source, classify `adapt/reject/defer`, and rewrite PAPI-owned modules with PAPI approval/evidence/privacy rules.
4. For first-batch PAPI ops skills, prefer reusable cross-ops capabilities before domain-specific modules: preflight, evidence/register discipline, approval gates, Linear finalization, and client-facing audit brief transformation.
5. When beginning work on a skill-library issue, use local git + `gh`: branch, commit, open a PR, verify `gh pr view --json commits,files,mergeable`, and post a Linear progress comment with the PR link. Do not merge unless Karan explicitly approves.

## Coding Harness Template Skill Slot Pattern

When Karan asks for PAPI issues related to the coding-task harness template:

1. Target repo is usually `sabnanikl-dev/agentic-harness-template`.
2. Keep the base coding harness template lean. If adding a skill slot, add only a tracked empty directory in V1:
   - `skills/.gitkeep`
3. Do **not** preload starter skills, `skills/README.md`, `skills/INDEX.md`, or skill-selection docs into the base coding harness unless Karan explicitly asks. The base template should remain generic.
4. Do **not** add a skill-copy helper script until the manual process has repeated enough times to reveal stable paths and conventions. Recommendation: manually select/copy skills for 2–3 real coding tasks first, then automate if the pattern is stable.
5. The skill-selection discussion is a planning behavior between Hermes and Karan before/during cloning a specific coding-task harness. It does not need to be documented inside the base repo in V1.
6. A good Linear issue for this pattern should specify:
   - Goal: future cloned coding-task harnesses include a `skills/` folder ready for selected task-specific skills.
   - Files: `skills/.gitkeep` only.
   - Non-goals: no starter skills, no skill index/readme, no selection docs, no copy script, no runtime/tooling behavior changes.
   - Acceptance criteria: fresh clone includes `skills/`; PR file list includes only `skills/.gitkeep` unless justified.

## Coding Task Harness + Skills Issue Enrichment Pattern

When updating a client coding issue to use the agent harness template (example: JMD-6):

1. Read the existing Linear issue first and preserve/expand its acceptance criteria; do not overwrite client constraints.
2. Ask Karan clarifying questions before drafting if he explicitly requests it. Confirm:
   - cloned harness vs existing repo,
   - tight vs broad skill set,
   - whether to include exact `npx skills add ...` install refs,
   - implementation agent (Codex/Claude Code),
   - whether scope is harness/spec/plan only or actual build/deploy,
   - whether tech stack is fixed or left to the agent based on `docs/spec.md`.
3. Spawn a research subagent to inspect `skills.sh` / GitHub skill sources and return include-now vs optional recommendations. Treat external skills as source references only.
4. Update the issue to require:
   - clone `sabnanikl-dev/agentic-harness-template`,
   - populate `docs/spec.md` with client/project requirements,
   - add selected task-specific skills into cloned harness `skills/`,
   - create a build plan before implementation,
   - avoid build/deploy/live changes unless explicitly in scope.
5. Include exact install refs when requested, e.g. `npx skills add https://github.com/anthropics/skills --skill webapp-testing`, but warn agents to review/adapt instead of blindly importing hooks/commands.
6. For frontend/client website tasks, a reusable tight starter set to consider is:
   - `planning-with-files`
   - `webapp-testing`
   - `frontend-design`
   - `web-design-guidelines`
   - `accessibility`
   - `seo`
   - `core-web-vitals`
   - `code-review-and-quality`
   - `ui-ux-pro-max-skill`
   Optional/conditional: `agent-browser`, `browser-trace`, `security-and-hardening`, `vercel-react-best-practices`, `shadcn`.
7. If new external skills look broadly reusable (e.g. `frontend-design`, `ui-ux-pro-max-skill`), create a separate PAPI skill-library issue to evaluate/adapt them rather than overloading the client issue.
8. Verify by re-querying Linear and checking key terms exist in the updated issue description.

## PAPI-34 Frontend/Coding Skill Adaptation Pattern

When evaluating frontend/design/web-quality skills for the PAPI ops skill library:

1. Treat external skills as source research, not dependencies to vendor wholesale.
2. Classify each source as `adapt`, `partial/defer`, or `conditional/defer`, and capture rationale in `docs/research/` plus `docs/source-research-backlog.md`.
3. Prefer a small PAPI-owned starter set for client coding harnesses:
   - `skills/coding/coding-harness-planning-discipline.md`
   - `skills/coding/browser-qa-evidence.md`
   - `skills/coding/code-quality-safety-review.md`
   - `skills/client-site/client-site-frontend-design.md`
   - `skills/client-site/local-client-web-quality-audit.md`
4. Adapt broadly useful sources like planning, webapp testing, frontend design, web design guidelines, accessibility, SEO, Core Web Vitals, code review, and security-hardening into lean modules.
5. Defer large/tool-specific packages like `ui-ux-pro-max-skill`, `agent-browser`, `browser-trace`, `shadcn`, and `vercel-react-best-practices` unless the task stack explicitly needs them.
6. Validate skill files for required sections/frontmatter, run `git diff --check`, local secret scan if GitHub Advanced Security is unavailable, then PR and move Linear to In Review.

## Linear API Key
Configured in `~/.hermes/.env` as `LINEAR_API_KEY`.

## References
- Full attack plan: `~/projects/consultancy/JMD-Menswear/plans/`
- Harness template: `sabnanikl-dev/agentic-harness-template`
- Saturday operating model discussion established this architecture
