---
name: google-workspace
description: Gmail, Calendar, Drive, Contacts, Sheets, and Docs integration via Python, with optional Google Workspace CLI (`gws`) advanced backend for broader Workspace APIs. Uses OAuth2 with automatic token refresh.
version: 1.0.0
author: Nous Research
license: MIT
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials (downloaded from Google Cloud Console)
metadata:
  hermes:
    tags: [Google, Gmail, Calendar, Drive, Sheets, Docs, Contacts, Email, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [himalaya]
---

# Google Workspace

Gmail, Calendar, Drive, Contacts, Sheets, and Docs through the stable Python wrapper, plus optional `gws` advanced backend for broader Google Workspace APIs and agent workflows.

## References

- `references/absorbed/google-workspace/references/gmail-search-syntax.md` — Gmail search operators (is:unread, from:, newer_than:, etc.)
- `references/absorbed/google-workspace/references/search-console-oauth.md` — Search Console read-only OAuth pattern, PKCE pitfalls, scope normalization, and API enablement blockers.

## Scripts

- `references/absorbed/google-workspace/scripts/setup.py` — OAuth2 setup (run once to authorize)
- `references/absorbed/google-workspace/scripts/google_api.py` — primary stable Python API wrapper CLI (agent uses this for core Gmail/Calendar/Drive/Sheets/Docs operations)
- `references/absorbed/google-workspace/scripts/gws_hermes.sh` — optional advanced wrapper for the Google Workspace CLI (`gws`) using the existing Hermes OAuth token; use for endpoints/workflows not covered by `google_api.py`

## First-Time Setup

The setup is fully non-interactive — you drive it step by step so it works
on CLI, Telegram, Discord, or any platform.

Define a shorthand first:

```bash
GSETUP="python ~/.hermes/skills/productivity/google-workspace/scripts/setup.py"
```

### Step 0: Check if already set up

```bash
$GSETUP --check
```

If it prints `AUTHENTICATED`, skip to Usage — setup is already done.

### Step 1: Triage — ask the user what they need

Before starting OAuth setup, ask the user TWO questions:

**Question 1: "What Google services do you need? Just email, or also
Calendar/Drive/Sheets/Docs?"**

- **Email only** → They don't need this skill at all. Use the `himalaya` skill
  instead — it works with a Gmail App Password (Settings → Security → App
  Passwords) and takes 2 minutes to set up. No Google Cloud project needed.
  Load the himalaya skill and follow its setup instructions.

- **Calendar, Drive, Sheets, Docs (or email + these)** → Continue with this
  skill's OAuth setup below.

**Question 2: "Does your Google account use Advanced Protection (hardware
security keys required to sign in)? If you're not sure, you probably don't
— it's something you would have explicitly enrolled in."**

- **No / Not sure** → Normal setup. Continue below.
- **Yes** → Their Workspace admin must add the OAuth client ID to the org's
  allowed apps list before Step 4 will work. Let them know upfront.

### Step 2: Create OAuth credentials (one-time, ~5 minutes)

Tell the user:

> You need a Google Cloud OAuth client. This is a one-time setup:
>
> 1. Go to https://console.cloud.google.com/apis/credentials
> 2. Create a project (or use an existing one)
> 3. Click "Enable APIs" and enable: Gmail API, Google Calendar API,
>    Google Drive API, Google Sheets API, Google Docs API, People API
> 4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
> 5. Application type: "Desktop app" → Create
> 6. Click "Download JSON" and tell me the file path

Once they provide the path:

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

### Step 3: Get authorization URL

```bash
$GSETUP --auth-url
```

This prints a URL. **Send the URL to the user** and tell them:

> Open this link in your browser, sign in with your Google account, and
> authorize access. After authorizing, you'll be redirected to a page that
> may show an error — that's expected. Copy the ENTIRE URL from your
> browser's address bar and paste it back to me.

### Step 4: Exchange the code

