---
name: gateway-troubleshooting
category: devops
description: Diagnose and fix Hermes gateway issues when messaging platforms (Telegram, Discord, Slack, etc.) stop responding.
---

## Trigger
- User reports not getting responses on Telegram/Discord/WhatsApp/etc.
- Gateway appears stuck, disconnected, or stopped
- `hermes doctor` reports gateway issues

## Diagnosis Steps

### 1. Check gateway state
```bash
cat ~/.hermes/gateway_state.json
```
Look for:
- `gateway_state`: "running" or "stopped"
- `platforms.telegram.state`: "connected" or "disconnected"
- If stopped, note the exit_time and reason

### 2. Check gateway process
```bash
ps aux | grep -i hermes
```
Compare PID with gateway_state.json pid. If no process matches, it's dead.

### 3. Check logs for last activity
```bash
tail -50 ~/.hermes/logs/gateway.log
```
Look for:
- Last successful message sent/received
- Any error before shutdown
- "Stopping gateway..." or "Disconnected" messages
- Pattern: agent may have killed its own process (self-kill during config change)

### 4. Check error logs
```bash
cat ~/.hermes/logs/gateway.error.log
```
Look for unhandled exceptions, API errors, authentication failures.

## Fix Steps

### Gateway is stopped
```bash
hermes gateway start
```
Verify:
```bash
cat ~/.hermes/gateway_state.json
# Should show "running" and "connected"
```

### Gateway is running but platform disconnected
```bash
hermes gateway restart
```
Or stop and start:
```bash
hermes gateway stop
hermes gateway start
```

### Gateway config issue (token revoked, etc.)
1. Check `~/.hermes/config.yaml` for the platform section (telegram, discord, etc.)
2. Verify the bot token/channel is still valid
3. Update token if needed: `hermes setup` or edit config.yaml directly
4. Restart gateway after config changes

## Common Pitfalls

### Self-kill during config changes
If the agent runs `kill <PID>` to restart while changing Discord/other platform config, it kills its own process and the restart never completes. This is the most common cause of "silent" gateway death. The agent cannot restart itself via `kill` -- it must use `hermes gateway restart` or `hermes gateway start`.

### launchd service drift
If the gateway was installed via launchd on macOS, run `hermes gateway start` (not just `hermes gateway run`) to ensure the service definition matches the current install.

### Token/credential expiration
Platform bot tokens can be revoked or expired. Check error logs for 401/auth errors. Reconfigure with `hermes setup` if needed.

### Nous Portal Tool Gateway auth expired
If web/search/browser/image/TTS are configured with `use_gateway: true` but tools fail as not configured, check `hermes portal status` before adding direct vendor API keys. When the user expects Nous subscription routing, reauth with `hermes auth add nous --type oauth`, relay the Portal URL/user code to the human, then verify `hermes portal tools`/`hermes status` and a tiny live web smoke test. Detailed flow: `references/nous-portal-tool-gateway-reauth.md`.

### Discord: token in config.yaml not enabling the platform
The gateway config loader at `gateway/config.py` may be missing the mapping of `discord.token` from config.yaml to the `DISCORD_BOT_TOKEN` env var. The adapter reads from env vars, not directly from config.yaml. This causes Discord to be silently skipped — gateway logs show `Gateway running with 1 platform(s)` with no Discord error, while `hermes status` shows `Discord ✗ not configured`.

Detailed reproduction/fix reference: `references/discord-token-env-mismatch.md`.

Fix both layers:
1. Add/ensure `.env` has `DISCORD_BOT_TOKEN=<same token>` (not only `DISCORD_TOKEN`). Do this by copying the existing `discord.token` value from config, without printing it.
2. Add the config-loader mapping in the Discord config block in `gateway/config.py`:
```python
discord_cfg = yaml_cfg.get("discord", {})
if isinstance(discord_cfg, dict):
    if "token" in discord_cfg and not os.getenv("DISCORD_BOT_TOKEN"):
        os.environ["DISCORD_BOT_TOKEN"] = str(discord_cfg["token"]).strip()
```
3. Restart: `hermes gateway restart`

Verification:
- `hermes status` should show `Discord ✓ configured`.
- After the active gateway session drains/restarts, `tail -20 ~/.hermes/logs/gateway.log` should show `✓ discord connected` and `Gateway running with 2 platform(s)`.
- If restart remains stuck in `draining`, wait until the current gateway-handled agent turn completes; the restart may not fully execute while an active Telegram/Discord agent session is still running.

