# Search Console OAuth + API Baseline Notes

Use this when Search Console is newly enabled for a client visibility baseline and the normal Google Workspace token does not include Search Console scopes.

## Durable pattern

1. Use a dedicated token when Search Console access is only needed for read-only visibility work:
   - token path: `~/.hermes/google_search_console_token.json`
   - minimum scopes: `openid`, `https://www.googleapis.com/auth/userinfo.email`, `https://www.googleapis.com/auth/webmasters.readonly`
2. Persist the PKCE `code_verifier` alongside the OAuth `state` before sending the auth URL to the user. Google auth codes are one-time-use; if exchange fails because the verifier was missing, generate a fresh URL.
3. For localhost desktop redirects like `http://localhost:1/`, set `OAUTHLIB_INSECURE_TRANSPORT=1` only for the token exchange subprocess.
4. Google may normalize/alter scopes during token exchange:
   - short `email` may be returned/canonicalized differently from `userinfo.email`.
   - `include_granted_scopes=true` can cause Google to return previously granted Gmail/Drive/Calendar/GBP scopes even when the helper expected only Search Console scopes.
   - If oauthlib raises only a scope-change warning after Google returns the expected Search Console scope, retry the exchange with `OAUTHLIB_RELAX_TOKEN_SCOPE=1` and the exact original callback/code. Do not ask the user for a new code unless the code was actually consumed or Google says malformed/invalid grant.
5. After token exchange, verify identity and scope before collecting metrics:
   - call `https://www.googleapis.com/oauth2/v2/userinfo`
   - check token scopes include `https://www.googleapis.com/auth/webmasters.readonly`
   - call Search Console `sites.list`

## Important failure distinction

Search Console can still fail after OAuth succeeds. Interpret common errors carefully:

- `403 insufficient authentication scopes`: OAuth token lacks Search Console scope; reauthorize with `webmasters.readonly`.
- `403 accessNotConfigured` with text like “Google Search Console API has not been used in project PROJECT_NUMBER before or it is disabled”: enable/confirm propagation for `searchconsole.googleapis.com` in the same Google Cloud project used by the OAuth client. This happens before property access can be checked.
- `sites.list` succeeds but the target site is absent: the signed-in Google account likely lacks access to the URL-prefix/domain property.

## Local SEO reporting boundary

Read-only Search Console API calls are safe for baseline reporting. Sitemap submission, property changes, verification changes, or website/DNS changes still require explicit approval and post-action verification.
