# Post-pilot profile skill access policy

Session-derived reference for Hermes Profiles + Kanban least-privilege operation.

## Core decision

Least privilege restricts tools and authority, not access to the right playbook. A skill is context/instructions; a tool is capability. Giving a worker a skill does not grant permission to deploy, merge, mutate client accounts, write memory, or use forbidden tools.

Approved hybrid model:

1. Small permanent role-native skill set per standing profile.
2. Task-scoped extra skills when a specific task requires them.
3. Excerpt injection for sensitive/client/account skills.
4. Escalation or reassignment when the needed skill implies a different role.
5. Only default Hermes/Karan can permanently broaden profile skill allowlists.
6. All standing profiles keep Hermes' native skill self-improvement loop: they may create or patch **local reusable skills** from lessons learned during assigned work, while leaving toolsets/profile allowlists/hub installs under default Hermes/Karan control.

## Permanent role-native skill sets

These are the V1 baseline sets used after the pilot:

- `orchestrator`: `kanban-orchestrator`, `linear`, `github-issues`, `ops-execution-harness`, `hermes-agent-skill-authoring`
- `researcher`: `research-workflow`, `firecrawl-search`, `firecrawl-scrape`, `firecrawl-map`, `maps`, `hermes-agent-skill-authoring`
- `pm-spec`: `writing-plans`, `plan`, `linear`, `github-issues`, `ops-execution-harness`, `project-kickoff`, `hermes-agent-skill-authoring`
- `builder`: `github-pr-workflow`, `test-driven-development`, `systematic-debugging`, `requesting-code-review`, `context7-cli`, `local-web-preview`, `ops-execution-harness`, `hermes-agent-skill-authoring`
- `reviewer`: `code-review`, `github-code-review`, `requesting-code-review`, `multi-agent-dev-workflow`, `github-pr-workflow`, `linear`, `hermes-agent-skill-authoring`
- `wiki-ops`: `daily-log`, `obsidian`, `hermes-brain-wiki`, `obsidian-wiki-maintenance`, `wiki-health-check`, `hermes-agent-skill-authoring`

## How tasks should carry skills

When creating a Kanban task, pass role-native skills in the task `skills` field / `--skill` flags and list them in the task body:

```md
## Required skills
- kanban-worker
- github-pr-workflow
- next-eslint-flat-config-migration

If another skill seems necessary:
- comment/block with `MISSING_SKILL_REQUEST: skill=<skill-name>; dangerous=<yes/no>; reason=<why>`.
- do not install hub/third-party skills, broaden scope, or proceed by guessing.
```

## Native skill self-improvement loop

Profiles may create or patch local Hermes skills when assigned work produces a reusable, project-agnostic procedure. This is allowed because it improves future execution without granting new external capabilities.

Boundaries:

- OK: `skill_manage(action='create')` for a generic local workflow skill, or `skill_manage(action='patch')` to add a pitfall/verification step to an existing skill.
- Not OK without default Hermes/Karan approval: installing hub/third-party skills, editing repo-shipped skills, publishing skills, changing profile allowlists, changing toolsets, or adding sensitive/client-account operating instructions.
- Skills must not contain secrets, credentials, private client data, raw one-off task context, stale PR/issue IDs, or duplicated narrow procedures.
- Workers should mention created/patched skills in their completion handoff so default Hermes can review whether any should become role-native later.

Use task-scoped extra skills for normal project/context needs. Use excerpts when the full skill contains sensitive account-operating instructions or client-specific details beyond the worker's role.

## Missing-skill auto-triage pattern

Workers use this machine-readable block/comment:

```text
MISSING_SKILL_REQUEST: skill=<skill-name>; dangerous=<yes/no>; reason=<one sentence>
```

Default Hermes may grant non-dangerous missing skills task-scoped without asking Karan, then unblock/retry work. Dangerous requests remain blocked until default Hermes/Karan approves the risky scope.

Mark `dangerous=yes` for skills that enable or strongly imply:

- live/client/account mutation
- credential/auth/config changes
- deployment
- outreach/email/client-facing messaging
- purchases
- destructive data operations
- permanent profile allowlist broadening

A local watchdog implementation can scan blocked tasks, append safe requested skills to the task's `skills` JSON, comment the grant, and `hermes kanban unblock <task_id>`.

## Implementation notes from the pilot

- The profile shell aliases can preload permanent skills with `hermes -p <profile> --skills skill-a,skill-b "$@"`.
- Kanban already supports task-scoped skills through `kanban_create(..., skills=[...])` or CLI `hermes kanban create --skill <name>`.
- `_default_spawn` always adds `kanban-worker`, then appends task-specific skills.
- If profile-local skill availability is the blocker, install/copy the skill to that profile or use an excerpt rather than broadening tools.
- Do not confuse skill access with toolset access. A worker may know a deployment playbook while still being forbidden from deploying.

## Task-scoped skill availability checks

Role-native pruning means a task-scoped extra skill may not exist in the assignee profile's local `skills/` directory. Before dispatching a task with `skills=[...]`, default Hermes/orchestrator should verify each extra skill is loadable by the target profile. If it is not:

- For non-dangerous local/project context skills, copy/install it task-scoped into the profile or replace it with a scoped excerpt in the task body.
- For sensitive client/account skills, prefer a scoped excerpt rather than broad profile access.
- For dangerous skills, block for Karan/default-Hermes approval.

Also check dependent child tasks: a builder task may load a project skill successfully while a reviewer child with the same task-scoped skill crashes if that skill is absent from the reviewer profile. Treat `Unknown skill(s): ...` in a worker log as a profile-skill availability failure, not a model failure.

## Tracker closeout responsibility

When a worker completes a GitHub PR task, the final tracker sync is an orchestration/default-Hermes responsibility unless the task explicitly delegated tracker mutation to a profile that has the right tracker skill.

Before reporting a Kanban task as fully wrapped, also check any downstream review child tasks. A builder task can be `done` while the reviewer child is `blocked` or `crashed`; surface that separately instead of implying the whole workflow is clean.

Expected closeout sequence:

1. Worker completes the scoped implementation/review work and reports PR URL, changed files, validation, and remote verification.
2. Default Hermes or the orchestrator verifies the PR state independently.
3. Default Hermes/orchestrator posts a Linear comment with the PR URL, summary, changed files, and verification details.
4. Default Hermes/orchestrator moves the Linear issue to the appropriate review state (usually `In Review`) when a PR is open and ready for human/code review.

Least-privilege note: `builder` normally should not need the `linear` skill just to update tracker status after opening a PR. Keep Linear tracker mutation with `orchestrator`, `pm-spec` during spec creation, `reviewer` during review closeout, or default Hermes as the final integrator.