### Discord: Discord-specific settings silently ignored
Settings like `tool_progress`, `background_process_notifications`, `auto_thread`, and `reactions` in config.yaml must be mapped to env vars (`DISCORD_TOOL_PROGRESS`, `DISCORD_AUTO_THREAD`, etc.) by the config loader. If these mappings are missing, the settings are silently ignored. The config loader section to check is around lines 538-553 in `gateway/config.py`.


### Discord: env var name mismatch — DISCORD_TOKEN vs DISCORD_BOT_TOKEN
The code expects `DISCORD_BOT_TOKEN` everywhere (gateway/config.py lines 783, 862), but `.env` files sometimes have `DISCORD_TOKEN` (without `_BOT_`). If you see Discord missing from connected platforms:

1. Check `.env`: `grep DISCORD ~/.hermes/.env`
2. If it says `DISCORD_TOKEN=...` (not `DISCORD_BOT_TOKEN`), the gateway silently skips Discord
3. Fix: either rename to `DISCORD_BOT_TOKEN` in `.env`, or add `discord.token` to `config.yaml` (the config.py loader now maps it to `DISCORD_BOT_TOKEN`)

Always test if the token is valid before restarting:
```bash
curl -s -H "Authorization: Bot YOUR_TOKEN" https://discord.com/api/users/@me
# Response should have "id" and "username" — if "401: Unauthorized", the token is revoked/expired
```

### Discord: token expired/revoked (401 Unauthorized)
If `curl` to `https://discord.com/api/users/@me` returns `401: Unauthorized`, the token has been revoked or regenerated by Discord:
1. Go to https://discord.com/developers/applications → your bot → Bot → Reset Token
2. Update both `~/.hermes/config.yaml` (`discord.token`) and `~/.hermes/.env` (`DISCORD_BOT_TOKEN` or `DISCORD_TOKEN`)
3. Restart gateway: `hermes gateway restart`

### Discord: user not in allowlist (403 Unauthorized)

Discord requires explicit user allowlisting. If you see "Unauthorized user: <user_id> (username)" in logs, add the Discord user ID to `~/.hermes/.env`:
```
DISCORD_ALLOWED_USERS=693136505438470275,1339702098698174486
```
Use a comma-separated list for multiple allowed users. Then restart the gateway.

Important: `patch`/`write_file` tools may refuse writes to `~/.hermes/.env` because it is treated as a protected credential file. If that happens, use a narrowly scoped `terminal` command or have the user edit the file manually.

### Discord: auto_thread 403 Forbidden (Missing Access)
If `auto_thread: true` and the bot can't create threads in a channel, you'll see `403 Forbidden: Missing Access`. Either:
- Set `auto_thread: false` in config.yaml discord section
- Grant the bot "Create Public Threads" and "Create Private Threads" permissions in Discord server settings

### Telegram: reducing tool-progress verbosity without affecting other platforms
When the user says Telegram is too noisy with tool-call progress, prefer the current display override system instead of changing global display defaults:
```bash
hermes config set display.platforms.telegram.tool_progress off
```

Why this shape:
- `display.platforms.<platform>.tool_progress` is resolved before global `display.tool_progress`.
- This quiets Telegram while leaving Discord/CLI/global behavior alone.
- Hermes currently supports this at the *platform* level; do not promise per-individual Telegram chat/thread behavior unless a channel-level display override feature exists.
- `/verbose` can cycle platform-level tool progress only when `display.tool_progress_command` is enabled; otherwise use `hermes config set` or edit config.yaml.

Verify without exposing secrets:
```bash
python3 - <<'PY'
import os, yaml
p=os.path.expanduser('~/.hermes/config.yaml')
with open(p) as f:
    cfg=yaml.safe_load(f) or {}
d=cfg.get('display') or {}
platforms=d.get('platforms') or {}
print('display.tool_progress:', d.get('tool_progress'))
print('display.platforms.telegram:', platforms.get('telegram'))
print('display.platforms.discord:', platforms.get('discord'))
PY
```
If `display.platforms.telegram.tool_progress` is `false`/`off`, Telegram should be quiet even if `display.tool_progress` remains `all`. A fresh gateway session/restart may be needed for already-cached agents to pick up config changes.

