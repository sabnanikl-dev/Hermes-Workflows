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
 AND m.active = 1
 AND m.timestamp >= ?
 AND m.timestamp < ?
GROUP BY s.id
ORDER BY first_msg;
```

This includes sessions started before the calendar boundary but active inside it while excluding rewound/inactive message branches.

## Compact transcript slices

For each lineage, begin with:

```sql
SELECT content
FROM messages
WHERE session_id = ?
  AND active = 1
  AND role = 'user'
  AND COALESCE(content, '') != ''
ORDER BY timestamp ASC
LIMIT 1;
```

```sql
SELECT content
FROM messages
WHERE session_id = ?
  AND active = 1
  AND role = 'assistant'
  AND COALESCE(content, '') != ''
ORDER BY timestamp DESC
LIMIT 1;
```

If the final response is a narrow answer or lacks the decision trail, inspect only substantive user/assistant messages from that lineage. Do not print complete `tool_calls` or `api_content` fields by default.

### Compaction-heavy continuations

A truncated `session_search(session_id=...)` read may show mostly tool payloads or an interim root closeout even when later continuation sessions contain the real outcome. For each child continuation:

1. Inspect its first active user message for a `CONTEXT COMPACTION` handoff.
2. Extract only the task goal, completed actions, active state, decisions, and unresolved next step; do not copy the whole handoff.
3. Compare that handoff with the child's final active, non-empty assistant message.
4. Treat both as retrieval leads. Verify “merged,” “closed,” deployed, or completed claims against the live source system before writing a current-status artifact.

This is especially useful when one workstream crosses several ACP/Buzz continuations and the root session's last assistant message predates the final approval or cleanup.

## Lineage grouping

Build a map of `id -> parent_session_id`, follow parents to the root, and group all descendants under that root. A continuation can itself have a parent continuation; follow the chain until `NULL` or a missing parent.

Run the compact first-user/last-assistant queries for **every** retained session in the lineage, not only the root. Sort members by `started_at` and compare their closeouts. The common failure mode is a root whose last answer says “review is starting” while a later child records a blocker, an approved merge, or verified cleanup. Treat the deepest/latest child closeout as provisional, then reconcile any completion claim against the current source system.

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