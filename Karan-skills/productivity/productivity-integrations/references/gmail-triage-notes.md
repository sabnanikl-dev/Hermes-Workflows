# Gmail Triage Notes

Concise operating notes for read-only Gmail checks.

## Auth check
Run before reading mail:

```bash
~/.hermes/venvs/google-workspace/bin/python ~/.hermes/skills/productivity/productivity-integrations/references/absorbed/google-workspace/scripts/setup.py --check
```

## Unread inbox check

```bash
~/.hermes/venvs/google-workspace/bin/python ~/.hermes/skills/productivity/productivity-integrations/references/absorbed/google-workspace/scripts/google_api.py gmail search 'is:unread newer_than:1d' --max 20
```

## Sent mail check

```bash
~/.hermes/venvs/google-workspace/bin/python ~/.hermes/skills/productivity/productivity-integrations/references/absorbed/google-workspace/scripts/google_api.py gmail search 'in:sent newer_than:7d' --max 30
```

## Reply-detection pitfall
`thread:<messageId>` does not work with `gmail search` on the messages list endpoint. To see whether a sent email got a reply, prefer:

1. Search broadly with `in:anywhere newer_than:7d from:<recipient>` to surface follow-up activity
2. Then confirm the conversation with `users.threads.get` (via `gws_hermes.sh`) on the sent message's `threadId`
3. Treat a lone `SENT` message in the thread as unreplied until a second message from someone else appears in the thread

Example thread lookup:
```bash
~/.hermes/skills/productivity/productivity-integrations/references/absorbed/google-workspace/scripts/gws_hermes.sh gmail users threads get --params '{"userId":"me","id":"THREAD_ID"}'
```

## Sent-message metadata pitfall
`gmail get` on sent mail can return empty `to` and `subject` fields. If you need the recipient or subject, recover them from the thread metadata or the original compose context instead of assuming those fields are meaningful. When available, trust the thread-level headers over the per-message search summary.
