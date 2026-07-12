# n8n + Sanity production smoke test pattern

Use this when a Drive → n8n → Sanity workflow has passed test-resource proof and the user explicitly approves a limited production smoke.

## Durable lessons

- Treat production smoke as a separate gate from production schedule activation. A successful smoke run does **not** authorize activation.
- Prefer a local gitignored overlay such as `.env.<issue>-production` for production smoke variables. Keep the base/test `.env` intact when possible.
- Create redacted inventories for production resources under an ignored secret directory; never post raw Drive folder IDs, token values, credential IDs, or execution payloads to Linear/GitHub.
- If the approved Drive folder lists zero supported files, do **not** treat it as success. Existing suspicious-zero guards should stop before mutation. Investigate folder shape read-only; many client folders contain nested category/season folders rather than images directly.
- If a nested folder is discovered, run a **read-only graph cut** (Drive list + normalize only, no Sanity nodes connected) before deciding whether to point the smoke overlay at that child folder or implement recursion later.
- For first production smoke, cap the batch to 1–3 approved files with a temporary limit patch/env var and restore the workflow afterward. Verify no temp Manual Trigger or smoke-limit code remains.
- If a limited smoke proves the path but the production import is intentionally incomplete, create a final cutover/PR child before closing the parent import issue. That child should persist the proven workflow inactive, run the full approved-source import with explicit approval, run a second idempotency pass, re-export/sanitize, and open the repo PR. Keep schedule activation separate unless the user explicitly approves it.

## Sanity token creation

From the Studio directory for the verified project/dataset:

```bash
npm exec -- sanity debug
npm exec -- sanity dataset list
npm exec -- sanity tokens add "<issue> n8n production write token" --role=editor --json --yes
```

Store the returned token only in the local ignored overlay. Redact stdout/logs before summarizing. The token label and role are safe to mention; the token value is not.

## n8n HTTP Header Auth credential gotcha

Creating `httpHeaderAuth` credentials through the n8n API may require `allowedDomains` in `data`:

```json
{
  "name": "<issue> PROD - Sanity HTTP Header Auth",
  "type": "httpHeaderAuth",
  "data": {
    "name": "Authorization",
    "value": "Bearer <SANITY_TOKEN>",
    "allowedDomains": "*.api.sanity.io"
  }
}
```

Bind Sanity credentials only to the Sanity HTTP nodes. Bind Drive credentials only to Drive list/download nodes. Re-query the workflow and report node names + credential purpose/name only.

## Safe production smoke sequence

1. Verify upstream Studio/project issue/PR is actually merged/closed and extract public project/dataset from repo docs.
2. Prepare ignored production overlay and redacted inventories.
3. Run preflight that only checks local overlay + n8n workflow state/credential slots — no Drive/Sanity read/mutation.
4. Create approved Sanity token and n8n credential; bind approved Drive/Sanity credentials to expected nodes.
5. Re-query workflow state: `active=false`, expected credential-bound nodes, no schedule activation.
6. If using CLI execution, add a temporary Manual Trigger and any smoke limit; save a workflow backup first.
7. When updating/restoring workflows through the n8n API, build the PUT payload from allowed workflow fields only. n8n GET responses can include read-only/instance-only `settings` keys such as `binaryMode` that the PUT schema rejects. Preserve `settings.executionOrder` if present, but strip rejected settings before PUT so restore cannot fail on schema validation.
8. Run first smoke (1–3 files), then second run for idempotency.
9. Read back Sanity docs and verify: deterministic `_id`, `sourceDriveFileId`, `status=published`, `syncStatus=synced`, `publishedAt`, image asset ref, duplicate source count `0`.
10. Restore workflow: remove temp Manual Trigger, remove smoke-limit code, keep `active=false`.
11. Run local validators and scan tracked/public files for raw Drive IDs/tokens/API keys.
12. Post evidence with execution IDs, counts, redacted read-back summary, inactive state, and remaining gates.

## Evidence language

Good summary shape:

- Baseline Sanity count.
- Run 1 execution ID + imported/skipped/unsupported/failed counts.
- Run 2 execution ID + idempotency counts.
- Sanity read-back summary without raw IDs.
- Workflow post-run inactive/restored state.
- Explicit remaining gates: schedule activation, archive/removal readiness, reporting/SOP, launch/deploy/client comms.
