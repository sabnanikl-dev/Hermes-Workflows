---
name: ops-execution-harness
description: Use when preparing lean, manual execution harnesses for non-coding client operations issues so Codex/Claude Desktop can execute with Linear context, task-specific skills, evidence, outputs, and approval gates.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ops, harness, linear, claude, codex, consulting]
    related_skills: [linear, project-kickoff]
---

# Ops Execution Harness

## Overview

Use this workflow for non-coding operations tasks: audits, research, local SEO, Google Business Profile work, reporting, outreach, content planning, access checks, and client-delivery prep.

The V1 pattern is deliberately lean and manual. Do **not** build a fully automated/headless orchestration system by default. Instead, create or clone a reusable task workspace, add only the context and skills needed for the specific Linear issue, and let the user open that folder in Codex Desktop or Claude Desktop where Linear integrations are already configured.

Core principle:

> Base harness = empty execution container. Task skills = added only after scoping the issue.

## When to Use

Use this when:

- The task is a Linear issue but is not primarily a code/PR task.
- The user wants Claude/Codex Desktop to execute inside a constrained folder.
- The work needs evidence, screenshots, reports, approval gates, or client-safe outputs.
- The task may use skills/playbooks but should not load a giant global context.
- The user wants to avoid premature automation and usage bloat.

Do not use this for:

- Regular coding work that should use a repo/branch/PR harness.
- Fully headless agent orchestration unless explicitly requested.
- Tasks where no durable output/evidence is needed.
- Simple Google Business Profile completeness checks where the API or native Google reports already provide the needed fields. For those, prefer a lightweight read-only Kanban/API task that outputs missing/weak fields and approval-needed updates. Escalate to a harness only if the GBP work becomes evidence-heavy, client-facing, multi-output, or includes coordinated account/directory actions.

## Repos

Known V1 repos:

- `sabnanikl-dev/papi-ops-execution-harness-template`
- Local path when already cloned: `~/projects/papi-ops-execution-harness-template`
- If local path is missing, verify with `gh repo view sabnanikl-dev/papi-ops-execution-harness-template` and clone directly from GitHub into the task workspace.
- Purpose: skill-light base template for cloned ops issue workspaces.

- `sabnanikl-dev/papi-ops-skill-library`
- Local path: `~/projects/papi-ops-skill-library`
- Purpose: empty/curated library of reusable ops skills that can be copied into task harnesses only when relevant.

## Base Harness Structure

The base template should stay small:

```txt
AGENTS.md
README.md
task.md
context.md
constraints.md
playbook.md
skills/
  manifest.md
commands/
  run-task.md
  review-output.md
evidence/
outputs/
```

The base template should not preload task-specific skills such as GBP audit, SEO, content calendars, review responses, or outreach. It should only teach the agent how to load skills when a cloned task harness includes them.

## V1 Workflow

Reference pattern for rewriting existing Linear issues into harness-first execution: `references/harness-first-linear-rewrite.md`.

1. **Scope the Linear issue**
   - Rewrite or verify the issue has context, goal, constraints, acceptance criteria, verification, and definition of done.
   - For existing broad ops issues, rewrite the Linear issue to be **harness-first**: clone/populate the task harness, then execute the audit/research/outreach inside it.
   - Include source template repo, target workspace path, approval mode, required harness files, evidence/output expectations, and the final comment draft requirement.
   - Linear remains the live source of truth.

1.5. **Run preflight before execution**
   - Confirm whether this is setup-only, full execution, review, or client-facing report generation.
   - Confirm live-account access path before starting evidence collection (dashboard/browser/API/export). Do not spend a full public-only pass if authenticated access is available or expected.
   - Confirm whether screenshots/API exports are allowed, where they should be stored, and what needs redaction.
   - Confirm whether domain-specific assumptions have changed (for example GBP Q&A/Ask Maps surface changes, API deprecations, platform UI changes).
   - Confirm expected final deliverables: internal audit, Linear comment, client-facing report/deck, follow-up issue list, or all of these.
   - Create or update `preflight.md` for complex ops tasks; if omitted, document preflight decisions in `task.md`.

2. **Clone the base harness**
   - Example folder name: `jmd-2-gbp-audit`.
   - Keep one cloned folder per ops task.

