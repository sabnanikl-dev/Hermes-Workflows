# JMD n8n Workflow Scaffold Pattern

Session-derived pattern for building deterministic n8n workflows outside a product repo while still preparing reviewable repo artifacts.

## When to use

Use this when a workflow has live credentials/runtime state in n8n, but the project needs versioned docs, tests, sanitized exports, and PR-reviewable artifacts.

## Recommended local scaffold

Create a separate automation workspace outside the app repo, for example:

```text
<client-project>/automation/<workflow-name>/
├── README.md
├── .env.example
├── .gitignore
├── package.json
├── config/
│   └── workflow.config.example.json
├── docs/
│   ├── architecture.md
│   ├── linear-source-summary.md
│   ├── operator-sop.md
│   └── sanity-contract.md
├── scripts/
│   ├── sanitize-workflow-export.mjs
│   └── validate-workflow-export.mjs
├── src/
│   └── reconciliation.js
├── test/
│   └── reconciliation.test.js
└── workflows/
    └── <workflow-name>.template.json
```

## What belongs in the local scaffold

- Pure reconciliation helpers for deterministic set math that would otherwise hide in n8n Code nodes.
- Tests for idempotency, archive ordering, safety guards, unsupported files, and repeated runs.
- Sanitizer script for exported workflow JSON.
- Validator script that checks for schedule trigger, required node types, guard/error path, and obvious secrets/credential metadata.
- Architecture, schema/API contract, and operator SOP docs distilled from Linear/GitHub issue packets.
- `.env.example` and config examples with variable names only.

## What belongs in n8n only

- Live credentials.
- Credential IDs/names that expose account details.
- Execution history.
- Activated schedules.
- Live Drive/Sanity mutations.

## What eventually goes into the app repo

Only after live/test workflow exists and is sanitized:

```text
app-repo/
  automation/n8n/
    <workflow-name>.workflow.json
    README.md
    env.example
    sanitization-notes.md
```

## Verification pattern

Before reporting scaffold completion, run local verification such as:

```bash
npm test
node scripts/validate-workflow-export.mjs workflows/<workflow-name>.template.json
```

For JMD-style Drive → Sanity workflows, tests should cover:

- supported image MIME filtering: JPEG, PNG, WebP;
- default HEIC skip/defer behavior;
- first import vs second idempotent run;
- `sourceDriveFileId` duplicate prevention;
- removed-file archive reason;
- latest-9 / 90-day / keep-minimum behavior;
- Drive listing failure and suspicious-zero aborts;
- max-archive threshold abort;
- sanitized workflow template validation.

## Safety boundary wording

Explicitly report no live mutation when scaffolding only:

- no live Google Drive changes;
- no live Sanity writes;
- no n8n credential creation/activation;
- no deploy/DNS/public website changes;
- no client-facing messages.
