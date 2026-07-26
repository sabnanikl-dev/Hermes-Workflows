# Claude Code Fix Prompt Template

> Used when Hermes spawns Claude Code CLI to address review findings.
> Fresh session every time.

```bash
env -u GH_TOKEN claude --model 'claude-opus-5' --print \
  --no-session-persistence \
  --permission-mode dontAsk \
  --allowedTools 'Read,Edit,Write,Glob,Grep,Bash(git *),Bash(gh *),Bash(npm *),Bash(node *),Bash(shasum *)' \
  --system-prompt-file AGENTS.md \
  "Checkout branch feat/issue-{ISSUE_NUMBER}.
   Read docs/spec.md for context.
   Fix these issues: {FINDINGS_LIST}.
   Run build and tests after fixes.
   Commit amend or new commit. Push.
   Post a comment on the PR summarizing what was fixed.
   The comment must end with:
   '---\nFixed by: Claude Code via Hermes orchestration\nPR: #{PR_NUMBER} | Issue: #{ISSUE_NUMBER}'
   At the very end of your output, print exactly:
   DONE: PR=<number> BRANCH=<branch> STATUS=success|failure"
```

## Rules
- Do NOT introduce new features while fixing
- Do NOT refactor unrelated code
- If a finding is a false positive, note it in the PR comment but don't "fix" it
- After fixes, run the same tests that failed (or full suite if unsure)
- Push with descriptive commit: `fix: address review feedback on {ISSUE_NUMBER}`
- Add signature to the fix comment on the PR
- Print completion marker at end of output

## Loop Termination
- One cycle = review + fix
- Max 2 cycles total (initial build + 2 review rounds = up to 3 reviews)
- If issues persist after 2 fix attempts, escalate to Karan
