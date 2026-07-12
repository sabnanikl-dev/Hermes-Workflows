# Dashboard-First Build Council Pattern

Use when Karan wants a QuadWork-like / tmux-like multi-agent coding workflow, but tailored to Hermes-led development.

## Product Shape

The desired v1 is dashboard-first, not CLI-first and not fully autonomous. The dashboard should feel like a local tmux/workbench where Karan can see and interact with each live agent:

- Hermes / Head pane
- Claude Code / Builder pane
- Codex Reviewer A pane
- Codex Reviewer B pane
- GitHub/PR/status pane

Karan should be able to chat with Hermes, Claude Code, or either Codex reviewer while the run is active. Agent panes should expose terminal/log output plus a control/chat history.

## Role Model

- **Karan**: stays in the loop, chooses/specs/delegates work, may approve or merge to main himself.
- **Hermes**: head/operator/thought partner. Starts runs, monitors state, summarizes, and intervenes when ambiguity/risk appears.
- **Claude Code**: Dev/builder. Builds from issue + project harness, opens PRs, fixes blockers, comments on the PR.
- **Codex Reviewer A**: independent review focused on correctness, tests, security, and regressions.
- **Codex Reviewer B**: independent review focused on architecture, maintainability, spec drift, and harness compliance.

## Source of Truth

Do **not** make Hermes carry long bespoke prompts full of project context. The source of truth should be the opened project harness plus GitHub/Linear artifacts:

- `AGENTS.md`
- `docs/spec.md`
- repo docs/conventions/friction/review docs
- GitHub issues
- PR descriptions/comments/review comments
- Linear issue/parent packet when applicable

Hermes should mostly give high-level commands such as:

- “Work on issue #N. Read the project harness.”
- “Review PR #N using your reviewer role doc.”
- “Re-review after Claude’s latest fix.”

If Hermes needs richer instructions, prefer improving the harness/repo docs over stuffing the prompt.

## Automatic PR Review Loop

Once Karan/Hermes starts a build, the inner PR loop should run automatically:

1. Claude Code builds from the issue and project harness.
2. Claude opens a PR.
3. Both Codex reviewers automatically begin independent reviews.
4. If blockers exist, Claude automatically picks them up, implements fixes, comments on the PR, and pushes.
5. Reviewers automatically re-review.
6. Loop continues until merge-ready or a stop condition fires.

Stop conditions:

- max review/fix cycles exceeded
- ambiguous or conflicting reviewer feedback
- agent/process failure
- tests/build cannot be stabilized
- Karan pauses/cancels
- high-risk action requires approval

Automation owns build/review/fix/re-review. Karan retains final approval/merge authority.

## Dashboard UX Requirements

V1 should prioritize a QuadWork/tmux-like feel over a polished SaaS kanban:

- multi-pane live terminal/log views
- per-agent chat/control input
- visible run state machine
- issue/PR status pane
- blockers and merge-readiness indicators
- pause/resume/cancel controls
- final “ready for Karan” / “merge-ready” state

A board/queue is useful, but the live workbench should be the main interaction surface.

## Harness Optimization for Dogfooding

Because the prototype will eventually be used to build itself, the repo harness must be strong from the first iteration. Add/maintain:

- slim `AGENTS.md` with role boundaries, no-main-push, no-self-approval, PR loop, and merge authority
- `docs/spec.md` describing dashboard-first product thesis and architecture
- review role docs, e.g. `docs/review/codex-a-correctness.md` and `docs/review/codex-b-architecture.md`
- workflow docs for issue-to-PR, PR review loop, and merge readiness
- friction logs for agent/process failures and fixes

Key harness rule: project-specific behavior belongs in the project harness, not in repeated Hermes prompts.
