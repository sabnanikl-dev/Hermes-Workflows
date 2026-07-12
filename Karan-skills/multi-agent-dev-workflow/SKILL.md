---
name: multi-agent-dev-workflow
description: "Multi-agent GitHub development workflow — headless CLI orchestration with cross-review, issue-based tracking, human-in-the-loop approval."
version: 2.0.0
author: Hermes Agent
---

# Multi-Agent Dev Workflow

## Umbrella Scope: Headless Multi-Agent Build and Review

This is the class-level skill for repo-centric multi-agent development: Hermes orchestration, Claude/Codex execution, headless build loops, cross-review, issue-based tracking, and human approval gates. The absorbed siblings now live as support references:

- `handling-codex-reviews`: how to process another agent's review comments, distinguish must-fix from optional feedback, and close the loop.
- `headless-build-loop`: how Hermes runs builder/reviewer agents repeatedly until quality gates pass.

Keep generic code-review checklists in `code-review`; use this skill for orchestration across agents and PR workflows.

Mode split:
- Use this umbrella skill for **issue-to-PR / end-to-end build orchestration**: scoping an issue, starting a builder, opening a PR, and supervising the whole workflow.
- Use `autonomous-pr-prover` for the narrower **existing-PR review/fix/re-review loop**: a PR already exists and the goal is to run independent reviewers, send unresolved blockers back to Claude Code, and verify merge-readiness without re-scoping the issue.

Support reference:
- `references/multi-agent-loop-leaning-2026-07-01.md` — Strategic Engineering NotebookLM critique of the current multi-agent workflow + PR prover split: lean root skills by offloading bulky historical pitfalls to references, add done-contract/rubric/budget experiments cautiously, and preserve PR bus, reviewer identity, current-head verification, and Karan approval gates.
- `references/godmode-dashboard-first-byoa.md` — use when designing or scaffolding QuadWork/tmux-style dashboard-first, bring-your-own-agent coding workflows where the harness is the source of truth and the PR review/fix loop runs automatically until merge-ready.
- `references/hermes-claude-codex-github-orchestration.md` — concise notes for the Hermes orchestrator + Claude Code builder + CodexReviewer reviewer pattern: hybrid manual/roll-call/webhook infrastructure, GitHub PR as coordination bus, separate reviewer identity, pointer-first blocker fix handoffs, and `.agentic/commands/` templates.
- `references/orchestration-loop-auth-pitfalls.md` — session-derived auth/validation pitfalls for loop tests: Claude Code `--bare` skips OAuth/keychain, expired OAuth can make `auth status` lie while calls 401, CodexReviewer `GH_TOKEN` checks, and the rule that Hermes fallback handoffs invalidate a clean dogfood-loop pass.
- `references/claude-code-setup-token-auth.md` — concrete Claude Code `setup-token` flow: diagnosing expired OAuth tokens, handling PTY-wrapped OAuth URLs for Telegram, and verifying with real `claude --print` calls rather than `auth status` alone.
- `references/claude-code-oauth-refresh.md` — preferred Claude Code auth repair path when `auth status` lies but model calls 401: normal `claude auth login --claudeai --email ...`, Telegram-safe URL/code handoff, and real smoke-test verification.
- `references/clean-loop-validation-checklist.md` — clean-pass/fallback criteria, identity gates, reviewer API submission fallback, and live GitHub readback checks for validating the full Hermes → Claude Code → CodexReviewer loop.
- `references/review-loop-cleanup-and-rerun.md` — how to clean up stale/process-invalid PR review state, dismiss superseded reviews without hiding audit history, rerun Reviewer A/B, and report fallback reviewer submissions honestly.
- `references/godmode-worktree-isolation-review-pitfalls.md` — GodMode worktree-isolation loop pitfalls: validate recorded worktree reuse paths, resolve verification commits from the run branch/worktree tip, guard clear-run cleanup authority, and checkpoint before spawning another fix cycle near tool limits.
- `references/stale-pr-head-worktree-refresh.md` — session-derived review/implementation checklist for current-head PR verification: `stale_head`, observed-head reconciliation, worktree-isolated GitHub refresh, bound-PR head selection, and adopt-current-head recovery.
- `references/godmode-loop-controller-review-pitfalls.md` — GodMode automatic review/fix loop controller pitfalls from issue #39: pointer-first Claude prompts, watcher failure halt behavior, async stage preemption after awaits, and targeted re-review loops.
- `references/electron-renderer-preview-visual-qa.md` — Visual QA pattern for GodMode/Electron renderer UI changes: Vite preview + browser screenshot/console as a layout/disabled-state check, while keeping real Electron smoke as the IPC/preload gate.
- `references/empty-data-component-visual-qa.md` — Pattern for frontend PRs that intentionally ship an empty public data artifact while the human needs screenshots of the populated UI: use a disposable localhost preview copy with clearly labeled temporary fixture data, disclose it, stop the server, then re-run canonical verification from the real PR worktree.
- `references/pr75-review-loop-lessons.md` — session-derived reviewer-loop pattern for dirty PR heads, stale native Node deps causing false local test blockers, disclosed fallback builder lanes, and current-head re-review closeout.
- `references/ab-reviewer-loop-mergeability-lessons.md` — session-derived A/B reviewer closeout pattern: a generic single Codex review is not enough, Reviewer A and B need distinct signed current-head outcomes, blockers require builder fix + same-lane re-review, and `latestReviews` can hide same-account role reviews.
- `references/codegraph-mcp-hang-and-budget-checkpoints.md` — session-derived operator pattern for silent Claude/Codex runs blocked on long-lived CodeGraph MCP child processes, plus review-loop budget checkpoint guidance.
- `references/claude-builder-authority-and-mcp-safe-mode.md` — recovery pattern when Hermes accidentally bypasses the Claude builder lane, plus MCP-disabled Claude launch syntax (`{"mcpServers":{}}`) that preserves builder authority while avoiding CodeGraph MCP stalls.
- `references/static-site-validator-and-timeout-closeout.md` — session-derived closeout pattern for static-site validator PRs: treat builder CLI timeouts as unknown state and inspect PR side effects before restarting, prove validators with negative mutations, avoid marker-name false positives in HTML comments, use same-origin iframe measurements for responsive CTA evidence, and wrap reviewer launches to avoid token/prompt quoting issues.
- `references/static-cms-build-render-review-pitfalls.md` — session-derived review checklist for static CMS build-render PRs: query/projector shape parity, JSON-LD script-context escaping, stale generated route cleanup, accidental binary/control-byte source files, and budget-safe closeout when fix lanes are still running.
- `references/current-head-rereview-and-local-sync.md` — session-derived closeout pattern for multi-commit review/fix loops: fast-forward the local worktree to the pushed PR head before verifying fixes, require A+B role-signed reviews on the current `headRefOid` after every follow-up commit, and do not treat fix comments as re-review evidence.
- `references/reviewer-network-failure-blocker-capsule.md` — recovery pattern when a reviewer identifies a real blocker but fails before posting the GitHub review/comment: preserve a clearly labeled fallback blocker capsule for the builder, require a signed fix comment, verify the push, then rerun A+B reviewers on the new current head.
- `references/fallback-builder-disclosure-and-doc-stewardship.md` — pattern for issue-to-PR runs where Claude Code/builder-profile lanes hang after partial drafts: disclose direct Hermes fallback provenance, salvage drafts only with explicit attribution, update stale “future work” docs when the PR lands that architecture, and rerun reviewers on the current head.
- `references/approval-gated-pr-evidence-and-screenshots.md` — pattern for PRs where repo-side work is merge-ready but the issue must stay open until an approval-gated live step: remove closing keywords from PR body and commit messages, verify `closingIssuesReferences` is empty, and provide honest repo-side screenshot proof when live UI evidence would require a deploy/dev-host/account mutation.
- `references/frontend-pr-visual-proof.md` — user-corrected proof pattern for frontend PRs: when Karan asks for screenshot proof, render the affected page/component at the exact PR head and show the changed UI/content, not merely GitHub PR status/checks.
- `references/static-site-responsive-visual-qa-browser-harness.md` — quick operator visual-QA pattern for static sites: create an uncommitted iframe harness with explicit viewport widths, verify DOM geometry/no overflow via browser console, screenshot/inspect the affected component, then delete the scratch file before final status/reviewer handoff.
- `references/static-carousel-fast-mount-pr-qa.md` — static/progressive-enhancement carousel PR pattern: remove full-feed preload gates, add fake-Image/timer fast-mount regression coverage, prove static fallback vs JS carousel replacement with DOM/browser evidence, and disclose when local `http.server` QA exercises committed static fallback rather than Vercel API routes.
- `references/human-design-review-after-agent-approval.md` — session-derived PR loop pattern: when Karan leaves a design/visual PR comment after A+B approvals, treat it as new source-of-truth input, send it through builder fix + visual QA + current-head A/B re-review; includes the CSS `aspect-ratio` + `min-height` mobile overflow pitfall from a static mini-map card.
- `references/static-faq-jsonld-visible-parity-qa.md` — static FAQ/GEO PR checklist: visible FAQ as source of truth, optional FAQPage JSON-LD parity, approval-gated issue-linking, targeted DOM/schema checks, browser fallback when cross-page JS fetch is blocked, and full review-surface readback when `latestReviews` hides one A/B lane.
- `references/review-loop-tool-budget-and-evidence-pitfalls.md` — session-derived closeout rules for PR review/fix loops near tool-call limits: do not launch a fix loop you cannot verify, wait for reviewer processes to exit before trusting review state, ensure screenshots actually show the changed component, and use synthetic fixture geometry QA for data-gated UI.