The user will paste back either a URL like `http://localhost:1/?code=4/0A...&scope=...`
or just the code string. Either works. The `--auth-url` step stores a temporary
pending OAuth session locally so `--auth-code` can complete the PKCE exchange
later, even on headless systems:

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED"
```

### Step 5: Verify

```bash
$GSETUP --check
```

Should print `AUTHENTICATED`. Setup is complete — token refreshes automatically from now on.

### Notes

- Token is stored at `~/.hermes/google_token.json` and auto-refreshes.
- **Back up your token:** After successful auth, copy `google_token.json` and `google_client_secret.json` to `~/.hermes/backups/` (or another safe location). If the token file is ever deleted, you can restore the backup instead of redoing the full OAuth flow.
- **macOS Python version pitfall**: The setup script requires Python 3.10+ (uses `str | None` syntax).
  If `setup.py` fails with `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`,
  the system Python is too old (e.g., macOS ships Python 3.9.6). Find a newer Python first:
  ```bash
  which python3.10 python3.11 python3.12
  ```
  **Option A — Rebuild the main venv** (if you control it):
  ```bash
  rm -rf <project-venv> && python3.11 -m venv <project-venv>
  source <project-venv>/bin/activate && pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
  ```
  **Option B — Persistent venv** (recommended when the main venv is uv-managed, externally managed, or you don't want to rebuild it):
  ```bash
  mkdir -p ~/.hermes/venvs
  python3.11 -m venv ~/.hermes/venvs/google-workspace
  ~/.hermes/venvs/google-workspace/bin/python -m pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
  # Then run scripts with:
  ~/.hermes/venvs/google-workspace/bin/python ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --check
  ~/.hermes/venvs/google-workspace/bin/python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py ...
  ```
  > **Why persistent?** `/tmp` gets wiped across reboots or sessions. A venv under `~/.hermes/venvs/` survives and avoids re-installing deps every time.
- **`--install-deps` may fail** if pip isn't available in the venv — install deps manually as shown above.
- Pending OAuth session state/verifier are stored temporarily at `~/.hermes/google_oauth_pending.json` until exchange completes.
- **PKCE callback pitfall:** If you write a one-off OAuth helper instead of using `setup.py`, persist the generated `code_verifier` alongside the `state` before sending the auth URL. On exchange, recreate the flow with the same `state`, `redirect_uri`, and `code_verifier`. If the helper only saves `state`, Google will reject the callback with `invalid_grant: Missing code verifier`; generate a fresh auth URL rather than retrying the stale callback code.
- To revoke: `$GSETUP --revoke`

## Usage

All core commands go through the stable Python API script. Set `GAPI` as a shorthand:

```bash
GAPI="python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
```

> **Karan workflow preference — CLI/direct API first:** Prefer this `google-workspace` Python API wrapper and the optional `gws` CLI over Google MCP tools whenever they cover the task. MCP Google tools add large startup schemas and have timed out in practice. Use MCP only for gaps, fallback, special structured actions, or workflows where MCP is clearly superior.

> **Default backend rule:** Use `google_api.py` first for supported Gmail, Calendar, Drive search, Contacts, Sheets, and Docs operations. It is stable, uses the existing Hermes token/refresh flow, and has known formatting/approval guardrails.
>
> Use `gws` only as the **advanced backend** when the Python wrapper does not support the needed endpoint, helper, or workflow.

> **Note:** If you created a persistent venv (Option B in Setup Notes), use that Python path:
> ```bash
> GAPI="~/.hermes/venvs/google-workspace/bin/python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
> GSETUP="~/.hermes/venvs/google-workspace/bin/python ~/.hermes/skills/productivity/google-workspace/scripts/setup.py"
> ```
> For convenience, add these exports to your shell profile (e.g. `.zshrc`) so they're available in every session.

## Optional Advanced Backend: Google Workspace CLI (`gws`)

`gws` is the Google Workspace CLI from `googleworkspace/cli`. It dynamically builds commands from Google's Discovery Service and returns structured JSON. It is useful when we need Workspace capabilities beyond the hand-written Python wrapper.

**Use `gws` for:**

- Drive uploads, folder creation, permissions/sharing, and multipart uploads
- Google Slides, Forms, Tasks, Keep, Meet, Chat, Classroom, Admin, Apps Script
- Discovery API methods not yet wrapped in `google_api.py`
- Helper/workflow commands such as Gmail triage/watch, Calendar agenda, meeting prep, weekly digest, and file announce
- Schema introspection before using unfamiliar endpoints

**Do not use `gws` as the default for:**

- Simple Gmail search/read/send/reply already supported by `google_api.py`
- Calendar list/create/delete already supported by `google_api.py`
- Sheets read/update/append already supported by `google_api.py`
- Any write/send/delete action without user approval

### Installed local wrapper

This skill includes a Hermes wrapper that refreshes the existing Google OAuth token and passes only the short-lived access token to `gws`:

```bash
GWS="~/.hermes/skills/productivity/google-workspace/scripts/gws_hermes.sh"
$GWS --version
$GWS drive files list --params '{"pageSize": 5}'
```

The wrapper:

1. Runs `setup.py --check` to refresh the Hermes token if needed.
2. Reads `~/.hermes/google_token.json` locally.
3. Exports `GOOGLE_WORKSPACE_CLI_TOKEN` for the subprocess only.
4. Executes `gws` without printing secrets.

### Installing `gws`

Preferred install is a verified GitHub release binary. Pick the target for the machine:

- macOS Apple Silicon: `aarch64-apple-darwin`
- macOS Intel: `x86_64-apple-darwin`
- Linux x86_64 glibc: `x86_64-unknown-linux-gnu`
- Linux ARM64 glibc: `aarch64-unknown-linux-gnu`

Example install to `~/.local/bin`:

```bash
TAG=v0.22.5
TARGET=aarch64-apple-darwin
mkdir -p ~/.local/bin ~/.cache/hermes-gws-install
cd ~/.cache/hermes-gws-install
BASE="https://github.com/googleworkspace/cli/releases/download/${TAG}/google-workspace-cli-${TARGET}.tar.gz"
curl -fsSLO "$BASE"
curl -fsSLO "$BASE.sha256"
shasum -a 256 -c "google-workspace-cli-${TARGET}.tar.gz.sha256"
tar -xzf "google-workspace-cli-${TARGET}.tar.gz"
install -m 0755 gws ~/.local/bin/gws
~/.local/bin/gws --version
```

Alternative installs:

```bash
brew install googleworkspace-cli
npm install -g @googleworkspace/cli
cargo install --git https://github.com/googleworkspace/cli --locked
```

Prefer the release + checksum path when security matters.

### Core `gws` command patterns

```bash
# Introspect service and method schemas
$GWS drive --help
$GWS schema drive.files.list
$GWS schema sheets.spreadsheets.values.append

