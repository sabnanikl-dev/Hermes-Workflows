# Session Transcript Fallback for Daily Log Cron

## Trigger
Use this when `session_search` is sparse or misses obvious sessions for the target date, especially during scheduled cron runs.

## Pattern
Recent sessions may appear in `session_search` recent mode but not match keyword search by date/session id. When that happens, inspect local session files directly:

1. Search for session files by date stamp:
   - `~/.hermes/sessions/session_*YYYYMMDD*.json`
2. Parse the JSON and summarize:
   - `session_start`, `last_updated`, `platform`, `model`, `message_count`
   - user prompt/task
   - final assistant answer
   - tool failures/successes relevant to the log
3. Use direct transcript details to create the daily log rather than treating sparse `session_search` as “no sessions.”

## What to avoid
- Do not create an empty log when recent mode shows sessions for the target date.
- Do not log raw secrets from transcripts. If credentials/tokens are inspected, record only paths, failure classes, and redacted metadata.
- Do not over-record transient session ids in durable logs unless needed for debugging the logging system itself.

## Example learning
On 2026-05-17, keyword `session_search` missed same-day cron sessions, while recent mode showed them and local files existed under `~/.hermes/sessions/session_*20260517*.json`. Direct JSON inspection revealed the daily-log cron success and Google Workspace OAuth `invalid_grant` failure, allowing a real daily log to be written instead of silently skipping.