---
name: kanban-orchestrator
description: Decomposition playbook + specialist-roster conventions + anti-temptation rules for an orchestrator profile routing work through Kanban. The "don't do the work yourself" rule and the basic lifecycle are auto-injected into every kanban worker's system prompt; this skill is the deeper playbook when you're specifically playing the orchestrator role.
version: 2.0.0
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, routing]
    related_skills: [kanban-worker]
---

# Kanban Orchestrator — Decomposition Playbook

> The **core worker lifecycle** (including the `kanban_create` fan-out pattern and the "decompose, don't execute" rule) is auto-injected into every kanban process via the `KANBAN_GUIDANCE` system-prompt block. This skill is the deeper playbook when you're an orchestrator profile whose whole job is routing.

## When to use the board (vs. just doing the work)

Create Kanban tasks when any of these are true:

1. **Multiple specialists are needed for planning/research/spec/review.** Research + analysis + writing is three profiles.
2. **The non-coding work should survive a crash or restart.** Long-running, recurring, or important.
3. **The user might want to interject.** Human-in-the-loop at any step.
4. **Multiple non-mutating subtasks can run in parallel.** Fan-out for speed.
5. **Review / iteration is expected on a plan, spec, or handoff.** A reviewer profile loops on drafter output.
6. **The audit trail matters.** Board rows persist in SQLite forever.

Karan's current preference: **do not use Kanban as the default execution lane for coding tasks.** For PAPI/Linear-style work, Kanban/Linear should usually stop at spec'ing implementation-ready GitHub issues. Actual coding should happen through GitHub issues → branches → PRs using the GitHub PR workflow, Codex/Claude Code, or a direct repo session outside Kanban unless Karan explicitly asks to route coding through Kanban.

If *none* of those apply — it's a small one-shot reasoning task — use `delegate_task` instead or answer the user directly.

## The anti-temptation rules

Your job description says "route, don't execute." The rules that enforce that:

- **Do not execute the work yourself.** Your restricted toolset usually doesn't even include terminal/file/code/web for implementation. If you find yourself "just fixing this quickly" — stop and create a task for the right specialist.
- **For any concrete task, create a Kanban task and assign it.** Every single time.
- **If no specialist fits, ask the user which profile to create.** Do not default to doing it yourself under "close enough."
- **Decompose, route, and summarize — that's the whole job.**

## The standard specialist roster (convention)

Do **not** invent assignees from role names. Kanban dispatch requires the assignee to be a real configured Hermes profile. Before creating tasks, check the actual profile roster (`hermes profile list` or the dashboard assignee list) and assign only to names that exist.

Karan's current standing profiles are:

| Profile | Does | Typical workspace |
|---|---|---|
| `orchestrator` | Routes/decomposes work and creates task graphs | `scratch` |
| `pm-spec` | Writes specs, acceptance criteria, implementation handoffs | `scratch` |
| `builder` | Writes code/docs in repos; covers frontend/backend implementation unless a more specific profile exists | `worktree` or `dir_serial` |
| `reviewer` | Reads output, leaves findings, gates approval | `scratch` |
| `researcher` | Reads sources, gathers facts, writes findings | `scratch` |
| `wiki-ops` | Maintains Hermes Brain / Obsidian wiki knowledge | `dir:` into the vault |

Role labels like `frontend-eng`, `backend-eng`, `analyst`, `writer`, `ops`, or `pm` are conceptual only unless `hermes profile list` shows those profiles exist. If the role you want does not exist, either map it to the closest standing profile (`frontend-eng`/`backend-eng` → `builder`, `pm` → `pm-spec`) or ask Karan whether to create a new profile.

## Orchestration discipline contract

Before creating worker tasks, classify the task graph in the orchestration layer. Do **not** push Hermes-specific orchestration internals into generic harness templates that may be read by Codex, Claude Code, Antigravity, or other non-Hermes agents. Harnesses should contain only plain-English scope rules; the full discipline below belongs in Kanban task bodies and Hermes skills.

### Workspace mode

Every Kanban task that may touch files should declare one workspace mode in the task body:

- `read_only` — research, analysis, review, summarization. Safe to parallelize.
- `scratch` — writes drafts or findings in isolated scratch space. Safe to parallelize.
- `worktree` — writes to a Git repo through an isolated worktree/branch. Preferred for parallel repo mutation.
- `dir_serial` — writes directly into a persistent directory/repo. Must be serialized with dependencies if sibling tasks touch the same repo.

Hard rule: if two tasks write to the same persistent repo/folder, do not dispatch them in parallel as `dir_serial`. Use worktrees, a dependency chain, or parallel scratch tasks followed by one integrator.

