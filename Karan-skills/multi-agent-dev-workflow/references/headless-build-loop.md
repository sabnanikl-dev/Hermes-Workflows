<!-- Archived source skill consolidated into `multi-agent-dev-workflow` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: headless-build-loop
description: "Headless multi-agent build loop: Hermes orchestrates, Claude Code builds via CLI, Codex evaluates, Karan decides. Minimal context switching."
version: 1.0.0
author: Hermes Agent
---

# Headless Build Loop

**Goal:** Karan says "work on issue #42" → agents build → Karan says "go" → Hermes merges. Zero context switching.

**Created:** April 23, 2026 after reviewing Anthropic, OpenAI, and Ralph Wiggum harness research.

---

## The Loop

```
Karan (Telegram): "lets work on issue #42"
↓
Hermes: fetches issue, checks acceptance criteria, drafts if missing
↓
Hermes spawns Claude Code CLI → builds → opens PR
↓
Hermes reviews code
↓
Hermes spawns Codex CLI → technical review
↓
[if issues found]
  Hermes spawns Claude Code CLI → fixes → pushes
  ↓
  Hermes + Codex re-review
  ↓
  [loop until clean — max 2 cycles]
↓
Hermes sends Karan ONE summary message → Karan says "go" → Hermes merges
```

---

## Agent Roles

| Agent | Role | Mode |
|-------|------|------|
| **Karan** | Vision + taste. Says what to build. Approves final output. | Telegram only |
| **Hermes** | Orchestrator. Spawns agents, reviews code, runs QA, reports in plain English. | Headless |

## Repository Template

**Use `sabnanikl-dev/agentic-harness-template`** — the slim template with just `AGENTS.md` + `docs/` (spec.md, conventions/, design/, friction/). NOT `sabnanikl-dev/Agentic-dev` which is bloated with Next.js boilerplate.

The harness template is repo-agnostic. Populate `docs/spec.md` with project-specific context (stack, pages, design tokens, constraints) before spawning builders.
| **Claude Code** | Lead builder. Implements features. | Headless CLI |
| **Codex** | Technical evaluator. Catches type issues, logic bugs, anti-patterns. | Headless CLI |

**Key principle:** Generation and evaluation are separate. The builder never grades its own work.

---

## CLI Commands

### Build Session

```bash
env -u GH_TOKEN claude --model 'claude-opus-5' --print \
  --no-session-persistence \
  --permission-mode dontAsk \
  --allowedTools 'Read,Edit,Write,Glob,Grep,Bash(git *),Bash(gh *),Bash(npm *),Bash(node *),Bash(shasum *)' \
  --system-prompt-file <repo-root-process-file> \
  "Read docs/spec.md for project context.
   Read issue #N (fetch via GitHub API).
   Start with git status to orient yourself.
   Create branch feat/issue-N.
   Implement per acceptance criteria.
   Run build and tests.
   Commit with descriptive message.
   Push and open PR."
```

**Fresh session every time.** No `--continue`. Context loaded from files.

### Review Session

```bash
codex --yolo exec "Review PR #N.
   Check for: type issues, logic bugs, anti-patterns, security issues.
   Do NOT review design/taste — that's Hermes + Karan's job.
   Output only BLOCKING issues with file:line references."
```

**Fresh session.** No knowledge of the build process.

### Fix Session (if needed)

```bash
env -u GH_TOKEN claude --model 'claude-opus-5' --print \
  --no-session-persistence \
  --permission-mode dontAsk \
  --allowedTools 'Read,Edit,Write,Glob,Grep,Bash(git *),Bash(gh *),Bash(npm *),Bash(node *),Bash(shasum *)' \
  --system-prompt-file <repo-root-process-file> \
  "Checkout branch feat/issue-N.
   Read docs/spec.md for context.
   Fix these issues: [Codex findings + Hermes findings].
   Run build and tests after fixes.
   Commit amend or new commit. Push."
```

---

## Loop Rules

- **Max 2 review cycles.** If issues persist after 2 fix attempts, escalate to Karan.
- **Hermes can short-circuit.** If Hermes disagrees with a Codex finding (false positive), note it in the summary and don't force a fix loop.
- **Karan never reads code diffs.** Hermes synthesizes everything into one plain-English message.

---

## Review Layers

### Codex checks (technical)
- Type correctness (TypeScript strict mode)
- Logic bugs and edge cases
- Anti-patterns (any casts, magic numbers, tight coupling)
- Security (unsafe inputs, leaked keys, XSS vectors)
- Unused imports / dead code
- Build and test pass

### Hermes checks (synthesis + visual)
- Does the PR actually solve the issue?
- Are acceptance criteria met?
- Visual QA — browser screenshots of affected pages
- No console.log or debug code left in
- Code style consistency
- Cross-review synthesis

### Karan checks (taste + vision)
- Does it feel right?
- Does it match the brand?
- Is the UX what we intended?

**Karan never checks:** Type correctness, edge cases, whether tests pass.

---

## Acceptance Criteria as Contract

Every issue must have testable acceptance criteria. If it doesn't, Hermes drafts them and asks Karan to confirm before building starts.

**Good AC example:**
```
- [ ] Contact form renders on /contact route
- [ ] Name, email, message fields are required
- [ ] Form submits to Formspree endpoint
- [ ] Success state shows confirmation message
- [ ] Error state shows inline validation messages
- [ ] Mobile responsive (tested at 375px, 768px, 1440px)
- [ ] Uses femme-plum (#831654) for submit button
```

**Bad AC example:**
```
- Build a contact form
```

---

## Golden Principles (Anti-AI-Slop)

Mechanical rules. Enforced at every layer.

- No hardcoded hex colors — use design tokens
- No `console.log` in production code
- No unused imports
- No arbitrary Tailwind values `[]` — extend config
- No placeholder implementations — full implementations only
- Parse, don't validate — type safety at boundaries

---

## Context Hygiene

- **Fresh sessions per task** — no `--continue`, no compaction
- **Explicit file loading** — agent is told exactly what to read
- **Progressive disclosure** — don't dump the entire spec into context
- **Strip scaffolding as models improve** — every component encodes an assumption about what the model can't do

---

## When to Use IDE Instead

For UI-heavy work where live browser preview matters (new page designs, layout changes Amanda will judge), the lead dev may still run inside an IDE. In this case:
- Karan still opens the IDE to give the lead dev the issue
- Hermes still does visual QA and Codex review after PR opens
- All other rules apply unchanged

The headless CLI workflow is the default. IDE is the exception for visual-first work.

---

## Verification (Non-Negotiable)

### Post-Push
After ANY `git push`:
1. `gh pr view <N> --json commits`
2. Confirm new commit appears
3. If not, push failed silently — retry

### Post-Merge
After ANY merge:
1. `gh pr view <N> --json merged,state`
2. Confirm `"merged": true` and `"state": "closed"`
3. Verify commit landed on main
4. NEVER report "merged" without completing these steps
