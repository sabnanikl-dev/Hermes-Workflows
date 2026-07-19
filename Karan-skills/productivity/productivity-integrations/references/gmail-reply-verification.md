# Gmail reply verification

Use this when a sent message needs to be checked for an actual reply, not just a search hit.

## Core rule
`gmail search` works on messages, not conversations. To determine whether a sent email was replied to, inspect the thread and count distinct messages.

## Read-only workflow
1. Search sent mail:
   ```bash
   ~/.hermes/venvs/google-workspace/bin/python ~/.hermes/skills/productivity/productivity-integrations/references/absorbed/google-workspace/scripts/google_api.py gmail search 'in:sent newer_than:7d' --max 30
   ```
2. From the search result, capture the `threadId`.
3. Fetch the thread:
   ```bash
   bash ~/.hermes/skills/productivity/productivity-integrations/references/absorbed/google-workspace/scripts/gws_hermes.sh gmail users threads get --params '{"userId":"me","id":"THREAD_ID"}'
   ```
4. Treat a thread with only one `SENT` message as unreplied.
5. Treat a thread as replied once a second message from another sender appears in the thread.

## Metadata pitfall
`gmail get` on sent mail can return empty or unhelpful `to` and `subject` fields. Prefer thread-level data when you need to confirm the recipient, subject, or reply status.