## When to Use

Karan says "work on issue #42". Hermes orchestrates Claude Code (builder) and Codex (reviewer) via headless CLI or a dashboard/workbench, reports back with a go/no-go summary, and preserves Karan's final approval/merge authority.

This skill is best for **Hermes-orchestrated repo-centric GitHub workflows** where Hermes directly runs Claude Code as builder and Codex as cross-reviewer from chat/terminal.

If the PR is already open and Karan wants only review → fix → re-review until merge-ready, load `autonomous-pr-prover` instead of carrying the full issue-to-PR flow.

### Hermes workflow vs GodMode workflow

Keep a clear distinction:

- **Hermes multi-agent-dev-workflow** is the current bootstrap workflow: Hermes is the active control tower, starts CLI agents, watches processes, verifies PRs, and reports to Karan through Telegram/Discord. Use it while GodMode itself is being built or when GodMode is not yet the chosen control surface.
- **GodMode workflow** is the target product workflow: GodMode becomes the durable dashboard/control surface for building GodMode and other repos. It should own run state, panes, process lifecycles, artifacts, reviewer/fix cycles, and operator visibility; Hermes supervises and synthesizes instead of acting as the execution substrate.
- During the transition, building GodMode with Hermes is dogfooding the *desired mechanics* (isolated worktrees, PR bus, reviewer loops), but do not confuse Hermes chat state with GodMode run state. When current blocking GodMode issues are closed, prefer operating through GodMode itself for future GodMode and external-project builds.

When designing or operating a QuadWork-like / tmux-like dashboard for Hermes-led builds, use the dashboard-first pattern in `references/dashboard-first-build-council.md`: Karan wants v1 to be dashboard-first, live-agent-pane oriented, and human-in-loop, with the project harness as source of truth and automatic PR review/fix loops after Claude opens a PR.

When the work is **consulting-operations or client-delivery oriented** — intake flows, client kanban, offer templates, and Codex-as-builder through Linear — use `codex-linear-consulting-operations` instead.

## Agent Roles

| Agent | Role | Primary Mode |
|-------|------|-------------|
| **Karan** | Vision + taste. Chooses/specs/delegates work, approves final output, and may merge to main himself. | Telegram or dashboard |
| **Hermes** | Head/operator. Reads issues, starts/supervises runs, synthesizes results, keeps Karan in the loop, and escalates risky/ambiguous decisions. | Hermes + dashboard pane |
| **Claude Code** | Lead builder. Implements from the issue + project harness, opens PRs, fixes blockers, and comments on PRs. | CLI subprocess / live pane |
| **Codex A** | Technical evaluator for correctness, tests, security, and regressions. | CLI subprocess / live pane |
| **Codex B** | Technical evaluator for architecture, maintainability, spec drift, and harness compliance. | CLI subprocess / live pane |

Key principle: Generation and evaluation are separate. Claude Code builds. Codex critiques. Hermes synthesizes. Karan decides.

For dashboard-first v1, each agent should be visible and directly addressable in a tmux-like pane. Karan should be able to chat/control Hermes, Claude Code, and each Codex reviewer while a run is active.

## Core Rules

1. ALL code requires cross-QA from the OTHER agent before merge
2. No self-approvals. Ever.
3. All work tracked via GitHub Issues (the task board), with Linear as parent/client tracker when applicable
4. Human gives go/no-go. Hermes may prepare/verify merge state, but Karan retains final merge authority unless he explicitly approves Hermes to merge.
5. **Self-review first** — the executing agent must review its own diff before opening the PR for cross-review.
6. **Automatic review/fix loop after PR open** — once Claude opens a PR, both Codex reviewers should automatically begin. If blockers exist, Claude Code (the builder/fix lane) fixes, comments, pushes, and triggers re-review until merge-ready or a stop condition fires. Hermes may patch directly only with explicit human approval or a clearly documented emergency workaround; otherwise direct Hermes fixes weaken dogfood evidence by bypassing the builder lane. If the user says Claude Code must be the builder after Hermes patched directly, discard/delete the Hermes-built branch/worktree when explicitly authorized and restart from a fresh Claude-owned branch; do not try to salvage the Hermes diff as clean workflow evidence.
7. **Visual QA before human review** — Hermes uses browser tools to screenshot/inspect the preview server and verify key pages before reporting to Karan when frontend/UI is affected. Screenshot proof must show the affected rendered page/section/component and changed content at the exact PR head, not just GitHub PR status/checks; see `references/frontend-pr-visual-proof.md`. For GodMode/Electron UI changes, a Vite renderer preview is acceptable for visual/layout/disabled-state sanity, but it does **not** replace `npm run smoke` when preload/main/IPC/PTTY wiring is touched; see `references/electron-renderer-preview-visual-qa.md`.
8. **One cycle = review + fix**. Max 2 cycles total (initial build + 2 review/fix rounds). Escalate to Karan if not resolved.
9. **Harness over prompt bloat** — the opened project harness, issue, PR, and comments are source of truth. Hermes should use short role commands and improve repo docs/harness when repeated context is needed.

## The Single Command Flow

```
Karan (Telegram): "lets work on issue #42"
↓
Hermes: fetches issue, checks acceptance criteria, drafts if missing
↓
Hermes runs Claude Code CLI (terminal pty=true) → builds → opens PR
↓
Hermes reviews code (reads diff via terminal/file tools)
↓
Hermes runs Codex CLI (terminal pty=true) → technical review
↓
[if issues found]
  Hermes runs Claude Code CLI → fixes → pushes
  ↓
  Hermes + Codex re-review
  ↓
  [loop until clean, max 2 cycles]
↓
Hermes sends Karan ONE message (via Telegram):
  "Issue #42 — Contact form. Codex found 2 things, both fixed.
   Build passes. No visual regressions. Recommendation: go."
↓
Karan: "go" → Hermes merges
```

Karan never opens: GitHub, Antigravity, terminal, or a code diff.

## Repository Knowledge Structure

Two files live at repo root. Everything else lives in `docs/`.

### AGENTS.md (slim — ~100 lines max)

General process bible. Applies to ANY project. Contents:
- Who does what (roles)
- Core rules (no self-approve, one task per PR, cross-review required)
- How to start a session (orientation sequence)
- How to commit and open a PR
- Branch naming convention
- Merge policy

AGENTS.md uses progressive disclosure — table of contents pointing to `docs/`, not a monolith.

**Important:** Hermes natively discovers AGENTS.md from the working directory and injects it into the system prompt. It also supports progressive subdirectory discovery. This means AGENTS.md is doing double duty:
1. Hermes reads it automatically as its project context
2. Claude Code reads it when you pass `--system-prompt-file AGENTS.md`

