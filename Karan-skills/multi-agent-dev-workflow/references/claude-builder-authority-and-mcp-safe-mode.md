# Claude builder authority + MCP-safe launch pattern

Session-derived note from a GodMode issue loop where Hermes accidentally implemented directly, the user corrected that Claude Code must be the builder, and the loop had to be restarted cleanly.

## Builder authority rule

For dogfood-quality `multi-agent-dev-workflow` runs, Claude Code must produce the implementation commits when the workflow says Claude is the builder. Hermes direct patches invalidate the clean builder/reviewer evidence unless the user explicitly approves an emergency workaround.

If Hermes has already implemented directly and the user rejects that path:

1. Stop treating the Hermes branch as usable evidence.
2. Delete the invalid local branch/worktree after explicit user instruction.
3. Verify no remote branch or PR exists for the invalid branch before reporting cleanup.
4. Create a fresh worktree/branch from current `main` with a Claude-owned prefix, e.g. `fe/cd-...`.
5. Relaunch Claude Code with a prompt that says the prior Hermes branch was deleted and must not be relied on.
6. Disclose the restart honestly if the PR history or session summary mentions it.

## MCP-safe Claude launch

When Claude Code repeatedly stalls behind a long-lived CodeGraph MCP child process, do not bypass Claude as builder. Relaunch Claude with MCP disabled but normal OAuth/keychain auth preserved:

```bash
env -u GH_TOKEN claude --model 'claude-opus-5' --print \
  --safe-mode \
  --strict-mcp-config \
  --mcp-config '{"mcpServers":{}}' \
  --permission-mode dontAsk \
  --allowedTools 'Read,Edit,Write,Glob,Grep,Bash(git *),Bash(gh *),Bash(npm *),Bash(node *),Bash(shasum *)' \
  --system-prompt-file AGENTS.md \
  -- "$(cat /tmp/builder-prompt.txt)"
```

Important details:

- Put a `--` separator before the prompt when using `--mcp-config '{"mcpServers":{}}'`. Recent Claude Code treats `--mcp-config` as variadic; without `--`, it can consume the prompt as another MCP config path and fail with `MCP config file not found: <prompt>`.
- Prefer `--system-prompt-file AGENTS.md` over `--system-prompt "$(cat AGENTS.md)"` for long GodMode builder/fix launches. Inlining the full harness creates huge process argv output, makes operator inspection noisy, and has produced launch attempts that sat idle until relaunched with `--system-prompt-file`.
- The empty MCP config must be shaped as `{"mcpServers":{}}`; `{}` can fail validation with `mcpServers: expected record, received undefined`.
- Keep `env -u GH_TOKEN` on builder/fix runs so a persisted reviewer token does not cause Claude to act as the reviewer identity.
- A quiet Claude `--print` run is not automatically hung. Check the worktree and process tree first. If files are changing, let it continue.
- This preserves the required builder role while avoiding the known long-lived `codegraph serve --mcp` stall.

## Review/fix loop discipline observed

When reviewers find blockers:

- Verify GitHub review objects exist before starting a fix cycle.
- Do not paste blocker prose into Claude's default fix prompt; point Claude to the live PR reviews/comments/threads.
- After Claude pushes, verify the new commit appears in `gh pr view <N> --json commits` before claiming the push.
- Re-run local gates and wait for CI on the new head before re-review.
- If the max review/fix cycle is reached, stop at a verified checkpoint instead of silently launching another cycle.
