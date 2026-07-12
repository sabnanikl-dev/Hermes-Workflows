# Google Search Console API checks

Use this when asked whether Hermes has Google Search Console API access.

## What to verify

1. Confirm the broad Google Workspace CLI identity if relevant:
   - `gws auth status` should show the expected account.
   - Do not assume `gws` can call Search Console: its default OAuth scopes may omit `https://www.googleapis.com/auth/webmasters.readonly`, and the CLI may not expose unlisted Search Console resources cleanly.

2. Prefer the dedicated Search Console OAuth token when present:
   - `~/.hermes/google_search_console_jmd_gbp_agent_token.json`
   - `~/.hermes/google_search_console_token.json`

3. Redact secrets/tokens in all output. It is okay to report:
   - token file path
   - client/project prefix
   - signed-in email from tokeninfo
   - whether `webmasters.readonly` is present
   - HTTP status and Google error reason

## Minimal live probe

Use Python or curl to:

1. Refresh the token with `refresh_token`, `client_id`, `client_secret`, and `grant_type=refresh_token` against `https://oauth2.googleapis.com/token`.
2. Inspect scopes via `https://oauth2.googleapis.com/tokeninfo?access_token=...`.
3. Call `GET https://www.googleapis.com/webmasters/v3/sites` with `Authorization: Bearer ...`.
4. If at least one property is returned, call `POST https://www.googleapis.com/webmasters/v3/sites/{urlencoded-siteUrl}/searchAnalytics/query` with a small recent date range and `rowLimit: 1` to prove a data endpoint works.

## Interpreting common results

- `sites.list` HTTP 200 with `siteEntry`: API and OAuth access work. Report visible properties and permission levels.
- `searchAnalytics.query` HTTP 200 but zero rows: API works; property has no search data for that range.
- OAuth refresh `invalid_grant`: stored refresh token is invalid/revoked/expired; rerun OAuth for the expected account/client. If the OAuth consent screen is External + Testing, Google-issued refresh tokens for non-basic scopes expire after 7 days; publish the app to production first, then re-authorize because publishing will not revive an already-invalid refresh token.
- `401 UNAUTHENTICATED` on direct API call using stored access token: access token is expired/invalid; try refresh before concluding access is broken.
- `403 accessNotConfigured`: token may be valid, but Search Console API is disabled or not propagated for the OAuth client project.
- Missing `webmasters.readonly`: existing OAuth grant is insufficient; rerun OAuth with the Search Console scope.

## Known local context

Historically, the dedicated `jmd-gbp-agent` OAuth client/project was the working client for Search Console + GBP-related access. The local client secret path is `~/.hermes/google_gbp_client_secret.json`; the working dedicated token path is `~/.hermes/google_search_console_jmd_gbp_agent_token.json`. Do not replace the general Google Workspace token just to test Search Console; use or recreate a dedicated least-privilege Search Console token instead.