Both agents see the same rules. Write it tool-agnostic ("the implementing agent should...") rather than addressing a specific tool.

### docs/spec.md (project-specific, living document)

Project context. Contents:
- What the project is (1 paragraph)
- Tech stack + versions
- Design system reference (colors, typography, tokens)
- Current architecture overview
- Open issues / known blockers
- Links to detailed docs (design/, api/, friction/)

**Spec drift convention (Option B):** Every PR that changes architecture MUST update spec.md. A weekly cron checks if spec.md was modified in the last 7 days. If not, flag it for review.

### docs/ directory layout

```
docs/
├── spec.md                 # Living project context
├── design/                 # Brand guidelines, inspiration, screenshots
├── api/                    # API schemas, endpoints
├── friction/               # Running logs — what broke and how we fixed it
└── conventions/            # Code style, naming, golden principles
```

Rule: If knowledge lives outside the repo, it doesn't exist to the agent.

## Session Lifecycle (Headless)

Every agent session starts with explicit orientation. No auto-discovery. No hidden context.

## Execution Model

Claude Code and Codex CLIs are **synchronous** — they run to completion, print to stdout, and exit. Hermes knows they're done because the process returns. No webhooks needed for the manual MVP.

For durable orchestration infrastructure, prefer a hybrid trigger model rather than pure cron:

1. **Manual trigger first** — Karan or Hermes starts a specific GitHub issue loop explicitly. This proves prompts, worktree isolation, PR verification, reviewer identity, and fix loops before autonomy.
2. **Roll-call watchdog second** — a periodic 5–10 minute reconciliation loop reads the run ledger and live GitHub state, advances only deterministic safe transitions, and stays quiet unless actionable. It catches missed events, stale workers, absent reviews, red/stuck CI, and ready-but-unreported PRs.
3. **GitHub webhooks third** — once stable, use issue label, PR opened/synchronized, review submitted, and CI completed events as the primary wake-up path. Keep roll call as the fallback, not the brain.

Hermes/GodMode owns the run state machine and local ledger; GitHub Issues/PRs/reviews remain the task and review truth. Cron should not independently choose new work until manual and roll-call modes have proven reliable.

### Mode Selection

| Task Type | Mode | Timeout | Rationale |
|-----------|------|---------|-----------|
| Quick fixes (<20 lines) | Foreground | 300s | Fast, no overhead |
| New features, components | Background + notify | 600s | Hermes stays responsive |
| Full page builds, complex flows | Background + polling | 1800s | Progress updates for Karan |

### Foreground (default)

```bash
terminal(command="claude --model 'claude-opus-4-8[1m]' --print ...", timeout=300)
```

Hermes waits. When the process exits, Hermes reads stdout. Good for quick tasks.

### Background + notify

```bash
terminal(command="claude --model 'claude-opus-4-8[1m]' --print ...", background=true, notify_on_complete=true)
```

Hermes gets notified when the process finishes. Good for builds that take 5–15 minutes.

### Background + polling (long builds)

```bash
session = terminal(command="claude --model 'claude-opus-4-8[1m]' --print ...", background=true)
# Poll every 2 minutes, send Karan "still building..." updates
```

Good for complex features where Karan wants progress updates.

### Completion Markers

All prompts must include a machine-readable completion marker so Hermes can parse results without reading walls of output:

**Claude Code builds:**
```
At the very end of your output, print exactly:
DONE: PR=<number> BRANCH=<branch> STATUS=success|failure
```

**Codex reviews:**
```
At the very end of your output, print exactly:
DONE: STATUS=pass|fail BLOCKING=<count>
```

---

### 5.1 Claude Code Build Session

#### Claude builder model pin: Opus 4.8

For `multi-agent-dev-workflow` runs, every Claude Code builder and fix lane MUST be launched with the explicit model flag:

```bash
--model 'claude-opus-4-8[1m]'
```

Do not rely on Claude Code's default model or the generic `opus` alias for these runs. Quote the model value because `[1m]` is shell-glob syntax. If the exact Opus 4.8 model is unavailable, stop and report the model/auth blocker before falling back to another builder lane; do not silently use Sonnet/default Claude for the Claude builder.

#### Builder CLI readiness and fallback ladder

Before launching a build or fix lane, smoke-test the intended builder instead of assuming the CLI is on the Hermes process `PATH`:

1. Check `command -v claude` and `claude --version`.
2. If `claude` is missing, check common install locations, especially `~/.local/bin/claude`. In Hermes desktop/TUI sessions the terminal `PATH` may omit `~/.local/bin` even when Claude Code is installed. If a valid Claude Code binary exists there, repair the current Hermes execution path by either exporting `PATH="$HOME/.local/bin:$PATH"` for the builder command or creating a stable symlink into an already-present Hermes path entry, e.g. `ln -sf "$HOME/.local/bin/claude" "$HOME/.hermes/node/bin/claude"`. Then verify with `command -v claude`, `claude --version`, and a real pinned-model smoke: `env -u GH_TOKEN claude --model 'claude-opus-4-8[1m]' --print 'Smoke test only. Reply exactly: CLAUDE_OK'`.
3. If Claude Code is present but auth/model calls fail, follow the Claude auth references in this skill (`claude-code-oauth-refresh.md`, `claude-code-setup-token-auth.md`) and verify with a real `claude --print` call; do not trust `auth status` alone.
4. If Claude Code remains unavailable, do **not** let default Hermes silently become the builder. First try the role-native Hermes builder profile as the degraded substitute builder lane: `hermes -p builder chat -q 'Builder profile smoke test only. Reply exactly: BUILDER_OK' --toolsets '' --quiet`. If that passes, launch `hermes -p builder chat -q "$(cat /tmp/builder-prompt.md)" --quiet` from the isolated repo/worktree with the same issue/harness prompt, completion marker, verification requirements, and PR-bus rules. Sign the PR/comment as `Built by: Hermes builder profile via Hermes orchestration`, and report it as a **degraded builder-profile fallback**, not a clean Claude Code pass.
5. Only if both Claude Code and the builder Hermes profile are unavailable should default Hermes implement directly, and only with explicit human approval or a documented emergency workaround. That direct fallback must be disclosed in the PR body and final report.

#### Mid-run pivot after Hermes has already drafted changes

If Karan explicitly says to use `multi-agent-dev-workflow` after Hermes has already inspected the issue or made a small local draft, do **not** simply continue as a Hermes-built PR. Pivot into the workflow and preserve agent-role integrity:

1. Load this skill immediately and switch the task plan to builder/reviewer lanes.
2. Smoke-test Claude Code with a tiny pinned-model call (`claude --model 'claude-opus-4-8[1m]' --print ...`) before launching the build lane.
3. Prompt Claude Code as the **builder owner** and disclose that a Hermes draft diff may exist; instruct Claude to inspect it as input only, adjust/revert as needed, run verification, and commit the final builder-owned result.
4. Hermes may still create/push the PR after the builder commit, but the PR body must honestly state the builder lane and verification evidence.
5. Run both Codex Reviewer A and B against the opened PR/current head before saying mergeable.
6. If the builder lane cannot run and Hermes must finish directly, disclose that as a degraded/fallback run rather than a clean multi-agent workflow pass.

```bash
# Hermes runs this via terminal(command="...", pty=true)
# Keep OAuth/keychain auth, but disable user/project MCP for Hermes-managed builder runs.
printf '{"mcpServers":{}}' > /tmp/claude-empty-mcp.json
env -u GH_TOKEN claude --model 'claude-opus-4-8[1m]' --print \
  --no-session-persistence \
  --dangerously-skip-permissions \
  --strict-mcp-config \
  --mcp-config /tmp/claude-empty-mcp.json \
  --system-prompt-file AGENTS.md \
  -- \
  "Read docs/spec.md for project context.
   Read issue #42 (fetch via GitHub API).
   Start with git status to orient yourself.
   Run existing tests to verify baseline before touching anything.
   Create branch feat/issue-[#].
   Implement per acceptance criteria.
   Run build and tests.
   Commit with descriptive message.
   Push and open PR.
   In the PR description, add this signature at the bottom:
   '---\nBuilt by: Claude Code via Hermes orchestration\nIssue: #42'
   At the very end of your output, print exactly:
   DONE: PR=<number> BRANCH=<branch> STATUS=success|failure"
```

