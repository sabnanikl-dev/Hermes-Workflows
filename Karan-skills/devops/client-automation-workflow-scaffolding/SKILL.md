---
name: client-automation-workflow-scaffolding
description: Use when turning a vague client automation/workflow request into repo-aligned Linear child issues, a safe local/off-repo scaffold, builder/reviewer contracts, credential gates, and sanitized repo artifacts.
tags: [client-automation, linear, github, n8n, workflow-scaffolding, agent-orchestration, credentials, repo-artifacts]
---

# Client Automation Workflow Scaffolding

Use this skill when a client workflow/automation needs to move from a broad parent issue or conversation into executable, agent-ready work without risking live accounts, credentials, or messy repo drift.

Typical examples:

- Google Drive → CMS/Sanity imports.
- n8n/Make/Zapier automations.
- Form/webhook → CRM/reporting workflows.
- Website-adjacent automations whose runtime belongs outside the repo but whose artifacts need repo review.
- Any client workflow involving external credentials, schedules, APIs, account mutations, or client-facing impact.

## Core principle

Separate **runtime operation** from **reviewable source artifacts**.

- Runtime system: n8n/Make/Zapier/CMS/API account where credentials, schedules, executions, and live mutations happen.
- Repo artifact: sanitized workflow export, docs, fixtures, verification notes, and restore/import instructions.
- Linear/GitHub contract: narrowly scoped issues that agents can execute and reviewers can verify.

Do not confuse a local JSON scaffold with a proven live workflow. A workflow artifact is not complete until it is validated/imported in the actual runtime or a clearly documented test runtime.

## Agent roles

Default roles:

- **Hermes** — orchestrator, final integrator, approval gate, repo/Linear hygiene, verification owner.
- **Builder agent** — Claude Code/Codex/OpenCode/Hermes subagent depending on fit; implements the scaffold/workflow.
- **Reviewer agent** — independent technical review, usually Codex for code/workflow logic and safety.
- **Human/Karan** — approval for credentials, live account mutation, production schedule activation, deploys, merges, client-facing messages, and authority expansion.

If a third-party skill repo or MCP server is involved, treat it as **task-scoped guidance** unless Karan explicitly approves installation/configuration into a sensitive/global profile.

## Workflow

### 1. Reconstruct source context

Before creating issues or scaffolds:

1. Read the parent Linear/GitHub issue or conversation source.
2. Inspect the target repo on the current default branch, not just a stale local branch.
3. Read repo harness docs/contracts, for example:
   - `AGENTS.md`
   - `docs/spec.md`
   - `docs/build-plan.md`
   - `docs/research/*`
   - `docs/api/*`
   - validation scripts / `package.json`
4. Inspect existing child issues/PRs to avoid duplicates.
5. Identify dependencies and sibling issue boundaries.

Do not create a giant child issue that absorbs the whole parent packet. Keep the slice narrow enough for one builder/reviewer cycle.

### 2. Define boundaries

Write down:

- Runtime system: where the automation actually runs.
- Repo artifact location: where sanitized exports/docs should eventually live.
- Local scaffold path: where draft code/workflow artifacts can be built safely.
- Source of truth: Drive folder/API/form/CMS/database/etc.
- Target system: CMS/CRM/database/API/etc.
- Idempotency key or reconciliation key.
- Approval gates.
- Non-goals.

Hard-gate by default:

- live credentials;
- production folder/API/CMS mutations;
- production schedule activation;
- deploys/DNS/hosting/account changes;
- client-facing messages;
- public website changes;
- installing sensitive third-party skills/MCP servers globally;
- deleting source/target data.

### 3. Scaffold locally/off-repo when runtime should not live in repo

If the automation is external to the app repo, create a local/off-repo project folder first.

Suggested shape:

```text
client-workflow-name/
├── README.md
├── .env.example
├── .gitignore
├── package.json or equivalent
├── config/
│   └── workflow.config.example.json
├── docs/
│   ├── architecture.md
│   ├── source-issue-summary.md
│   ├── operator-sop.md
│   └── target-contract.md
├── scripts/
│   ├── sanitize-workflow-export.*
│   └── validate-workflow-export.*
├── src/
│   └── reconciliation-or-transform-logic.*
├── test/
│   └── workflow-policy.test.*
└── workflows/
    └── workflow.template.json
```