### Telegram: tool_progress silently ignored (legacy bug pattern)
Older Hermes versions had two failure modes:
1. Settings like `tool_progress` and `background_process_notifications` in config.yaml's top-level `telegram` section needed mapping to env vars (`TELEGRAM_TOOL_PROGRESS`, `TELEGRAM_BACKGROUND_PROCESS_NOTIFICATIONS`) by the config loader.
2. Runtime code read only `display.tool_progress` instead of resolving `display.platforms.telegram.tool_progress` first.

If a modern `display.platforms.telegram.tool_progress: off` override is ignored, inspect `gateway/display_config.py` and `gateway/run.py` to confirm `resolve_display_setting(user_config, platform_key, "tool_progress")` is used. Do not fall back to global `display.tool_progress: off` unless the user wants all platforms quiet.

### macOS launchd: env vars don't propagate from .env
If Hindsight (or any service) runs as a macOS launch agent, changes to `~/.hermes/.env` **do NOT take effect** because the launchd plist (`~/Library/LaunchAgents/io.vectorize.hindsight.api.plist`) has hardcoded `EnvironmentVariables` that completely override `.env` changes. To change model, API key, or any env var for a launchd-running service:
```bash
# Update the plist values directly
plutil -replace EnvironmentVariables.HINDSIGHT_API_LLM_MODEL -string "openai/gpt-4o-mini" ~/Library/LaunchAgents/io.vectorize.hindsight.api.plist
plutil -replace EnvironmentVariables.HINDSIGHT_API_LLM_API_KEY -string "sk-or-v1-your-key" ~/Library/LaunchAgents/io.vectorize.hindsight.api.plist

# Verify the change took effect
plutil -extract EnvironmentVariables xml1 -o - ~/Library/LaunchAgents/io.vectorize.hindsight.api.plist

# Reload the service
launchctl unload ~/Library/LaunchAgents/io.vectorize.hindsight.api.plist
launchctl load ~/Library/LaunchAgents/io.vectorize.hindsight.api.plist
```

### Telegram: token in config.yaml
Ensure `telegram.token` is set in config.yaml AND the `TELEGRAM_BOT_TOKEN` env var is properly mapped. The Telegram adapter reads from env vars, not directly from config.yaml.

For non-threaded shared channels like `#femme-events`, disabling `auto_thread` is often the better UX if users expect normal channel replies instead of thread creation.

### `MEDIA:` path shows as text or does not attach (Telegram/Discord)
If a user says "send the actual file" and the response only shows a path or blank attachment area, check whether the file path is outside Hermes' allowed media roots. The gateway may log:

```text
Skipping unsafe MEDIA directive path outside allowed roots
```

`MEDIA:/Users/.../Downloads/file.png` or `MEDIA:/Users/.../.hermes/media_cache/file.png` can be rejected even when the file exists. Copy files into Hermes-managed delivery caches first:

```bash
# Images (PNG/JPG/WebP/GIF)
mkdir -p ~/.hermes/cache/images/<task-name>
cp /path/to/*.png ~/.hermes/cache/images/<task-name>/

# Documents / zips / PDFs / HTML bundles
mkdir -p ~/.hermes/cache/documents/<task-name>
cp /path/to/report.pdf ~/.hermes/cache/documents/<task-name>/
# For multiple generated files, zip them for easier mobile download:
cd ~/.hermes/cache/images/<task-name> && zip -j ~/.hermes/cache/documents/<task-name>/files.zip ./*
```

Then send the cached file with a `MEDIA:` tag:

```text
MEDIA:/Users/creator/.hermes/cache/images/<task-name>/image.png
MEDIA:/Users/creator/.hermes/cache/documents/<task-name>/files.zip
```

Verify the cached file is non-empty before replying. This is a delivery-safety constraint, not proof that attachments are broken.

Discord-specific pitfall: if `send_message` returns success but warnings include `Discord API error (403): Missing Permissions`, the bot reached the channel but lacks the relevant permission (commonly **Attach Files** for file uploads, or channel-specific overwrite permissions). Grant the bot Attach Files in that channel/category and retry from the safe cache path.

### Discord: reply-to-bot should trigger even without a fresh @mention
If the desired UX is “mention or reply only” (not a free-response channel), the stock mention gate may still ignore replies unless the adapter explicitly checks whether the replied-to message was authored by the bot.