Fresh session every time. No `--continue`. Context is loaded from files, not from previous session state. Do **not** use `--bare` for Claude Code builder/fix runs unless you intentionally provide `ANTHROPIC_API_KEY` or an `apiKeyHelper`; Claude Code v2.1.x `--bare` skips OAuth/keychain reads and can falsely fail with `Not logged in` even when interactive/non-bare Claude Code is logged in. When using a separate reviewer `GH_TOKEN` in the same Hermes terminal session, invoke the builder with `env -u GH_TOKEN claude ...` unless you intentionally provide a builder-specific token; the terminal environment can persist exported `GH_TOKEN` across calls, causing Claude to open PRs as the reviewer account and invalidating the identity-split loop test. Prefer prompt files or carefully single-quoted prompts for long CLI prompts so shell backticks in instructions do not execute before the agent receives them. **Claude `--mcp-config` is variadic:** if a smoke/build command includes `--mcp-config <file>` and then an inline prompt, place `--` before the prompt; otherwise Claude may interpret the prompt text as another MCP config path and fail before the smoke/build starts.

## Codex Review Sessions (Reviewer A + Reviewer B)

When the user invokes `multi-agent-dev-workflow` for issue-to-PR work, run **both** Codex reviewer lanes before reporting merge-readiness unless the user explicitly authorizes a faster single-review path. A single generic `Codex via Hermes orchestration` review is **not** sufficient for an A/B loop.

Required split:

| Reviewer | Focus | Required signature |
|---|---|---|
| Codex Reviewer A | Correctness, tests, security, edge cases, regression risk | `Reviewed by: Codex Reviewer A via Hermes orchestration` |
| Codex Reviewer B | Architecture, maintainability, docs/spec drift, harness compliance, scope control | `Reviewed by: Codex Reviewer B via Hermes orchestration` |

Each reviewer must inspect the live PR and current head commit independently. Both must either submit a formal GitHub PR review or, if same-account/API limitations prevent another formal review, post a clearly signed PR conversation comment. Hermes must verify both surfaces against the current `headRefOid` before saying the PR is mergeable.

```bash
# Hermes runs this twice via terminal(command="...", pty=true or foreground): once for Reviewer A, once for Reviewer B.
codex exec --dangerously-bypass-approvals-and-sandbox "Review PR [#] as Codex Reviewer <A|B>.
   Focus area: <A correctness/tests/security/regressions OR B architecture/docs/harness/scope>.
   Check live PR metadata, current head commit, diff, issue AC, review objects/comments, and relevant tests.
   Do NOT review design/taste — that's Hermes + Karan's job.
   Output only BLOCKING issues with file:line references.
   Submit a GitHub review or signed PR comment whose body says whether the PR is mergeable from your lane.
   The body must end with this exact signature:
   '---\nReviewed by: Codex Reviewer <A|B> via Hermes orchestration\nPR: #[#] | Issue: #[#]'
   At the very end of your output, print exactly:
   DONE: REVIEWER=<A|B> STATUS=pass|fail BLOCKING=<count> MERGEABLE=yes|no"
```

- **Codex CLI Flags (Verified):**
- **Primary for PR reviewers that must submit GitHub reviews:** run Codex with normal shell access instead of the macOS sandbox, e.g. `codex exec --dangerously-bypass-approvals-and-sandbox ...` (or the current unsandboxed equivalent for the installed CLI). This is allowed for reviewer roles because they need reliable `gh pr review`/REST/GraphQL submission and the sandbox has caused false `GH_TOKEN`/`api.github.com` failures.
- **Use `--sandbox workspace-write` only** for review runs that do not need authenticated GitHub mutations or when deliberately testing sandbox behavior.
- **Custom reviewer prompts with base diffs:** Codex CLI v0.130.0 rejects `codex exec review --base <branch> <custom prompt>` (`--base` cannot be combined with a prompt). For role-specific A/B reviewer prompts, use regular `codex exec --cd <repo> --dangerously-bypass-approvals-and-sandbox "..."` and instruct Codex to inspect `git diff origin/main...HEAD` / live PR state itself. Use `codex exec review --base` only when the default review prompt is sufficient.
- **Deprecated/legacy:** Codex CLI v0.130.0 warns that `--full-auto` is deprecated; older installs may still accept it but prefer the explicit sandbox/unsandboxed modes above.
- **Avoid:** `--yolo` unless explicitly approved for a throwaway/sandboxed worktree; it bypasses all approvals and is less explicit than the modern unsandboxed flag.

Fresh session. Codex has no knowledge of the build process or Claude Code's reasoning.

### 5.3 Claude Code Fix Session (if needed)

**Default rule: PR feedback is the source of truth. Do not paste reviewer findings into the fix prompt.** The builder/fix agent must read the live PR review objects, review threads, inline comments, and conversation comments itself, then fix only unresolved blocking findings.

Hermes may include only identifiers and task boundaries (PR number, branch, issue number, cycle limit, verification requirements). Do not courier blocker prose unless the builder cannot access GitHub; if that fallback is necessary, label it explicitly as fallback data and treat the run as degraded.

```bash
env -u GH_TOKEN claude --model 'claude-opus-4-8[1m]' --print --dangerously-skip-permissions \
  --system-prompt-file AGENTS.md \
  "Checkout branch feat/issue-[#].
   Read docs/spec.md for context.
   Read the latest GitHub PR state for PR #[#]: review objects, review threads, inline comments, and conversation comments.
   Identify unresolved BLOCKING reviewer feedback only; ignore already resolved, outdated, optional, or non-blocking notes unless they reveal a direct regression.
   Fix only those unresolved blockers.
   Run build and tests after fixes.
   Commit a follow-up fix commit. Push.
   Post a PR comment summarizing which live PR blockers were fixed and what verification passed.
   The comment must end with:
   '---\nFixed by: Claude Code via Hermes orchestration\nPR: #[#] | Issue: #[#]'
   At the very end of your output, print exactly:
   DONE: PR=<number> BRANCH=<branch> STATUS=success|failure"
```

### 5.4 Loop Termination

- **One cycle = review + fix.** Max 2 cycles total (initial build + 2 review rounds = up to 3 reviews).
- If issues persist after 2 fix attempts, escalate to Karan: "This issue is hitting complexity we didn't anticipate. Needs your input."
- Hermes can short-circuit. If Hermes disagrees with a Codex finding (false positive), Hermes notes it in the summary and doesn't force a fix loop.

### 5.5 Hermes Subagent Delegation (read-only tasks)

For tasks that don't require Claude Code or Codex specifically, Hermes can use its native `delegate_task` to spawn subagents with isolated context. Best used for:

- **Parallel research**: Searching docs, checking upstream APIs, reading changelogs
- **Code analysis**: Scanning files for patterns, checking for regressions across modules
- **Summarization**: Condensing large diffs or test output before it enters the primary context

```python
# Example: Hermes delegates research while Claude Code builds
delegate_task(tasks=[
    {"goal": "Check if the Formspree API has changed since our last integration",
     "context": "We use Formspree for contact form submissions. Check their docs.",
     "toolsets": ["web"]},
    {"goal": "Scan frontend/ for any existing contact form components we should reuse",
     "context": "Project at /path/to/repo. Look for form components or patterns.",
     "toolsets": ["file"]}
])
```

Rule of thumb: `delegate_task` for reasoning-heavy read-only work. `terminal(pty=true)` for spawning Claude Code / Codex as external builder/reviewer processes.

### GitHub-as-artifact-bus fix cycles
When Claude Code is the builder and Codex/CodexReviewer leaves PR feedback, **Hermes must not paste reviewer findings into builder fix prompts by default.** The PR is the artifact bus and the source of truth.

