# JMD showroom photo automation — timing explanation

Use this when Karan asks for a plain-English/client-safe explanation of how JMD showroom photos move from Drive to the website, especially timing, retention, and removal behavior.

## Flow

```text
Lucky/Danny approved real photos
  → configured Google Drive approved folder
  → n8n scheduled reconciliation
  → Sanity `showroomPhoto` docs + Sanity image assets
  → website “On the Floor” feed reads Sanity-derived public data only
```

Do **not** describe this as direct Drive-to-website publishing. The website must not serve public Drive URLs or expose Drive IDs/file names/operator sync metadata.

## Timing model

There are two distinct timing layers:

1. **Drive → Sanity backend**: n8n reconciles the approved Drive folder on its configured schedule. In the verified JMD local workflow, the schedule was every 6 hours. Explain as “picked up on the next scheduled sync,” not “instant.” If exact timing matters, inspect the current workflow schedule/export or n8n DB/API before stating hours.
2. **Sanity → public static website**: the current static site uses a generated `site/assets/js/on-the-floor.data.js` public feed built from Sanity. A Sanity change does not automatically change the public website unless the feed is rebuilt and deployed, or a future dynamic/revalidation path is added.

Client-safe wording:

> Photos are picked up by the backend on the next scheduled sync. Once the website feed is refreshed and published, they appear on the site.

## New image behavior

On each successful reconciliation:

- n8n lists the approved Drive folder and descends one level into collection subfolders.
- Supported image files are matched to Sanity by `sourceDriveFileId`.
- Missing files are downloaded from Drive, uploaded to Sanity’s image CDN, and created as published `showroomPhoto` docs.
- Existing files are **touched**, not duplicated: sync/source metadata is refreshed, but image assets/status/published/archive fields are not unnecessarily rewritten.

Repeated runs should be idempotent: the same Drive file should not create duplicate public records.

## How long photos stay live

Default policy concepts:

- `LIVE_LIMIT`: newest-N live window.
- `MIN_LIVE`: newest-N floor that age policy cannot archive.
- `MAX_PHOTO_AGE_DAYS`: age cutoff for source-present photos, subject to `MIN_LIVE`.
- `MAX_ARCHIVE_PER_RUN`: safety threshold; too many archives in one run should fail closed.

Before giving current numeric values, inspect the current env/workflow config because values can change. In the June 2026 JMD production env, observed values were `LIVE_LIMIT=50`, `MIN_LIVE=3`, `MAX_PHOTO_AGE_DAYS=90`, `MAX_ARCHIVE_PER_RUN=40`.

## Removal behavior

If a photo is moved out of or removed from the approved Drive folder, the next successful reconciliation archives the matching Sanity doc with `archivedReason = removed_from_drive_folder`. Archive means hidden from the public feed, **not deleted**.

For the current static feed, public disappearance still requires the website feed to be refreshed/deployed after Sanity changes.

## Safety language

Mention the fail-closed safety posture when explaining to Karan/client:

- failed Drive listing does not mass-archive everything;
- suspicious empty source while live docs exist aborts;
- duplicate ledger/auth/query failures abort;
- too many archive candidates abort;
- v1 archives/restore-patches only — no Drive deletion and no Sanity hard-delete.

## Verification checklist before client-facing claims

Before saying “this runs every X hours” or “this is live now,” verify current state:

- workflow schedule from the n8n export/API/DB;
- whether the workflow is active and whether a runner is actually running;
- latest successful `mode=trigger` execution, not just CLI/manual runs;
- current env policy values (`LIVE_LIMIT`, `MIN_LIVE`, `MAX_PHOTO_AGE_DAYS`, `MAX_ARCHIVE_PER_RUN`);
- whether the website is still static feed rebuild/deploy or has a dynamic/revalidation path.
