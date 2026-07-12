# Google Workspace: use `gws` CLI as fallback/control plane when MCP OAuth stalls

Use this when Google Workspace MCP servers discover tools successfully but real authenticated calls hang, or when you need a more auditable Workspace workflow than direct MCP calls.

## When this helps

- Google MCP `hermes mcp test google_*` succeeds, but calls such as `mcp_google_people_get_user_profile`, `mcp_google_gmail_list_labels`, or `mcp_google_drive_list_recent_files` time out.
- You need CLI-first behavior: JSON output, dry-runs where available, repeatable commands, and easier OAuth/debug visibility.
- You want to avoid treating MCP discovery as proof of authenticated access.

## Install `gws`

Preferred on macOS:

```bash
brew install googleworkspace-cli
gws --version
gws auth status
```

Alternative:

```bash
npm install -g @googleworkspace/cli
```

## OAuth setup without `gcloud`

`gws auth setup` requires `gcloud`. If `gcloud` is not installed, use an existing Google OAuth Desktop client JSON or create one manually in Google Cloud Console.

`gws` expects the client file at:

```bash
~/.config/gws/client_secret.json
chmod 600 ~/.config/gws/client_secret.json
```

The JSON must be a full Google OAuth client export with an `installed` block and fields like `project_id`, `client_id`, `client_secret`, `auth_uri`, and `token_uri`. A minimal MCP dynamic-client JSON is not enough; if `gws auth status` reports `missing field project_id`, use the full downloaded client secret JSON instead.

Then authenticate with narrow scopes first to avoid unverified-app scope limits:

```bash
gws auth login --readonly -s drive,gmail,calendar,people
```

For human-in-loop OAuth, keep the `gws auth login` process running while the browser consent flow completes. If the browser shows or redirects to a `localhost` callback URL, paste/open that URL while the listener process is still alive; stale callback URLs fail with connection refused after the listener exits.

## Verify after auth

Do not stop at `gws auth status`; run one low-risk read command and inspect real JSON output. Examples:

```bash
gws drive files list --params '{"pageSize": 3}'
gws gmail users.labels.list --params '{"userId": "me"}'
gws calendar calendarList list --params '{"maxResults": 3}'
```

If an API returns `accessNotConfigured`, enable the named API in the Google Cloud project from the error’s `enable_url`, wait briefly, then retry.

## Relationship to Google MCP

- Use `gws` for reliable execution/debugging and for mutations where CLI dry-runs or JSON payload review are helpful.
- Use Google MCP for quick low-risk reads/actions once real authenticated tool calls have been verified.
- After fixing OAuth or tokens, restart/reload the Hermes process using MCP connections before expecting fresh tokens to be picked up everywhere.
