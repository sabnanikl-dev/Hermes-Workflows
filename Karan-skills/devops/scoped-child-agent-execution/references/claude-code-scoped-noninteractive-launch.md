# Claude Code Scoped Non-Interactive Launch

## Why the outer approval can fire

Hermes and Claude Code enforce separate permission layers. Claude's `--dangerously-skip-permissions` flag may be appropriate inside some disposable sandboxes, but its blanket-bypass semantics can cause Hermes' outer smart scanner to escalate the launcher. That does not mean the user must separately approve Claude by identity.

When the user already authorized the branch/PR workflow and does not want per-builder prompts, keep Hermes smart approvals enabled and narrow Claude's permissions instead.

## Known scoped pattern

Check `claude --help` first. For a trusted isolated worktree, a known non-interactive pattern is:

```bash
env -u GH_TOKEN claude \
  --model 'claude-opus-5' \
  --print \
  --no-session-persistence \
  --safe-mode \
  --permission-mode dontAsk \
  --allowedTools 'Read,Edit,Write,Glob,Grep,Bash(git *),Bash(gh *),Bash(npm *),Bash(node *),Bash(shasum *)' \
  --strict-mcp-config \
  --mcp-config /tmp/claude-empty-mcp.json \
  --system-prompt-file AGENTS.md \
  -- "$(</tmp/builder-prompt.md)"
```

`dontAsk` denies unlisted tools instead of waiting for an interactive approval. Adapt the allowlist minimally to the repository. For example, add a test runner or package manager only when the repo requires it; do not pre-authorize merge/deploy/destructive commands.

`--safe-mode` disables Claude customizations, so explicitly provide the repo's system instructions and an empty MCP config when isolation matters. Preserve OAuth/keychain authentication as needed; removing `GH_TOKEN` keeps reviewer/model prompts from inheriting a token environment variable, but `gh` may still use the host keychain when the authorized builder workflow permits GitHub operations.

## Timeout recovery

If the original blanket-bypass launch times out at Hermes approval:

1. Do not retry until the user responds when the tool explicitly says not to.
2. Explain the two permission layers and own the launcher mistake.
3. Do not request a redundant phrase such as “approve Claude” if the task was already authorized.
4. After the response, relaunch with the scoped pattern.
5. Confirm the background process started, then continue normal progress and exact-head verification.

## Verification

After the child exits:

- inspect `git status` and the full diff;
- run the required repository checks independently;
- verify local `HEAD` equals the remote branch head;
- verify the PR's `headRefOid` and commit list contain that head;
- read back any PR body/comment the child claims it posted;
- confirm merge/deploy did not occur unless separately authorized.
