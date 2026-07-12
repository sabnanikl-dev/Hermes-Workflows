# JMD Drive → Sanity Photo Automation Pattern

Session source: JMD Menswear planning discussion around deterministic n8n workflows for website photo rotation.

## Business Constraints

- JMD website is a showroom, not e-commerce.
- Real JMD photos only: no AI-generated images and no stock photos.
- Avoid checkout, price, quantity, exact size availability, live inventory, or “in stock” claims.
- For v1, if Lucky/Danny place an image in the configured Drive folder, that counts as approval.

## Recommended v1 Architecture

- **Google Drive approved folder**: source of truth.
- **n8n**: deterministic scheduled reconciliation.
- **Sanity**: CMS/image CDN and operational ledger.
- **Website**: queries Sanity only; never Drive URLs directly.

Core rule:

> Given the current approved Drive folder, make Sanity match the desired website state.

## Deterministic Rules

### Import

- List current files in approved Drive folder.
- Filter supported image MIME types: JPEG, PNG, WebP. HEIC is an explicit open decision.
- For each file, check Sanity for `sourceDriveFileId`.
- If absent: download from Drive, upload asset to Sanity, create `showroomPhoto` doc.
- If present: skip asset creation or patch metadata only.
- Set imported approved images to `status = published` and `publishedAt = now`.

### Archive / Rotation

Preferred v1 hybrid policy:

- Show latest 9 approved Drive images.
- Archive older images.
- Archive anything older than 90 days.
- Keep at least 3 live images if at least 3 approved images exist.
- If a Drive file is removed/moved out of the folder, archive matching Sanity doc with `archivedReason = removed_from_drive_folder`.
- Never hard-delete Sanity docs/assets in v1.

### Mass-Archive Guard

If Drive listing fails or unexpectedly returns zero, abort instead of archiving everything. Use Stop And Error and notify Karan/Hermes.

## Sanity Schema Fields

Recommended doc type: `showroomPhoto`.

Core fields:

- `mainImage`
- `altText`
- `sourceDriveFileId`
- `sourceDriveFileName`
- `sourceDriveCreatedTime`
- `sourceDriveModifiedTime`
- `sourceDriveMimeType`
- `importedAt`
- `publishedAt`
- `archivedAt`
- `archivedReason`
- `syncLastSeenAt`
- `syncStatus`
- `syncError`
- `status`

Avoid product fields: price, quantity, SKU, checkout, cart, stock, exact size availability.

## n8n Components That Matter

Useful:

- Google Drive node: list/search/download files.
- HTTP Request node: Sanity API calls and binary asset upload.
- Code node: deterministic set math, sorting, archive decisioning, payload shaping.
- Error Workflow + Stop And Error: dangerous states and failure notifications.
- n8n CLI / Server CLI: workflow export/import, execution inspection, backups.
- Workflow JSON export: store as repo artifact with credentials redacted.

Noise / avoid for v1:

- n8n AI agents.
- custom n8n node development.
- n8n source-code internals.
- Google Drive Trigger as the sole source of truth.
- n8n Data Tables unless Sanity docs/logs prove insufficient.
- decrypted credential exports except controlled migration.

## Linear Packet Created

Parent issue: deterministic Google Drive → Sanity photo automation for JMD showroom images.

Child issue categories:

1. n8n-first architecture doc.
2. Sanity showroom photo schema/query contract.
3. n8n scheduled Drive → Sanity import reconciliation.
4. archive/removal reconciliation rules.
5. website showroom section from Sanity only.
6. n8n run reporting and owner-safe SOP.

Do not store specific issue numbers in durable memory; this reference keeps the reusable plan shape.
