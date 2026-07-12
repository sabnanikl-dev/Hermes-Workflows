# Production cutover gates for client automations

Use when a workflow has already passed test-resource validation and the user supplies a real production source/target identifier (Drive folder, CMS dataset, CRM list, etc.).

## Pattern

1. Treat the supplied production identifier as sensitive operational config even if it arrived as a URL in chat.
2. Store the full value only in a gitignored local secret/config location (`.env`, encrypted vault, or client-specific ignored secret dir).
3. Add only a redacted local inventory file, e.g. `.jmd36-secrets/approved-drive-folder.redacted.json`, containing:
   - issue/task id;
   - resource purpose;
   - who supplied it;
   - env var / local storage name;
   - redacted identifier shape (`prefix…suffix`);
   - `access_verified: false` until a read/list check is approved and run;
   - explicit warning not to post/commit the full value.
4. Ensure the secret dir is ignored and locked down (`0700` dir, `0600` file where possible).
5. Create or update a gate checklist doc with remaining approvals before any production read/list/binding/run:
   - approved account/credential for source read;
   - approved target project/dataset/token scope;
   - approval for first smoke test to create/mutate real records;
   - exact limited items for first smoke test;
   - separate schedule/activation approval after evidence.
6. If updating Linear/GitHub, post only redacted status: env var names, credential purposes, run-state expectations, and boundaries. Do not post raw source IDs/URLs or tokens.
7. Verify before reporting:
   - tests/validators still pass if files changed;
   - no raw production identifier appears in public/tracked files;
   - workflow remains inactive;
   - no production read/list, target mutation, credential binding, or activation happened unless explicitly approved.

## Key pitfall

“Preparing the gate” is not the same as “starting production cutover.” A real source folder/dataset URL from the user authorizes storing/preparing the approval packet, not listing the folder, binding production credentials, smoke-running, or activating a schedule unless those actions are explicitly approved.