3. **Populate task files**
   - `task.md`: client, Linear issue key, task type, approval mode, expected outputs.
   - `context.md`: relevant client/project context only.
   - `constraints.md`: safety, approval, account-change, client-facing rules.
   - `playbook.md`: step-by-step workflow for this task.
   - If Karan narrows scope to **setup only** (e.g. "don't complete the task for now, just clone/populate files"), stop at harness preparation. Create clearly labeled placeholder evidence/output files, but do not execute the downstream audit/research/outreach or represent templates as completed deliverables. See `references/setup-only-harness-population.md`.

4. **Select task-specific skills**
   - Add only the skills needed for the issue into `skills/`.
   - Update `skills/manifest.md` with Required and Optional skills.
   - Do not install large external skill packs wholesale.

5. **User opens in Codex/Claude Desktop**
   - Prompt: `Read AGENTS.md, read the Linear issue listed in task.md, load skills from skills/manifest.md, execute inside this harness, save evidence and outputs, and do not make live changes without approval.`

6. **Review outputs**
   - Use `commands/review-output.md` or a second agent pass to check gaps, unsupported claims, missing evidence, and acceptance criteria.

7. **Finalize**
   - The agent writes a final summary or Linear comment draft.
   - Hermes/user reviews before any live account/client-facing changes.

## Skill Loading Pattern

`skills/manifest.md` starts empty in the base template.

For repo-specific autonomous experiments, a repo may also carry a local skill directory such as `skills/<local-skill>/SKILL.md`. Use this when the behavior should apply only inside that repo, not as a globally installed Hermes skill. See `references/repo-local-skill-and-telegram-approval-gates.md` for the pattern, including Telegram-origin approval requests and agent-owned external setup accounts.

After scoping a real issue, update it like:

```md
# Skill Manifest

## Required Skills
- `skills/gbp-audit.md`
- `skills/local-seo.md`
- `skills/evidence-capture.md`
- `skills/client-approval.md`

## Optional Skills
- `skills/technical-seo.md` only if the issue expands into website audit.

## Do Not Load
Do not run full website crawler or programmatic SEO workflows unless explicitly added to the issue.
```

AGENTS.md should instruct:

1. Read `skills/manifest.md` before execution.
2. Load only Required skills.
3. Load Optional skills only if the Linear issue requires them.
4. If a skill conflicts with `constraints.md`, the stricter safety rule wins.
5. If no skills are loaded, use `playbook.md`, `constraints.md`, and the Linear issue.

## External Skill Repos and Skill Marketplaces

Treat external repositories and marketplaces such as Agentic SEO Skill or `skills.sh` as source libraries, not automatic dependencies.

Good uses:

- Extract a local SEO rubric for a local-search task.
- Adapt a technical SEO checklist for a website audit.
- Copy a relevant template into a specific task harness.
- Use `skills.sh` discovery to enrich Linear issues for reusable PAPI skill packs: spawn parallel subagents by research stream, collect ranked skill links/patterns, then adapt only useful procedures into PAPI-owned modules.

Recommended `skills.sh` review streams for ops-audit skill-pack work:

1. Domain skills: e.g. GBP/local SEO/reviews/maps/listings/competitor workflows.
2. Evidence and reporting skills: e.g. screenshots, browser traces, scraping, spreadsheets, docs/PDFs, client deliverables.
3. Harness/meta workflow skills: e.g. planning files, context mapping, checklist discipline, validation, instruction governance.

When converting marketplace findings into PAPI work, update the Linear issue with:

- Ranked external skill references and what to adapt from each.
- PAPI-owned module/file names to create.
- Evidence/register standards and required artifacts.
- Approval, cost, scraping, privacy, and redaction gates.
- Acceptance criteria and verification that prove the external patterns were adapted safely rather than imported wholesale.

Avoid:

- Loading every external SEO skill into every ops harness.
- Including scripts/tools irrelevant to the task.
- Letting large skill packs override client constraints or approval rules.
- Treating marketplace skills as trusted instructions without PAPI safety adaptation.

## Evidence and Outputs

Ops work uses evidence-backed deliverables instead of PR checks.

Common folders:

- `evidence/`: screenshots, exports, source files, URLs, timestamped notes, unavailable-evidence notes.
- `outputs/`: audit docs, recommendations, approval-needed lists, blocked items, final Linear comment drafts.