Required pattern:
1. Reviewer agents submit their blocking findings to GitHub as PR reviews, review-thread comments, inline comments, or clearly signed PR conversation comments.
2. Hermes verifies those GitHub surfaces exist before starting the fix cycle.
3. The builder/fix prompt contains only the PR number, branch, issue number, and instruction to read the latest PR reviews/comments/threads and fix unresolved blocking findings only.
4. Builder comments back on the PR with exactly which live PR blockers were fixed and the verification run.
5. Hermes verifies the new commit, reruns reviewers, and reads GitHub surfaces again.

Hermes may normalize blocker text for synthesis/audit and may include a compact fallback blocker capsule **only** if the builder cannot access GitHub directly or the reviewer could not post to GitHub. Label that as fallback data, point back to the PR as authoritative, and report the run as degraded/fallback rather than a clean PR-bus loop. If a reviewer finds a real blocker but fails before posting it, follow `references/reviewer-network-failure-blocker-capsule.md`: preserve the exact actionable blocker as a fallback capsule, send it to the builder only with disclosure, require a signed fix comment, verify the follow-up push, and rerun both reviewers on the new current head before saying merge-ready.

### Separate reviewer GitHub identity
When practical, run CodexReviewer from a distinct GitHub account/token from the builder account. This enables real PR reviews/approvals or request-changes states and avoids same-account self-review limitations. CodexReviewer should usually have read + PR review/comment permissions and no content write/merge/deploy authority.

When using a macOS Keychain-stored reviewer PAT, fetch it only at process launch and inject it as per-process `GH_TOKEN` rather than exporting it globally. Smoke-test both identity and target-repo access before the reviewer run: `GH_TOKEN=*** gh api user --jq .login` and `GH_TOKEN=*** gh repo view <owner>/<repo> --json nameWithOwner,isPrivate`. A token can identify as the intended reviewer but still lack access to a private repo; in that case `REQUEST_CHANGES`/`APPROVE` will either 404 or fall back to the PR author's account, causing GitHub's same-author review rejection. Inside Codex CLI sandbox, `gh auth status` may incorrectly report `GH_TOKEN` invalid even when `gh api user` and PR reads work; trust concrete `gh api`/`gh pr view` smoke tests over `gh auth status` for that path. For loop-validation tests, the reviewer agent itself must submit the GitHub review; if Hermes submits the review body after Codex cannot, mark the run as a failed/fallback test rather than a clean loop pass. If Codex's `gh pr review` path repeatedly fails with a transient `api.github.com` transport error while `gh api` reads work, Codex may submit the review itself through `gh api -X POST repos/<owner>/<repo>/pulls/<pr>/reviews --input review.json` (`event: APPROVE` or `REQUEST_CHANGES`) and then verify the review via the reviews API. This is acceptable because the reviewer agent, not Hermes, performed the mutation.

Fallback review-submission pattern: when Codex has completed a re-review and produced an explicit pass/fail decision/body but cannot submit the GitHub review because of sandbox auth/network quirks, do not claim the approval/request landed. First save the exact prepared review body, then submit it from Hermes with a tiny wrapper that reads the reviewer PAT from Keychain, injects it only as that subprocess's `GH_TOKEN`, smoke-tests `gh api user --jq .login`, runs `gh pr review ... --body-file`, and immediately verifies `latestReviews`, `reviewDecision`, check status, and review threads. Report this as a disclosed fallback submission, not a clean reviewer-agent submission.

### Hermes-owned repo-local orchestration templates
For repo-local templates used by Hermes to dogfood the loop, prefer an explicit namespace such as `.agentic/hermes-orchestration/` instead of a generic `.agentic/commands/` folder. The folder README should state that these are Hermes operational templates, not product runtime commands or feature requirements, unless a scoped GitHub Issue explicitly asks for product support.

## PR Comment Signatures

Every agent action on a PR must be signed. Since Claude Code, Codex, and Hermes all act as `sabnanikl-dev` on GitHub, signatures create a readable audit trail.

### Signature Format

All signatures follow this pattern:
```markdown
---
<Action> by: <Agent> via Hermes orchestration
PR: #<N> | Issue: #<N>
```

### Where Signatures Go

| Action | Location | Example |
|--------|----------|---------|
| **Claude Code opens a PR** | Bottom of PR description | `Built by: Claude Code via Hermes orchestration` |
| **Claude Code pushes fixes** | New comment on PR | `Fixed by: Claude Code via Hermes orchestration` |
| **Codex reviews** | Review comment on PR | `Reviewed by: Codex via Hermes orchestration` |
| **Hermes merges** | Merge comment on PR | `Merged by: Hermes on behalf of Karan` |

### Rules

- Signatures go at the **bottom** of PR descriptions or comments
- Use the exact format above — consistent, machine-parseable
- If an agent cannot post a comment directly (e.g., Codex CLI has no GitHub API access), include the comment text + signature in its output, and Hermes will post it via `gh pr comment`
- Hermes should verify signatures exist when reviewing PRs

### Hermes Posting Comments

If an agent's CLI cannot post GitHub comments directly, Hermes posts on its behalf:

```bash
# Post review comment from Codex output
gh pr comment <N> --body "$(cat codex-review-output.md)"

# Post fix summary from Claude Code output
gh pr comment <N> --body "$(cat claude-fix-output.md)"
```

---

## Review Standards

### What Codex Checks (technical)
- Type correctness (TypeScript strict mode)
- Logic bugs and edge cases
- Anti-patterns (any casts, magic numbers, tight coupling)
- Security (unsafe inputs, leaked keys, XSS vectors)
- Unused imports / dead code

### What Hermes Checks (synthesis + visual)
- Does the PR actually solve the issue?
- Are acceptance criteria met?
- Visual QA — browser screenshots of affected pages
- No console.log or debug code left in
- Code style consistency
- Cross-review synthesis — reconciling Codex findings with Hermes's own review

### What Karan Checks (taste + vision)
- Does it feel right?
- Does it match the brand?
- Is the UX what we intended?

Karan never checks: Type correctness, edge cases, whether tests pass. That's the agents' job.

## Branch Naming

- Hermes: `fe/hermes-<description>`
- Claude Code: `fe/cd-<description>`
- Codex: `fe/codex-<description>`
- GPT agent: `fe/gpt-<description>`
- Urgent fixes: `hotfix/<description>`
- Integration (temporary): `preview/<name>` — only for consolidating multiple PRs, delete after merge

## PR Requirements

- Linked to a GitHub Issue
- Summary of changes and reasoning
- No unrelated refactoring in the same PR
- All changes tested before opening

## AI Slop Prevention (Harness Engineering Patterns)

Agents accumulate suboptimal patterns over time ("AI slop"). Prevent this with:

### Golden Principles (mechanical, not suggestions)
- No hardcoded hex colors — must use femme-* Tailwind tokens
- No `console.log` or debug code in production
- No unused imports in committed code
- No arbitrary Tailwind values `[]` — extend config instead
- Components follow existing naming conventions
- No placeholder implementations — full implementations only
- Parse, don't validate — type safety at boundaries
- **Search before implementing** — use `rg` / `grep` to check if similar code already exists

### Enforcement Layers
1. **Pre-write** — AGENTS.md + docs/ progressive disclosure teach conventions
2. **Pre-commit** — ESLint/Stylelint catch violations locally
3. **Pre-review** — executing agent self-reviews its own diff
4. **Cross-review** — other agent reviews the PR diff
5. **Visual QA** — Hermes screenshots key pages, catches visual regressions

## Communication Protocol

| Channel           | Purpose                                                       |
| ----------------- | ------------------------------------------------------------- |
| **Telegram**      | Human ↔ Hermes only. Issue creation, go/no-go, questions.     |
| **GitHub Issues** | Task tracking. Single source of truth for what's in progress. |
| **GitHub PRs**    | Code review between agents. Human sometimes may read these.   |
| **AGENTS.md**     | Process rules. All agents must read.                          |
| **docs/spec.md**  | Project state. Updated by agents as work progresses.          |

No Slack, no Notion, no Google Docs. If it's not in the repo or Telegram, it doesn't exist.

### PR as the Agent Coordination Bus

For GitHub-first coding workflows, treat the PR itself as the shared coordination layer between builder and reviewer agents:

