---
name: n8n-deterministic-workflows
description: Design, implement, review, and operate deterministic n8n workflows for file/API reconciliation, especially Drive-to-CMS automations with safe idempotency, backups, and error handling.
tags: [n8n, automation, workflows, reconciliation, google-drive, sanity, cms, operations]
triggers:
  - "n8n"
  - "workflow automation"
  - "Google Drive to Sanity"
  - "Drive to CMS"
  - "scheduled reconciliation"
  - "n8n workflow JSON"
  - "n8n CLI"
---

# n8n Deterministic Workflows

Use this skill when designing or reviewing n8n workflows that should behave predictably: file intake, CMS sync, scheduled jobs, archive/rotation policies, reporting, and API glue.

## Core Principle

Prefer **deterministic reconciliation** over fragile event-only automation.

Good shape:

> Given the current source-of-truth state, make the target system match the desired state.

Avoid:

> A trigger fired, so assume the single event is complete truth.

Triggers can be useful as a fast path, but a scheduled reconciliation run should be able to repair missed events, retries, duplicate uploads, workflow pauses, and API hiccups.

## Standard Architecture

For Drive/CMS photo or file intake workflows:

1. **Source of truth**: one clearly-scoped folder or data source.
2. **n8n**: scheduled reconciliation layer.
3. **Target backend**: CMS/database/image CDN, not public Drive links.
4. **Website/app**: reads the target backend only.
5. **Repo artifact**: workflow JSON/export and docs live in version control.
6. **Error path**: dangerous conditions stop and notify instead of mutating blindly.

## Design Checklist

### 1. Define deterministic source and target

- Name the source folder/API/query exactly.
- Decide whether folder placement equals approval or whether a separate approval state exists.
- Define the target record type/schema.
- Choose one idempotency key, usually a source file ID or external object ID.

### 2. Use idempotency everywhere

- Query target by the idempotency key before creating.
- If the target record exists, skip or patch metadata; do not create duplicates.
- Store the source ID, source timestamps, import timestamp, status, last-seen timestamp, and last error.
- For binary assets, store the target asset reference so retries do not create duplicate assets when avoidable.

### 3. Prefer scheduled reconciliation

- Use Schedule Trigger as the reliability backbone.
- Optionally add a source trigger, such as Google Drive Trigger, only to run the same reconciliation sooner.
- Never make archive/delete behavior depend only on a single trigger event.

### 4. Separate transformation from API calls

- Use native nodes for supported apps (Google Drive list/download, etc.).
- Use Code nodes only for deterministic transformation/set math: sorting, filtering, desired-state calculation, safety checks, payload shaping.
- Use HTTP Request nodes for external REST APIs and binary uploads.
- Keep credentials in n8n credentials or hosting secrets, not in Code nodes or exported JSON.

### 5. Add safety guards before mutation

For workflows that archive, delete, unpublish, or rotate content:

- If the source list fails, abort.
- If the source list is suspiciously empty, abort unless an explicit empty-source mode is approved.
- If the mutation count exceeds an expected threshold, abort or require review.
- Never hard-delete in v1 when archive/unpublish can preserve recovery.
- Use Stop And Error to intentionally fail dangerous runs and trigger the error workflow.

### 6. Ship with observability

Every production-bound workflow should produce a run summary:

- timestamp
- source checked
- source item count
- created/imported count
- updated count
- archived/unpublished count
- skipped count
- failed count
- failed item IDs/names
- execution URL if available

Use a reusable Error Workflow with Error Trigger for failures.

## Useful n8n Docs / References

