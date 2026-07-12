# Hermes → Claude Code → CodexReviewer Orchestration

Session-derived reference for GodMode dogfooding workflows where Hermes is the orchestrator, Claude Code is the builder, and CodexReviewer is the independent reviewer.

## Core architecture

- GitHub Issues are the coding-task queue.
- GitHub PRs are the code artifact and audit trail.
- Hermes owns orchestration, state transitions, verification, and Karan-facing summaries.
- Claude Code owns implementation, branch/PR creation, and fixing review blockers.
- CodexReviewer owns PR review and should ideally use a separate GitHub account so reviews are not same-account self-approvals.
- Karan keeps final merge/deploy/client-facing authority.

## Infrastructure sequence

Start manual, then add automation:

1. **Manual trigger** — Karan/Hermes starts a specific issue run.
2. **Roll call watchdog** — every ~10 minutes, reconcile local run state against live GitHub/worker state; stay quiet unless a safe transition or human decision exists.
3. **GitHub webhooks** — PR opened/synchronized, review submitted, and CI completed events wake Hermes/GodMode; cron remains fallback.
4. **Queue mode** — only after proven manual runs, allow `agent:ready` issues to keep one worker active.

Cron should be a roll call/reconciliation loop, not an autonomous random-task starter.

## Fix-cycle rule

When CodexReviewer requests changes, the Claude Code fix prompt should normally say:

```text
The PR has blocking review feedback.
Read the latest GitHub PR reviews, review threads, inline comments, and conversation comments yourself.
Identify unresolved blocking feedback from CodexReviewer.
Resolve only those blockers.
Run verification, push a follow-up commit, and comment what changed.
```

Hermes/GodMode may store normalized blocker text for synthesis/audit/fallback, but should not paste blocker summaries as the default source of truth.

## Repo-local template namespace

Use explicit Hermes ownership for operational templates:

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

Do **not** use a vague `.agentic/commands/` namespace for this class of templates; future agents may confuse it with GodMode product runtime commands.

The README should state:

- this folder is not GodMode product runtime code;
- it contains Hermes dogfooding/orchestration templates;
- `AGENTS.md`, `docs/spec.md`, and the live GitHub Issue/PR outrank the templates;
- do not implement features from these templates unless a GitHub Issue explicitly asks for it.

If product support is later implemented, use an explicit config namespace such as:

```yaml
orchestration:
  owner: hermes
  templates:
    builder_start: .agentic/hermes-orchestration/templates/claude-builder-start.md
    builder_fix: .agentic/hermes-orchestration/templates/claude-builder-fix.md
    reviewer_start: .agentic/hermes-orchestration/templates/codex-reviewer-start.md
```

## Verification gates

Before reporting ready:

- PR exists and links the issue.
- Remote PR head commit matches expected local/worker commit.
- CodexReviewer review is present and non-blocking, or blockers are explicitly adjudicated.
- CI/build/test state is checked.
- For UI changes, visual QA is performed when practical.
- Merge remains human-approved only unless Karan explicitly changes policy.
