# Search Console Access Resolved Baseline Pattern

Use this when a local SEO / Google visibility issue was previously blocked on Search Console access, and the user says the agent account has now been added as a Search Console user.

## Immediate read-only sequence

1. Refresh/verify the OAuth token for the intended Google identity.
   - Confirm the signed-in identity before reading account data.
   - For this setup, the intended agent identity is commonly `karanagent20@gmail.com`, but verify from token/userinfo rather than assuming.
2. Re-run Search Console `sites.list`.
   - If the target property appears, record property type and permission level.
   - Prefer the visible property exactly as returned, e.g. `sc-domain:example.com` vs URL-prefix properties.
3. Pull Search Analytics for a comparison-ready baseline.
   - Use a 90-day window ending 2–3 days before today to allow Search Console data lag.
   - Query totals plus top `query`, `page`, `country`, and `device` dimensions.
   - If rows are empty, treat that as a valid baseline finding: “API succeeds; no rows returned,” not as an access failure.
   - Optionally run a 16-month back-check to distinguish new/no-data properties from short-window gaps.
4. Check sitemap state read-only.
   - `sitemaps.list` for all known/submitted sitemaps.
   - `sitemaps.get` for the current production sitemap URL.
   - Watch for stale legacy `http://` sitemap submissions vs current `https://` sitemap URLs.
5. Run URL Inspection read-only for the canonical homepage and any relevant alternate host (`www` vs non-`www`).
   - Capture coverage state, robots/indexing state, page fetch, last crawl, Google canonical, user canonical, and referring URLs if present.
   - If `www` is indexed but production redirects to non-`www`, record it as a monitoring item after recrawl, not necessarily an immediate bug.
6. Save the raw read-only API export under the project’s data folder, then update the human-readable artifact.
7. Keep mutation boundaries explicit.
   - Do not submit sitemaps, request indexing, alter verification, DNS, robots, redirects, or website code without explicit approval.

## Artifact language

Useful status phrases:

- “Access resolved: `sites.list` shows `<property>` with `<permissionLevel>`.”
- “Search Analytics API succeeds but returns no rows for the baseline window; use as zero/no recorded performance baseline.”
- “Current HTTPS sitemap is live in production but not submitted/known in Search Console.”
- “Legacy HTTP sitemap is still listed in Search Console; monitor or replace only after approval.”
- “URL Inspection shows crawled but currently not indexed; crawling/indexing are allowed, so next action is sitemap submission/recrawl monitoring if approved.”

## Linear handoff

When updating a Linear visibility issue after this sequence:

- Link the updated artifact and raw API export.
- State the verified property and permission level.
- Summarize no-row metrics clearly so it is not mistaken for a failed pull.
- List URL Inspection and sitemap findings.
- End with: “No Search Console mutation was performed. Sitemap submission remains approval-gated.”