# Read/list with structured JSON
$GWS drive files list --params '{"pageSize": 10}'
$GWS calendar events list --params '{"calendarId": "primary", "maxResults": 10}'

# Auto-paginate as NDJSON, then process with jq
$GWS drive files list --params '{"pageSize": 100}' --page-all | jq -r '.files[].name'

# Drive multipart upload
$GWS drive files create --json '{"name": "report.pdf"}' --upload ./report.pdf

# Create a spreadsheet
$GWS sheets spreadsheets create --json '{"properties": {"title": "Q1 Budget"}}'

# Sheets ranges contain !, so keep JSON in single quotes
$GWS sheets spreadsheets values get \
  --params '{"spreadsheetId": "SPREADSHEET_ID", "range": "Sheet1!A1:C10"}'

# Dry-run before unfamiliar writes
$GWS chat spaces messages create \
  --params '{"parent": "spaces/xyz"}' \
  --json '{"text": "Deploy complete."}' \
  --dry-run
```

### Approval and safety rules for `gws`

1. **Same approval policy as Python:** never send email, create/delete/update calendar events, modify Drive permissions, upload/share files, write Sheets/Docs/Slides/Forms, or message Chat without showing the planned action and getting user approval.
2. **Prefer `--dry-run`** before any unfamiliar write endpoint.
3. **Use narrow scopes.** Do not run `gws auth login` with broad/recommended scopes unless explicitly needed. Unverified OAuth apps can fail around ~25 scopes.
4. **Never print tokens.** Use `references/absorbed/google-workspace/scripts/gws_hermes.sh`; do not echo `GOOGLE_WORKSPACE_CLI_TOKEN`.
5. **Verify JSON output** after writes by re-reading the affected resource when practical.
6. **If `gws` breaks**, fall back to direct Python Google API calls using the existing token and document the gap in this skill.

### Useful workflow ideas for Karan

- **Femme Events inquiry ops:** read Gmail inquiry → append lead to Sheet → create Calendar hold → create/share Drive folder → draft prep Doc.
- **Papi AI client ops:** weekly digest from Calendar/Gmail/Drive → client status Doc → task list updates.
- **Meeting prep:** upcoming Calendar events + related Gmail threads + recent Drive files → concise briefing.
- **Reputation engine:** collect GBP/client follow-up emails → Sheets queue → draft responses/tasks.

### Known `gws` caveats

- The project states it is not an officially supported Google product.
- It is pre-1.0 and may introduce breaking changes.
- `gws auth setup` requires `gcloud`; use the Hermes wrapper when possible to avoid duplicate OAuth setup.
- Some APIs require scopes not currently in `~/.hermes/google_token.json`; if an endpoint returns 403 insufficient permissions, update `SCOPES` in both `setup.py` and `google_api.py`, revoke/re-auth, then retry.
- Access-token mode uses the current token only; the wrapper refreshes before execution, but very long-running `gws` operations may still need a fresh run.

### Gmail

```bash
# Search (returns JSON array with id, from, subject, date, snippet)
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"

