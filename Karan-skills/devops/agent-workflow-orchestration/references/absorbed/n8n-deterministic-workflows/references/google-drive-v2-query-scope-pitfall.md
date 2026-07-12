# Google Drive v2 raw-query scope pitfall in n8n

Use this when a Google Drive node can authenticate, but a folder-list/search run fails with `403 insufficientScopes` or returns no rows even though the OAuth token has Drive scope.

## Symptom

- n8n credential test says `Connection Successful`.
- Direct Google Drive API list with the same OAuth token works when using `spaces=drive`.
- n8n Google Drive v2 `fileFolder` search fails with Google error text like:
  - `The granted scopes do not give access to all of the requested spaces.`
  - or `403 insufficientScopes`.

## Cause

For Google Drive v2 `fileFolder` search, n8n's default raw query path can include:

```text
spaces=appDataFolder, drive
corpora=allDrives
```

A normal Drive OAuth token may have `https://www.googleapis.com/auth/drive` but not the app-data scope. The request can fail because n8n asks Google for the app-data space unnecessarily.

Separately, raw Drive `q` syntax requires folder IDs to be quoted:

```text
'<folderId>' in parents and trashed = false
```

An unquoted ID can produce `400 Invalid Value` at parameter `q`.

## Fix pattern

On the Google Drive list/search node:

1. Use the raw query path explicitly:
   - `searchMethod = query`
2. Quote folder IDs in the query expression:
   - n8n expression shape: `={{ "'" + $json.approvedFolderId + "' in parents and trashed = false" }}`
3. Add a folder filter with root to force n8n's helper to narrow request space:
   - `filter.folderId = { "__rl": true, "value": "root", "mode": "id" }`
   - this causes `spaces=drive` and `corpora=user` rather than `spaces=appDataFolder, drive`.

## Safe verification pattern

Before running the full workflow:

1. Keep the workflow inactive.
2. Temporarily add a Manual Trigger if CLI execution requires one.
3. Temporarily cut all downstream connections immediately after the Drive-list node so no CMS/API mutation nodes can execute.
4. Run the workflow once and confirm the Drive node returns the expected fixture names/MIME types.
5. Restore the clean graph, verify the temporary trigger is gone, and verify `active=false`.
6. Only then proceed to the separate credentialed dry-run approval gate.

## Boundaries

This verification proves Drive listing only. It does not authorize or prove downstream CMS writes, idempotency, unsupported-file handling, or production activation.
