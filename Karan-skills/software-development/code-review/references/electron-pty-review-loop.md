# Electron + PTY scaffold review loop checklist

Use this when reviewing a local desktop scaffold that exposes PTYs or process control from an Electron renderer.

## Review prompt pattern
Ask the reviewer for blocking-only output with file/line refs and a final marker:

```text
Review the current scaffold. Focus only on blocking issues before commit/push: Electron/PTY safety, BYOA role separation, repository hygiene, and build correctness. Do not modify files. Output only BLOCKING findings with file:line references, plus final line exactly: DONE: STATUS=pass|fail BLOCKING=<count>
```

Patch blockers, run the repo verification command, then re-review until:

```text
DONE: STATUS=pass BLOCKING=0
```

## Electron/PTY blockers to actively check
- Renderer must not pass arbitrary command/cwd directly to main process PTY spawn.
- IPC payloads need runtime validation in main, including fire-and-forget `ipcMain.on` handlers. Invalid payloads should be ignored/logged, not thrown through the main event listener.
- Dev server URLs must be restricted to trusted localhost before exposing privileged PTY APIs.
- PTYs should run in the selected project root or an explicitly allowed directory, not arbitrary renderer-provided cwd.
- PTY environment should be minimal/intentional; avoid blindly passing all of `process.env` where credentials may leak.
- Each PTY needs stop controls and kill-all on app quit/window close.
- Renderer reload/unmount/crash should stop or detach owned PTYs so sessions cannot continue invisibly.
- Replacement session races: if an old PTY exits after a new PTY starts for the same pane, its exit callback must not delete the new session mapping.
- Non-zero process exits must stay visible as failures unless the command contract explicitly defines that exit as success. Do not let an exit callback mark a failed one-shot reviewer/session `completed` or trigger success markers just because the process emitted an exit event.
- Workflow/state-machine reachability: when a UI or IPC handler has a start/restart button, compare its allowed statuses against the canonical transition table and fix-loop states. A common blocker is allowing `pr_opened`/`reviewers_running` but forgetting re-review states such as `reviewers_rerunning`, which makes fresh post-fix reviews unreachable while later synthesis remains possible.
- Start scripts should actually load the dev renderer (`VITE_DEV_SERVER_URL`/`NODE_ENV`) instead of silently falling back to stale/missing production files.

## BYOA checks
- Core shared types should use generic adapter kinds (`cli`, `mcp`, `acp`, `custom`) rather than vendor-specific adapters.
- Hermes/Claude/Codex names are acceptable in config defaults, docs examples, and display labels, but not as core abstraction names.

## Verification
- Run the repo's normal verification (`npm run build`, tests, etc.).
- If the normal build writes ignored artifacts, that is fine; confirm `.gitignore` excludes them before commit.
- For review-only temp builds, emitting to `/private/tmp` can validate main/renderer outputs without dirtying the working tree.
