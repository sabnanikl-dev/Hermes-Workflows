# JMD-style test resource gate for n8n Drive → Sanity dry-runs

Use this pattern when a credential-gated dry-run needs test Google Drive + test Sanity + local n8n resources before production activation.

## Separate setup from execution approval

Creating disposable **test-only** resources can be a prep step, but it is not the same as approving the workflow execution gate. Keep these states distinct:

1. **Resource setup** — create/locate test Drive folder, test Sanity dataset/project/token, local n8n API access, fixture files, and redacted inventory.
2. **Execution approval** — human/Hermes explicitly approves manual run against those named test resources, including whether Sanity test assets/docs may be created/updated/deleted.

Never treat “set up test resources” as permission to run the workflow.

## Minimum setup packet

- Test Drive folder name/purpose, with actual folder ID stored only in local `.env` or secret store.
- Safe fixture set: 1–2 supported images plus 1 unsupported file for skip/log proof. Avoid client-sensitive images.
- Test Sanity target: project/dataset name, dataset visibility, token label/role; actual project ID/token stored only locally.
- n8n test instance URL/API check; do not activate schedules.
- `.env`/secret directory permissions checked (`0600`/`0700` on macOS/Linux when local files are used).
- `.gitignore` covers local secret/resource folders.
- Redacted handoff note in repo docs with names/purposes only, no token/folder/private IDs.

## Pre-run checks before approving execution

Before manual dry-run, require the builder to confirm the **actual n8n process environment**, not just the local `.env` file:

- `DRY_RUN=true` is visible to n8n.
- Workflow uses `GOOGLE_DRIVE_TEST_FOLDER_ID`, not `GOOGLE_DRIVE_APPROVED_FOLDER_ID`.
- Sanity resolves to the test dataset/project.
- Credentials are bound only in the local/test n8n credential store.
- Workflow is inactive; execution is manual/test-only.

If the n8n process was already running before `.env` changes, restart/relaunch it with the updated environment before dry-run.

## Evidence to capture after execution

- First-run import counts and created Sanity doc/asset IDs, redacted as needed.
- Second-run idempotency: zero duplicate docs/assets.
- Unsupported-file skip/log evidence without run failure.
- Sanity read-back: deterministic `_id`, `sourceDriveFileId`, contract fields/enums.
- n8n execution IDs/log snippets with secrets redacted.
- If workflow changed: re-import → re-export → re-sanitize → validate → Hermes secret scan before PR/final handoff.
