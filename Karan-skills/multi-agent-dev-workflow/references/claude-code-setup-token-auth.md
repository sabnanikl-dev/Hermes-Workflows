# Claude Code setup-token auth: durable workflow notes

Use this when Claude Code says `claude auth status` is logged in but real `claude --print` calls return `401 Invalid authentication credentials`, or when Karan is tired of repeated Claude Code re-auth.

## Diagnosis pattern

1. Verify auth metadata:

```bash
claude auth status
```

2. Verify actual model calls, preferably in safe mode:

```bash
claude --safe-mode --model sonnet --print 'Reply exactly CLAUDE_READY'
```

3. If status is logged-in but calls return 401, inspect the OAuth expiry without printing token values:

```bash
python3 - <<'PY'
from pathlib import Path
import json, datetime, time
p = Path.home()/'.claude/.credentials.json'
data = json.loads(p.read_text())['claudeAiOauth']
exp = data.get('expiresAt', 0) / 1000
print('expires', datetime.datetime.fromtimestamp(exp).isoformat())
print('expired_seconds', int(time.time() - exp))
PY
```

## Preferred fix

Prefer a long-lived Claude Code token over repeated OAuth login:

```bash
claude setup-token
```

This is interactive and browser-based. It may display a one-time URL and then wait for:

```text
Paste code here if prompted>
```

Karan may need to open the URL and paste the code back into Telegram.

## Telegram/OAuth URL handling pitfall

Claude Code prints long setup URLs in a PTY, and the terminal output can wrap mid-parameter (`redir\nect_uri`, split `code_challenge`, etc.). Do **not** blindly copy wrapped terminal text as-is.

When sending the URL to Karan on Telegram:

1. Prefer the URL that Claude opened in the browser automatically if available.
2. If reconstructing from PTY output, join wrapped fragments carefully and verify required query params exist:
   - `client_id`
   - `response_type=code`
   - `redirect_uri`
   - `scope=user:inference`
   - `code_challenge`
   - `code_challenge_method=S256`
   - `state`
3. Send both:
   - a Markdown clickable link
   - the raw URL in a fenced `text` block for long-press/copy
4. If Karan reports `invalid oauth request`, assume the URL was malformed, stale, or host-normalized incorrectly. Kill the waiting `claude setup-token` process, start a fresh one, and send the fresh URL rather than trying to salvage the old one.

## Verification after token setup

After submitting the code to the waiting process, verify both:

```bash
claude auth status
claude --safe-mode --model sonnet --print 'Reply exactly CLAUDE_READY'
```

Only report Claude Code fixed after the model call succeeds; `auth status` alone is insufficient.
