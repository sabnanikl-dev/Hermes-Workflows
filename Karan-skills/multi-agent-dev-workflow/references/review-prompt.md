# Codex Review Prompt Template

> Used when Hermes spawns Codex CLI via `terminal(command="...", pty=true)` for technical code review.
> Fresh session every time. Codex has no knowledge of the build process or Claude Code's reasoning.

```bash
# Reviewer runs that must submit GitHub reviews should run without the Codex sandbox.
# Scope safety comes from the prompt: do not edit/commit/push/merge; only submit the review.
GH_TOKEN="$REVIEWER_TOKEN" codex exec --dangerously-bypass-approvals-and-sandbox \
  "Review PR #{PR_NUMBER}.
   Check for: type issues, logic bugs, anti-patterns, security issues.
   Do NOT review design/taste — that's Hermes + Karan's job.
   Output only BLOCKING issues with file:line references.
   Submit a GitHub PR review yourself using gh pr review or the GitHub Reviews API.
   The review body must end with this signature:
   '---\nReviewed by: Codex via Hermes orchestration\nPR: #{PR_NUMBER} | Issue: #{ISSUE_NUMBER}'
   At the very end of your output, print exactly:
   DONE: STATUS=pass|fail BLOCKING=<count> REVIEW_ID=<id-or-none>"
```

## Alternative: Safer Flag (if `--full-auto` still prompts)
```bash
codex exec --yolo \
  "Review PR #{PR_NUMBER}.
   Check for: type issues, logic bugs, anti-patterns, security issues.
   Do NOT review design/taste — that's Hermes + Karan's job.
   Output only BLOCKING issues with file:line references.
   Include a review comment with your findings.
   The comment must end with:
   '---\nReviewed by: Codex via Hermes orchestration\nPR: #{PR_NUMBER} | Issue: #{ISSUE_NUMBER}'
   At the very end of your output, print exactly:
   DONE: STATUS=pass|fail BLOCKING=<count>"
```

## What Codex Checks
- Type correctness (TypeScript strict mode)
- Logic bugs and edge cases
- Anti-patterns (any casts, magic numbers, tight coupling)
- Security (unsafe inputs, leaked keys, XSS vectors)
- Unused imports / dead code
- No arbitrary Tailwind values
- No hardcoded colors

## What Codex Does NOT Check
- Design/taste (Hermes + Karan)
- Brand consistency (Hermes + Karan)
- Whether ACs are met (Hermes)

## Review Output Format
Codex should output:
1. Summary line: "X blocking issues found" or "LGTM"
2. For each issue: `file:line` reference + description + severity
3. Signature block at the bottom
4. Completion marker on the last line