# Read full message (returns JSON with body text)
$GAPI gmail get MESSAGE_ID

# Send
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1><p>Details...</p>" --html

# Reply (automatically threads and sets In-Reply-To)
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."

# Labels
$GAPI gmail labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD
```

#### Gmail attachments / empty body fallback

If `$GAPI gmail get MESSAGE_ID` returns an empty `body`, omits attachments, or the task needs to save files from email, use the Gmail API directly with the existing OAuth token and `format='full'`. This avoids relying on Himalaya config and handles multipart MIME reliably.

```bash
~/.hermes/venvs/google-workspace/bin/python - <<'PY'
import base64, json, pathlib, re
from html.parser import HTMLParser
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

MSG_ID = 'MESSAGE_ID'
OUT = pathlib.Path('/tmp/gmail-export')
ATT = OUT / 'attachments'
ATT.mkdir(parents=True, exist_ok=True)

class HTMLText(HTMLParser):
    def __init__(self): super().__init__(); self.out=[]
    def handle_data(self, d): self.out.append(d)
    def handle_starttag(self, tag, attrs):
        if tag in ('br','p','div','li','tr','h1','h2','h3'): self.out.append('\n')
    def text(self): return re.sub(r'\n{3,}', '\n\n', ''.join(self.out))

def b64url(data):
    return base64.urlsafe_b64decode(data + '=' * ((4 - len(data) % 4) % 4))

creds = Credentials.from_authorized_user_file(str(pathlib.Path.home() / '.hermes/google_token.json'))
svc = build('gmail', 'v1', credentials=creds)
msg = svc.users().messages().get(userId='me', id=MSG_ID, format='full').execute()
headers = {h['name'].lower(): h['value'] for h in msg['payload'].get('headers', [])}
texts, attachments = [], []

