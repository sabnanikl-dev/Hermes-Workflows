# Migration pre-cutover GSC baselines

Use this for same-domain or cross-domain migrations where rankings/traffic must remain attributable after cutover.

## Read-only capture sequence

1. Confirm OAuth identity, scope, property URL/type, and the current account's permission level.
2. Record the verified owner separately from the GSC UI. `sites.list` exposes the caller's permission level, not the verified owner's identity; do not infer owner from `siteFullUser`.
3. Query Search Analytics over the required 3–6 month window, ending several days back for data lag. Capture page, query, date, device, and country dimensions when useful.
4. Also query a 16-month-ish diagnostic window when seasonality matters.
5. If Search Analytics returns zero rows, report **no Performance rows available**, not “zero traffic.” Keep clicks, impressions, CTR, position, top pages/queries, and seasonality UNKNOWN until data appears or a manual export is supplied.
6. Record that the Page Indexing report's aggregate count is not exposed by the API. Get the total from the GSC UI; do not substitute an inspection sample as a global count.
7. Read `sitemaps.list` without mutating it. Separately fetch the current public sitemap/index and recursively inventory its `<loc>` URLs.
8. URL-inspect the migration-critical inventory: homepage, legacy pages, every product/product-category URL, legal/shop/account surfaces, and any taxonomy/pagination paths implicated by the move.
9. Cross-check indexed URLs against the redirect manifest. Check public path shapes beyond obvious `/product/*` and `/product-cat/*` rules—color/tag/taxonomy paths, pagination, and query-form taxonomies can otherwise fall through to 404.
10. Preserve a date-stamped Markdown report plus sanitized JSON export before cutover.

## Interpreting URL Inspection

- Summarize counts by `coverageState`, but preserve URL-level results in the JSON export.
- Treat indexed legacy product/category/legal URLs as evidence that direct single-hop 301s are a real migration precondition.
- “Unknown to Google” or “discovered/not indexed” URLs may still need deterministic visitor-safe handling even if they carry less search-equity risk.
- A net-new destination starts with no history. Post-cutover monitoring should track first indexing and first impressions rather than calling early flatness a regression.

## Suspicious or stale submitted sitemaps

Historical misspelled, HTTP, erroring, or now-404 sitemap submissions are a finding, not proof of a current compromise.

- Record path, submission/download dates, warnings/errors, and current HTTP status.
- Check Security Issues and Manual Actions in the GSC UI through the human approval gate.
- Do not delete stale sitemap records, file reviews/reconsideration requests, or submit a replacement sitemap without explicit approval.
- Keep the current public sitemap's state distinct from GSC's submitted-sitemap history.

## Analytics continuity is a separate gate

GSC clicks are not web-analytics sessions. Before declaring measurement continuity:

- Inspect the live site's actual tracking tags and identify whether they are current or retired.
- Confirm reporting access; the mere presence of a tag is not evidence that usable reports exist.
- Verify the replacement site has its selected provider implemented, loads once, and records agreed conversion events.
- If an initial public HTML fetch is blocked by an anti-bot/security response, retry with browser-like request headers or a browser before concluding tags are absent.
- Keep the migration tracker open when analytics implementation, provider choice, or reporting access is unresolved.

## Artifact and tracker closeout

- Sanitize exports: exclude access tokens, refresh tokens, client secrets, and Authorization headers.
- Verify JSON parsing, report/export number parity, folder/index references, approval-boundary wording, and durable wiki/client-profile readback.
- If no canonical project test exists, run a temporary ad-hoc verifier and label it as ad-hoc verification, not suite green.
- Do not check acceptance criteria that remain data-dependent. Keep the issue In Progress and comment the captured evidence plus explicit blockers.
- Start the 4–8 week monitoring cadence only after cutover; do not pretend a pre-cutover watcher satisfies post-cutover monitoring.
