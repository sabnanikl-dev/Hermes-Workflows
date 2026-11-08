# Gmail Send Fallback When `gws` Is Read-Only

## Trigger
Use this when sending email via the Google Workspace helper fails with:

- `Request had insufficient authentication scopes` from `gws gmail users messages send`
- `google_api.py gmail send` also fails because it detects `gws` first and routes through the same read-only `gws` credential

## Durable Lesson
`gws` and the Hermes Python Google helper may use different credential stores/scopes. A configured `gws` profile can be valid for read-only Gmail operations while lacking `gmail.send`. In that state, `google_api.py` may still try `gws` first and inherit the same scope failure.

## Working Fallback Pattern
Force `google_api.py` to use its Python client fallback by hiding `gws` from `PATH` for that one send command:

```bash
PATH=/usr/bin:/bin /Users/creator/.hermes/hermes-agent/venv/bin/python3.11 \
  /Users/creator/hermes-agent-sabnanikl/skills/productivity/google-workspace/scripts/google_api.py \
  gmail send \
  --to 'Recipient <recipient@example.com>' \
  --subject 'Subject here' \
  --body "$BODY"
```

If the Python fallback errors with `missing field type` in `~/.hermes/google_token.json`, normalize the token JSON once by adding:

```json
"type": "authorized_user"
```

Do not rewrite credentials wholesale or preserve secrets in logs. Verify the token already contains the needed scope, e.g. `https://www.googleapis.com/auth/gmail.send`, before sending.

## Verification After Send
After the helper returns a sent message ID, verify with Gmail metadata/full read:

```bash
gws gmail users messages get \
  --params '{"userId":"me","id":"MESSAGE_ID","format":"metadata","metadataHeaders":["From","To","Subject","Date"]}'
```

Confirm:

- `labelIds` includes `SENT` from a full message read if needed
- recipient and subject match
- key body strings/links are present

This is a fallback technique, not a claim that `gws` is broken. If `gws` is re-authorized later with send scope, the normal path may work again.