- `references/absorbed/n8n-deterministic-workflows/references/jmd-drive-sanity-photo-automation.md` — concrete Drive → Sanity photo automation pattern and signal/noise assessment from the JMD planning session.
- `references/jmd-n8n-workflow-scaffold.md` — local project scaffold pattern for building/test-validating n8n workflows outside the app repo while preparing sanitized repo artifacts.
- `references/jmd-test-resource-gate.md` — JMD-style test-resource setup and approval-gate split for credentialed n8n Drive → Sanity dry-runs.
- `references/jmd-credentialed-dry-run-verification.md` — JMD-style credentialed dry-run verification ladder, evidence checklist, per-file failure isolation, and fixture-failure closeout language.
- `references/google-drive-v2-query-scope-pitfall.md` — fix and verification pattern for n8n Google Drive v2 raw-query searches that request `appDataFolder, drive`, causing `403 insufficientScopes` despite Drive OAuth scope.
- n8n API CLI docs: `https://docs.n8n.io/api/n8n-cli/`
- n8n Server CLI docs: `https://docs.n8n.io/hosting/cli-commands/`
- Workflow export/import docs: `https://docs.n8n.io/workflows/export-import/`
- Google Drive node docs: `https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googledrive/`
- Google Drive Trigger docs: `https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.googledrivetrigger/`
- HTTP Request node docs: `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/`
- Code node docs: `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/`
- Error handling docs: `https://docs.n8n.io/flow-logic/error-handling/`
- Official n8n skills repository: `https://github.com/n8n-io/skills`

## n8n CLI vs Server CLI

Use the right tool:

- **n8n CLI (`@n8n/cli`)**: API-based, can run remotely, requires running n8n, uses API key. Good for workflow get/list/create/update, execution inspection, and developer/agent workflows. It is beta; do not make it the production backbone without review.
- **Server CLI (`n8n ...`)**: runs on the n8n host/container, talks to the database, can work when the service is stopped. Good for self-hosted backups, imports, emergency admin. Treat it as privileged.

Safe default:

- Use CLI/API to export workflow JSON into the repo and inspect executions.
- Do not export decrypted credentials except for an explicitly approved controlled migration.

## Workflow JSON as Source Artifact

For client or recurring business workflows, the n8n UI alone is not enough — but a hand-written local JSON file alone is also not enough.

- Export workflow JSON after meaningful changes.
- Store redacted/anonymized workflow JSON in the repo where builders/reviewers can diff it.
- Document required credentials and environment variables by name only, never values.
- Verify imports against a test n8n instance or test project before production activation.
- Treat “real n8n workflow built” as: nodes/connections/expressions load in a real inactive test workflow, then the workflow is exported back out, sanitized, and validated. Do not claim done from a pretty local JSON skeleton alone.

### Linear-as-builder-contract pattern

When an autonomous coding agent will build the n8n workflow, prefer durable Linear child issues over one large chat prompt:

1. Prepare build lane and n8n skills/MCP/UI/API path.
2. Build local inactive workflow skeleton and deterministic Code-node logic.
3. Import/create inactive workflow in a test n8n instance and validate actual nodes.
4. Export, sanitize, and prepare the repo-ready artifact for review.
5. Run credential-gated dry-run tests against test source/target systems only after explicit approval.

Before creating those issues, inspect the target repo’s current contract files and include exact repo expectations, paths, validation commands, enum values, and safety boundaries in the issue body. Keep higher-risk archive/removal mutations in a separate issue when their blast radius differs from import-only work.

See `references/jmd-linear-builder-contract-pattern.md` for the concrete JMD Drive → Sanity pattern.

## Local Scaffold Pattern Before Live Build

When the workflow is operationally live in n8n but the implementation still needs tests, docs, and reviewable artifacts, create a separate local automation workspace outside the app repo before touching live credentials or schedules.

Recommended shape:

- `README.md` with boundaries, build order, and approval gates.
- `.env.example` and `config/*.example.json` with variable names only.
- `docs/` for architecture, source issue summary, target schema/API contract, and owner/operator SOP.
- `src/` with pure deterministic reconciliation helpers that mirror Code-node set math.
- `test/` with fixture coverage for idempotency, archive rules, unsupported files, repeated runs, and dangerous-source aborts.
- `scripts/sanitize-workflow-export.*` to redact credentials/secrets from real n8n exports.
- `scripts/validate-workflow-export.*` to check for Schedule Trigger, Drive/API nodes, guard/error path, and obvious secret leakage.
- `workflows/*.template.json` as a sanitized starter/reference, not an activated production workflow.

