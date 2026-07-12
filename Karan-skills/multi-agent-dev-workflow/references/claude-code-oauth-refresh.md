# Claude Code OAuth Refresh and Telegram Handoff

Use when `claude auth status` says logged in but actual `claude --print` calls fail with `401 Invalid authentication credentials`, or when Karan is tired of repeated Claude Code re-auth loops.

## Diagnosis

Do not trust `claude auth status` alone. It can report a valid Max subscription while model calls fail.

Check real execution first:

```bash
claude --safe-mode --model sonnet --print 'Reply exactly CLAUDE_READY'
```

If that returns `401`, inspect token expiry without printing token values:

```bash
python3 - <<'PY'
from pathlib import Path
import json, datetime, time
p = Path.home()/'.claude/.credentials.json'
data = json.loads(p.read_text())['claudeAiOauth']
exp = data.get('expiresAt', 0) / 1000
print('expires', datetime.datetime.fromtimestamp(exp).isoformat())
print('expired_seconds', int(time.time() - exp))
print('token_lengths', len(data.get('accessToken','')), len(data.get('refreshToken','')))
PY
```

## Preferred repair

Try normal subscription login before `setup-token`:

```bash
claude auth login --claudeai --email sabnani.kl@gmail.com
```

Run it in a PTY/background process. Send Karan the full OAuth URL as a raw code block if Telegram link previews mangle query params. Karan will paste back a value shaped like:

```text
<code>#<state>
```

Submit that exact string to the PTY prompt.

## Why normal login first

In one session, `claude setup-token` accepted the pasted token (masked as `****`) but hung and did not update credentials. Normal `claude auth login --claudeai --email ...` exited with `Login successful` and immediately restored real `claude --print` calls, even though `~/.claude/.credentials.json` still showed the old expired `expiresAt`. The active credential path may be keychain/internal rather than that JSON file.

## Verification

After login, verify both generic and builder-lane calls:

```bash
claude --safe-mode --model sonnet --print 'Reply exactly CLAUDE_READY'

cd /path/to/repo
env -u GH_TOKEN claude --safe-mode --model sonnet --print \
  --dangerously-skip-permissions \
  --system-prompt-file AGENTS.md \
  'Smoke test only. Do not edit files. Run git status --short --branch, then reply DONE: CLAUDE_BUILDER_READY'
```

Report Claude Code usable only after actual output matches `CLAUDE_READY` / `DONE: CLAUDE_BUILDER_READY`.

## Telegram OAuth URL pitfalls

- Prefer raw code blocks over markdown links for long OAuth URLs.
- If the browser says `Missing client_id`, Telegram or the browser likely opened only part of the query string. Ask Karan to copy/paste the entire raw URL manually.
- If a setup-token/auth process hangs after token paste and credentials do not update, kill the process before starting a new auth flow.
