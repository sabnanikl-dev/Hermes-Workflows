---
name: google-search-console
description: "Lightweight Google Search Console API workflow: OAuth refresh, property access checks, Search Analytics smoke tests, sitemap/status reads, and approval boundaries."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [google, search-console, seo, oauth, femme-events, visibility]
    related_skills: [productivity-integrations, local-seo-visibility-ops, google-business-profile-api-access]
---

# Google Search Console

## When to use

Load this when working on Google Search Console (GSC) for Femme Events, JMD, or future Papi visibility clients, especially when asked to:

- Check whether GSC API access works.
- Re-run or debug Search Console OAuth.
- List visible GSC properties and permission levels.
- Pull Search Analytics baselines.
- Inspect sitemap/indexing state via API.
- Decide whether a GSC action is read-only or approval-gated.

## References

- `references/project-local-gsc-wiring.md` — reusable pattern for wiring GSC credentials into a project via ignored symlinks/env files plus ad-hoc verification.
- `references/sitemap-submission-scope-blocker.md` — approved sitemap submission flow when a read-only token blocks `sitemaps.submit` with `ACCESS_TOKEN_SCOPE_INSUFFICIENT`.
- `references/migration-precutover-baselines.md` — rankings-preserving migration baseline workflow: zero-row interpretation, URL Inspection inventory, redirect-map cross-checks, stale sitemap handling, analytics continuity, and artifact verification.

## Migration baseline rules

For pre-cutover migration baselines, do not stop at a page/query export:

1. Separate property access, current-user permission, and verified-owner identity; `sites.list` does not prove who the owner is.
2. Treat zero-row Search Analytics responses as **data unavailable**, never as proof of zero traffic.
3. State that the Page Indexing aggregate count requires the GSC UI; URL Inspection samples are not a substitute total.
4. Recursively inventory the current public sitemap and URL-inspect migration-critical legacy URLs, including taxonomy and pagination surfaces.
5. Cross-check indexed URLs against redirect rules by actual public path shape, not only broad prose descriptions.
6. Keep stale/suspicious submitted-sitemap history distinct from current compromise claims; UI security/manual-action checks and sitemap deletion remain human-gated.
7. Verify web-analytics continuity separately from GSC before claiming measurement is ready.
8. Save sanitized Markdown + JSON evidence, verify report/export parity, and leave unresolved acceptance criteria open.

See `references/migration-precutover-baselines.md` for the full sequence and pitfalls.

## Known local context

- Expected OAuth identity: `karanagent20@gmail.com`.
- Dedicated working OAuth client/project: `jmd-gbp-agent`.
- Client secret path: `~/.hermes/google_gbp_client_secret.json`.
- Dedicated Search Console token path: `~/.hermes/google_search_console_jmd_gbp_agent_token.json`.
- Project-local workspaces may expose GSC credentials through ignored symlinks/env files instead of copying secrets; see `references/project-local-gsc-wiring.md`.
- Standard `gws` Workspace OAuth is not enough unless it explicitly includes `https://www.googleapis.com/auth/webmasters.readonly`.
- GSC API endpoint family still uses `webmasters/v3` for many calls.
- Known Femme property: `sc-domain:femmeevents.com`.

Do **not** replace the general Google Workspace token just to test GSC. Use or recreate a dedicated least-privilege Search Console token.

## Approval boundary

Read-only checks are okay:

- OAuth/token refresh validation.
- `sites.list` property listing.
- Search Analytics query/read baselines.
- Sitemap read/status checks.
- URL Inspection reads where available.
- Public fetches of `robots.txt` / `sitemap.xml`.

Require explicit approval before mutations:

- Submitting or deleting sitemaps.
- Changing verification/property settings.
- Adding/removing users or permissions.
- Updating live website, DNS, redirects, `robots.txt`, or `sitemap.xml`.
- Any client/account-facing Google setting change.

Important scope boundary:

- `https://www.googleapis.com/auth/webmasters.readonly` is enough for reads, but not for `sitemaps.submit`.
- Approved sitemap submission via API needs a write-capable Search Console token, typically `https://www.googleapis.com/auth/webmasters`.
- Save write-capable tokens separately first (for example `~/.hermes/google_search_console_write_token.json`, mode `0600`) instead of overwriting a working read-only token until the write path is verified.
- If submission returns HTTP 403 `ACCESS_TOKEN_SCOPE_INSUFFICIENT`, preserve the approval but report the action as blocked/not completed, then verify `sitemaps.get` or the UI still does not show the sitemap as submitted.
- After write-scope OAuth, verify identity, `webmasters` scope, property permission, and a read smoke test before retrying the mutation. Treat `sitemaps.submit` HTTP 204 as success only after `sitemaps.get` or `sitemaps.list` confirms the submitted sitemap is known.
- If OAuth fails with a scope-change warning because Google returned a superset of scopes, use `OAUTHLIB_RELAX_TOKEN_SCOPE=1` in the local OAuth helper, then verify the saved token via tokeninfo/userinfo before using it.

Detailed recovery flow: `references/sitemap-submission-scope-blocker.md`. 

## Fast health check

Use Python/curl directly rather than relying on `gws` for GSC resources.

1. Refresh the saved token.
2. Confirm tokeninfo email and scope.
3. Call `sites.list`.
4. If a property exists, run a tiny `searchAnalytics.query` with `rowLimit: 1`.

Minimal Python probe shape:

```python
import datetime, json, os, urllib.parse, urllib.request

path = os.path.expanduser('~/.hermes/google_search_console_jmd_gbp_agent_token.json')
tok = json.load(open(path))

post = urllib.parse.urlencode({
    'client_id': tok['client_id'],
    'client_secret': tok['client_secret'],
    'refresh_token': tok['refresh_token'],
    'grant_type': 'refresh_token',
}).encode()
with urllib.request.urlopen(urllib.request.Request(
    tok.get('token_uri', 'https://oauth2.googleapis.com/token'),
    data=post,
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
), timeout=30) as r:
    refreshed = json.load(r)
access = refreshed['access_token']

with urllib.request.urlopen(
    'https://oauth2.googleapis.com/tokeninfo?access_token=' + urllib.parse.quote(access),
    timeout=30,
) as r:
    info = json.load(r)
scopes = sorted(info.get('scope', '').split())

req = urllib.request.Request(
    'https://www.googleapis.com/webmasters/v3/sites',
    headers={'Authorization': 'Bearer ' + access},
)
with urllib.request.urlopen(req, timeout=30) as r:
    sites_body = json.load(r)
sites = sites_body.get('siteEntry', [])

analytics = None
if sites:
    site = sites[0]['siteUrl']
    end = (datetime.date.today() - datetime.timedelta(days=3)).isoformat()
    start = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
    enc = urllib.parse.quote(site, safe='')
    req = urllib.request.Request(
        f'https://www.googleapis.com/webmasters/v3/sites/{enc}/searchAnalytics/query',
        data=json.dumps({'startDate': start, 'endDate': end, 'dimensions': ['query'], 'rowLimit': 1}).encode(),
        headers={'Authorization': 'Bearer ' + access, 'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.load(r)
    analytics = {'siteUrl': site, 'startDate': start, 'endDate': end, 'rowCount': len(result.get('rows', []))}

print(json.dumps({
    'ok': True,
    'tokeninfo_email': info.get('email'),
    'has_webmasters_readonly': 'https://www.googleapis.com/auth/webmasters.readonly' in scopes,
    'site_count': len(sites),
    'sites': [{'siteUrl': s.get('siteUrl'), 'permissionLevel': s.get('permissionLevel')} for s in sites],
    'searchanalytics_check': analytics,
}, indent=2))
```

Report only non-secret fields: account email, scope presence, HTTP status/error reason, property URLs, permission levels, and row counts. Never print tokens, refresh tokens, or client secrets.

## OAuth reauthorization workflow

Use this when refresh returns `invalid_grant`, token is missing the Search Console scope, or the user asks to re-run OAuth.

Important pitfall:

- If OAuth consent screen is **External + Testing**, Google refresh tokens for non-basic scopes can expire after 7 days.
- Publishing to production should prevent future 7-day expiry, but it will **not** revive an already-invalid refresh token.
- After publishing, re-authorize and save a fresh token.

Reauthorization outline:

1. Use client secret `~/.hermes/google_gbp_client_secret.json`.
2. Request scopes:
   - `openid`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/webmasters.readonly`
3. Use installed-app/local-server OAuth.
4. Sign in as `karanagent20@gmail.com`.
5. Save token to `~/.hermes/google_search_console_jmd_gbp_agent_token.json` with mode `0600`.
6. Immediately verify refresh + `sites.list` + tiny Search Analytics query.

A local one-off script may use:

```python
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.discovery

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/webmasters.readonly',
]
flow = InstalledAppFlow.from_client_secrets_file(
    os.path.expanduser('~/.hermes/google_gbp_client_secret.json'),
    scopes=SCOPES,
)
creds = flow.run_local_server(
    host='localhost',
    port=0,
    open_browser=True,
    prompt='consent',
    access_type='offline',
    include_granted_scopes='true',
)
creds.refresh(Request())
service = googleapiclient.discovery.build('webmasters', 'v3', credentials=creds, cache_discovery=False)
print(service.sites().list().execute())
```

## Common errors

- `invalid_grant` during refresh: stored refresh token is dead/revoked/expired. Re-run OAuth for the expected account/client; check Testing-mode 7-day expiry.
- `401 UNAUTHENTICATED`: access token is expired/invalid. Try refresh before concluding access is broken.
- Missing `webmasters.readonly`: wrong token/grant; re-authorize with GSC scope.
- `403 accessNotConfigured`: OAuth token may be valid, but Search Console API is disabled or not propagated for the OAuth client project.
- `sites.list` returns no properties: OAuth works, but account lacks property access.
- Search Analytics HTTP 200 with zero rows: API works; property has no data for that range.

## Femme quick facts

For Femme Events visibility work:

- Website: `https://femmeevents.com`.
- Known GSC property: `sc-domain:femmeevents.com`.
- Prior working permission: `siteFullUser`.
- Treat sitemap submission as approval-gated.
- Public technical checks of `https://femmeevents.com/robots.txt` and `https://femmeevents.com/sitemap.xml` are safe/read-only.

## Completion checklist

Before reporting GSC access is working, verify and state:

- [ ] Token refresh succeeded.
- [ ] Tokeninfo email matches expected account.
- [ ] `webmasters.readonly` scope is present.
- [ ] `sites.list` succeeded.
- [ ] Visible property/properties and permission levels.
- [ ] At least one data endpoint smoke test (`searchAnalytics.query`) succeeded, even if zero rows.
- [ ] Any mutation remains unperformed unless explicitly approved.

When GSC work creates repo artifacts such as a Markdown report plus JSON export, also run focused artifact verification before closeout: JSON parse, no obvious token/secret markers, report numbers/statuses match the export, folder indexes mention new artifacts, and approval-boundary wording preserves whether sitemap submission or other account mutations were actually approved/performed. If the repo has no canonical test suite, use a temporary `hermes-verify-` ad-hoc verifier and describe it as ad-hoc verification, not suite green.
