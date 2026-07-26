# Claude Code Build Prompt Template

> Used when Hermes spawns Claude Code CLI via `terminal(command="...", pty=true)` for implementation work.
> Fresh session every time. No `--continue`.

```bash
env -u GH_TOKEN claude --model 'claude-opus-5' --print \
  --no-session-persistence \
  --permission-mode dontAsk \
  --allowedTools 'Read,Edit,Write,Glob,Grep,Bash(git *),Bash(gh *),Bash(npm *),Bash(node *),Bash(shasum *)' \
  --system-prompt-file AGENTS.md \
  "Read docs/spec.md for project context.
   Read issue #{ISSUE_NUMBER} (fetch via GitHub API).
   Start with git status to orient yourself.
   Run existing tests to verify baseline before touching anything.
   Create branch feat/issue-{ISSUE_NUMBER}.
   Implement per acceptance criteria.
   Run build and tests.
   Commit with descriptive message.
   Push and open PR.
   In the PR description, add this signature at the bottom:
   '---\nBuilt by: Claude Code via Hermes orchestration\nIssue: #{ISSUE_NUMBER}'
   At the very end of your output, print exactly:
   DONE: PR=<number> BRANCH=<branch> STATUS=success|failure"
```

## Rules Injected via AGENTS.md
- One task per PR
- No self-approval
- Cross-review required before merge
- Branch naming: `feat/issue-{N}` or `fe/cd-<description>`
- Search before implementing (use `rg`/`grep` to find existing code)
- No hardcoded hex colors, no console.log, no unused imports
- No arbitrary Tailwind values `[]` — extend config

## Fresh Session Checklist
- [ ] Read AGENTS.md (auto-loaded via `--system-prompt-file`)
- [ ] Read docs/spec.md for project context
- [ ] Read linked GitHub Issue for acceptance criteria
- [ ] Run `git status` to orient
- [ ] Run tests to verify baseline passes
- [ ] Search for existing similar code before writing new code
- [ ] Create branch from latest main
- [ ] Implement
- [ ] Run build + tests
- [ ] Commit + push + open PR
- [ ] Add signature to PR description
- [ ] Print completion marker
