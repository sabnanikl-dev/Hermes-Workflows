# JMD-style credentialed Drive → Sanity dry-run verification

Use this reference when a Drive → Sanity n8n workflow reaches the credentialed dry-run stage. It captures the durable lessons from the JMD-35 test-only dry run.

## Preferred environment ladder

Do not jump straight from static workflow validation to production Drive + production Sanity.

1. **Test Drive folder → test Sanity dataset**
   - Proves the full integration path without touching production content.
   - Required evidence: first-run import, second-run idempotency, unsupported-file skip, Sanity read-back, n8n execution IDs/logs, workflow still inactive.
2. **Real approved Drive folder → test Sanity dataset**
   - Proves real-world filenames, sizes, mime types, and folder access while keeping CMS output non-production.
   - Useful before production cutover because JMD treats approved-folder placement as approved showroom intake.
3. **Real approved Drive folder → production Sanity dataset**
   - Last step only, manual/inactive first, preferably with a tiny curated batch.
   - Still requires explicit approval before any schedule activation or public website dependency.

## Evidence to verify independently

After a builder/Claude/Codex claims the dry run passed, Hermes should verify directly:

- Sanitized artifact validates with the workflow validator.
- Unit/integration tests pass after any workflow changes.
- Sanitized artifact hash, active state, node count, connection count, and empty credential objects.
- Live n8n workflow remains inactive and has no temporary Manual Trigger left behind.
- Live credential bindings are test-only and bound only to expected nodes.
- n8n execution records show the claimed execution IDs and success/error states.
- Sanity read-back confirms expected doc count, deterministic `_id` / `sourceDriveFileId`, `status`, `syncStatus`, and image asset reference.
- Independent secret scan covers refreshed handoff artifacts, evidence docs, and templates.

## Per-file failure isolation

For import workflows, a single bad image should not abort the whole batch if the business goal is reconciliation.

- Use n8n `onError: continueErrorOutput` on download/upload/create-patch nodes where item-level failures should be isolated.
- Route failures into a dedicated collection/summary node.
- Pair back to origin items using n8n `pairedItem`, not array index, because successful and failed siblings can diverge across outputs.
- Do not write a Sanity doc for a failed asset upload. Let the next reconciliation run retry it.
- Adjust run summary counts so runtime failures net out of imported counts and appear in failure arrays.

## Fixture lesson

A corrupt or degenerate image fixture can be useful: it proves failure isolation. Do not hide this as a failed dry run if the workflow correctly imports valid items, skips unsupported files, records the failure, and remains idempotent.

If the user needs a clean demo, replace the bad fixture and re-run; otherwise, 1 clean import + 1 isolated image-pipeline failure can be stronger evidence than a synthetic 2/2 happy path.

## Closeout wording

Be precise:

- “Functionally satisfied” is appropriate when the core path, idempotency, skip behavior, failure isolation, Sanity read-back, inactive workflow, and secret scan are verified.
- “2/2 clean import proof” is only true if both supported fixtures import successfully.
- Keep production boundaries explicit: no production Drive, no production Sanity, no schedule activation, no deploy, no client-facing changes unless separately approved.