### Output scope

Every task should state where its output belongs:

- `base_template` — reusable template files only; no client names, Linear issue IDs, pilot status files, or one-off reviewer verdicts.
- `task_harness` — cloned task/client harness; task/client-specific outputs allowed in the harness.
- `skill_library` — durable reusable skill modules only; no tracker state or one-off task artifacts.
- `linear_comment_draft` — final tracker update text only; do not post unless authorized.
- `github_pr` — repo changes intended for PR review/merge.

Put concrete allowed/forbidden paths in the Kanban task body, not in the generic harness template. Example:

```md
## Task Scope
Workspace mode: worktree
Output scope: base_template
Allowed paths:
- AGENTS.md
- README.md
- preflight.md
Forbidden:
- outputs/papi-28-ac-status.md
- docs/review/reviewer-verdict.md
Must stay generic: yes
Client-specific content allowed: no
Issue-specific artifacts allowed: no
```

### Safe graph patterns

Choose one before dispatch:

1. **Parallel research → one integrator**: researchers/analysts write scratch outputs, then one integrator mutates the real repo.
2. **Serialized repo mutation**: builder task 1 → builder task 2 → reviewer, when all tasks touch the same repo.
3. **Worktree fan-out**: separate worktrees/branches for independent repo changes.
4. **PM-spec before build**: pm-spec defines AC/DoD, generic-vs-task-specific boundary, and approval gates before builder starts.

Default for client work: PM-spec → builder → reviewer → default Hermes finalization. Default for safe parallelism: read-only/scratch research fan-out, then one integrator.

### Harness template boundary

For reusable templates, only add a small non-Hermes rule such as "Template vs Task Harness" in plain English. Avoid terms like Kanban workspace mode, output scope taxonomy, or Hermes profile routing inside template docs unless the template is explicitly Hermes-only.

### Skill access policy

Least privilege restricts tools and authority, not the worker's access to the right playbook. Use this hybrid policy when a task needs skills:

1. Keep a small permanent role-native skill set per profile.
2. Add task-scoped extra skills in the Kanban task body when the task requires them.
3. For sensitive/client/account skills, inject only the relevant excerpt instead of the full skill.
4. Reassign or escalate when the needed skill implies a different role.
5. Only default Hermes or Karan may permanently broaden a profile's skill allowlist.

**Important:** documenting role-native skills in a profile `SOUL.md` or wrapper alias is not enough. If the profile's `$HERMES_HOME/skills/` directory still contains the full bundled library, the worker can discover and load out-of-role skills. For strict role separation, the named profile's actual `skills/` directory must be pruned to the role-native set and protected from reseeding with `.no-bundled-skills`. Use the Hermes Agent profile skill isolation workflow for this; do not treat SOUL.md prose as an access boundary.

When creating tasks, include role-native skills in the task's `skills` field / `--skill` flags and list them in a `Required skills` section. Add task-specific extras only when needed.

Default permanent role-native skill sets include each role's domain playbooks plus `hermes-agent-skill-authoring` so every specialist retains Hermes' native self-improvement loop:

- `orchestrator`: `kanban-orchestrator`, `linear`, `github-issues`, `ops-execution-harness`, `hermes-agent-skill-authoring`
- `researcher`: `research-workflow`, `firecrawl-search`, `firecrawl-scrape`, `firecrawl-map`, `maps`, `hermes-agent-skill-authoring`
- `pm-spec`: `writing-plans`, `plan`, `linear`, `github-issues`, `ops-execution-harness`, `project-kickoff`, `hermes-agent-skill-authoring`
- `builder`: `github-pr-workflow`, `test-driven-development`, `systematic-debugging`, `requesting-code-review`, `context7-cli`, `local-web-preview`, `ops-execution-harness`, `hermes-agent-skill-authoring`
- `reviewer`: `code-review`, `github-code-review`, `requesting-code-review`, `multi-agent-dev-workflow`, `github-pr-workflow`, `linear`, `ops-execution-harness`, `hermes-agent-skill-authoring`
- `wiki-ops`: `daily-log`, `obsidian`, `hermes-brain-wiki`, `obsidian-wiki-maintenance`, `wiki-health-check`, `hermes-agent-skill-authoring`

Skill self-improvement rule: workers may create or patch local reusable skills when assigned work produces a durable, project-agnostic procedure. They may not install hub/third-party skills, publish skills, edit repo-shipped skills, change profile allowlists, or change toolsets unless the task explicitly authorizes it. New skills must avoid secrets, private client data, raw one-off task context, stale PR/issue IDs, and duplicate narrow skills.