- Prefer a separate GitHub identity for the reviewer agent (for example `CodexReviewer`) so reviews can be real GitHub `APPROVE` / `REQUEST_CHANGES` events instead of same-account synthetic comments.
- When review blockers exist, do **not** normally paste Hermes' summarized blocker text into the builder prompt. Prompt the builder to read the live PR reviews, review threads, inline comments, and conversation comments itself, then fix only unresolved blocking feedback.
- Hermes may include only a compact fallback blocker capsule when the builder cannot access GitHub directly; label it as fallback data and still point back to the live PR as source of truth.
- Hermes remains the adjudicator: classify reviewer findings as blocking, follow-up, false positive, or needs-human before advancing the run state, but keep durable coordination on GitHub rather than in private chat transcripts.

## Error Handling & Escalation

| Scenario | Action |
|----------|--------|
| Build fails after fix | Loop again (count toward max 2 cycles) |
| Codex and Hermes disagree | Hermes decides, notes it in summary |
| Issue ACs are unclear | Hermes drafts ACs, asks Karan to confirm |
| Max 2 review cycles exceeded | Escalate to Karan with context |
| Merge conflict on PR | **Auto-resolve trivial conflicts** (lockfiles, generated code). **For semantic conflicts**, escalate to Karan with a summary of what each branch changed and a recommended action. |
| Visual regression detected | Block merge, ask Claude Code to fix |
| Agent hangs or crashes | Kill process, restart fresh session |
| Claude Code CLI missing from `PATH` | Check common install locations (`~/.local/bin/claude` first), repair the Hermes execution path or per-command `PATH`, then verify `claude --version` and a real pinned Opus 4.8 smoke (`claude --model 'claude-opus-4-8[1m]' --print ...`) before falling back. |
| Claude Code installed but auth/model call fails | Follow the Claude auth refresh/setup references and verify with real `claude --print`; do not trust `auth status` alone. |
| Claude Code remains unavailable | Use the `builder` Hermes profile as the degraded builder lane if its smoke test passes; otherwise stop and ask/escale before default Hermes implements directly. |
| Codex CLI unavailable | First verify the binary path, not just `command -v`: Homebrew cask symlinks can go stale (`/opt/homebrew/bin/codex` exists but target under `/opt/homebrew/Caskroom/codex/<version>/` is missing). If the symlink is broken, repair with `brew reinstall --cask codex`, then smoke-test `codex --version` and a tiny `codex exec --dangerously-bypass-approvals-and-sandbox 'Smoke test only. Reply exactly: CODEX_OK'` before launching reviewers. If repair/auth still fails, report to Karan and suggest manual fallback or retry after install/auth repair. |
| Terminal backend timeout | Retry once with increased timeout, then escalate |

## Merge Conflict Resolution Policy

