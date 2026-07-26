# SQLite Lineage Probe

Use `python3.11` and `~/.hermes/state.db` when semantic session search does not provide a complete target-day inventory.

## Inventory query

Compute timezone-aware start/end epochs, then join `sessions` to `messages` where message timestamps fall inside the interval:

```sql
SELECT
  s.id,
  s.source,
  s.title,
  s.parent_session_id,
  s.started_at,
  s.ended_at,
  s.message_count,
  s.tool_call_count,
  MIN(m.timestamp) AS first_msg,
  MAX(m.timestamp) AS last_msg,
  SUM(CASE WHEN m.role = 'user' THEN 1 ELSE 0 END) AS users,
  SUM(CASE WHEN m.role = 'assistant' THEN 1 ELSE 0 END) AS assistants
FROM sessions s
JOIN messages m
  ON m.session_id = s.id
 AND m.timestamp >= ?
 AND m.timestamp < ?
GROUP BY s.id
ORDER BY first_msg;
```

This includes sessions started before the calendar boundary but active inside it.

## Compact transcript slices

For each lineage, begin with:

```sql
SELECT content
FROM messages
WHERE session_id = ?
  AND role = 'user'
  AND COALESCE(content, '') != ''
ORDER BY timestamp ASC
LIMIT 1;
```

```sql
SELECT content
FROM messages
WHERE session_id = ?
  AND role = 'assistant'
  AND COALESCE(content, '') != ''
ORDER BY timestamp DESC
LIMIT 1;
```

If the final response is a narrow answer or lacks the decision trail, inspect only substantive user/assistant messages from that lineage. Do not print complete `tool_calls` or `api_content` fields by default.

## Lineage grouping

Build a map of `id -> parent_session_id`, follow parents to the root, and group all descendants under that root. A continuation can itself have a parent continuation; follow the chain until `NULL` or a missing parent.

Recommended exclusions when represented by a parent:

- `source = 'subagent'`;
- IDs prefixed with `bg_`;
- delegated worker transcripts whose consolidated result appears in the root session.

Recommended cron filter:

- include durable writes, state changes, actionable findings, and meaningful reports;
- exclude final outputs such as `NO_ALERT`, `NO_CHANGE`, `[SILENT]`, or empty health checks.

## Token-control rules

- Query metadata before content.
- Truncate exploratory snippets; retrieve more only for ambiguous lineages.
- Use low-limit `session_search` queries based on lineage titles.
- Never use a common date string as the only high-limit semantic query.
- Summarize one outcome per workstream rather than one bullet per session ID.