Every meaningful recommendation should be traceable to evidence or marked as an assumption.

Evidence quality rules:

- Prefer screenshots/API exports for account dashboards, metrics baselines, field settings, review tabs, product/post/photo state, and other high-value evidence when permission allows.
- Written observation notes are acceptable for private dashboards only when screenshots/exports are unavailable, disallowed, or unsafe; explicitly state this limitation in `evidence/unavailable-evidence-note.md`.
- Maintain an `evidence/index.md` mapping each evidence file to source, date, sections covered, and limitations.
- For metrics-heavy tasks, add `outputs/metrics.md` or a metrics section that converts raw counts into action rates/conversion rates where useful.
- For client-facing deliverables, add `outputs/client-report-brief.md` or equivalent to translate internal evidence into owner-safe language.

For setup-only passes, use explicit placeholders:

- `evidence/unavailable-evidence-note.md`: explains evidence was not captured because execution was intentionally deferred.
- `outputs/<deliverable>.md`: a scaffold/status template marked "not completed yet".
- `outputs/final-linear-comment.md`: a draft/setup note, not a completion claim.

## Approval Modes

Use explicit approval modes in `task.md`:

- `read_only`: inspect and report only.
- `draft_only`: draft recommendations/copy, no live changes.
- `approval_required_write`: live changes only after explicit user approval.
- `autonomous_internal_write`: safe internal harness/docs outputs only.

For client account/dashboard work, default to `draft_only` unless the user explicitly approves writes.

## Common Pitfalls

1. **Automating too early.** V1 is manual: clone harness, add skills, open in desktop agent.
2. **Preloading too many skills.** Keep the base harness skill-light; add skills after issue scoping.
3. **Duplicating Linear too heavily.** The issue is the live source of truth; local files should guide execution, not drift from Linear.
4. **Letting skills override constraints.** Safety and approval constraints always win.
5. **Skipping evidence.** Ops deliverables need screenshots/exports/notes just like code needs tests.
6. **Over-executing after a setup-only instruction.** If Karan says to only clone/populate the harness, do not run the actual audit/research/outreach. Populate templates/placeholders and make the deferred status unmistakable.
7. **Building every skill from scratch forever.** After repeated use, promote reusable skills into the separate skill library.
8. **Skipping preflight and causing sequential rework.** If access, evidence permissions, current platform behavior, or output format are unclear, execution often devolves into public-only pass → authenticated pass → strategy correction → client report rewrite. Resolve these before the evidence pass.
9. **Leaving stale setup-only instructions.** When scope changes from setup-only to full execution, update `task.md` and `playbook.md` together so future agents do not follow obsolete stop conditions.
10. **Treating raw metrics as strategy.** For performance/GBP/local SEO tasks, convert raw counts into useful operating rates (click rate, call rate, directions rate, combined action rate) and define the follow-up measurement cadence.
11. **Parallel Kanban writes to the same harness repo.** If using Kanban to update the ops harness template or skill library, do not dispatch multiple mutating tasks against the same `dir:<repo>` workspace at once. Use dependencies, separate worktrees, or scratch outputs plus one integrator task; otherwise commits can capture sibling changes and stale AC/status files.

## Verification Checklist

- [ ] Linear issue has clear context, constraints, AC, verification, and DoD.
- [ ] Preflight decisions are documented: run mode, access path, evidence permissions, domain assumptions, and expected deliverables.
- [ ] Cloned harness has `task.md`, `context.md`, `constraints.md`, and `playbook.md` populated.
- [ ] `task.md` and `playbook.md` agree on setup-only vs full-execution scope; no stale stop conditions remain.
- [ ] `skills/manifest.md` lists only task-relevant skills.
- [ ] Evidence and output folders exist.
- [ ] Evidence index maps files to source/date/sections/limitations.
- [ ] Approval mode is explicit.
- [ ] Agent instructions say no live changes without approval.
- [ ] Metrics-heavy work includes raw metrics plus calculated action/conversion rates where useful.
- [ ] Final output includes a Linear comment/update draft.
- [ ] Client-facing output, if requested, is owner-safe and separates what works, what needs fixing, approvals, blockers, and next actions.
- [ ] User/Hermes reviews before account or client-facing changes.
