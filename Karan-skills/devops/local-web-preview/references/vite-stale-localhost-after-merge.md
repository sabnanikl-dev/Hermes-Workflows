# Vite localhost still shows old content after a PR merge

Use this when a user says they merged a PR but `localhost:3000` does not show the change.

## Durable pattern

Root cause is often not browser cache or a failed merge. It is commonly that the running Vite server is serving a stale local checkout, feature branch, or pre-fetch `origin/main`.

## Investigation checklist

1. Verify GitHub/source truth first:
   - Fetch `origin main`.
   - Confirm the PR is actually merged with the REST/API merged boolean when relevant.
   - Confirm `origin/main` contains the expected content with `git show origin/main:path/to/file` or equivalent.

2. Inspect the running localhost process:
   - Find the process on the requested port, usually `lsof -nP -iTCP:3000 -sTCP:LISTEN`.
   - Inspect the command and working directory for that PID.
   - Compare that working directory's branch and HEAD to `origin/main`.

3. If the process is serving a stale checkout/branch:
   - Do not mutate or reset a working checkout that may contain another agent's work.
   - Create or reuse a clean preview worktree from `origin/main`.
   - Install dependencies there if needed.
   - Stop the old server on the port.
   - Start the dev server from the clean preview worktree.

4. Verify the rendered behavior, not just file contents:
   - Load `http://127.0.0.1:3000/`.
   - Interact with collapsed/accordion UI if the target text is hidden by default.
   - Confirm the text appears in the DOM after the required interaction.

## Example commands

```bash
REPO=/path/to/repo
PREVIEW=/path/to/worktrees/local-main-preview

cd "$REPO"
git fetch origin main --prune
git show origin/main:src/components/FAQ.tsx | grep -n -A2 -B1 'Do you do destination weddings'

PID=$(lsof -nP -iTCP:3000 -sTCP:LISTEN -t | head -1 || true)
if [ -n "$PID" ]; then
  ps -p "$PID" -o pid,ppid,command
  lsof -a -p "$PID" -d cwd -Fn | sed -n 's/^n//p'
fi

if [ ! -d "$PREVIEW/.git" ]; then
  git worktree add "$PREVIEW" origin/main -b preview/local-main
else
  cd "$PREVIEW"
  git fetch origin main --prune
  git checkout preview/local-main
  git reset --hard origin/main
fi

cd "$PREVIEW"
[ -d node_modules ] || npm ci

OLD_PIDS=$(lsof -nP -iTCP:3000 -sTCP:LISTEN -t || true)
[ -z "$OLD_PIDS" ] || kill $OLD_PIDS
npm run dev -- --port=3000 --host=0.0.0.0
```

## Pitfalls

- Do not report "the merge did not work" until GitHub and `origin/main` have been checked.
- Do not assume curling `/` will reveal text hidden inside accordions; use browser interaction or targeted DOM inspection after clicking.
- Do not `git reset --hard` the user's active working tree just to preview main; use a separate preview worktree.
