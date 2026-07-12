# Search Console Baseline Blocker Ladder

Use this when a local SEO / Google visibility phase needs Search Console metrics but access is not fully working yet.

## Ladder

1. Verify OAuth scope first.
   - Required read-only scope: `https://www.googleapis.com/auth/webmasters.readonly`.
   - If missing, complete OAuth reauthorization before claiming property access is blocked.
2. Verify Search Console API enablement for the OAuth client project.
   - Run read-only `sites.list`.
   - If the response is `403 accessNotConfigured`, document API enablement/propagation as the blocker and include the project number/link from Google’s error.
   - Do not say the site/property is missing until `sites.list` can actually run.
3. Verify property access.
   - If `sites.list` succeeds but the target `https://example.com/` URL-prefix or domain property is absent, document account/property access as the blocker.
4. Only after the property is visible, pull performance/indexing/sitemap metrics.
5. Keep mutation boundaries explicit.
   - Read-only metrics and sitemap status checks are okay.
   - Sitemap submission, property verification changes, DNS changes, and website changes require explicit approval.

## Artifact language

For docs-first visibility repos, distinguish:

- “OAuth scope blocker” — token lacks `webmasters.readonly`.
- “API enablement blocker” — token has scope, but Google Cloud project has Search Console API disabled/not propagated.
- “Property access blocker” — API lists sites, but target property is absent.
- “Metrics baseline complete” — performance/page/query/sitemap data has actually been read and recorded.

This prevents prematurely asking the user for property access when the current blocker is really the OAuth client project/API configuration.
