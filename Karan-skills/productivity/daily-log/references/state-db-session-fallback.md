# State DB Session Fallback for Daily Logs

Use this when daily-log cron discovery is sparse and `~/.hermes/sessions/session_*YYYYMMDD*.json` files do not exist for the target date, but recent-mode `session_search()` shows sessions happened.

## Why

Some Hermes sessions are persisted primarily in `~/.hermes/state.db` instead of per-session JSON files. Keyword search for the literal date can also miss sessions because user/assistant messages rarely contain the date string.

## Workflow

1. Compute the target day's local time window, usually America/New_York for the 1 AM ET daily-log cron.
2. Open `~/.hermes/state.db` with `sqlite3` from `python3.11`.
3. Query `sessions` where `started_at >= start_ts and started_at < end_ts`, ordered by `started_at`.
4. For each session, query `messages` by `session_id`, ordered by `id`.
5. Summarize only useful signal:
   - first/combined user prompts
   - final non-empty assistant response
   - notable tool names/counts
   - verified writes or created artifacts mentioned in the final response
6. Exclude empty placeholder sessions and redact secrets.
7. Roll related subagent sessions into the parent workstream instead of listing every child independently.

## Example probe

```python
import sqlite3, datetime, textwrap
from zoneinfo import ZoneInfo
from collections import Counter

DB = '/Users/creator/.hermes/state.db'
target = datetime.date(2026, 5, 27)
tz = ZoneInfo('America/New_York')
start = datetime.datetime(target.year, target.month, target.day, tzinfo=tz).timestamp()
end = (datetime.datetime(target.year, target.month, target.day, tzinfo=tz) + datetime.timedelta(days=1)).timestamp()

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
sessions = con.execute(
    'select * from sessions where started_at>=? and started_at<? order by started_at',
    (start, end),
).fetchall()

for s in sessions:
    msgs = con.execute(
        'select id, role, content, tool_name, timestamp from messages where session_id=? order by id',
        (s['id'],),
    ).fetchall()
    users = [m['content'] for m in msgs if m['role'] == 'user' and m['content']]
    assistants = [m['content'] for m in msgs if m['role'] == 'assistant' and m['content']]
    tools = Counter(m['tool_name'] for m in msgs if m['role'] == 'tool' and m['tool_name'])
    print('\n==', s['id'], s['source'], s['message_count'], s['tool_call_count'])
    print('USER:', textwrap.shorten(' | '.join(users), width=500, placeholder='...'))
    if assistants:
        print('LAST:', textwrap.shorten(assistants[-1].replace('\n', ' | '), width=800, placeholder='...'))
    if tools:
        print('TOOLS:', tools.most_common(8))
```

## Pitfalls

- Do not use `around_message_id=1` with `session_search` scroll mode unless message id 1 is actually in that session. Scroll mode requires a real message id returned by discovery.
- Do not create an empty log just because keyword search missed the day. Check recent sessions and state DB first.
- Keep the final daily log under 3,000 chars; group subagent/research branches under the parent task.
