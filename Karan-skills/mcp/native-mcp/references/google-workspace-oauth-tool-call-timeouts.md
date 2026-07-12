# Google Workspace MCP OAuth: discovery succeeds but real tool calls timeout

Use this when Google Workspace MCP servers (`google_calendar`, `google_drive`, `google_gmail`, `google_people`) pass `hermes mcp test` / tools discovery but actual MCP tool calls hang until the configured timeout.

## Symptom pattern

- `hermes mcp test <server>` connects and lists tools.
- Real low-risk calls such as these return `TimeoutError` after 120s:
  - `mcp_google_calendar_list_calendars`
  - `mcp_google_gmail_list_labels`
  - `mcp_google_people_get_user_profile`
  - `mcp_google_drive_list_recent_files`
- Logs may show:
  - `MCP OAuth for '<server>': non-interactive environment and no cached tokens found`
- `~/.hermes/mcp-tokens/<server>.client.json` or `<server>.meta.json` may exist, but that is not proof a usable OAuth access/refresh token exists.

## Key distinction

Google MCP servers can allow initialize/tools-list without proving authenticated resource access. Treat discovery as necessary but insufficient.

Token cache indicators:

- Real token file: `~/.hermes/mcp-tokens/<server>.json`
- Metadata/client registration only: `~/.hermes/mcp-tokens/<server>.meta.json`, `<server>.client.json`

If the real token file is missing or stale, actual tool calls may hang/timeout even though discovery succeeded.

## Safe diagnostic sequence

1. Run discovery for all servers:

```bash
hermes mcp list
for s in codegraph filesystem github google_calendar google_drive google_gmail google_people playwright; do
  echo "===== $s ====="
  hermes mcp test "$s" 2>&1 || true
  echo
done
```

2. Inspect recent logs without dumping secrets:

```bash
grep -iE 'mcp|oauth|google_calendar|google_drive|google_gmail|google_people|timeout|failed|error' ~/.hermes/logs/agent.log ~/.hermes/logs/gateway.log | tail -120
```

3. Check token cache file presence/metadata only:

```bash
find ~/.hermes/mcp-tokens -maxdepth 1 -type f -print0 \
  | xargs -0 stat -f '%Sp %z %Sm %N' -t '%Y-%m-%d %H:%M:%S %Z'
```

4. Verify with one low-risk real tool call per server after OAuth. Do not claim success from `hermes mcp test` alone.

## Fix

Re-authentication writes Google account OAuth tokens, so get explicit approval before running these flows.

```bash
hermes mcp login google_calendar
hermes mcp login google_gmail
hermes mcp login google_people
# optionally, if Drive also times out or has stale state:
hermes mcp login google_drive
```

Then restart/reload the process that will use MCP so it gets fresh connections:

```bash
hermes gateway restart
# or exit and start a fresh CLI session
```

## Verification after fix

Run discovery again, then real calls:

- Calendar: `list_calendars`
- Gmail: `list_labels`
- People: `get_user_profile`
- Drive: `list_recent_files`

Only report the Google MCPs as fixed after the real calls return data or an expected authorization/permission error rather than a transport timeout.