**Trivial conflicts (auto-resolve by Hermes):**
- Lockfiles (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`) — accept both and regenerate
- Generated code (build artifacts, `.d.ts` files, auto-generated API clients)
- Snapshot files (Jest, Playwright) — accept both and regenerate
- Import order conflicts in `src/App.tsx` where both sides added different imports — keep all

**Semantic conflicts (escalate to Karan):**
- Both branches modified the same business logic
- Both branches added different implementations of the same feature
- Component API changed in conflicting ways
- Database schema conflicts

When escalating, provide:
1. Branch names and PR numbers
2. Files with conflicts
3. Summary of what each branch changed in those files
4. Recommended action (which branch's approach is better, or whether to combine)

## CRITICAL: Post-Merge Verification (Mandatory)

After ANY merge API call (`PUT /repos/{owner}/{repo}/pulls/{n}/merge`):

1. **Parse the response body** — check for `"merged": true` in the JSON response
2. **If response is ambiguous or missing**, re-query: `GET /repos/{owner}/{repo}/pulls/{n}` and confirm `"merged": true` and `"state": "closed"`
3. **Verify the commit landed on main**: `GET /repos/{owner}/{repo}/branches/main` — the latest commit message should match
4. **NEVER report "merged" to the human without completing steps 1-3**
5. If merge fails (conflicts, branch protection, etc.), report the actual error state immediately — do not retry silently or claim success

This rule exists because a false "merged" report left the Femme Events repo in a broken state for 12+ hours. Trust erosion from false confirmations is the most damaging kind of agent error.

## CRITICAL: Post-Push Verification (Mandatory)

After `git push` to a PR branch, ALWAYS verify the commit landed on GitHub:

1. Run `gh pr view <N> --json commits --jq '.commits[] | .oid[:7] + " " + .messageHeadline'`
2. Confirm your new commit appears in the output
3. If it doesn't appear, the push may have failed silently or you may have pushed the wrong branch

Alternative: wrap verification in `execute_code` with structured error handling:

```python
import subprocess, json, sys

def verify_push(pr_number, expected_commit_msg_substring):
    try:
        result = subprocess.run(
            ['gh', 'pr', 'view', str(pr_number), '--json', 'commits'],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        commits = data.get('commits', [])
        for c in commits:
            if expected_commit_msg_substring in c.get('messageHeadline', ''):
                return {"verified": True, "commit_oid": c.get('oid', '')[:7]}
        return {"verified": False, "error": f"Commit '{expected_commit_msg_substring}' not found in PR #{pr_number}", "commits": [c.get('messageHeadline') for c in commits]}
    except subprocess.CalledProcessError as e:
        return {"verified": False, "error": f"gh CLI failed: {e.stderr.strip()}", "commits": []}
    except json.JSONDecodeError as e:
        return {"verified": False, "error": f"Invalid JSON from gh: {e}", "commits": []}
    except Exception as e:
        return {"verified": False, "error": f"Unexpected error: {str(e)}", "commits": []}

result = verify_push(42, "fix: address review")
print(json.dumps(result, indent=2))
```

This rule exists because a bug-fix commit was reported as "pushed" but only existed locally. The commit was lost when switching branches, and the buggy code was still on the PR.

## Verification via execute_code (Token Optimization)

For mechanical verification steps, use `execute_code` to collapse multiple tool calls into a single inference turn:

```python
import subprocess, json, sys

def verify_merge(pr_number):
    try:
        result = subprocess.run(
            ['gh', 'pr', 'view', str(pr_number), '--json', 'merged,state'],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        assert data.get('merged') == True, f"PR not merged: merged={data.get('merged')}"
        assert data.get('state') == 'CLOSED', f"PR not closed: state={data.get('state')}"
        return {"ok": True, "pr": pr_number, "state": data.get('state')}
    except AssertionError as e:
        return {"ok": False, "pr": pr_number, "error": str(e)}
    except subprocess.CalledProcessError as e:
        return {"ok": False, "pr": pr_number, "error": f"gh CLI failed: {e.stderr.strip()}"}
    except Exception as e:
        return {"ok": False, "pr": pr_number, "error": f"Unexpected: {str(e)}"}

print(json.dumps(verify_merge(42), indent=2))
```

## Integration Branch "Ship PR" Pattern

When Claude Code's follow-up fixes land on an integration branch (e.g., `preview/all-issues`) that contains all the latest work:

1. Check if the integration branch is missing code from any individual PR branch
2. If missing, merge the individual branch INTO the integration branch locally: `git merge origin/fe/cd-blog-infrastructure`, resolve conflicts
3. Push the updated integration branch to origin
4. Create ONE PR from the integration branch → main. In the body, list all issues it closes and note that it supersedes the individual PRs
5. Immediately close all the individual PRs as superseded after the ship PR merges
6. Delete all stale branches

This is cleaner than backporting fixes into individual PR branches and avoids merge-conflict chaos at merge time.

## Resolving Merge Conflicts on Integration PRs

When an integration PR (e.g., `preview/all-issues` → `main`) has conflicts because `main` moved forward after the PR was opened:

1. Clone the repo fresh to a temp directory
2. `git checkout <integration-branch>`
3. `git rebase main` — replay integration commits on top of current main
4. Resolve conflicts at each step (commonly `src/App.tsx` imports, `package.json` deps, `CLAUDE.md`)
   - For App.tsx: usually both sides added different imports/components — keep all of them
   - For package.json: usually both sides added different deps — keep all, validate JSON
   - For package-lock.json: merge both sides, or accept incoming and regenerate
5. `git push origin <branch> --force-with-lease`
6. Wait ~5 seconds, then re-check PR mergeable state via API
7. Only merge once `"mergeable": true` and `"mergeable_state": "clean"`
8. Follow Post-Merge Verification steps above

## Context Management

Context windows are the constraint. Structured files are the solution.

**Tactics:**
- Fresh sessions per task — no `--continue`, no compaction
- Explicit file loading — agent is told exactly what to read
- JSON for machine state — task tracking, progress (resilient to LLM corruption vs. Markdown)
- Progressive disclosure — don't dump the entire spec into context
- Subagent delegation for read-only tasks — keeps primary context clean
- Strip scaffolding as models improve — every harness component encodes an assumption about what the model can't do

## Friction Log → Skill Self-Improvement Loop

When Hermes hits a problem during the workflow:

1. **Document it** in `docs/friction/YYYY-MM-DD-<slug>.md` (what happened, what fixed it)
2. **Update the skill** via `skill_manage(action="patch")` if the fix changes the procedure
3. **Update AGENTS.md** if the fix is a new convention all agents need to follow

Example: Hermes discovers that Codex `--yolo` flag was deprecated in favor of `--auto-approve`.
- Friction log: "Codex --yolo failed. Used --auto-approve instead."
- Skill patch: Update `references/review-prompt.md` with new flag
- AGENTS.md: No change needed (it's tool-specific, not a convention)

## Pitfalls — Antigravity/Claude Code Specific

- **Do not disturb another agent's active worktree** — if Claude Code/Antigravity is actively working in the main checkout (e.g., `git status` shows modified files on `fe/cd-*`), do NOT switch branches, reset, stash, or edit files in that checkout. Instead create an isolated worktree from latest main:
  ```bash
  mkdir -p ~/projects/femme-events/worktrees
  git fetch origin main --prune
  git worktree add ~/projects/femme-events/worktrees/<task-slug> origin/main -b fe/hermes-<task-slug>
  ```
  Work, test, commit, push, and open the PR from the isolated worktree. Before reporting, verify the original checkout is still on the other agent's branch and clean except for that agent's expected files. This avoids clobbering Claude's local progress while Hermes handles unrelated issues in parallel.
- **Claude Code may leave changes uncommitted/unpushed** — during an Antigravity session, Claude Code can make local file changes that never get pushed to GitHub or opened as PRs. If the human says "I changed X but don't see it", check:
  1. `git status` on the local repo for uncommitted changes
  2. `git branch -a` for branches that exist on the Mac but not on GitHub
  3. `git stash list` for stashed work
  - Solution: Tell Claude Code in Antigravity to "commit everything, push to a new branch, and open a PR"
- **Claude Code uses preview/all-branches integration branches** — Claude Code often pushes follow-up fixes (font tweaks, sizing adjustments, text changes, palette updates) to a single integration branch like `preview/all-issues` instead of updating individual feature branches. If the human says "I worked on X today but don't see it in the PRs", check for `preview/*` branches on the repo. They contain the fully-integrated working state.
- **Don't backport fixes to individual PR branches** — when preview/all-issues (or similar integration branch) exists with all follow-up fixes across multiple features, DON'T ask Claude to backport changes into individual PR branches. Merge the integration branch as a single PR to main instead. It supersedes the individual PRs and is the cleanest path.
- **Antigravity MCP is not .env file access** — Claude Code in Antigravity should use its MCP-configured GitHub auth, NOT scrape local env files. That's a security boundary violation.
- **PR review via API blocked for same-account PATs** — if your classic PAT is under `sabnanikl-dev` and Claude Code pushes under the same account, you CANNOT approve PRs through the GitHub API (422: "Review Can not approve your own pull request"). Hermes must do manual review analysis and report to Karan for the go/no-go decision.

## Pitfalls

- **Silent external-agent runs are not automatically hung** — Claude Code `--print` can run for 10+ minutes with no stdout while still editing files, running CodeGraph MCP, installing deps, or executing verification. Before killing/restarting a quiet builder, inspect the worktree (`git status --short --branch`, `git diff --stat`) and process tree/CPU to confirm whether progress is happening. If files or verification artifacts are moving, let it continue. If the only active child is a long-lived CodeGraph MCP server (for example `npm exec @colbymchenry/codegraph ... serve --mcp`) and the worktree is otherwise idle, terminate that child process first rather than killing the builder; this can let the builder continue and finish. If the same builder relaunches CodeGraph MCP and remains idle despite an explicit bounded-CodeGraph/no-MCP instruction, stop the builder attempt, disclose the run as degraded/not a clean Claude-builder dogfood pass, and either restart with the approved builder-profile fallback or implement directly only when necessary with later independent review. Do not assume `claude --mcp-config '{"mcpServers":{}}'` or an empty MCP config file will suppress repo/user/plugin-spawned CodeGraph in every Claude Code install; user-scoped MCP servers can still load unless `--strict-mcp-config` is set. For JMD/static-site builder runs where CodeGraph has stalled, prefer `--strict-mcp-config --mcp-config /tmp/jmd-empty-mcp.json` with `{ "mcpServers": {} }`, then verify by checking child processes and worktree progress. For CodeGraph evidence after an MCP hang, prefer bounded CLI commands (`codegraph init`, `sync`, `query/impact`) with explicit timeouts and record limitations honestly. See `references/codegraph-mcp-hang-and-budget-checkpoints.md`.
- **Do not misclassify buffered/silent builder output as a hang** — Full issue-to-PR builds such as JMD Sanity/static-site endpoint work can exceed a 600s foreground terminal timeout, and `claude --print` / `hermes -p builder --quiet` may buffer useful output until the run exits. A foreground timeout (`exit 124`) or 2–3 minutes of no stdout is not root-cause evidence. For large builds, start the Claude Code builder in background with `notify_on_complete=true` and a 20–30 minute budget, poll worktree/process state every few minutes, and only kill after proving no file/test/process progress. If Claude Code is the intended builder, do not fall back to the Hermes builder profile merely because output is quiet; first verify: process still alive vs exited, child process tree, CPU activity, `git status --short`, `git diff --stat`, new files/artifacts, and test/build subprocess activity. Karan has specifically corrected this failure mode: premature Claude termination weakens the multi-agent workflow and should be treated as an operator mistake unless the evidence shows a true stall. If `--safe-mode` is used without `--dangerously-skip-permissions`, Claude may stop on `gh`/shell approval prompts in non-interactive `--print`; for trusted isolated builder worktrees use `--dangerously-skip-permissions` plus `--strict-mcp-config`, or run in a PTY where approvals can be answered.
- **Refresh native Node deps before treating native-backed test failures as code blockers** — In Electron/Node repos with native modules (`better-sqlite3`, `node-pty`, etc.), local test failures can come from stale ABI/native builds after Node changes rather than PR code. If failures point at backend selection/load behavior or native modules and seem unrelated to the diff, run `npm ci --silent` once, then rerun the exact verification before posting/accepting the blocker. If it still fails after dependency refresh, treat it as real. See `references/pr75-review-loop-lessons.md`.
- **Do not start another fix/re-review cycle unless you can verify it** — In long review/fix loops, especially near the chat/tool-call ceiling, stop at a verified checkpoint before spawning another builder or reviewer. A launched fix/re-review that finishes after the operator loses tool access leaves the PR in an unknown state. Before each new cycle, confirm you still have enough budget to: observe the builder/reviewer completion markers, inspect the resulting diff, verify local `HEAD` vs PR `headRefOid`/commit list, rerun required tests/build, read GitHub review objects/comments, launch and observe required re-reviewers, and synthesize the go/no-go. Treat a fix cycle as incomplete until re-review has been launched and read back; having a verified fix commit plus prepared reviewer prompts is only a checkpoint, not a clean loop closeout. If not enough budget remains for the complete fix→verify→re-review→synthesis sequence, report the exact verified checkpoint and next commands instead of launching the cycle. If a hard tool-call ceiling or user stop arrives mid-cycle, do **not** claim the fix landed; state the last verified PR head/review state and mark any running builder result as unknown until inspected. See `references/review-loop-tool-budget-and-evidence-pitfalls.md`.
- **For current-head PR verification, worktree isolation changes what “observed PR head” means** — Do not rely only on the active PR derived from the primary checkout branch. In GodMode worktree-isolated runs, the bound run branch lives in the run worktree, so a GitHub refresh must reconcile the bound PR by PR number/branch using a PR list or direct PR fetch that includes `headRefOid`. Otherwise `VerificationPane` can keep showing old green evidence after a follow-up push. Require tests for repo-wide pull-list head selection and observed-head drift without manual reverify. See `references/stale-pr-head-worktree-refresh.md`.
- **Correct stale verification evidence after independent reruns** — Builder/reviewer summaries can contain stale pass counts or copied verification text (for example, `npm test` counts changing after new tests land). After Hermes reruns verification, compare the PR body/comments against the real output. If PR metadata claims the wrong command result, edit the PR body and/or add a signed correction comment before reporting go/no-go; do not leave known-false verification evidence in the PR even when the code itself is good.
- **Do not overclaim preview/API smoke when deployment URLs return HTML** — Vercel PR preview URLs from comments can be branch/root preview links, feedback/auth shells, or otherwise not the exact API route under test. If an endpoint smoke like `/api/testimonials` returns HTML instead of JSON, report the preview smoke as blocked/inconclusive, keep repo validators/checks as the verified evidence, and leave the live/post-merge smoke as a gated follow-up. Do not convert a non-JSON preview response into either “endpoint failed” or “endpoint passed” without inspecting the actual deploy routing/source.
- **When a PR turns future-scoped docs into landed architecture, update the docs before closeout** — Data paths, endpoints, components, schemas, and validators often have nearby docs that say “future issue #N will supply this.” When implementing that issue, search related component/API/spec docs for stale future-tense handoff language and update it in the same PR. If an evaluator flags this as a blocker, patch the source doc, rerun verification, push a follow-up commit, verify the PR head, comment with the fix evidence, then rerun the reviewer lane on the current head. See `references/fallback-builder-disclosure-and-doc-stewardship.md`.
- **Direct Hermes completion after builder-lane hangs is fallback work, not clean dogfood evidence** — If Claude Code and the approved builder-profile fallback hang or timeout after producing a partial draft, Hermes may finish the repo-side implementation only with explicit provenance. Salvage the draft as implementation input, but disclose in the PR body/final report that Hermes direct fallback completed the work and do not claim a clean Claude/builder-lane pass. See `references/fallback-builder-disclosure-and-doc-stewardship.md`.
- **Sanity Studio localhost visual QA can be gated by project host registration** — When `sanity dev` loads a “Connect this studio to your project” screen for `localhost`/`127.0.0.1`, do not click “Register studio” or “Add development host” without explicit human approval; those are Sanity project/account mutations. Prefer deterministic offline desk/schema evidence (for example a script that renders/asserts the desk tree), capture/report the registration screen as the reason browser QA is blocked, and leave live Studio host registration/deploy as a gated follow-up.
- **`gh pr view --json latestReviews` is not sufficient review evidence** — when reviewers post comment reviews rather than approvals/request-changes, `latestReviews` may be empty even though review objects exist. Also, when Reviewer A and Reviewer B use the same GitHub account/token, `latestReviews` can collapse to only the account's latest review and hide the other role-signed review, even when both formal reviews exist on the current head. A reviewer process may also submit an early approval/comment and then continue running to a later final `REQUEST_CHANGES`; do not trust intermediate GitHub review state while the reviewer process is still running. For loop closeout, first wait for every reviewer process to exit and read its `DONE:` marker, then verify all review surfaces: `gh api repos/<owner>/<repo>/pulls/<N>/reviews` filtered by current `commit_id` and role-signature lines, `gh api repos/<owner>/<repo>/pulls/<N>/comments`, regular PR comments, GraphQL review threads, and `reviewDecision`/checks before declaring “0 blockers” or “A+B approved”. See `references/review-loop-tool-budget-and-evidence-pitfalls.md`.
- **Do NOT push work to main** — only merge PRs after cross-QA + human approval
- **Approval-gated issues must avoid closing keywords everywhere** — If a PR ships repo-side work but the issue should remain open until a later human-approved live/deploy/account step, remove `Closes`/`Fixes`/`Resolves` not only from the PR body but also from every commit message before merge. GitHub can close issues from commit-message closing keywords when commits land on the default branch via merge/rebase. Use `Refs #N`, verify `closingIssuesReferences` is empty, and scan `git log origin/main..HEAD --format='%s%n%b'` for closing keywords before requesting re-review.
- **When asked to “work on” an already-open issue, check for existing merged repo-side PRs before spawning builders** — Some issues intentionally remain open after a merged PR because the final AC is an approval-gated live smoke/content mutation/deploy. Before launching Claude/Codex for a new branch, inspect PRs mentioning the issue plus the issue timeline. If a repo-side PR is already merged with `Refs #N` and no closing refs, do not duplicate the work: verify the merge, rerun the relevant local validators/tests from current `origin/main`, inspect prior A/B reviews, smoke any non-mutating live endpoint/rendered UI evidence that is safe, then report the issue as “repo-side complete; still open only for gated live/manual AC” with a close-or-keep-open recommendation.
- **Do NOT create code without an Issue** — every PR must trace back to a task
- **Hermes should never self-approve** — always wait for Claude Code review
- **Do NOT include multiple unrelated changes in one PR** — one task, one PR
- **Check integration branches** — Claude Code may push an integration branch (like `preview/all-issues`) that contains all fixes but might miss some features from individual PRs. When reviewing, check both: individual PRs AND any integration branches. The integration branch is the ground truth for what Karan actually saw.
- **Claude Code should NEVER read files outside the repo** (like local env files). If it does, that's a security violation. GitHub auth should work via MCP server.
- **PAT limitations** — A GitHub PAT with `repo` scope cannot approve PRs from the same account. PR reviews fail with "Review Can not approve your own pull request." Claude Code and Hermes both act as `sabnanikl-dev`, so automated approvals won't work.
- **Review before merging** — Claude's PRs don't capture all changes Karan saw locally. Follow-up fixes (font glyphs, sizing tweaks, CTA changes, palette updates) often live on separate integration branches. Always check for those before reviewing.
- **Fine-grained PATs cannot create PRs** — they can create/delete issues but PR creation returns 403 "Resource not accessible". Use a classic PAT with `repo` scope.
- **Branch protection on personal repos requires GraphQL** — the REST `PUT /branches/main/protection` API always fails for personal (non-org) repos due to org-only `restrictions` parameter. Use the GraphQL `createBranchProtectionRule` mutation with `repositoryId`.
- **Claude Code is not a real GitHub user** — cannot assign Issues to it directly, use `assigned:claude-code` label instead
- **PR conflicts from stale base branches** — if a PR was created before a file existed on main (e.g., PR adds CLAUDE.md to a repo that already has CLAUDE.md from a prior merge), it will show "dirty" mergeable_state. Fix by:
  1. Close the stale PR
  2. Create a new branch from `main`, apply just the new changes
  3. Open a fresh PR
- **Nested repo paths with spaces** — user's repo lives at `~/projects/femme-events/website/Femme Events Website Build/Femme-Events-Website/`. The outer folder sometimes has a stray `.git` folder from a prior init that tracks everything (bloated). Fix: delete the outer `.git` (`rm -rf "Femme Events Website Build/.git"`). Git should only live inside the inner `Femme-Events-Website/` directory.
- **End-Session Protocol** — `.claude/skills/end-session-audit.md` exists in the repo as a mandatory checklist all lead dev agents must run before signing off. It catches orphaned branches, unlinked commits, and unpushed changes. Hermes should verify it was run when reviewing PRs.
- **Contaminated branch fix: cherry-pick onto clean branch** — When another agent's feature branch includes your commits from a different PR (because they branched from your un-merged branch), their PR becomes contaminated with unrelated + potentially buggy code. Do NOT merge the contaminated PR. Instead: (1) close the contaminated PR with an explanation, (2) cherry-pick only the relevant commit(s) onto a fresh branch from current main, (3) open a clean PR with just the intended changes.
