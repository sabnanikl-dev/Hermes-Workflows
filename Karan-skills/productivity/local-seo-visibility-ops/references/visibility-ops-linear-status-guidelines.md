# Visibility-Ops Linear Status Guidelines

Use this when a local SEO / visibility project has both a GitHub-backed operations repo and a Linear project. The goal is to keep Linear as the active execution tracker while the repo/wiki hold durable artifacts.

## Core rule

Linear tracks execution; the repo/wiki hold durable source-of-truth artifacts. Do not let repo docs become a parallel task tracker, and do not let Linear comments become the canonical business source of truth.

## Recommended repo scaffold

For a docs-first visibility-ops repo, add:

- `AGENTS.md` — lightweight orientation and safety guide.
- `docs/workflows/linear-issue-management.md` — project-specific Linear workflow/status guidance.
- Existing project docs such as `docs/<client>/local-seo-source-of-truth.md`, approval ledger, read-only baselines, and reuse notes.

Link the Linear workflow doc from both `AGENTS.md` and `README.md` so agents see it during orientation.

## Status semantics

Map named Linear states to operational meaning, not vibes:

- **Triage** — rough incoming item; needs shaping, deduping, or routing.
- **Backlog** — valid but not selected for the current visibility push.
- **Ready** — shaped enough to start; includes outcome, owner/lane, files/accounts, acceptance criteria, approval boundaries, and verification plan.
- **In Progress** — an agent or human is actively working now.
- **In Review** — artifact/PR/report/decision checklist is ready for owner or reviewer approval, or a parent issue is paused on a human-review child issue.
- **Done** — acceptance criteria are verified, links/comments are posted, and no remaining blocker belongs to the issue.
- **Canceled/Duplicate** — explicitly not doing or superseded; link replacement when applicable.

## Human-review child pattern

When a parent visibility issue is blocked by Karan/Amanda decisions:

1. Move the parent to **In Review**.
2. Create a child review issue with a checkable decision list and comment-answer instructions.
3. Keep human answers on the child issue.
4. When the child is **Done**, move the parent back to **In Progress**.
5. Apply decisions to wiki/repo artifacts.
6. Verify consistency.
7. Comment finalization summary on the parent.
8. Move parent back to **In Review** for final owner closeout, or **Done** if completion was already approved.

Do not leave human-blocked parent issues in **In Progress**.

## Work-type rules

### Source-of-truth / approval-ledger docs

- **Ready:** fields, source paths, and approval boundaries are defined.
- **In Progress:** an agent is actively reconciling website/wiki/API/public-source facts.
- **In Review:** draft source-of-truth and ledger are ready for owner decisions.
- **Done:** approved decisions are applied to wiki/repo copies, unresolved items are in the ledger or follow-up issues, and final links are commented.

### Read-only research / competitor / GBP audits

- **Ready:** targets and output format are defined.
- **In Progress:** research/API checks are actively running.
- **In Review:** findings/recommendations are ready for review.
- **Done:** findings are linked, no public mutations occurred, and follow-up implementation issues are created if needed.

### Website implementation issues

- **Ready:** brief includes target route/files, acceptance criteria, validation commands, visual evidence needs, and claims guardrails.
- **In Progress:** Claude Code/Codex implements through GitHub PR workflow.
- **In Review:** PR is open with summary, validation, and evidence/reviewer notes.
- **Done:** PR is merged only after approval, GitHub confirms `merged: true`, deployment/build is verified when applicable, and Linear closeout comment is posted.

### Public-account or directory work

- **Ready:** approved source-of-truth fields and exact platform/action list exist.
- **In Progress:** approved public/account action is actively being performed.
- **In Review:** draft/evidence is waiting for owner check before submission, or submission evidence is ready for review.
- **Done:** live platform state is verified directly and final evidence/URLs are commented.

Never move public-account work to **Done** from a draft alone.

## Safe status mutation pattern

Agents changing Linear statuses should:

1. Query the issue and confirm identifier, title, team, project, and current state.
2. Query workflow states for that team and select target state ID by name/type.
3. Add a durable handoff/comment before or immediately after the status change when context is needed.
4. Run the status mutation.
5. Re-query the issue and verify the new state before reporting success.

Never rely only on a mutation response when the status change is important for handoff.
