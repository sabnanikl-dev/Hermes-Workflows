# Search Console Post-Access Baseline Pattern

Use this when Search Console access has just been granted after an earlier OAuth/API/property blocker.

## Sequence

1. Re-run the blocker ladder from the top, but treat the old blocker as stale until reverified:
   - refresh/verify the OAuth token identity,
   - run `sites.list`,
   - confirm the intended property and permission level are visible.
2. Capture a read-only baseline export before any mutation:
   - `sites.list`,
   - Search Analytics totals and dimensions for a 90-day window ending ~3 days before today,
   - optional 16-month back-check if the 90-day window returns no rows,
   - `sitemaps.list` and `sitemaps.get` for the current production sitemap,
   - URL Inspection for canonical and obvious alternate homepage URLs (`www` vs non-`www`).
3. Interpret no-row Search Analytics responses carefully:
   - HTTP 200 with no rows is not an access failure.
   - Record it as zero/no recorded performance baseline for comparison, with the exact date range.
4. Compare Search Console sitemap state to production reality:
   - Current production sitemap may be live but not submitted/known in Search Console.
   - Legacy HTTP sitemap entries can remain from old sites; document them separately from the current HTTPS sitemap.
5. Keep mutation boundaries explicit:
   - read-only inspection/reporting is okay,
   - sitemap submission is a Search Console account mutation and needs explicit approval,
   - DNS, verification, robots, sitemap, redirect, and canonical changes need their own approval/PR lane.
6. If a parent issue mixed baseline capture with approval-gated sitemap submission, split remaining work into a Ready child issue rather than leaving the baseline issue ambiguous.

## Artifact language

Prefer:

- “Access resolved; baseline captured.”
- “Search Analytics returned no rows for DATE_RANGE; use as zero/no recorded performance baseline.”
- “Current HTTPS sitemap is live but not submitted/known in Search Console.”
- “Sitemap submission remains approval-gated and is tracked separately.”

Avoid:

- Saying metrics are still blocked when the API returns HTTP 200 with no rows.
- Treating sitemap submission as part of read-only baseline work.
- Closing over historical `www` / HTTP state without documenting how production currently redirects/canonicalizes.
