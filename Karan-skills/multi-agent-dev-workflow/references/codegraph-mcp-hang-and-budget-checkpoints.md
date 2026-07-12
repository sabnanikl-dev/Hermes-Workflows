# CodeGraph MCP child hangs and review-loop budget checkpoints

Session-derived note from a GodMode issue/PR loop.

## Symptom

A Claude Code builder/fix run can appear silent while it has spawned a long-lived CodeGraph MCP server child process, e.g. `npm exec @colbymchenry/codegraph@... serve --mcp`. The main Claude process may continue waiting with no stdout and no file progress.

## Operator pattern

1. Before killing the builder, inspect the process tree and worktree:
   - `pgrep -P <builder-pid> -l`
   - `ps -o pid,ppid,stat,etime,%cpu,%mem,command -p <child-pids>`
   - `git status --short --branch && git diff --stat`
2. If a long-lived CodeGraph MCP server is the only active child and the worktree is otherwise idle, kill the CodeGraph child process, not the builder.
3. Wait for the builder to resume and finish. In the observed run, killing the MCP child allowed Claude Code to continue, complete verification, push, and print the required completion marker.
4. In future builder/reviewer prompts, prefer bounded CodeGraph commands or explicitly warn: do not leave a long-lived CodeGraph MCP server running; if CodeGraph hangs, continue with source/diff inspection and disclose that limitation.

## Budget checkpoint pattern

Do not start fresh re-review agents near the tool-call/session ceiling unless there is enough remaining budget to read their completion markers, verify GitHub review objects, and synthesize the final go/no-go. If budget is low, stop at a verified checkpoint: pushed commit, PR URL, verification output, and exact next commands for the follow-up session.
