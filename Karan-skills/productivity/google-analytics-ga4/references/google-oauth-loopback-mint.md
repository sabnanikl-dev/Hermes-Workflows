# Google OAuth Loopback Mint — Working Recipe & 400 Diagnosis

Recipe proven 2026-07-28 minting a GA4 token from `~/.hermes/google_client_secret.json`
(installed-app client, project `hermes-492218`, registered redirect `http://localhost`).

## Working recipe

```python
import json, os, threading, http.server, urllib.parse, webbrowser
from pathlib import Path
from google_auth_oauthlib.flow import Flow

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"   # MUST precede fetch_token for http loopback

SECRET = Path.home() / ".hermes/google_client_secret.json"
SCOPES = [...]  # least privilege for the task
PORT = 8484

flow = Flow.from_client_secrets_file(str(SECRET), scopes=SCOPES,
                                     redirect_uri=f"http://localhost:{PORT}/")
url, _ = flow.authorization_url(access_type="offline", prompt="consent")
webbrowser.open(url)

done = {}
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        done["q"] = urllib.parse.urlparse(self.path).query
        self.send_response(200); self.end_headers()
        self.wfile.write(b"<h3>Auth complete. You can close this tab.</h3>")
    def log_message(self, *a): pass

srv = http.server.HTTPServer(("localhost", PORT), H)
srv.handle_request()  # exactly one request

flow.fetch_token(authorization_response=f"http://localhost:{PORT}/?" + done["q"])
c = flow.credentials
out = Path.home() / ".hermes" / "google_<service>_token.json"
out.write_text(json.dumps({
    "token": c.token, "refresh_token": c.refresh_token, "token_uri": c.token_uri,
    "client_id": c.client_id, "client_secret": c.client_secret,
    "scopes": sorted(c.scopes)}))
out.chmod(0o600)
```

Refresh pattern (no google-auth needed): POST `client_id`, `client_secret`, `refresh_token`,
`grant_type=refresh_token` to `token_uri`, then persist the rotated `access_token` back into
the same file. Verify with `tokeninfo?access_token=…` (check email + scope) and one live API read.

## Failure ladder observed (in order)

1. **`redirect_uri_mismatch`-class 400** — used `http://127.0.0.1:PORT/oauth`. The installed
   client only registers `http://localhost`. Fix: bind + redirect to `localhost`, bare path.
2. **Generic "400. That's an error." with NO error code** — occurred with
   `include_granted_scopes='true'` in the auth request on this client. Fix: drop that param;
   keep only `access_type='offline'` and `prompt='consent'`. Two confirmed causes when it
   reappears later, and the disambiguation matters:
   (a) **Stale/zombie consent tab** — if the user clicks through an old errored or timed-out
   consent tab from a previous run instead of the freshly generated URL, Google returns a
   generic 400. Observed 2026-07-28: the exact three-scope URL that 400'd rendered consent
   cleanly minutes later when regenerated fresh. Fix: ask the user to close every Google
   consent tab and use only the newest link.
   (b) **Scope not on the consent screen** — testing-mode OAuth apps only allow listed
   scopes; an unlisted scope 400s. Fix: Google Cloud Console → APIs & Services → OAuth
   consent screen → Scopes → add → re-consent.
   Diagnosis shortcut: generate auth URLs for scope-set A (known good), B (good+new), C (new
   only) and ask the user which render consent vs 400. If a set that previously worked now
   400s, suspect (a) first — not (b).
3. **`InsecureTransportError` at fetch_token** — oauthlib refuses http even for loopback.
   Fix: `export OAUTHLIB_INSECURE_TRANSPORT=1` in the shell env (BSD `sed -i` line-insert
   syntax differs from GNU; set the env var in the shell rather than editing the script).
4. **Retry-with-stale-state trap** — re-running the flow after the user already approved once
   can hit `InsecureTransportError` from a *new* consent attempt's callback. Not a real
   regression: just re-run with the env var set and have the user approve once more.

## Scope reference (Google Analytics)

| Need | Scope |
|---|---|
| Read accounts/properties/streams/retention | `analytics.readonly` |
| PATCH retention settings | `analytics.edit` |
| Read access bindings (who has what role) | `analytics.manage.users.readonly` (v1alpha only) |
| Change access bindings | `analytics.manage.users` (approval-gated) |

Full per-endpoint scope requirements are in the discovery doc:
`curl -s "https://analyticsadmin.googleapis.com/\$discovery/rest?version=v1alpha"` —
walk `resources.*.methods` and read each method's `scopes` list. Note: the discovery doc has
NO `searchConsole` methods — GA4↔GSC links are UI-only.
