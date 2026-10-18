# n8n Local Operations Notes

Use these notes when the user asks to run or access a local n8n server from Hermes.

## Starting n8n locally

1. Check whether n8n is already installed and whether the default port is occupied:
   ```bash
   command -v n8n || true
   command -v npm || true
   command -v node || true
   lsof -nP -iTCP:5678 -sTCP:LISTEN || true
   pgrep -fl 'n8n|node.*n8n' || true
   ```
2. If port `5678` is free, start n8n as a tracked Hermes background process, not with shell `&`:
   ```bash
   N8N_HOST=127.0.0.1 N8N_PORT=5678 N8N_SECURE_COOKIE=false npx --yes n8n start
   ```
   Use `background=true` and a readiness watch pattern such as `Editor is now accessible`, `n8n ready`, or `Server is listening`.
3. For a user-authorized long-lived server, explicitly set `persist_on_release=true` on the tracked terminal process; a normal background process is session-owned and must not be assumed to survive cleanup. This does not survive host/process restarts or replace an approved OS service. Pin and install a security-reviewed runtime rather than using an unversioned `npx` launcher for unattended recovery. Set `N8N_LISTEN_ADDRESS=127.0.0.1` as well as `N8N_HOST=127.0.0.1`: HOST alone does not establish loopback binding. Verify both UI and task-broker listeners.
4. Verify readiness independently:
   ```bash
   lsof -nP -iTCP:5678 -sTCP:LISTEN || true
   curl -sS -I http://127.0.0.1:5678/
   ```
   Report the local URL only after an HTTP `200 OK` or equivalent reachable response.

## Updating and running a published workflow on n8n 2.26.x

For a live workflow update, export and back up the current workflow/database before mutation. Preserve the live export's credentials, settings, schedule, IDs, and activation state; apply only the reviewed graph transform rather than importing a sanitized credential-free repository artifact directly.

Important n8n 2.26.x behavior:

- `import:workflow` **deactivates** an imported workflow, even when the JSON says `active: true`.
- Restore activation with `publish:workflow --id=<workflow-id>` after import, then restart n8n. The deprecated `update:workflow --active=true` should not be the default.
- Independently export the workflow after import/publish and verify active state, node count, credential-reference shape, schedule, absence of pin data, and the reviewed graph change.
- Stop the running n8n server before CLI execution. Otherwise the CLI's internal task broker can fail because port `5679` is already occupied.
- `n8n execute --id=<workflow-id>` requires an `Execute Workflow Trigger`; a schedule-only workflow fails with `Missing node to start execution`.

Safe controlled-run pattern for a schedule-only production workflow:

1. Stop the tracked n8n server.
2. Export the exact published workflow as the restore artifact.
3. Prepare a temporary runnable copy by adding only one `Execute Workflow Trigger` wired to the normal first processing node; set the temporary copy inactive.
4. Import the temporary copy and run `n8n execute --id=<workflow-id>` with the approved production environment and a non-default broker port if needed.
5. Use a trap/finally path to re-import the exact restore artifact and run `publish:workflow --id=<workflow-id>` even when execution fails.
6. Export/read back the restored workflow and prove the temporary trigger is absent, the reviewed graph is present, credentials/schedule are unchanged, and the workflow is active.
7. Restart n8n, verify `/healthz` and the `Activated workflow ...` log line, then verify the saved execution and downstream data independently.

Never leave a temporary trigger, test folder ID, pin data, inactive schedule, or unverified import behind after the controlled run.

## Upgrade and security verification

- Back up the entire n8n home, including encryption configuration and storage, with a consistent SQLite backup. Keep backups private. Test migrations on an isolated copy with every workflow deactivated; do not start a cloned production scheduler.
- Check both the exact n8n version in OSV and its resolved dependency tree with npm audit. Aggregate inherited package ratings are not independent exploitable vulnerabilities. Review concrete advisories and relevant module resolutions before accepting risk; do not claim zero risk from a clean direct-package query.
- Do not run `npm audit fix --force` blindly: suggested fixes can downgrade n8n across major versions. For a reviewed narrow dependency patch, preserve a lockfile, verify `npm ls` exits cleanly, and exercise the actual Code/task-runner and Drive/HTTP paths before production. Exact global overrides can invalidate already-newer nested versions; a patched compatible range plus lockfile can preserve those versions without downgrading them.
- A production-folder read-only preview must physically remove downstream mutation nodes/edges in an isolated workflow copy. `DRY_RUN` may only choose the test folder or stamp output; do not assume it guards writes. Keep the production workflow untouched during the preview, and execute the exact installed normalization/planning nodes rather than a stale repo implementation.
- On newer n8n 2.x, check `workflow_publication_trigger_status` for the active version and the schedule node's `activated` status, not only `workflow_entity.active`. A stale publication outbox entry can fail while a later reconcile entry successfully activates the current version; distinguish them before retrying publication.
- Keep first scheduled-run verification separate from a successful CLI catch-up. A freshness monitor may count an explicitly approved production CLI catch-up, but retain/report its actual `mode` and require `dryRun=false`, zero file failures, and a bounded freshness window.

## Password / account handling

- Do not claim to know a plaintext n8n password. n8n stores the user password hashed in the local SQLite DB.
- If the user asks “what is my password?”, first identify the owner account without exposing hashes:
  ```bash
  sqlite3 /Users/creator/.n8n/database.sqlite ".tables" | tr ' ' '\n' | grep -Ei 'user|auth|settings|credential'
  sqlite3 -header -column /Users/creator/.n8n/database.sqlite "SELECT id,email,firstName,lastName,roleSlug,disabled,mfaEnabled FROM user;"
  ```
- Summarize the account email/name/role/MFA state. Offer a reset only if needed.
- Resetting n8n user management or setting a new password is an account mutation; get explicit approval before doing it.

## Pitfalls

- `npx --yes n8n start` can take a while on first run and emit many npm peer/deprecation warnings. The durable signal is whether a `node ... n8n start` child process is listening on port `5678` and the HTTP endpoint responds.
- Avoid printing credential rows from `credentials_entity` or password hashes from `user.password` in the chat unless specifically needed for a safe diagnostic, and redact sensitive values.
