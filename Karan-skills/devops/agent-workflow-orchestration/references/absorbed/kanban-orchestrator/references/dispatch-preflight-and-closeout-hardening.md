# Dispatch Preflight and Closeout Hardening

Session source: JMD-19 workflow postmortem (May 2026). Use this as a concrete pattern when hardening Kanban orchestration after invalid assignees, missing task-scoped skills, or PR/tracker closeout drift.

## Failure class

Observed failures:

- A task was created with conceptual assignee `frontend-eng`, which was not a configured Hermes profile.
- A reviewer child task crashed because it was dispatched with `--skills jmd-menswear`, but the `reviewer` profile could not load that task-scoped skill after role-native pruning.
- A builder task opened a PR, but Linear did not receive the final comment/status transition until default Hermes manually closed the loop.

## Deterministic fix shape

Use preflight checks before spawning a worker. Do not rely on model behavior or wait for the worker process to crash when the dispatcher can know the task is impossible.

Preflight checks:

1. Normalize the assignee with Hermes profile naming rules.
2. Verify the assignee exists in the configured profile roster.
3. Verify `kanban-worker` plus every task-scoped skill resolves exactly as the target profile would resolve CLI `--skills`.
4. If preflight fails, block the task with a clear comment/event rather than retrying a doomed worker.

## Important implementation detail

Do not approximate skill availability by scanning only `<profile>/skills`. Real Hermes skill loading can include:

- profile-local skills
- configured `skills.external_dirs`
- category/path identifiers
- legacy `.md` skills
- platform-disabled filtering
- plugin-qualified skill identifiers

When implementing a Python preflight, reuse the same resolver path used by CLI skill preloading. In the current codebase that means `agent.skill_commands._load_skill_payload()` / `build_preloaded_skills_prompt()` behavior, ideally via a small profile-scoped subprocess or a public resolver extracted from that code. This avoids false negatives that would block valid dispatches.

Robust subprocess pattern notes:

- Set `HERMES_HOME` to the target profile dir.
- Set `HERMES_PROFILE` to the normalized profile name.
- Set `cwd` to the Hermes agent repo root so `agent.skill_commands` imports reliably.
- Parse the last non-empty stdout line as JSON to survive incidental import logging.
- Keep the check read-only: no LLM calls, no network, no writes.

## Blocked-state wording

Use a deterministic, actionable block reason:

```text
KANBAN_PREFLIGHT_FAILED: This task cannot dispatch as configured.
Reason: task-scoped skill `jmd-menswear` is not installed/resolvable for reviewer.
Next action: default Hermes should inject a scoped excerpt, task-scope grant the skill if safe, reassign the task, or archive/cancel if human review supersedes automation.
```

## PR-to-tracker closeout checklist

When a worker completes a builder task that produced a PR, default Hermes/orchestrator should not treat the workflow as complete until tracker closeout is verified:

1. Read the builder task summary and metadata.
2. Extract PR URL/number and tracker issue identifier.
3. Verify the PR remotely (`gh pr view ... --json commits,state,mergeable,mergeStateStatus,url,title`).
4. Query child tasks; explicitly surface failed/blocked reviewer children.
5. Add a tracker comment with PR URL, changed scope, verification, and remaining human gates.
6. Move the tracker issue to review only after comment creation succeeds.
7. Re-query PR and tracker before reporting success.

Keep live GitHub/Linear mutation behind explicit approval unless the user has already authorized that exact closeout scope.
