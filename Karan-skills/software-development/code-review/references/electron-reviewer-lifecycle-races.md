# Electron reviewer/PTY lifecycle race review notes

Use this as a compact checklist when reviewing Electron agent-harness flows that launch reviewer/build agents, capture PTY output, and post GitHub marker comments.

## Durable race classes to check

1. **Run/root drift across awaits**
   - If a handler captures `run`, `projectRoot`, PR number, or selected project, then awaits a live call (`gh`, `git`, filesystem, network), re-confirm the current run id and selected root before any later side effect.
   - Side effects include spawning PTYs, writing artifacts, updating run state, emitting snapshots, and refreshing GitHub panes.

2. **Same-run relaunch drift**
   - Guarding only by run id/root is insufficient when the app allows idempotent relaunches inside the same run.
   - If sessions are replaced under stable pane ids (`reviewer_a`, `reviewer_b`), each launch needs an opaque per-launch token stored in the tracked session and closed over by async callbacks.
   - PTY `onData`, PTY `onExit`, and delayed `gh pr comment` result handlers should compare the current token to the captured token before patching state.

3. **Failure states must not collapse into green marker states**
   - Non-zero one-shot reviewer exits are session failures, not completed review sessions.
   - Capture failures and launch failures should remain visibly failed.
   - Operator overrides for marker comments should be allowed only for sessions that actually ran (`running`, clean `completed`, or already `comment_posted`), not `launching` or `failed`.

4. **State-machine launch edges must cover fix cycles**
   - If the workflow has `fix_pushed -> reviewers_rerunning -> synthesis`, the reviewer launch UI and IPC handler must accept the fix-cycle launch state, not just the initial `pr_opened` state.
   - Add regression tests for both initial launch and fix-cycle relaunch.

## Useful regression tests

- Launch reviewers from initial PR state and from fix-pushed state.
- Non-zero reviewer exit becomes failed and does not auto-post a marker.
- Manual marker post refuses failed/launching sessions.
- Async post result refuses to patch state after run/root change.
- Async post result refuses to patch state after same-run reviewer relaunch.
- Old PTY `onData`/`onExit` callbacks refuse to patch or post for a freshly relaunched session.
