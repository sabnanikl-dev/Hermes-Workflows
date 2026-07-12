---
name: kanban-worker
description: Pitfalls, examples, and edge cases for Hermes Kanban workers. The lifecycle itself is auto-injected into every worker's system prompt as KANBAN_GUIDANCE (from agent/prompt_builder.py); this skill is what you load when you want deeper detail on specific scenarios.
version: 2.0.0
metadata:
  hermes:
    tags: [kanban, multi-agent, collaboration, workflow, pitfalls]
    related_skills: [kanban-orchestrator]
---

# Kanban Worker — Pitfalls and Examples

> You're seeing this skill because the Hermes Kanban dispatcher spawned you as a worker with `--skills kanban-worker` — it's loaded automatically for every dispatched worker. The **lifecycle** (6 steps: orient → work → heartbeat → block/complete) also lives in the `KANBAN_GUIDANCE` block that's auto-injected into your system prompt. This skill is the deeper detail: good handoff shapes, retry diagnostics, edge cases.

## Task contract discipline

At the start of every Kanban run, read the task body and restate the practical contract to yourself before editing:

- **Workspace mode**: `read_only`, `scratch`, `worktree`, or `dir_serial` if provided.
- **Output scope**: `base_template`, `task_harness`, `skill_library`, `linear_comment_draft`, or `github_pr` if provided.
- **Allowed paths** and **forbidden paths**.
- Whether the output must stay generic.
- Whether client-specific or issue-specific content is allowed.

If the task body does not include these fields, infer the safest version and say so in your completion summary. For reusable templates, default to generic output: no client names, Linear issue IDs, pilot-specific status files, or one-off reviewer verdicts. For cloned task harnesses, task-specific outputs belong under the task's documented `outputs/`, `evidence/`, or task docs.

Do not write outside declared allowed paths. If a needed change falls outside scope, comment/block instead of expanding scope silently. If you are in a shared persistent Git repo and see unrelated uncommitted changes, do not sweep them into your commit unless the task explicitly says to integrate sibling work.

### Missing skill behavior

If the task appears to require a skill that is not loaded or provided:

1. Check whether the task body lists it under `Required skills` or includes an excerpt.
2. If not, comment/block using this exact shape so default Hermes can auto-triage it:

```text
MISSING_SKILL_REQUEST: skill=<skill-name>; dangerous=<yes/no>; reason=<one sentence>
```

3. Mark `dangerous=yes` if the skill enables or strongly implies live/client/account mutation, credential changes, deployment, outreach, purchases, external/client-facing messages, destructive data operations, or permanent profile allowlist broadening.
4. Do not self-install hub/third-party skills, broaden your profile, or proceed by guessing.
5. If the skill implies a different role, ask for reassignment instead of requesting more access.
6. If the skill is sensitive/client/account-specific, ask default Hermes for a scoped excerpt.

Default Hermes is allowed to grant non-dangerous missing skills task-scoped without asking Karan, then unblock/retry the work. Dangerous requests must stay blocked until default Hermes/Karan explicitly approves the risky scope. For the orchestrator-side policy and watchdog pattern, see `kanban-orchestrator/references/profile-skill-access-policy.md`.

### Native skill self-improvement loop

You may create or patch a local Hermes skill when your assigned work produces a genuinely reusable, project-agnostic workflow or troubleshooting procedure. This is part of Hermes' native self-improvement loop, not profile allowlist broadening.

Rules:
- Prefer patching an existing relevant skill over creating a near-duplicate.
- Keep skills generic and portable: no secrets, credentials, private client data, raw task context, one-off tracker IDs, or stale PR/issue numbers.
- Use `skill_manage(action='create')` for new local skills and `skill_manage(action='patch')` for small improvements.
- Load/use `hermes-agent-skill-authoring` when drafting or validating a skill.
- Do not install third-party/hub skills, publish skills, edit repo-shipped skills, change profile allowlists, or change toolsets unless the task explicitly authorizes it.
- Mention any created/patched skill in your completion handoff for default Hermes review.

Skills are playbooks/context; tools are capability. Receiving or creating a skill never grants permission to use forbidden tools, deploy, merge, write memory, or mutate live/client accounts unless the task contract explicitly allows it and approval exists.

Include the contract in `kanban_complete` metadata when possible:

```python
kanban_complete(
    summary="updated generic preflight template; no client-specific artifacts added",
    metadata={
        "workspace_mode": "worktree",
        "output_scope": "base_template",
        "changed_files": ["preflight.md", "README.md"],
        "generic_template_check": "pass",
        "forbidden_paths_touched": [],
    },
)
```

## Workspace handling

Your workspace kind determines how you should behave inside `$HERMES_KANBAN_WORKSPACE`:

| Kind | What it is | How to work |
|---|---|---|
| `scratch` | Fresh tmp dir, yours alone | Read/write freely; it gets GC'd when the task is archived. |
| `dir:<path>` | Shared persistent directory | Other runs will read what you write. Treat it like long-lived state. Path is guaranteed absolute (the kernel rejects relative paths). If it is a Git repo, check `git status`, branch, recent commits, and whether sibling Kanban tasks are running before mutating. |
| `worktree` | Git worktree at the resolved path | If `.git` doesn't exist, run `git worktree add <path> <branch>` from the main repo first, then cd and work normally. Commit work here. |

## Tenant isolation

If `$HERMES_TENANT` is set, the task belongs to a tenant namespace. When reading or writing persistent memory, prefix memory entries with the tenant so context doesn't leak across tenants:

- Good: `business-a: Acme is our biggest customer`
- Bad (leaks): `Acme is our biggest customer`

## Good summary + metadata shapes

The `kanban_complete(summary=..., metadata=...)` handoff is how downstream workers read what you did. Patterns that work:

**Coding task:**
```python
kanban_complete(
    summary="shipped rate limiter — token bucket, keys on user_id with IP fallback, 14 tests pass",
    metadata={
        "changed_files": ["rate_limiter.py", "tests/test_rate_limiter.py"],
        "tests_run": 14,
        "tests_passed": 14,
        "decisions": ["user_id primary, IP fallback for unauthenticated requests"],
    },
)
```

**Research task:**
```python
kanban_complete(
    summary="3 competing libraries reviewed; vLLM wins on throughput, SGLang on latency, Tensorrt-LLM on memory efficiency",
    metadata={
        "sources_read": 12,
        "recommendation": "vLLM",
        "benchmarks": {"vllm": 1.0, "sglang": 0.87, "trtllm": 0.72},
    },
)
```

**Review task:**
```python
kanban_complete(
    summary="reviewed PR #123; 2 blocking issues found (SQL injection in /search, missing CSRF on /settings)",
    metadata={
        "pr_number": 123,
        "findings": [
            {"severity": "critical", "file": "api/search.py", "line": 42, "issue": "raw SQL concat"},
            {"severity": "high", "file": "api/settings.py", "issue": "missing CSRF middleware"},
        ],
        "approved": False,
    },
)
```

Shape `metadata` so downstream parsers (reviewers, aggregators, schedulers) can use it without re-reading your prose.

## Block reasons that get answered fast

Bad: `"stuck"` — the human has no context.

Good: one sentence naming the specific decision you need. Leave longer context as a comment instead.

```python
kanban_comment(
    task_id=os.environ["HERMES_KANBAN_TASK"],
    body="Full context: I have user IPs from Cloudflare headers but some users are behind NATs with thousands of peers. Keying on IP alone causes false positives.",
)
kanban_block(reason="Rate limit key choice: IP (simple, NAT-unsafe) or user_id (requires auth, skips anonymous endpoints)?")
```

The block message is what appears in the dashboard / gateway notifier. The comment is the deeper context a human reads when they open the task.

## Heartbeats worth sending

Good heartbeats name progress: `"epoch 12/50, loss 0.31"`, `"scanned 1.2M/2.4M rows"`, `"uploaded 47/120 videos"`.

Bad heartbeats: `"still working"`, empty notes, sub-second intervals. Every few minutes max; skip entirely for tasks under ~2 minutes.

## Retry scenarios

If you open the task and `kanban_show` returns `runs: [...]` with one or more closed runs, you're a retry. The prior runs' `outcome` / `summary` / `error` tell you what didn't work. Don't repeat that path. Typical retry diagnostics:

- `outcome: "timed_out"` — the previous attempt hit `max_runtime_seconds`. You may need to chunk the work or shorten it.
- `outcome: "crashed"` — OOM or segfault. Reduce memory footprint.
- `outcome: "spawn_failed"` + `error: "..."` — usually a profile config issue (missing credential, bad PATH). Ask the human via `kanban_block` instead of retrying blindly.
- `outcome: "reclaimed"` + `summary: "task archived..."` — operator archived the task out from under the previous run; you probably shouldn't be running at all, check status carefully.
- `outcome: "blocked"` — a previous attempt blocked; the unblock comment should be in the thread by now.

## Do NOT

- Call `delegate_task` as a substitute for `kanban_create`. `delegate_task` is for short reasoning subtasks inside YOUR run; `kanban_create` is for cross-agent handoffs that outlive one API loop.
- Modify files outside `$HERMES_KANBAN_WORKSPACE` unless the task body says to.
- Create follow-up tasks assigned to yourself — assign to the right specialist.
- Complete a task you didn't actually finish. Block it instead.

## Pitfalls

**Task state can change between dispatch and your startup.** Between when the dispatcher claimed and when your process actually booted, the task may have been blocked, reassigned, or archived. Always `kanban_show` first. If it reports `blocked` or `archived`, stop — you shouldn't be running.

**Workspace may have stale artifacts or concurrent sibling edits.** Especially `dir:` and `worktree` workspaces can have files from previous runs. Read the comment thread — it usually explains why you're running again and what state the workspace is in. If working in a shared Git repo, check `git status --short --branch` and `git log --oneline -5` before and after your changes. If you see unrelated uncommitted changes, do not sweep them into your commit unless the task explicitly says to integrate sibling work; comment/block or commit only your scoped paths.

**Don't rely on the CLI when the guidance is available.** The `kanban_*` tools work across all terminal backends (Docker, Modal, SSH). `hermes kanban <verb>` from your terminal tool will fail in containerized backends because the CLI isn't installed there. When in doubt, use the tool.

## CLI fallback (for scripting)

Every tool has a CLI equivalent for human operators and scripts:
- `kanban_show` ↔ `hermes kanban show <id> --json`
- `kanban_complete` ↔ `hermes kanban complete <id> --summary "..." --metadata '{...}'`
- `kanban_block` ↔ `hermes kanban block <id> "reason"`
- `kanban_create` ↔ `hermes kanban create "title" --assignee <profile> [--parent <id>]`
- etc.

Use the tools from inside an agent; the CLI exists for the human at the terminal.