Reliable fix in `gateway/platforms/discord.py`:
1. Read `message.reference.message_id`
2. Resolve/fetch the referenced message
3. Detect whether `ref_msg.author.id == self._client.user.id`
4. Bypass the mention requirement when `replied_to_bot` is true
5. Populate `reply_to_text` on the resulting `MessageEvent` so older cross-session replies get context injected by `gateway/run.py`

This preserves a strict channel policy:
- respond to fresh @mentions
- respond to direct replies to Hermes
- do not turn the whole channel into free-response

If the user wants mention-or-reply behavior in a normal channel (not thread-per-conversation), disabling `auto_thread` is usually the right default.

### Discord: mention-only vs reply-to-bot behavior
`require_mention: true` only guarantees response to explicit @mentions. In the stock Discord adapter, plain replies to a Hermes message may still be ignored unless the adapter explicitly treats "replying to the bot" as a valid trigger.

Diagnosis steps:
1. Check `~/.hermes/config.yaml`:
   - `discord.require_mention`
   - `discord.free_response_channels`
   - `discord.auto_thread`
2. Check allowlist in `~/.hermes/.env`:
   - `DISCORD_ALLOWED_USERS`
3. Inspect `gateway/platforms/discord.py` around `_handle_message()`:
   - If mention gating is just `if self._client.user not in message.mentions: return`, replies to Hermes will not trigger unless they also include a fresh mention.
4. Confirm whether reply context is populated into `MessageEvent`:
   - `reply_to_message_id`
   - `reply_to_text`

Reusable fix pattern when user wants mention-or-reply (but NOT free-response):
- Keep `require_mention: true`
- Keep `free_response_channels: ''`
- Set `auto_thread: false` unless threads are desired and bot has permission
- Add all intended humans to `DISCORD_ALLOWED_USERS`
- Patch `gateway/platforms/discord.py` so `_handle_message()`:
  - fetches the referenced message when `message.reference` is present
  - detects whether the replied-to message author is the Hermes bot
  - bypasses the mention gate when `replied_to_bot == True`
  - passes `reply_to_text` into `MessageEvent` for context injection in `gateway/run.py`

Verification:
- Restart with `hermes gateway restart`
- Confirm logs show `[Discord] Connected as ...` and `✓ discord connected`
- Test both:
  - fresh `@Hermes` mention
  - plain text reply to an existing Hermes message

### Discord: tool_progress should be "off" for non-technical users
Set `tool_progress: 'off'` in the discord config section of config.yaml to hide tool progress messages (💻 terminal, 🔎 searching, etc.) from Discord users like Amanda. Without the config loader bug fix, this setting is silently ignored.

Also set the global display defaults to avoid confusing CLI/gateway mismatches:
```yaml
display:
  tool_progress: off
  background_process_notifications: off

discord:
  tool_progress: 'off'
  background_process_notifications: 'off'
```
This keeps Discord clean even if Amanda is sensitive to internal tool chatter.

Important nuance: gateway runtime tool progress and background watcher notifications are primarily controlled by the global `display` section in `~/.hermes/config.yaml`, not just `discord.*` keys. For a truly quiet Discord experience, also set:
- `display.tool_progress: off`
- `display.background_process_notifications: off`

Then keep the Discord-specific keys off as well for consistency:
- `discord.tool_progress: 'off'`
- `discord.background_process_notifications: 'off'`

### Model/provider mismatch — every turn fails with `'NoneType' object is not iterable`
Symptom: every user message on Telegram/Discord replies with `⚠️ 'NoneType' object is not iterable`. `~/.hermes/logs/errors.log` shows repeated:
```
agent.conversation_loop: API call failed (attempt 1/3) error_type=TypeError ... provider=<X> base_url=<Y> model=<Z> summary='NoneType' object is not iterable
agent.conversation_loop: Non-retryable client error: 'NoneType' object is not iterable
```

Root cause pattern: `~/.hermes/config.yaml` `model.provider` / `model.default` / `model.base_url` point at a provider whose response adapter is failing (commonly an expired/broken `openai-codex` chatgpt-mode token, or a model id the provider no longer serves), while `~/.hermes/auth.json` `active_provider` may have already been rotated to a different provider (e.g. `nous`) — the two stores disagree and the agent loop ends up with a None response payload it then iterates.

