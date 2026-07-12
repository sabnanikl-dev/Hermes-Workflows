# CMS Fallback Merge Pattern

Use this when a Femme Events section is partly migrated from static fallback data to Sanity CMS.

## Problem pattern

A fetch layer that chooses `CMS data if result.length > 0 else fallback` can erase most of the site when Amanda creates a single test CMS record. This happened on Issue 62: Sanity returned one test vendor category/vendor, so the frontend stopped rendering the full fallback vendor list.

## Correct behavior

- CMS records should appear first and win when they match fallback records.
- Static fallback records should remain visible for any missing categories/items.
- Empty CMS, failed CMS, or unconfigured Sanity should still return fallback data.
- Duplicates should be removed using stable human keys such as normalized category title, vendor name, or slug.
- Do not rely on array length alone as the decision boundary for replacing fallback content.

## Implementation checklist

1. Keep `src/data/<type>.ts` as the authoritative fallback interface + local data.
2. Add a pure merge helper in `src/lib/<type>Merge.ts` or similar.
3. Normalize keys before comparison: lowercase, trim whitespace, and use slug/name fallbacks.
4. For nested structures, merge by category first, then merge category items by vendor/item key.
5. Prefer CMS fields on conflicts, but append fallback-only records.
6. Add/keep guards for no Sanity client, fetch errors, and empty results.
7. Verify by testing all three states:
   - no CMS data
   - sparse CMS test data
   - overlapping CMS data that should de-dupe fallback entries
8. Mention the merge behavior in the PR so reviewers know partial CMS entry will not blank the public site.

## Review pitfall

If adding a new Sanity schema or CMS-backed section, reviewers should explicitly check whether sparse CMS data hides fallback content. The failure mode is visible only after someone creates one real/test CMS record.