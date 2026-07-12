---
name: autonomous-coding-agents
description: "Use when delegating coding work to external autonomous coding CLIs or isolated lanes: Claude Code, Codex, OpenCode, and Kanban-backed Codex lanes."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [autonomous-agents, coding, claude-code, codex, opencode, kanban]
    related_skills: [hermes-agent, github-pr-workflow, subagent-driven-development]
---

# Autonomous Coding Agents

## Overview
Use this umbrella when Hermes should coordinate another coding agent process instead of doing all implementation directly. It covers external CLIs, one-shot delegation, interactive/tmux workflows, and Kanban isolated implementation lanes.

## When to Use
- Delegate a bounded feature, bugfix, refactor, or PR review to Claude Code, OpenAI Codex CLI, or OpenCode.
- Run a coding agent in an isolated worktree/lane while Hermes owns planning, tests, reconciliation, and handoff.
- Compare or cross-review outputs from multiple autonomous coding agents.

## Agent Choices

### Claude Code
Useful for strong coding/refactoring execution when the Claude Code CLI is installed and authenticated. Give it a self-contained prompt, exact repo path, acceptance criteria, and required verification commands.

### Codex
Useful for OpenAI Codex CLI work, especially repository modifications and review. Check auth/provider state first; run in a worktree or explicit branch; verify its output yourself before reporting success.

### OpenCode
Useful as an alternate autonomous coding CLI for implementation or review. Treat its summary as a self-report: verify files, diffs, tests, and external side effects.

### Kanban Codex lane
Use when a Kanban worker wants Codex as an implementation lane while Hermes remains accountable for lifecycle, reconciliation, tests, and final user/client updates.

## Operating Pattern
1. Define the task contract: goal, repo path, branch/worktree, constraints, acceptance tests, and forbidden changes.
2. Start the external agent in an isolated environment when edits are likely.
3. Monitor output without flooding context; capture durable artifacts, diffs, and logs.
4. If the assigned coding agent reaches an approval gate for an external handoff (push, PR creation, review request), and the user approves, steer that same agent to perform its own handoff when feasible instead of taking over silently. This matters for dogfooding agent workflows: Hermes remains accountable for verification, but builder ownership should stay with the builder agent. If literal terminal typing is blocked, try the agent's resume/remote-control/session mechanism; if Hermes must take over, say so explicitly.
5. Verify independently with git diff, tests, linters, app-specific checks, and remote state (for PRs: branch/head SHA, issue linkage, and PR state).
6. Reconcile and summarize: what changed, evidence, remaining risks.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/`.

## Scheduled adversarial reviewer lanes

When Karan wants a recurring external-agent critique loop, especially Claude Code/Opus reviewing a product lane, prefer a **script-only read-only cron** over a mutating builder agent. The cron should write timestamped reports plus a stable `latest.md` pointer outside the repo, then downstream product/build crons should read that pointer before choosing their next move. See `references/claude-code-cron-adversarial-review.md` for the wrapper pattern, prompt contract, downstream cron prompt block, and verification checklist.

## Verification Checklist
- [ ] External CLI is installed/authenticated before delegation.
- [ ] Worktree/branch isolation is clear.
- [ ] Hermes independently verifies all claimed edits and test results.
- [ ] User-facing final answer cites real verification output, not the child agent's self-report alone.
- [ ] For scheduled reviewer lanes, latest findings are written to a stable path and downstream crons are explicitly told how to consume them.