def walk(part):
    mime = part.get('mimeType', '')
    filename = part.get('filename') or ''
    body = part.get('body', {})
    data = body.get('data')
    att_id = body.get('attachmentId')
    if data and mime in ('text/plain', 'text/html'):
        text = b64url(data).decode('utf-8', errors='replace')
        if mime == 'text/html':
            p = HTMLText(); p.feed(text); text = p.text()
        texts.append(text.strip())
    if filename and att_id:
        att = svc.users().messages().attachments().get(userId='me', messageId=MSG_ID, id=att_id).execute()
        raw = b64url(att['data'])
        safe = re.sub(r'[^A-Za-z0-9._-]+', '-', filename).strip('-') or f'attachment-{len(attachments)+1}'
        dest = ATT / safe
        dest.write_bytes(raw)
        attachments.append({'filename': filename, 'mimeType': mime, 'size': len(raw), 'path': str(dest)})
    for child in part.get('parts', []) or []:
        walk(child)

walk(msg['payload'])
(OUT / 'body.txt').write_text('\n\n'.join(t for t in texts if t), encoding='utf-8')
(OUT / 'metadata.json').write_text(json.dumps({'id': MSG_ID, 'threadId': msg['threadId'], 'headers': headers, 'attachments': attachments}, indent=2), encoding='utf-8')
print(json.dumps({'out': str(OUT), 'attachments': len(attachments), 'body_chars': sum(map(len, texts))}, indent=2))
PY
```

Use this pattern for CMS/content ingestion tasks: save raw body, metadata, and attachments into a dated project asset folder, then create cleaned Markdown/JSON derived files for the CMS workflow.

### Calendar

```bash
# List events (defaults to next 7 days)
$GAPI calendar list
$GAPI calendar list --start 2026-03-01T00:00:00Z --end 2026-03-07T23:59:59Z

# Create event (ISO 8601 with timezone required)
$GAPI calendar create --summary "Team Standup" --start 2026-03-01T10:00:00-06:00 --end 2026-03-01T10:30:00-06:00
$GAPI calendar create --summary "Lunch" --start 2026-03-01T12:00:00Z --end 2026-03-01T13:00:00Z --location "Cafe"
$GAPI calendar create --summary "Review" --start 2026-03-01T14:00:00Z --end 2026-03-01T15:00:00Z --attendees "alice@co.com,bob@co.com"

# Delete event
$GAPI calendar delete EVENT_ID
```

### Drive

```bash
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5
```

### Contacts

```bash
$GAPI contacts list --max 20
```

### Sheets

```bash
# Read
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Write
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'

