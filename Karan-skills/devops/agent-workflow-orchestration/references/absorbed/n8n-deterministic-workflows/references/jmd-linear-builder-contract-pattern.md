# JMD Linear Builder Contract Pattern for n8n Workflows

Session source: JMD showroom Drive → Sanity n8n workflow planning, June 2026.

## Durable Pattern

When a user wants an n8n workflow built by an autonomous coding agent, use Linear child issues as the durable builder contract instead of a one-off chat prompt.

Recommended agent roles:

- Hermes: orchestrator, repo/Linear alignment, approval gates, final verification.
- Claude Code: primary builder when using `czlonkowski/n8n-skills` / `n8n-mcp` guidance.
- Codex: reviewer for deterministic logic, idempotency, credential leakage, and workflow artifact safety.

## Key Distinction

An n8n workflow’s nodes/connections are represented by workflow JSON, but a local JSON file alone is not sufficient proof. The actual workflow should be imported/created in a real test n8n instance and validated there before treating the export as review-ready.

Use a staged contract:

1. **Prepare build lane** — confirm local scaffold, repo contract files, n8n skills/MCP/UI/API path, and missing prerequisites.
2. **Build local skeleton** — draft inactive workflow JSON and deterministic Code-node logic locally with tests; no live n8n/account mutation.
3. **Validate in test n8n** — import/create inactive workflow in a test n8n instance; confirm nodes, expressions, connections, and credential slots are recognized.
4. **Export/sanitize** — export from the real inactive test workflow, sanitize secrets/credential metadata, validate locally, and prepare repo-ready artifact.
5. **Credential-gated dry-run** — only after explicit approval, run against test Drive + test Sanity; prove first-run import, second-run idempotency, unsupported-file skip, and Sanity read-back.

## Repo Alignment Step

Before creating Linear child issues or builder prompts, inspect the current target repo state — not memory alone. Capture the exact contract files the builder/reviewer must read, for example:

- `AGENTS.md`
- `docs/spec.md`
- `docs/build-plan.md`
- architecture/research docs
- API/schema contract docs
- current schema/source files
- validation scripts and package commands

Include repo-aligned expectations directly in the Linear issue body: deterministic IDs, enum values, output paths, validation commands, and boundaries.

## Scope Pitfall

Keep import and archive/removal work separated when risk differs. For Drive → CMS workflows, import-only mistakes are usually easier to detect/recover than archive/removal mistakes. Do not let an import issue absorb destructive or visibility-removing archive behavior unless the parent explicitly approves that scope.

## Safety Boundaries

Linear contracts should state explicitly:

- no production credentials;
- no production workflow activation;
- no live Sanity/Drive mutations without approval;
- no credential IDs/tokens/private folder IDs committed;
- real n8n validation required before treating workflow JSON as done;
- final repo artifact should be sanitized workflow JSON + import/restore notes + env/credential names only + verification evidence.
