# GodMode Dashboard-First BYOA Coding Workflow

Use this reference when designing, scaffolding, or operating a QuadWork/tmux-inspired coding dashboard where Hermes is the default head but the product must stay bring-your-own-agent native.

## Session-derived product lessons

- Karan wants **dashboard-first v1**, not CLI-first: the product should look/feel like QuadWork/tmux with live panes for each agent.
- The operator should be able to **chat/control each agent pane**: head/operator, builder, reviewer A, reviewer B.
- Karan's default stack is:
  - Head/operator: Hermes
  - Builder/dev: Claude Code
  - Reviewer A: Codex for correctness/security/tests/regressions
  - Reviewer B: Codex for architecture/spec/harness compliance
- The product must be **bring-your-own-agent native**: OpenClaw, Claude, Codex, Hermes, OpenCode, Gemini, or custom CLIs can occupy any role.
- Code and docs should model **roles separately from agents/adapters**. Avoid core names like `ClaudePane` or `CodexPane`; prefer `BuilderPane`, `ReviewerPane`, `head`, `builder`, `reviewer_a`, `reviewer_b`.
- Hermes should not over-prompt Claude/Codex with large bespoke prompts. The **project harness is the source of truth**: `AGENTS.md`, `docs/spec.md`, review role docs, GitHub Issues, PR comments, and PR state.
- Hermes/head should issue minimal commands like “work on this issue, read the harness” or “review this PR using your role doc.”

## Automatic PR loop preference

Once the builder opens a PR:

1. Reviewer A and Reviewer B start automatically.
2. If either reviewer finds blockers, the builder automatically receives accepted blockers.
3. Builder fixes, pushes, and comments on the PR.
4. Reviewers automatically re-review.
5. The loop continues until merge-ready, max cycles, failure, pause, or human intervention.
6. Karan retains final merge authority; do not auto-merge to main in v1.

## Recommended v1 tech stack for GodMode-like dashboard

- macOS-first Electron desktop app.
- TypeScript end-to-end.
- React + Vite renderer.
- xterm.js terminal panes.
- Node.js main process + `node-pty` for interactive CLI sessions.
- SQLite via `better-sqlite3` for projects, runs, sessions, findings, and events.
- `git` + `gh` CLI for v1 GitHub operations.
- Project-local config such as `.agentic/godmode.yaml`.

Rationale: PTY/process orchestration and local CLI integration are the core risks. Electron + Node is the fastest practical path to working tmux-like panes, Mac packaging, local filesystem access, and agent CLI control.

## Harness requirements for dogfooding

For self-building agent dashboards, write the harness before deep coding:

- `AGENTS.md` with role-based rules, BYOA constraints, branch/PR policy, review loop, merge authority, and verification rules.
- `docs/spec.md` as the living product/tech spec.
- `docs/review/reviewer-a-correctness.md` and `docs/review/reviewer-b-architecture.md` or equivalents.
- `.agentic/godmode.yaml` or equivalent role/config map.
- `docs/friction/` for non-obvious failures and harness lessons.

Key harness rule: durable workflow behavior belongs in repo docs/config, not one-off Hermes prompts.