Keep `.env.example` to variable names only. Never put real tokens, private folder IDs, production dataset names, credential IDs, or account secrets in committed artifacts.

### 4. Update parent issue as the builder contract umbrella

Patch the parent issue with a section like:

```markdown
## Builder contract decomposition

Use this issue as the parent contract for the <slice> workflow.

### Repo alignment sources
- `AGENTS.md`
- `docs/spec.md`
- `docs/build-plan.md`
- `<contract docs>`
- `<validation scripts>`

### Current repo expectations verified on <branch/date>
- ...

### Agent roles
- Builder: <agent>
- Reviewer: <agent>
- Orchestrator / approval gate: Hermes
- Human approval: Karan before ...

### Build lane
Local scaffold: `<path>`
Final repo artifact target: `<repo path>`

### External skills/reference
- `<task-scoped skill refs>`

### Decomposition
1. Prepare build lane/prereqs.
2. Build local inactive skeleton/logic.
3. Validate/import in test runtime.
4. Export/sanitize repo-ready artifact.
5. Credential-gated dry-run/test execution.

Sibling issue boundaries:
- `<what stays out of this parent>`
```

### 5. Create targeted child issues

Default decomposition for workflow automations:

1. **Prepare build lane / prerequisites**
   - Confirm local scaffold.
   - Decide runtime validation path: UI import, API, MCP, CLI.
   - Identify missing credentials/access without requesting production secrets.
   - Document task-scoped external skills/MCP guidance.

2. **Build local inactive workflow skeleton and deterministic logic**
   - Build workflow graph/config locally.
   - Implement pure/testable transform/reconciliation logic.
   - Keep workflow inactive/dry-run first.
   - Avoid real credentials and production IDs.

3. **Import/create inactive workflow in test runtime and validate actual nodes**
   - Use test n8n/Make/Zapier/CMS/API environment.
   - Verify runtime accepts nodes/expressions/connections.
   - Keep production activation out of scope.
   - Export fixes back to the local scaffold.

4. **Export, sanitize, and prepare repo-ready artifact for review**
   - Export from actual test runtime, not only hand-written JSON.
   - Sanitize secrets, credential metadata, private IDs, tokens, headers, account values.
   - Add import/restore notes and env/credential names only.
   - Run local validators/tests.
   - Request independent review.

5. **Credential-gated dry-run/test execution**
   - Requires explicit approval.
   - Use test resources only.
   - Prove first run, second idempotent run, unsupported item handling, target read-back.
   - Confirm production workflow remains inactive.

Use fewer/more child issues when justified, but preserve the same gates.

### 6. Keep sibling scopes separate

Do not let one implementation issue swallow riskier sibling scopes or slower non-critical scopes.

Examples:

- Import/create belongs in one slice.
- Archive/delete/unpublish belongs in a separate higher-risk slice.
- Website rendering belongs in frontend slice.
- Reporting/SOP can be separate from core mutation logic.
- Production activation should usually be a final gated issue, not hidden inside build work.
- CMS/admin foundation that unblocks automation cutover should not absorb unrelated content-model work (for example, split blog CMS schemas from showroom/Sanity readiness if blog modeling would block a Drive → Sanity launch path).

If the scaffold contains helper logic for a sibling, mark it as scaffold/test-only until that sibling issue is explicitly active. When a frontend can be built from fixture/staging data before backend policy is complete, encode the dependency as “soft for implementation, hard for production launch/readiness unless explicitly waived” instead of blocking all work.

### 7. Prepare production cutover gates without starting cutover

When the test-resource proof is complete and the user supplies a real production source/target identifier (for example a Google Drive folder URL):