Diagnosis:
1. `hermes config show | grep -A1 '^  Model:'` — note current provider/model/base_url
2. `hermes portal status` — note `Model: currently <X>` line; if it disagrees with config, the stores are out of sync
3. Inspect auth without leaking tokens:
   ```bash
   python -c "import json,pathlib; d=json.loads((pathlib.Path.home()/'.hermes'/'auth.json').read_text()); print('active_provider=', d.get('active_provider')); print('providers=', list(d.get('providers', {}).keys()))"
   ```
4. `tail -50 ~/.hermes/logs/errors.log | grep NoneType` confirms the provider/model in the failing call — that's the one to replace.

Fix (non-interactive, when Nous Portal is already authed):
```bash
hermes config set model.provider nous
hermes config set model.default anthropic/claude-opus-4.7   # or whatever id you confirmed below
hermes config set model.base_url https://inference-api.nousresearch.com/v1
hermes gateway restart   # REQUIRES USER APPROVAL — drops the bot for ~3s while you're texting through it
```

For interactive selection, `hermes model` is the supported path; non-interactive `config set` is the fallback when you're operating through the gateway and can't run a TUI picker.

See `references/nous-portal-model-discovery.md` for the technique that lists available Nous models from a script (uses the cached `agent_key` in `auth.json` — works without `hermes model`'s interactive picker).

Important: **never restart the gateway without explicit user approval** when the user is messaging *through* that gateway. The restart will momentarily kill the conversation channel. State the diagnosis and the exact `gateway restart` command and wait for go-ahead.

### tirith security checker crash
If `tirith_enabled: true` but the tirith binary isn't installed, `check_command_security()` can crash with `TypeError: expected str, bytes or os.PathLike object, not NoneType`. This blocks terminal command approval/disapproval flows. Fix: either install tirith or set `tirith_enabled: false` in config.yaml security section. There's also a code bug at `tools/tirith_security.py` line ~620 where a None guard is missing.

### Desktop app: approval prompts not visible, tasks time out
When a user reports Hermes Desktop tasks timing out because approval prompts never appear, verify the approval event path before assuming config is disabled:

1. Check config still requires approval:
   ```bash
   hermes config path
   grep -A8 '^approvals:' ~/.hermes/config.yaml
   ```
   Expected manual gate: `approvals.mode: manual`. The short CLI timeout is `approvals.timeout`; gateway/TUI wait uses `approvals.gateway_timeout` if set, otherwise the backend default.
2. Inspect the backend approval flow:
   - `tools/approval.py` emits/block-waits through `register_gateway_notify()` and `approval.request`.
   - `tui_gateway/server.py` registers `lambda data: _emit("approval.request", sid, data)` for desktop/TUI sessions.
   - The TUI handles `approval.request` by rendering an approval overlay and responding with `approval.respond`.
3. Inspect the desktop renderer event handler, especially `apps/desktop/src/app/session/hooks/use-message-stream.ts`. If it handles `clarify.request` but not `approval.request`, the backend is waiting correctly but the UI never surfaces the prompt.
4. Also check `apps/desktop/src/lib/desktop-slash-commands.ts`: if `/approve` and `/deny` are classified as messaging-only blocked commands, the user cannot work around the missing desktop overlay from the desktop composer.

Safe temporary workarounds:
- Use `hermes --tui`, CLI, Telegram, or Discord for terminal/file-heavy work that may require approval.
- Use session-scoped `/yolo` only for trusted dev tasks where bypassing dangerous-command prompts is acceptable.
- Prefer `hermes config set approvals.mode smart` over global `off` when the issue is false-positive approvals; it auto-approves low-risk commands and escalates uncertain ones.

Durable fix pattern: add desktop handling for `approval.request`, render the same choices as the TUI (`once`, `session`, `always`, `deny`), and send `approval.respond` with the active `session_id`. Treat silence/timeouts as denial; never auto-consent because the UI missed the event.

## Quick One-Liner Diagnosis
```bash
echo "=== State ===" && cat ~/.hermes/gateway_state.json && echo -e "\n=== Process ===" && ps aux | grep -i "[h]ermes-gateway" && echo -e "\n=== Last Log ===" && tail -5 ~/.hermes/logs/gateway.log
```