# Append rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'
```

### Docs

```bash
$GAPI docs get DOC_ID
```

## Output Format

All commands return JSON. Parse with `jq` or read directly. Key fields:

- **Gmail search**: `[{id, threadId, from, to, subject, date, snippet, labels}]`
- **Gmail get**: `{id, threadId, from, to, subject, date, labels, body}`
- **Gmail send/reply**: `{status: "sent", id, threadId}`
- **Calendar list**: `[{id, summary, start, end, location, description, htmlLink}]`
- **Calendar create**: `{status: "created", id, summary, htmlLink}`
- **Drive search**: `[{id, name, mimeType, modifiedTime, webViewLink}]`
- **Contacts list**: `[{name, emails: [...], phones: [...]}]`
- **Sheets get**: `[[cell, cell, ...], ...]`

## Rules

1. **Never send email or create/delete events without confirming with the user first.** Show the draft content and ask for approval.
2. **Sender identity for Karan's agent inbox:** emails sent from `karanagent20@gmail.com` are from Hermes, not directly from Karan. Unless the user explicitly provides a different signature, sign outbound emails exactly:
   ```text
   Hermes, Karan’s personal agent
   ```
   Do not sign as “Karan” from this account.
3. **EMAIL FORMATTING -- CRITICAL:** When using `gmail send`, you MUST choose ONE path:
   - **HTML mode (preferred, always renders nicely):** Use `--html` flag AND the body must contain proper HTML tags -- `<p>` for paragraphs, `<ul><li>` for lists, `<strong>` for bold, `<br>` for line breaks. Example: `<html><body><p>Hey!</p><ul><li>Item one</li></ul></body></html>`
   - **Plain text mode:** Omit the `--html` flag entirely. Body should be plain text. Line breaks work but are dependent on the recipient's email client.
   - **NEVER** use `--html` with plain text that has no HTML tags. This renders as one unbroken wall of text in Gmail. This has already happened once -- do not repeat it.
3. **QA step:** Before sending, mentally verify: does the body match the mode? HTML body + `--html` flag = good. Plain text body without `--html` = good. Plain text body WITH `--html` = BAD, stops here.
2. **Check auth before first use** — run `setup.py --check`. If it fails, guide the user through setup.
3. **Use the Gmail search syntax reference** for complex queries — load it with `skill_view("google-workspace", file_path="references/absorbed/google-workspace/references/gmail-search-syntax.md")`.
4. **Calendar times must include timezone** — always use ISO 8601 with offset (e.g., `2026-03-01T10:00:00-06:00`) or UTC (`Z`).
5. **Respect rate limits** — avoid rapid-fire sequential API calls. Batch reads when possible.

## Drive Operations Beyond Search

The `google_api.py` CLI only supports `drive search`. For creating folders, sharing, uploading, or other Drive write operations, prefer the `gws` advanced backend when it supports the needed operation:

```bash
GWS="~/.hermes/skills/productivity/google-workspace/scripts/gws_hermes.sh"

# Create a folder
$GWS drive files create --json '{"name": "Folder Name", "mimeType": "application/vnd.google-apps.folder"}'

# Upload a file
$GWS drive files create --json '{"name": "report.pdf"}' --upload ./report.pdf
```

If `gws` cannot handle the workflow or breaks due to a CLI change, fall back to the Google API directly via the persistent venv:

```bash
~/.hermes/venvs/google-workspace/bin/python -c "
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file('$HOME/.hermes/google_token.json')
service = build('drive', 'v3', credentials=creds)

# Create a folder
folder = service.files().create(body={
    'name': 'Folder Name',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': ['PARENT_FOLDER_ID']  # omit for root
}, fields='id, name, webViewLink').execute()

