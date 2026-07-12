# Vendor import from static branch data

Use this when a branch adds or updates static vendor fallback data and Karan asks to populate the live Sanity CMS with the same records.

## Pattern

1. Inspect the branch data source, usually `src/data/vendors.ts`, and the matching Studio schemas under `studio/schemas/vendor*.ts`.
2. Query Sanity first to see existing `vendorCategory` and `vendor` documents. If live data contains test/placeholder content, ask before deleting it. If the user does not respond and the task should proceed, prefer non-destructive cleanup: unpublish placeholder vendors rather than deleting documents.
3. Create a temporary import script under `studio/scripts/*.tmp.ts` so `sanity exec` can resolve `sanity/cli` from the Studio install. Remove it after the import.
4. Use stable deterministic IDs so reruns are idempotent:
   - `vendorCategory-<slug(label)>`
   - `vendor-<slug(name)>`
5. Use `createOrReplace` for categories and vendors in a transaction.
6. Convert full Instagram URLs to handles because the schema field is `instagramHandle` and frontend code normalizes it into a URL.
7. Set `published: true` for real imported vendors and numeric `order` fields in display order.
8. Verify by querying Sanity for the expected category count, vendor count, and visible vendor names. Confirm temporary files are deleted and `git status --short` is clean.

## Node/Sanity CLI workaround

If the local Sanity CLI fails under a bleeding-edge Node version with an ESM/CJS error from `yargs`, do not record that as a permanent broken-tool fact. Run the command with a supported Node version one-shot instead, for example:

```bash
npx -p node@22 -p sanity@3.50.0 sanity exec scripts/import-vendors.tmp.ts --with-user-token
npx -p node@22 -p sanity@3.50.0 sanity documents query '*[_type == "vendor"]{name,published}' --api-version 2024-01-01
```

Adjust the Sanity version to match `studio/package.json` when it changes.