- Treat the full identifier as sensitive operational config. Store it only in gitignored local config/secret storage (for example `.env`), never in Linear/GitHub comments or repo artifacts.
- Create a redacted local inventory under an ignored secret directory with purpose, supplied-by, storage env var name, redacted identifier shape, and `access_verified: false` until an approved read/list check is actually run.
- Add/update a production cutover gate document that separates: source read approval, target credential/dataset approval, limited smoke-test mutation approval, and separate schedule activation approval.
- Do **not** list/read the production source, bind production credentials, run a smoke test, mutate production target data, or activate a schedule merely because the user supplied the production URL/ID. Those are separate explicit approvals.
- When posting tracker status, mention only env var names, credential purposes, workflow active/inactive state, and redacted evidence. Do not post raw production IDs, folder URLs, credential IDs, tokens, or private account identifiers.
- If a limited production smoke intentionally imports only a few records, do not close the parent automation/import issue as complete until a final cutover child exists (or the user explicitly defers it). That final child should own: persist/import the proven runtime graph inactive, run the full approved-source import with explicit approval, run the second idempotency pass, re-export/sanitize, and open the repo artifact PR.
- When the automation has a mirrored GitHub issue, make the PR close/link behavior executable in the child issue: name the exact GitHub issue to close (for example `Closes #64`), name Linear references, and explicitly list adjacent issues/scopes the PR must **not** close (archive/removal, schedule activation, deploy, account changes, client comms).
- If the final live schedule activation depends on multiple sibling scopes (for example import readiness plus archive/removal readiness), create a separate activation gate issue under the broader parent/epic rather than hiding activation inside an import or archive child. Its acceptance criteria should require fresh approval, pre/post active-state checks, first scheduled-run evidence, target read-back, and explicit dependency handling (complete sibling vs user-approved deferral).
- For higher-risk sibling behavior such as archive/removal, split repo implementation from live proof: one child owns deterministic logic/tests/sanitized artifact PR and closes the mirrored GitHub issue; a second child owns credentialed/live safety verification with fresh approval and no schedule activation.

See `references/production-cutover-gates.md` for the reusable gate-prep pattern. For the approved n8n + Sanity production-smoke execution pattern (Sanity token creation, n8n `httpHeaderAuth` API gotcha, nested Drive folder read-only checks, smoke limits, restoration, and evidence shape), see `references/n8n-sanity-production-smoke.md`.

### 8. Verify mutations and artifacts

After creating/updating issues:

- Re-read the parent issue and verify the new section is live.
- Re-read child issues and verify parent linkage, project, labels, state, and descriptions.
- Comment on the parent with created child links and no-live-change boundary.
- If repo files were changed, run appropriate tests and verify paths.
- If a workflow was imported/exported, verify active state and sanitize before sharing.
- If a production identifier was supplied, scan tracked/public artifacts for the raw value and confirm it exists only in approved local secret/config storage.

## Verification checklist

Before reporting done:

- [ ] Parent issue read and updated with builder contract.
- [ ] Repo default branch inspected for current expectations.
- [ ] Existing issues/PRs checked to avoid duplicates.
- [ ] Local/off-repo scaffold created if appropriate.
- [ ] Child issues are narrow, ordered, and parent-linked.
- [ ] Runtime vs repo artifact boundary is explicit.
- [ ] Builder/reviewer/orchestrator roles are explicit.
- [ ] Credential/live mutation/client-facing approval gates are explicit.
- [ ] Sibling risk scopes are not accidentally pulled in.
- [ ] Created/updated Linear/GitHub state is re-read and verified.
- [ ] Any scaffold tests/validators pass, or blockers are stated.

## Pitfalls

- **Pretty JSON trap:** a workflow JSON can be syntactically valid but rejected by n8n/Make/Zapier. Require runtime validation.
- **Scope creep:** import, archive/delete, reporting, and frontend rendering have different risk profiles. Split them.
- **Credential leakage:** workflow exports often include credential names/IDs/headers. Sanitize before repo/PR.
- **Production identifier leakage:** user-supplied real folder/dataset/list URLs often look harmless but can reveal client operational structure. Store full values only in ignored local config/secret storage; trackers and repo artifacts get env var names and redacted evidence only.
- **Gate-prep confusion:** receiving a production URL/ID allows preparing the checklist and local config, not listing/reading it, binding production credentials, mutating the target, or activating schedules. Treat each as a separate approval gate.
- **Repo drift:** child issues must name current repo contract files and validation commands, or builders will implement stale assumptions.
- **Builder self-review:** keep builder and reviewer separate; Hermes verifies both.
- **Production by accident:** keep workflows inactive until explicit production activation approval.
- **Direct-folder assumption:** client-approved Drive URLs may point to a parent folder that contains nested folders rather than images directly. If the workflow is direct-folder only, a zero-supported-files result should fail safe; do a read-only child-folder check and either point the smoke overlay at the real image child folder or create a separate recursion issue.
- **n8n credential API schema:** `httpHeaderAuth` credential creation can require `allowedDomains`; include `allowedDomains: "*.api.sanity.io"` when creating Sanity HTTP Header Auth credentials through the n8n API.
