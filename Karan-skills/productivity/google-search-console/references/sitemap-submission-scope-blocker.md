# Search Console sitemap submission scope blocker

Use this when a sitemap submission is approved but the API call fails with `ACCESS_TOKEN_SCOPE_INSUFFICIENT`.

## Pattern

A read-only Search Console token with `https://www.googleapis.com/auth/webmasters.readonly` can verify:

- token identity and property access,
- `sites.list`,
- `sitemaps.list` / `sitemaps.get`,
- Search Analytics,
- URL Inspection reads.

It cannot submit sitemaps. `sitemaps.submit` is a Search Console mutation and needs a write-capable Search Console scope, typically `https://www.googleapis.com/auth/webmasters`.

## Correct workflow

1. Confirm explicit user approval for the sitemap submission.
2. Pre-check the sitemap URL publicly returns HTTP 200 and is the exact URL to submit.
3. Attempt submission only with a write-capable token.
4. If the API returns HTTP 403 with `ACCESS_TOKEN_SCOPE_INSUFFICIENT`:
   - record the approval and attempted action,
   - record that submission did **not** complete,
   - re-check `sitemaps.get` / `sitemaps.list` to prove the sitemap is still not submitted/known,
   - leave the issue/report blocked on write-scope OAuth reauthorization or manual UI submission.
5. If the user approves write-scope reauthorization:
   - use the existing approved OAuth client if appropriate,
   - request `openid`, `https://www.googleapis.com/auth/userinfo.email`, and `https://www.googleapis.com/auth/webmasters`,
   - save the write-capable token separately first (for example `~/.hermes/google_search_console_write_token.json`) rather than overwriting the read-only token,
   - set token file permissions to `0600`,
   - verify token refresh, identity, write scope, property access, and a read smoke test before retrying the mutation.
6. Retry the approved submission.
7. Verify success with more than the submit response:
   - `sitemaps.submit` may return HTTP 204 with no body,
   - `sitemaps.get` for the submitted HTTPS sitemap should return HTTP 200,
   - `sitemaps.list` should include the submitted HTTPS sitemap,
   - URL Inspection and Search Analytics can be smoke-checked but do not prove sitemap processing.
8. Record a follow-up date to re-check downloaded/processed sitemap state because submission does not mean Google has processed it yet.

## OAuth scope-change pitfall

Google may return a superset of scopes when `include_granted_scopes=true` is used (for example adding older granted scopes such as `webmasters.readonly` or `business.manage`). Some OAuth libraries treat this as a scope-change warning/error even when the requested write scope was granted.

If the flow fails with a warning like:

> Scope has changed from ... to ...

and the returned scope set includes the required `https://www.googleapis.com/auth/webmasters`, rerun the local OAuth helper with:

```python
import os
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
```

Then verify the saved token via `tokeninfo` / userinfo before using it. Do not skip identity/scope verification because the OAuth flow completed.

## Artifact/report language

Prefer:

- “Approved submission attempted; blocked by OAuth scope.”
- “The blocker is credential scope, not sitemap readiness.”
- “Post-attempt `sitemaps.get` still returns 404/not submitted.”
- “Next unblocker: reauthorize with `webmasters` scope or submit manually in Search Console UI.”
- After successful write-scope submission: “`sitemaps.submit` returned HTTP 204; `sitemaps.get` now returns HTTP 200 and `sitemaps.list` includes the HTTPS sitemap.”
- “Follow-up monitoring is still needed because Google may not have downloaded/processed the sitemap yet.”

Avoid:

- “Submitted” unless `sitemaps.get` / UI confirms the sitemap is submitted/known.
- “API failed” without naming `ACCESS_TOKEN_SCOPE_INSUFFICIENT` and the required write-scope fix.
- Treating HTTP 204 alone as sufficient proof if `sitemaps.get` / `sitemaps.list` was not rechecked.