Report the boundary explicitly: scaffolding alone should not mutate Google Drive, Sanity, n8n credentials/schedules, deployments, DNS, or client-facing channels. Later, copy only sanitized/exported workflow artifacts into the app repo for PR review.

See `references/jmd-n8n-workflow-scaffold.md` for a concrete JMD Drive → Sanity scaffold.

## Common Pitfalls

- **Setup ≠ execution approval**: For credential-gated dry-runs, creating test Drive/Sanity/n8n resources is not permission to run the workflow. Keep resource setup and execution approval separate, record a redacted resource inventory, and require explicit approval before any manual run that creates Sanity test assets/docs. Confirm the actual n8n process environment sees `DRY_RUN=true` and test dataset/folder values; a local `.env` update does not affect an already-running n8n process until it is relaunched.
- **Dry-run environment ladder**: For client CMS imports, test the integration in stages: (1) test source → test target, (2) real approved source → test target, (3) real approved source → production target only after explicit approval and preferably a tiny curated batch. Do not use real Drive + production Sanity for the first full dry-run.
- **Per-file failure isolation**: For reconciliation imports, one corrupt/unreadable source file should not abort an otherwise valid batch. Use `onError: continueErrorOutput` on item-level download/upload/mutate nodes, route failures into a collector, pair results back to origin items via `pairedItem` rather than array index, and net runtime failures out of imported summary counts.
- **Fixture failure interpretation**: A corrupt image fixture that is isolated cleanly can be useful evidence. Report it as “1 clean import + 1 isolated failure” rather than overclaiming a 2/2 import; offer a valid replacement fixture only if the user needs the clean happy-path demo.
- **Trigger-only fragility**: Drive triggers can miss bulk/moved files or behave differently in manual vs activated runs. Use scheduled reconciliation as the backbone.
- **Archive-all accidents**: A failed source list can look like an empty folder. Abort on suspicious empty source states.
- **Auto-publish metadata conflicts**: If folder placement counts as approval and imports publish automatically, required fields such as `altText` need deterministic v1 sources/fallbacks. Do not require manual CMS edits before publish unless the workflow also includes a non-published `draft/ready` state.
- **Ambiguous archive precedence**: Rotation rules like “latest 9,” “older than 90 days,” “keep at least 3 live,” and “removed from source” can conflict. Document deterministic precedence before implementation; for example, source-removed archives usually outrank keep-minimum, while keep-minimum may intentionally override age-based archive for source-present records.
- **Google Drive v2 raw-query scope trap**: a Drive credential can test as connected and have full Drive OAuth scope, but n8n's Google Drive v2 raw search may request `spaces=appDataFolder, drive`, causing `403 insufficientScopes` if the token lacks app-data scope. For folder-list workflows, set `searchMethod=query`, quote the Drive folder ID in `q` (`'<folderId>' in parents and trashed = false`), and add `filter.folderId=root` so n8n sends `spaces=drive`. Verify with a read-only temporary graph cut immediately after the Drive-list node before allowing downstream CMS writes. See `references/google-drive-v2-query-scope-pitfall.md`.
- **Credential leakage**: Exported workflow JSON may include credential names/IDs or imported HTTP headers. Redact before sharing or committing.
- **Code node overuse**: Code nodes should compute state, not become hidden apps with direct HTTP calls and secrets.
- **Public Drive URLs**: Avoid serving website images directly from Drive. Import into a real backend/CDN.
- **Unversioned UI changes**: If workflow JSON is not exported, the workflow becomes invisible tribal knowledge.

## Review Checklist

Before calling a workflow plan ready:

- [ ] Source of truth is explicit.
- [ ] Target schema is explicit.
- [ ] Idempotency key is explicit.
- [ ] Scheduled reconciliation exists or is planned.
- [ ] Dangerous mutations have safety guards.
- [ ] Error workflow/alert path exists.
- [ ] Workflow JSON/export is part of the deliverable.
- [ ] Credentials are referenced by name only.
- [ ] Non-goals are listed to prevent overengineering.