Example task body:

```md
## Required skills
- kanban-worker
- github-pr-workflow
- next-eslint-flat-config-migration

If another skill seems necessary:
- comment/block with `MISSING_SKILL_REQUEST: skill=<skill-name>; dangerous=<yes/no>; reason=<why>`.
- do not self-install, broaden scope, or proceed by guessing.
```

Default Hermes may grant non-dangerous missing skills task-scoped without asking Karan. Ask Karan before granting skills that enable or strongly imply live/client/account mutation, credential changes, deployment, outreach, purchases, external/client-facing messages, destructive data operations, or permanent profile allowlist broadening.

Do not solve repeated missing context by granting broad memory/tool access. Prefer scoped task context, a skill, a wiki page, or an intentional allowlist update.

## Decomposition playbook

### Step 1 — Understand the goal

Ask clarifying questions if the goal is ambiguous. Cheap to ask; expensive to spawn the wrong fleet.

### Step 2 — Sketch the task graph

Before creating anything, draft the graph out loud (in your response to the user). Example for "Analyze whether we should migrate to Postgres":

```
T1  researcher        research: Postgres cost vs current
T2  researcher        research: Postgres performance vs current
T3  analyst           synthesize migration recommendation       parents: T1, T2
T4  writer            draft decision memo                       parents: T3
```

Show this to the user. Let them correct it before you create anything.

### Step 3 — Create tasks and link

```python
t1 = kanban_create(
    title="research: Postgres cost vs current",
    assignee="researcher",
    body="Compare estimated infrastructure costs, migration costs, and ongoing ops costs over a 3-year window. Sources: AWS/GCP pricing, team time estimates, current Postgres bills from peers.",
    tenant=os.environ.get("HERMES_TENANT"),
)["task_id"]

t2 = kanban_create(
    title="research: Postgres performance vs current",
    assignee="researcher",
    body="Compare query latency, throughput, and scaling characteristics at our expected data volume (~500GB, 10k QPS peak). Sources: benchmark papers, public case studies, pgbench results if easy.",
)["task_id"]

t3 = kanban_create(
    title="synthesize migration recommendation",
    assignee="analyst",
    body="Read the findings from T1 (cost) and T2 (performance). Produce a 1-page recommendation with explicit trade-offs and a go/no-go call.",
    parents=[t1, t2],
)["task_id"]

t4 = kanban_create(
    title="draft decision memo",
    assignee="writer",
    body="Turn the analyst's recommendation into a 2-page memo for the CTO. Match the tone of previous decision memos in the team's knowledge base.",
    parents=[t3],
)["task_id"]
```

`parents=[...]` gates promotion — children stay in `todo` until every parent reaches `done`, then auto-promote to `ready`. No manual coordination needed; the dispatcher and dependency engine handle it.

### Step 4 — Complete your own task

If you were spawned as a task yourself (e.g. `planner` profile was assigned `T0: "investigate Postgres migration"`), mark it done with a summary of what you created:

```python
kanban_complete(
    summary="decomposed into T1-T4: 2 researchers parallel, 1 analyst on their outputs, 1 writer on the recommendation",
    metadata={
        "task_graph": {
            "T1": {"assignee": "researcher", "parents": []},
            "T2": {"assignee": "researcher", "parents": []},
            "T3": {"assignee": "analyst", "parents": ["T1", "T2"]},
            "T4": {"assignee": "writer", "parents": ["T3"]},
        },
    },
)
```

### Step 5 — Report back to the user

Tell them what you created in plain prose:

> I've queued 4 tasks:
> - **T1** (researcher): cost comparison
> - **T2** (researcher): performance comparison, in parallel with T1
> - **T3** (analyst): synthesizes T1 + T2 into a recommendation
> - **T4** (writer): turns T3 into a CTO memo
>
> The dispatcher will pick up T1 and T2 now. T3 starts when both finish. You'll get a gateway ping when T4 completes. Use the dashboard or `hermes kanban tail <id>` to follow along.

## Common patterns

**Fan-out + fan-in (research → synthesize):** N `researcher` tasks with no parents, one `analyst` task with all of them as parents.

**Pipeline with gates:** `pm → backend-eng → reviewer`. Each stage's `parents=[previous_task]`. Reviewer blocks or completes; if reviewer blocks, the operator unblocks with feedback and respawns.

