# JMD Showroom Run Reporting + Owner-Safe SOP Contract

Use this when grooming or implementing JMD-29 / GitHub #66-style work: run reporting, owner-safe SOPs, and branded operator reports for the Drive → n8n → Sanity showroom photo automation.

## Target artifact

The deliverable should be a **beautiful branded HTML report**, not a plain markdown dump or raw n8n summary. It should be understandable by Karan/Hermes as an operator report and by Lucky/Danny as an owner-safe SOP without requiring them to know n8n or Sanity.

Recommended artifact locations:
- Website repo implementation tracker: GitHub #66 / Linear JMD-29.
- Likely repo path: `automation/n8n/reporting/` or another clearly documented path under `automation/n8n/`.
- Pair a generated sample report with source/template/generator docs if that improves maintainability.

## JMD brand requirements

Match the website design language from `docs/design/jmd-brand-context.md`:
- Navy `#010092`
- Midnight `#000846`
- Gold `#C8A24A`
- Cotton/off-white `#F7F7F4`
- Ink `#090A18`
- Border `#E7E7EA`
- Steel `#8C8FA3`
- White `#FFFFFF`
- Typography: Libre Franklin / Inter / system sans; mono labels for operational metadata.
- Visual style: premium menswear, crisp cards, uppercase mono labels, navy header/footer, gold rules/badges, generous spacing, mobile-first, print-friendly.

Required report sections:
- Branded header with title, run status, timestamp.
- Executive summary cards for counts.
- Status badges: success / warning / failed / guard-aborted / dry-run / production.
- Owner-safe SOP section in plain English.
- Operator diagnostics section with details separated from owner-facing content.
- Failure table that is actionable without leaking secrets.
- Responsive layout and print/export-friendly styling.

## Current automation facts to reflect

Canonical flow:
`Lucky/Danny approved real photos → Google Drive approved parent/collection folder → n8n scheduled reconciliation → Sanity showroomPhoto docs + image assets → JMD website On the Floor section reads Sanity only`.

Current production graph is the 25-node Drive → Sanity import/touch/archive workflow:
- Schedule Trigger.
- Load runtime config from env.
- List approved Drive folder.
- Partition direct files vs one-level nested collection folders.
- List nested collection folder files.
- Normalize/filter image records.
- Suspicious-zero / empty-source guard.
- Query Sanity `showroomPhoto` ledger.
- Compute import/touch/archive plan.
- Import branch: download missing file → upload Sanity asset → create/patch doc.
- Touch branch: patch existing source-present sync/metadata fields only.
- Archive branch: patch docs to `status='archived'` with `archivedAt` + `archivedReason`; never delete.
- Build run summary.

Evidence known from related work:
- Import completed against production: 50 approved source photos mapped to deterministic docs/assets; re-runs idempotent.
- Archive/removal implemented and verified; archive is patch-only / no hard-delete.
- Website `#on-the-floor` reads production Sanity only and exposes a public-safe projection with only image URL, alt text, dimensions.
- Earlier schedule activation had a verified successful trigger-mode run with 50 source docs, 18 live, and 32 archived under the older limit/window state.
- Later live-limit restore work expanded the intended public/showroom window to 50; current reporting fixtures/samples should reflect the current contract/end-state (50 live/published, 0 archived, desiredLive 50) unless deliberately rendering an archived historical run.
- Durable runner remains separate under JMD-42; do not hide it inside reporting/SOP work.

## Report data contract

Support graceful `N/A` when fields are unavailable.

Run identity:
- generated timestamp **and actual run/execution timestamp** (separate fields; saved summaries may be rendered later), workflow name, workflow ID/internal label, n8n execution ID/link, trigger mode (`scheduled`, `manual`, `cli`, optional Drive fast-path), dry-run/test vs production, n8n version, workflow export/source path.

Source/folder:
- safe Drive source label (not raw private folder ID in owner-safe mode), direct vs collection-container mode, collection folder count/names, supported image count, unsupported file count/reasons, Drive listing success, suspicious-zero/empty-with-live-docs guard state.

Reconciliation counts:
- source images found, existing Sanity docs observed, imported, touched/synced, published/live after run, archived this run, archived total after run, skipped, failed, unsupported, desired live count, duplicate `sourceDriveFileId` count, doc/asset deltas if available.

Archive detail:
- `removed_from_drive_folder`
- `older_than_live_limit`
- `older_than_90_days`
- `manual_archive`
- `sync_error`

