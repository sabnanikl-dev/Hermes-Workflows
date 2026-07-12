# Vite PR branch preview checklist

Use when Karan asks to open a dev server for an unmerged PR branch.

## Why this matters

A PR preview should not mutate or depend on the main checkout. The main repo may have unrelated untracked files, active branch state, or another agent's work. Use a temporary worktree from the PR head, start a tracked background server, and verify the URL before reporting it.

## Checklist

1. Identify repo and PR branch/head SHA:

```bash
OWNER_REPO=$(git remote get-url origin | sed -E 's|.*github\.com[:/]||; s|\.git$||')
gh pr view <PR> --repo "$OWNER_REPO" --json headRefName,headRefOid,baseRefName,mergeable,mergeStateStatus
```

2. Create or refresh a temp worktree:

```bash
REPO=/path/to/repo
WT=/tmp/<repo>-pr<PR>-dev
BRANCH=<headRefName>
cd "$REPO"
git fetch origin main "$BRANCH" --prune
rm -rf "$WT"
git worktree add "$WT" "origin/$BRANCH"
cd "$WT"
git status --short --branch
```

3. Install dependencies only inside the worktree:

```bash
[ -d node_modules ] || npm ci
```

4. Pick a free Vite port, usually 5173+:

```bash
PORT=$(python3 - <<'PY'
import socket
for port in range(5173, 5195):
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1', port)) != 0:
            print(port)
            break
PY
)
```

5. Start the dev server as a Hermes-tracked background process:

```bash
npm run dev -- --host 127.0.0.1 --port "$PORT"
```

Use `background=true` with a watch pattern such as `Local:`. Do not use `nohup`, `&`, `disown`, or shell-level daemonizing; Hermes needs the process session id so it can be stopped later.

6. Verify the server responds before reporting:

```bash
for i in $(seq 1 20); do
  if curl -fsS --max-time 2 "http://127.0.0.1:$PORT/" >/tmp/pr-preview-index.html; then
    echo "ready=http://127.0.0.1:$PORT/"
    break
  fi
  sleep 1
done
```

7. Report exactly:

- URL: `http://127.0.0.1:<port>/`
- PR branch and worktree path
- background process session id
- note that you can stop it later

## Cleanup

When the user says to stop it, or before merging if the preview is no longer needed:

```bash
# Kill via Hermes process(action='kill') using the session id.
git -C "$REPO" worktree remove --force "$WT"
```

If the branch was merged with `--delete-branch`, remove the worktree after stopping the dev server so the deleted remote branch does not leave stale local preview state.
