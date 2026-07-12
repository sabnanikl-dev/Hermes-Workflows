# Antigravity / Claude status check for GodMode issue work

Use this when Karan asks what Claude was doing in Antigravity for a GodMode issue and does **not** ask you to take over or mutate GitHub state.

## Goal
Determine whether Claude/Antigravity has implemented, committed, pushed, or opened a PR for the issue, using tool-backed evidence rather than GUI vibes.

## Minimal workflow

1. Identify active Antigravity/Claude processes and their working directories:
   ```bash
   ps -ax -o pid=,ppid=,tty=,stat=,etime=,command= | grep -Ei 'Antigravity|Claude|claude|godmode' | grep -v grep
   lsof -a -p <claude-pid> -d cwd -Fn
   ```
2. Pick the Claude process whose cwd matches the relevant repo, e.g. `/Users/creator/godmode`.
3. Inspect repo status from that cwd:
   ```bash
   git status --short --branch
   git branch -vv --no-color
   git log --oneline --decorate -n 8
   git diff --stat origin/main...HEAD
   git diff --name-status origin/main...HEAD
   ```
4. Inspect GitHub issue and PR state:
   ```bash
   gh issue view <issue> --json number,title,state,labels,body,url,updatedAt
   gh pr list --head <branch> --state all --json number,title,state,url,headRefName,baseRefName,updatedAt
   git ls-remote --heads origin <branch>
   ```
5. If local work exists, run the repo’s verification commands before summarizing status when cheap and safe:
   ```bash
   npm test
   npm run build
   ```
6. Report separately:
   - active app/process status,
   - repo branch and local commit state,
   - pushed/PR state,
   - GitHub issue state,
   - verification results,
   - whether a next step requires approval.

## Pitfalls

- Do not confuse “Claude is running” with “Claude is actively working.” Check CPU/process state and repo state.
- Do not claim pushed from a local commit. Verify the remote branch or PR commit list.
- Do not create a PR, push, close an issue, or interact with Claude’s terminal unless Karan approved that mutation.
- macOS screenshot/computer-use probes may fail because of permission or display state. Prefer process cwd + git/GitHub evidence for status checks; use GUI only when the status cannot be inferred otherwise.
