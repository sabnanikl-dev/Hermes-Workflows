# Kanban Pilot Closeout Pattern

Session-derived pattern from a multi-profile pilot that moved Linear issues through Kanban, GitHub PRs, review comments, merge, and Linear Done.

## What Worked

- Keep specialist responsibilities distinct:
  - `orchestrator`: decomposes/routes.
  - `pm-spec`: writes repo-local specs, acceptance criteria, approval gates, and handoff docs.
  - `builder`: creates harness/code/template artifacts.
  - `researcher`: extracts reusable skill/domain guidance.
  - `reviewer`: checks AC/DoD, stale assumptions, template/client-specific leakage, and no-live-change boundaries.
  - default/control tower: final integration across GitHub, Linear, logs, and user communication.
- Human PR review is valuable: user comments can expose portability/design issues that worker profiles missed.
- Reusable harnesses must be agent-agnostic: required guidance belongs in repo files (`AGENTS.md`, `docs/spec.md`, `docs/build-plan.md`, `skills/manifest.md`), while Hermes-local skills should be optional references only.
- Final merge/reporting must verify each PR independently with GitHub API `merged: true`; do not trust local state or a successful merge command alone.

## What Did Not Work

- Parallel builder tasks mutating the same repo/workspace caused overlapping commits and stale status artifacts.
- Issue-specific artifacts leaked into reusable template repos, e.g. one-ticket AC status or reviewer verdict files.
- Initial skill manifests overfit to Hermes-local skills, reducing portability to Claude Code, Codex Desktop, Antigravity, or other agents.
- Worker outputs still needed control-tower integration for PR hygiene, Linear comments/statuses, merge verification, local cleanup, and daily logging.

## Efficiency Improvements

1. Before dispatch, classify each output target:
   - base template repo
   - cloned task harness
   - domain skill library
   - Linear comment draft
   - client-facing deliverable
2. If two tasks write the same Git repo, use one of:
   - dependency chain
   - separate git worktrees
   - parallel scratch/research tasks followed by one integrator task
3. Add a reviewer checklist for reusable templates:
   - no ticket/client-specific artifacts in base template
   - no issue IDs unless deliberately example-only
   - no Hermes-only required skills
   - no stale repo/remote blockers
   - no live-change authorization
4. Let specialists produce artifacts, then have the default/control-tower profile perform final integration:
   - GitHub PR comments and merges
   - merge verification (`merged: true`)
   - branch cleanup/local sync
   - Linear wrap-up comments/status updates
   - daily log

## Wrap-up Checklist

- [ ] All profile tasks completed or intentionally canceled.
- [ ] User review comments converted into concrete repo changes.
- [ ] PR commits verified on remote before reporting.
- [ ] PRs merged and each `merged: true` verified by REST API.
- [ ] Remote feature branches gone after merge.
- [ ] Local repos on `main` and clean/tracking `origin/main`.
- [ ] Linear issues commented with final summary and moved to appropriate terminal state.
- [ ] Daily log updated.
