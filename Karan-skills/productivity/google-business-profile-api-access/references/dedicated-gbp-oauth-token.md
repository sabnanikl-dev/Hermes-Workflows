# Dedicated Google Business Profile OAuth Token

Use this when setting up GBP API access for local SEO operations while preserving least-privilege separation from Gmail/Drive/Calendar.

## Pattern

- Keep GBP OAuth separate from the general Google Workspace token and client where possible.
- Store GBP token at `~/.hermes/google_gbp_token.json` or an equivalent clearly named token path.
- Store the GBP OAuth client secret at `~/.hermes/google_gbp_client_secret.json`; it must come from the Google Cloud project that actually has GBP API approval/quota. A token signed in by an approved/test-user email will still fail if the OAuth client belongs to an unapproved project with 0 quota.
- Do not add `https://www.googleapis.com/auth/business.manage` to the general Google Workspace OAuth flow unless the user explicitly asks for a combined token and accepts the broader blast radius.
- Use OAuth user consent, not service accounts.

## Minimum scopes

```text
openid
https://www.googleapis.com/auth/userinfo.email
https://www.googleapis.com/auth/business.manage
```

`openid` + `userinfo.email` are included only so the agent can verify the signed-in Google identity without adding Gmail/People scopes. Prefer the canonical `https://www.googleapis.com/auth/userinfo.email` form instead of short `email`; Google may canonicalize `email` during token exchange and oauthlib can fail with a strict "Scope has changed" warning/error.

## Re-auth procedure

When the user asks to re-auth GBP API access, force a clean dedicated GBP OAuth flow rather than refreshing silently:

1. Confirm the preferred client secret exists at `~/.hermes/google_gbp_client_secret.json` and belongs to the approved/quota-bearing project.
2. Back up any existing token before starting:

```bash
stamp=$(date +%Y%m%d-%H%M%S)
backup_dir="$HOME/.hermes/backups/gbp-reauth-$stamp"
mkdir -p "$backup_dir"
if [ -f "$HOME/.hermes/google_gbp_token.json" ]; then
  mv "$HOME/.hermes/google_gbp_token.json" "$backup_dir/google_gbp_token.pre-reauth.json"
  chmod 700 "$backup_dir"
  chmod 600 "$backup_dir/google_gbp_token.pre-reauth.json"
fi
```

3. Run the dedicated helper, ideally as a tracked background process if the user needs time to complete browser consent:

```bash
"$HOME/.hermes/scripts/gbp_oauth_setup.py"
```

4. If the auth URL is needed, read `~/.hermes/gbp_auth_url.txt` and/or open it on the same Mac. The callback URL is localhost, so the browser must be able to reach the Hermes machine.
5. The helper should finish by printing JSON with `ok: true`; do not report success until that happens.

## Required verification before any GBP API call

1. Verify token file exists at the dedicated GBP token path and is mode `600`.
2. Verify the signed-in identity with OpenID Connect userinfo:
   - endpoint: `https://openidconnect.googleapis.com/v1/userinfo`
   - expected email should match the intended agent/workspace account for the task.
3. Verify granted scopes include `https://www.googleapis.com/auth/business.manage`.
4. Verify the token has a refresh token when the goal is durable re-auth, not just a one-hour access token.
5. Smoke-test Account Management:
   - `GET https://mybusinessaccountmanagement.googleapis.com/v1/accounts`
   - If this returns `SERVICE_DISABLED`, enable **My Business Account Management API** in the exact Google Cloud project tied to the OAuth client, wait a few minutes, then retry.
   - If it succeeds but only unrelated/personal accounts appear, the OAuth/API setup is working; the signed-in account still needs Manager/Owner access to the target GBP location/account.
6. Only after identity + scope + account discovery are verified, run read-only Business Information calls. Prefer the local helper if present:

```bash
"$HOME/.hermes/scripts/gbp_readonly_audit.py"
```

7. In the final report, include what was verified: token path, client project, signed-in email, granted scope, refresh-token presence, account discovery result, and any target location found. Do not paste access tokens or refresh tokens.

## Wrong-account handling

If the token belongs to the wrong Google account:

- Stop immediately.
- Move/quarantine the token instead of overwriting silently.
- Do not call Gmail, Drive, Calendar, or GBP APIs with the wrong account.
- Reauthorize with the intended account.

## Local callback note

For CLI OAuth flows, prefer printing and saving the auth URL visibly before waiting for the local callback. If a helper wraps `flow.run_local_server()` and stdout is buffered, the URL can be hidden while the process waits. A robust setup script should:

- allocate a localhost port,
- build `authorization_url()` manually,
- write the URL to a local file such as `~/.hermes/gbp_auth_url.txt`,
- print the URL with flushing enabled,
- run a tiny localhost callback server,
- exchange the received code with `flow.fetch_token(code=...)`.

This makes the flow usable from Telegram/agent sessions where the user needs a clickable auth URL.

## Safety boundary

Successful GBP OAuth does not authorize public mutations. Profile edits, LocalPosts, review replies, media uploads, Q&A, directory submissions, or anything public-facing still require explicit user approval with current value -> proposed value -> reason.