# Hermes–Claude–Codex GitHub Orchestration Notes

Use this reference when designing a GitHub-first coding loop where Hermes/GodMode orchestrates, Claude Code builds, and CodexReviewer reviews.

## Source Pattern

The motivating pattern is a maintainer-orchestrator loop: one lightweight control-plane agent wakes periodically, monitors many worker lanes, directs work to focused threads, and asks the owner only for decision-ready items.

Adaptation for Karan/GodMode:

- GitHub Issues are the task queue.
- GitHub PRs are the artifact and audit trail.
- Hermes/GodMode owns orchestration, verification, and human briefs.
- Claude Code owns implementation and fix commits.
- CodexReviewer owns independent PR review, ideally from a separate GitHub account.
- Karan keeps final merge authority.

## Infrastructure Shape

Prefer staged infrastructure:

1. Manual trigger: `run Claude/Codex loop on issue #N`.
2. Roll-call watchdog every 5–10 minutes: reconcile run ledger, worker process state, PR/review/CI state, and advance only safe deterministic transitions.
3. GitHub webhooks: issue labeled, PR opened/synchronized, review submitted, CI completed.
4. Queue mode: only after several clean manual runs, keep one worker active on `agent:ready` issues.

Roll call is not autonomous task picking. It is floor-walking: who is active, who finished, who is blocked, what transition is now safe, and what needs Karan.

## Builder Fix Handoff

When CodexReviewer requests changes, the normal Claude Code fix prompt should be pointer-first:

```text
The PR has blocking review feedback.
Read the latest GitHub PR reviews, review threads, inline comments, and conversation comments yourself.
Identify unresolved blocking feedback from CodexReviewer.
Resolve only those blockers.
Run verification, push a follow-up commit, and comment what changed.
```

Do not paste Hermes' summarized blockers by default. Use a normalized blocker capsule only as fallback when the builder cannot access GitHub directly.

## Repo Command Template Folder

For GodMode-style operated projects, store executable prompt templates under `.agentic/commands/` and reference them from `.agentic/godmode.yaml`:

```text
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

These are harness inputs, not general documentation. Keep them role-first and pointer-first. `docs/` explains behavior; `.agentic/commands/` drives behavior.

## Verification Gates

Before reporting ready:

- PR exists and links the issue.
- Remote PR head/commit matches the claimed branch commit.
- All review surfaces were inspected: reviews, inline comments, conversation comments, review threads.
- CodexReviewer pass/approval is verified from GitHub, not just stdout.
- CI/build/test evidence is current.
- Merge is still human-gated unless Karan explicitly changes policy.
