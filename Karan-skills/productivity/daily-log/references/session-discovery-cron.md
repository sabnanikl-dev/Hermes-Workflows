# Daily Log Cron Session Discovery

Use this when synthesizing yesterday's daily log and keyword/date search misses obvious activity.

## Why
`session_search(query="YYYY-MM-DD")` only finds sessions whose message text contains that date. Many real user sessions do not mention the date, so date-keyword search can be sparse even when the session DB has activity for the target day.

## Recommended discovery sequence
1. Check whether the target daily-log file already exists. If it does, stop silently.
2. Run targeted date-keyword discovery (`YYYY-MM-DD`, `Month D YYYY`, `Month D`).
3. Run recent-mode `session_search()` and filter sessions by `started_at` / `last_active` for the target calendar day.
4. Search for likely high-signal project/task terms from recent previews when needed (for example: `Femme`, `Amanda`, `gateway`, `cron`, `Google Sheet`, `closeout`).
5. If recent-mode still looks sparse, inspect `~/.hermes/sessions/request_dump_*YYYYMMDD*.json` and summarize verified user/assistant messages from the transcript dumps.

## Summarization guidance
- Group busy days into workstreams rather than one bullet per chat.
- Include decisions, discussions, verification categories, and meaningful outputs.
- Avoid temporary details like PR numbers, commit SHAs, one-off message IDs, and raw tool dumps.
- Create standalone lesson pages only for durable mistakes, workflow fixes, or repeatable provider/tool quirks; link them from `Mistakes & Lessons`.