# Share with a user
service.permissions().create(
    fileId=folder['id'],
    body={'type': 'user', 'role': 'writer', 'emailAddress': 'user@example.com'},
    sendNotificationEmail=True
).execute()
"
```

**Pitfalls:**
- The `~/.hermes/google_token.json` uses `drive.readonly` scope by default. For write operations (create folders, upload files), the token must include `https://www.googleapis.com/auth/drive` scope. If writes fail with 403, revoke and re-auth with the `drive` scope: `$GSETUP --revoke` then redo Steps 3-5.
- Use the persistent venv (`~/.hermes/venvs/google-workspace/bin/python`), not system python3 — it has `google-api-python-client` installed.
- The MCP `mcp_google_drive_*` tools may time out. The direct Python API approach via the venv is more reliable for write operations.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Run setup Steps 2-5 above |
| `REFRESH_FAILED` | Token revoked or expired — redo Steps 3-5 |
| **`REFRESH_FAILED: invalid_grant` and backup token also fails** | Treat this as a required reauthorization, not a recoverable cache issue. Do not keep retrying stale backups. Run a fresh `$GSETUP --auth-url` / `$GSETUP --auth-code` flow, then verify with `$GSETUP --check`. Record cron impact in the daily log/lesson if scheduled Gmail checks were blocked. |
| `HttpError 403: Insufficient Permission` | Missing API scope — `$GSETUP --revoke` then redo Steps 3-5 |
| `HttpError 403: Access Not Configured` | API not enabled — user needs to enable it in Google Cloud Console |
| **Search Console OAuth exchange fails around PKCE/scope normalization** | For read-only Search Console baselines, use a dedicated token and persist both OAuth `state` and PKCE `code_verifier` before sending the auth URL. If Google returns expected Search Console scope but oauthlib raises a scope-change warning because `email` was normalized or `include_granted_scopes` returned extra prior scopes, retry the same callback with `OAUTHLIB_RELAX_TOKEN_SCOPE=*** before asking for a fresh code. See `references/absorbed/google-workspace/references/search-console-oauth.md`. |
| **Search Console `sites.list` returns `403 accessNotConfigured` after OAuth succeeds** | This is not a property-access problem yet. Enable/confirm propagation for `searchconsole.googleapis.com` in the exact Google Cloud project used by the OAuth client, then retry `sites.list`. If listing succeeds but the target site is absent, then check Search Console property access. |
| **Drive/Docs write operations fail** | Default scopes may only include `drive.readonly` and `documents.readonly`. To create files or write to docs, the scope list in `setup.py` must include `https://www.googleapis.com/auth/drive` and `https://www.googleapis.com/auth/documents` (not the `.readonly` variants). After changing scopes, run `$GSETUP --revoke` then redo Steps 3-5. |
| **Google Business Profile API returns `ACCESS_TOKEN_SCOPE_INSUFFICIENT`** | The token needs `https://www.googleapis.com/auth/business.manage`. Add that scope to both `setup.py` and `google_api.py`, start a fresh `$GSETUP --auth-url` / `$GSETUP --auth-code` flow, then verify with `GET https://mybusinessaccountmanagement.googleapis.com/v1/accounts` before reading locations. |
| **`invalid_scope` on token refresh** | The SCOPES list in `google_api.py` must match the scopes the token was originally authorized with. If the script has `.readonly` variants (e.g. `drive.readonly`) but the token was authorized with full scopes (`drive`), refresh fails. Fix: edit the `SCOPES` list in `google_api.py` to match the token's scopes. Check with: `python3 -c "import json; print(json.load(open('$HOME/.hermes/google_token.json'))['scopes'])"` |
| `ModuleNotFoundError` | Run `$GSETUP --install-deps` |
| **MCP Gmail search/reply/draft tools time out** | If `mcp_google_gmail_search_threads` / `get_thread` / draft tools return `TimeoutError`, or OAuth errors like `OAuth callback timed out`, `OAuth flow error`, or `Protected resource ... does not match expected ...`, stop retrying MCP and switch to the direct API wrapper (`google_api.py`) or raw Gmail API with the existing token. For Gmail draft creation specifically, use the persistent venv + Gmail API `users().drafts().create(...)`, then verify with `google_api.py gmail search "in:drafts subject:\"...\""`. See `references/absorbed/google-workspace/references/gmail-mcp-troubleshooting.md`. |
| **User pastes a Google OAuth callback URL but `setup.py --auth-code` says `No pending OAuth session found`** | The callback probably belongs to a different OAuth flow/listener (often MCP browser auth with a random high localhost port like `127.0.0.1:65117`). Do not keep replaying it or call the localhost URL; the listener is usually gone and the code/state will not match this skill's PKCE verifier. Start a fresh flow with this skill: run `$GSETUP --auth-url`, send that exact URL, then exchange the returned URL with `$GSETUP --auth-code "..."`. |
| **`google_token.json` looks present but Gmail returns 401/invalid credentials** | Re-run `setup.py --check`. If it still reports `Token is invalid`, `REFRESH_FAILED`, or `invalid_grant: Token has been expired or revoked`, the token has likely expired or been revoked; re-authorize with setup and replace the token before retrying. |
| Advanced Protection blocks auth | Workspace admin must allowlist the OAuth client ID |

## Revoking Access

```bash
$GSETUP --revoke
```