Failure detail:
- safe file name, step (`Drive list`, `download`, `Sanity query`, `asset upload`, `doc create`, `touch patch`, `archive patch`, `guard`), error summary, continued vs aborted, recommended next action. Raw file IDs and credential IDs should be operator-only and omitted/redacted in owner-safe mode.

Guard aborts should read as protective safety stops when no mutation occurred — not as generic unexplained failures.

## Owner-safe SOP content

For Lucky/Danny:
1. Put only approved real JMD showroom photos in the approved Drive folder.
2. Folder placement means “approved for website showroom use” in v1.
3. Use clear, well-lit, public-ready JMD photos.
4. No stock images or AI images.
5. Avoid customer faces unless intentionally approved.
6. Move/remove a photo from the approved folder if it should stop showing.
7. Moving/removing archives it from the website feed; it does not delete the record/assets.
8. The site shows recent showroom highlights, not a full inventory catalog.
9. If something looks wrong, tell Karan/Hermes rather than trying to edit n8n.

For Karan/Hermes:
- Name sanitized workflow artifact paths and restore/import notes.
- List env var names only, not values: `DRY_RUN`, `GOOGLE_DRIVE_TEST_FOLDER_ID`, `GOOGLE_DRIVE_APPROVED_FOLDER_ID`, `SANITY_PROJECT_ID`, `SANITY_DATASET`, `SANITY_API_VERSION`, `LIVE_LIMIT`, `MIN_LIVE`, `MAX_PHOTO_AGE_DAYS`, `MAX_ARCHIVE_PER_RUN`, plus `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` when using `$env.*` in n8n nodes.
- Name credential purposes only: Google Drive OAuth2 for folder read/download; Sanity HTTP Header Auth for query/upload/create/sync patch/archive patch.
- Explain how to distinguish n8n execution modes (`trigger`, `manual`, `cli`) **when checking recent executions**.
- Include paused/deactivated workflow response: do not reactivate production schedules from the report alone; confirm whether inactive/paused/error-disabled state is intentional; get explicit Karan approval before activation; verify env access, credentials, workflow version, and a safe test/dry-run path first.
- Failure response: do not delete Sanity docs/assets; check Drive access/source emptiness; check Sanity token/project/dataset; confirm n8n env access; test/dry-run before production mutation when possible; export → sanitize → validate after workflow logic changes.

## Implementation pattern that worked

For JMD-29-style branded reporting, a maintainable repo artifact is stronger than a one-off static HTML file:
- Put the reporting layer under `automation/n8n/reporting/` with a zero-dependency generator, safe/redacted JSON fixtures, committed owner-safe sample HTML outputs, and a README explaining regeneration.
- Default the generator to **owner-safe mode**; require an explicit `--operator` flag for internal diagnostics that may retain raw IDs. Do not commit operator/internal reports as canonical samples.
- Include fixtures for at least three states: success/idempotent, continued file-level failure, and guard-aborted protective stop. This makes the acceptance criteria executable rather than prose-only.
- Add a validator that regenerates samples and checks required sections, owner-safe redaction/no secret-like patterns, responsive CSS hooks, and print CSS hooks. Wire it into the repo's normal test path when appropriate.
- For visual QA, serve the repo over local HTTP, open a temporary responsive harness with 375px / 768px / 1440px iframes, inspect with browser/vision, check computed grid columns, confirm print CSS exists, and read browser console errors before handoff.
- In the PR/body/handoff, explicitly separate evidence classes: static/package validation, local browser rendering, redaction scan, and no-live-mutation boundary. Do not overclaim live end-to-end proof unless a separately approved credentialed run happened.

## Hard gates / exclusions

Do not use this issue to authorize:
- live credential/account changes;
- schedule activation/deactivation;
- live Drive or Sanity mutation without a separate explicit approval;
- Drive deletion or Sanity hard-delete;
- website deploy/DNS/hosting changes;
- client/owner-facing delivery to Lucky/Danny.

Owners should not be asked to use n8n or Sanity directly in v1.

## Verification checklist

- Render/open the HTML report locally.
- Check 375px, 768px, 1440px.
- Check print/export styling.
- Render success/idempotent, file-level failure, and guard-aborted fixture states.
- Verify fixtures include an actual run/execution timestamp separate from report generation time.
- If the source contract moved since the first report draft (for example live-limit 9 → 50), rebase/sync first and update success fixtures to the current state rather than preserving stale historical counts.
- Verify owner-safe mode redacts/omits raw private IDs and secrets.
- Search artifacts for token/API-key/private ID patterns.
- Confirm SOP does not contradict current automation: 25-node graph, nested folder support, Sanity-only website, archive-not-delete, no Drive deletion, mass-archive guards.