**Same-profile queue:** 50 tasks, all assigned to `translator`, no dependencies between them. Dispatcher may spawn multiple ready tasks for the same profile, so this pattern is safe only when each task has an isolated workspace (`scratch` or separate `worktree`) or is read-only. If tasks mutate the same persistent `dir:` workspace/repo, serialize them with dependencies or use a scratch+integrator pattern.

**Shared repo mutation:** For multiple changes to the same Git repo, prefer one of:
- A dependency chain: template edit → metrics edit → evidence edit → review.
- Separate `worktree` workspaces per task/branch.
- Parallel `scratch` research/patch tasks followed by one integrator task in the real repo.
Do **not** dispatch several repo-mutating tasks in parallel to the same `dir:<repo>` workspace; their commits and status docs can overlap.

**Human-in-the-loop:** Any task can `kanban_block()` to wait for input. The comment thread carries the full context, but comments are only context — they do **not** automatically unblock or respawn a blocked task. After adding approval/input in a comment, explicitly unblock/reclaim and dispatch the task (or create the required follow-up task) so a worker actually resumes:

```bash
hermes kanban unblock <task_id> --note "approved: open PR"   # if available in this install
hermes kanban reclaim <task_id>                              # if a stale/failed run lock exists
hermes kanban dispatch --max 1
hermes kanban runs <task_id>
```

If the task blocked because it needed an external artifact (issue, PR, approval token), default Hermes should either create/verify the artifact itself when authorized or create a follow-up task that includes the artifact link, then dispatch the dependent reviewer/integrator task.

See `references/absorbed/kanban-orchestrator/references/shared-workspace-parallel-dispatch.md` for the session-specific PAPI pilot example and safe graph alternatives.

See `references/absorbed/kanban-orchestrator/references/pilot-closeout-pattern.md` for the class-level closeout pattern from a multi-profile JMD/PAPI pilot: specialist roles, what worked, what failed, and efficiency improvements for future pilots.

See `references/absorbed/kanban-orchestrator/references/profile-skill-access-policy.md` for the post-pilot least-privilege profile skill matrix, task-scoped missing-skill grant pattern, and auto-triage watchdog approach.

See `references/absorbed/kanban-orchestrator/references/dispatch-preflight-and-closeout-hardening.md` for the JMD-19-derived implementation pattern: deterministic assignee/skill preflight before worker spawn, blocked-state wording, and PR-to-tracker closeout checks.

## Pitfalls

**Do not invent missing operational profiles.** If the route calls for "ops" but `hermes profile list` does not show an `ops` profile, do not assign the card to `ops`. Map the work to an existing profile (`pm-spec` for packet/spec drafting, `builder` for repo mutation, `reviewer` for QA, `researcher` for research) or ask Karan/default Hermes whether to create a new profile. A ready task with a nonexistent assignee can sit ready without a worker ever launching. If that invalid task is a parent, inspect its children too: they can remain in `todo` forever even if their own assignee/skills are valid, because dependency promotion waits on the broken parent.

**Skill-library leakage can make specialists act like orchestrators.** If a non-orchestrator profile unexpectedly loads `kanban-orchestrator`, compare the task's explicit `skills` field with the spawned profile session JSON. If the task did not request it but `<available_skills>` exposed it and the worker called `skill_view`, the profile's on-disk skills are over-broad or a prompt snapshot is stale. Use the Hermes Agent profile skill isolation workflow rather than only editing SOUL.md.

**Reassignment vs. new task.** If a reviewer blocks with "needs changes," create a NEW task linked from the reviewer's task — don't re-run the same task with a stern look. The new task is assigned to the original implementer profile.

**Argument order for links.** `kanban_link(parent_id=..., child_id=...)` — parent first. Mixing them up demotes the wrong task to `todo`.

**Don't pre-create the whole graph if the shape depends on intermediate findings.** If T3's structure depends on what T1 and T2 find, let T3 exist as a "synthesize findings" task whose own first step is to read parent handoffs and plan the rest. Orchestrators can spawn orchestrators.

**Tenant inheritance.** If `HERMES_TENANT` is set in your env, pass `tenant=os.environ.get("HERMES_TENANT")` on every `kanban_create` call so child tasks stay in the same namespace.

**Parallel shared-workspace mutation.** The dispatcher can run multiple ready tasks concurrently, even with the same assignee. In the PAPI ops harness pilot, four `builder` tasks against the same `dir:/Users/creator/projects/papi-ops-execution-harness-template` repo all ran at once. They completed, but commits captured sibling changes and a reviewer follow-up was needed to fix stale AC status. Before creating parallel tasks, check `workspace_path`: if two tasks will write the same persistent directory or Git repo, add parent dependencies or give them isolated worktrees/scratch workspaces.
