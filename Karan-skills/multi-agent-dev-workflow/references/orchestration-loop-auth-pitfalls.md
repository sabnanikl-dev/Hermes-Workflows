# Orchestration Loop Auth Pitfalls

Session-derived reference for validating a Hermes → Claude Code → CodexReviewer loop where the point of the test is that the external agents, not Hermes, perform their own handoffs.

## Claude Code auth failures

### `--bare` false login failure

Claude Code v2.1.x `--bare` skips OAuth/keychain reads. It may print:

```text
Not logged in · Please run /login
```

even when normal Claude Code is logged in and works.

Use non-bare builder/fix commands for OAuth/keychain-backed local Claude Code:

```bash
claude --model 'claude-opus-4-8[1m]' --print --dangerously-skip-permissions \
  --system-prompt-file AGENTS.md \
  "..."
```

Only use `--bare` when intentionally supplying `ANTHROPIC_API_KEY` or an `apiKeyHelper` via settings.

### `auth status` says logged in but `--print` returns 401

Claude Code can report a valid subscription via `claude auth status` while actual model calls fail with:

```text
Failed to authenticate. API Error: 401 Invalid authentication credentials
```

Check whether `~/.claude/.credentials.json` has an expired OAuth access token without printing token values:

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

If expired and normal calls still 401, prefer `claude setup-token` over repeated `claude auth login`: it creates a longer-lived token for Claude Code subscription auth. It is interactive/browser-based and may require Karan to paste the one-time code. See `references/claude-code-setup-token-auth.md` for the full Telegram-safe URL handoff pattern.

**Important:** `claude setup-token` prints long OAuth URLs inside a PTY and they can wrap mid-parameter. When sending Karan a copyable Telegram link, do not paste wrapped terminal output blindly. Send a Markdown clickable link plus the raw unwrapped URL in a fenced `text` block. If the user reports `invalid oauth request`, kill/restart `claude setup-token` and send the fresh URL rather than trying to reuse the old one.

If expired and normal calls still 401, first try a normal Claude subscription login refresh; it may repair the active keychain/internal credential path even when `~/.claude/.credentials.json` still shows an old `expiresAt`:

```bash
claude auth login --claudeai --email <user-email>
# paste the browser one-time code into the PTY prompt
```

Verify success with a real model call, not `auth status` or the JSON expiry field alone:

```bash
claude --safe-mode --model sonnet --print 'Reply exactly CLAUDE_READY'
```

Only escalate to `claude setup-token` if normal login does not repair real calls. `setup-token` is interactive/browser-based, may require Karan to paste a one-time code, and can hang after masking the pasted token; kill the stuck PTY and fall back to `claude auth login` if credentials do not update and the process does not exit.

Smoke test before a loop run:

```bash
claude --model 'claude-opus-4-8[1m]' --print 'Reply exactly CLAUDE_READY'
claude --model 'claude-opus-4-8[1m]' --print --dangerously-skip-permissions --system-prompt-file AGENTS.md \
  'Smoke test only. Do not edit files. Run git status --short --branch, then reply DONE: CLAUDE_BUILDER_READY'
```

## CodexReviewer reviewer-token validation

Inject the reviewer GitHub PAT as a per-process `GH_TOKEN` from macOS Keychain:

```bash
TOKEN="$(security find-generic-password -a codex-reviewer -s hermes-codex-reviewer-github-token -w)"
GH_TOKEN="$TOKEN" gh api user --jq .login
GH_TOKEN="$TOKEN" codex exec --dangerously-bypass-approvals-and-sandbox '...review prompt...'
```

Reviewer roles that need to submit real GitHub reviews do **not** need to run in the Codex CLI sandbox. Prefer unsandboxed/danger-full-access reviewer runs for loop validation so `gh pr review`, REST review submission, and GraphQL review submission use the same network/auth path as Hermes verification. Use `--sandbox workspace-write` only for read-only review dry runs or deliberate sandbox testing.

Inside Codex CLI sandbox, `gh auth status` can report `GH_TOKEN` invalid and `gh pr review`/GitHub review POSTs can fail with `error connecting to api.github.com` even when concrete `gh api user` reads work. Treat that as a sandbox artifact unless it reproduces unsandboxed. Prefer these concrete checks:

```bash
gh api user --jq .login
gh pr view <PR> --repo <owner>/<repo> --json reviewDecision,latestReviews --jq .
```

If `gh api user` returns the reviewer login but `gh pr review` fails, treat it as a reviewer-submit failure to debug, not as a clean loop pass.

## Dogfood-loop validity rule

For a loop-validation test, the external role must perform its own handoff:

- Builder agent creates/commits/pushes/opens the PR.
- Reviewer agent submits the GitHub review itself.

Hermes may verify, synthesize, and clean up, but if Hermes performs a handoff after the agent fails, the run is a fallback/manual recovery and must be reported as a failed loop test, even if the final GitHub state looks correct.

## Reporting pattern

When a run fails as a loop test, say so directly:

```text
This is not a clean loop pass.
Builder handoff: failed because ...
Reviewer handoff: failed because ...
Manual/Hermes fallback performed: yes/no
Verified final state: ...
Next corrected test: ...
```
