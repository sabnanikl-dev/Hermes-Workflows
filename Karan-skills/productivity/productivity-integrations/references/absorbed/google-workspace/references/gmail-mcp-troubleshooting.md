# Gmail MCP Troubleshooting

Use this when the Gmail MCP tools fail in cron or non-interactive sessions.

## Failure signatures observed
- `mcp_google_gmail_search_threads` / `mcp_google_gmail_get_thread` return `TimeoutError`
- `mcp.client.auth.oauth2: OAuth flow error`
- `OAuth callback timed out — no authorization code received`
- `Protected resource https://gmailmcp.googleapis.com/mcp/v1 does not match expected https://gmailmcp.googleapis.com`
- `google_api.py` or raw Gmail API requests return `401 Invalid Credentials`
- `setup.py --check` reports `Token is invalid`

## What to do
1. **Stop retrying the MCP tool unchanged.** Repeated retries just burn the cron budget.
2. **Check token health first.** Run `setup.py --check`.
3. **If the token is invalid or revoked, re-authenticate** and replace `~/.hermes/google_token.json`.
4. **Prefer the direct API wrapper** for read-only Gmail triage when MCP Gmail is unstable:
   - `python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py gmail search "is:unread newer_than:1d" --max 50`
   - `python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py gmail search "in:sent newer_than:7d" --max 50`
5. **For thread detail**, use `gmail get MESSAGE_ID` or a direct Gmail API request with the cached token.
6. **If Gmail search works but sent/reply status is unclear**, inspect raw message headers / thread IDs before declaring a sent item unreplied.

## Notes
- The MCP Gmail server can be reachable while still failing OAuth during the search call.
- Non-interactive cron runs are especially sensitive to callback-based OAuth flows.
- A present token file is not proof of validity; always verify with an actual API call or `setup.py --check`.
