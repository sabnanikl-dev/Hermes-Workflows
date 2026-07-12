<!-- Archived source skill consolidated into `memory-provider-setup` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: hindsight-memory-setup
category: mlops
description: Guide to setting up Hindsight as a memory provider for Hermes Agent (local mode). Created after discovering package naming confusion and the migration to native Hermes support.
---

## Background

Hindsight (by Vectorize) is a memory provider with:
- **Knowledge graph** with entity resolution and cross-memory synthesis
- **Multi-strategy retrieval**: semantic, keyword, entity-based, temporal
- **`hindsight_reflect`**: the only memory provider with cross-memory synthesis — asks "what patterns have emerged across all my vendor negotiations?" and gets synthesized answers
- **`hindsight_remember`**: store facts
- **`hindsight_forget`**: delete facts

Hermes Agent has **native Hindsight support** via NousResearch PR #5094 (added ~Apr 2026). The old `hindsight-hermes` pip package was dropped because the integration now lives in Hermes itself.

## Package Naming (Critical)

| Package | Purpose | Status |
|---------|---------|--------|
| `hindsight` | **BROKEN** — old package, use_2to3 error with modern setuptools | Dead |
| `hindsight-all` | Local mode with embedded PostgreSQL + API server | Current |
| `hindsight-client` | Cloud-only client (needs running server) | Works alone |

**You need `hindsight-all`** for local mode.

## Setup Steps

### 1. Install the package in a dedicated Hindsight venv
Do **not** install `hindsight-all` into `~/.hermes/hermes-agent/venv` unless you are deliberately upgrading Hermes' own dependency set. Hindsight API packages can pull newer dependencies (for example `cryptography>=48`) that conflict with Hermes' pinned runtime deps. Keep the API server isolated and leave the Hermes venv with only the lightweight client/plugin dependencies.

Also clear Hermes' `PYTHONPATH` when creating/installing the venv; Hermes sessions often export `PYTHONPATH=~/.hermes/hermes-agent:~/.hermes/hermes-agent/venv/...`, which can accidentally pollute a new venv and make pip think packages are installed in the Hermes venv.

```bash
env -u PYTHONPATH -u PYTHONHOME ~/.hermes/hermes-agent/venv/bin/python -m venv ~/.hindsight/venv311
env -u PYTHONPATH -u PYTHONHOME ~/.hindsight/venv311/bin/python -m pip install --upgrade pip
env -u PYTHONPATH -u PYTHONHOME ~/.hindsight/venv311/bin/python -m pip install hindsight-all
```

If `hindsight-all` was accidentally installed into the Hermes venv, clean up the top-level API packages and restore Hermes' pinned dependency before continuing:
```bash
~/.hermes/hermes-agent/venv/bin/python -m pip uninstall -y hindsight-all hindsight-api-slim hindsight-embed
~/.hermes/hermes-agent/venv/bin/python -m pip install 'cryptography==46.0.7'
~/.hermes/hermes-agent/venv/bin/python -m pip check
```

### 2. Start the local server (embedded mode)
Current `hindsight-all` releases include embedded PostgreSQL via `pg0-embedded`; no Docker or separate `pg0` install should be needed when the dedicated venv is used. If older logs say `pg0 binary not found`, first upgrade/install `hindsight-all` in the dedicated venv before using the external `curl | bash` pg0 installer.

```bash
# IMPORTANT: OpenRouter API keys fail LLM verification in the OpenAI SDK
# (curl works but Python SDK gets 401). Skip verification to proceed.
export HINDSIGHT_API_SKIP_LLM_VERIFICATION=true

# Known-good production path for this deployment: GPT-4o Mini through the
# OpenAI-compatible OpenRouter endpoint, using the dedicated Hindsight key.
export HINDSIGHT_API_LLM_PROVIDER=openai
export HINDSIGHT_API_LLM_MODEL=openai/gpt-4o-mini
export HINDSIGHT_API_LLM_BASE_URL=https://openrouter.ai/api/v1
export HINDSIGHT_API_LLM_API_KEY="sk-or-v1-your-key"

# Qwen 3.5 9B is Hindsight's documented OpenRouter default and is cheaper, but
# DO NOT switch this deployment without a full retain -> recall -> reflect canary.
# On Hindsight v0.8.4 in 2026-07, native provider=openrouter was required for
# correct structured retention; even then qwen/qwen3.5-9b and :nitro showed
# highly variable tiny-retain latency (~3 seconds to 7-8 minutes), while reflect
# reached ~121 seconds and exceeded the Hermes wrapper timeout. Plain health and
# a single successful reflect are insufficient verification.
# If testing a model with <=32K output, cap retain above the 3K chunk size:
# export HINDSIGHT_API_RETAIN_MAX_COMPLETION_TOKENS=16000

~/.hindsight/venv311/bin/hindsight-api --host 127.0.0.1 --port 9100 &
```

The API server runs on `http://localhost:9100`. Startup can take 30-60 seconds while local embeddings/reranker and pg0 initialize. Verify:
```bash
curl -s http://localhost:9100/health
# Expected: {"status":"healthy","database":"connected"}
```

### 3. Configure Hermes (config.yaml)
Add or update the `memory` section in `~/.hermes/config.yaml`:
```yaml
memory:
  provider: hindsight
  mode: hybrid  # auto-inject + explicit tools
  bank_id: hermes
```

### 4. Add env vars to `~/.hermes/.env`
```
HINDSIGHT_API_URL=http://localhost:9100
HINDSIGHT_API_API_KEY=local
HINDSIGHT_CONNECTION_MODE=local
```

### 5. Verify
```bash
hermes memory status  # should show hindsight as active
```

## Local Mode Requirements

- **Python**: 3.11+
- **LLM API key**: Required for extraction/synthesis (already have via OpenRouter)
- **Embedded PostgreSQL**: Included in `hindsight-all`, no separate install needed
- **Disk**: Heavier than SQLite — PostgreSQL + indexes consume more space
- **Memory**: PostgreSQL process running in background

## Migration from Holographic

```bash
hermes memory setup  # select "hindsight"
```

Your built-in memory mirrors to providers, so no data loss. Both can coexist during transition.

## macOS Launch Agent (Persistence)

Hindsight API should run as a background service via a macOS launch agent, not cron. The plist is at `~/Library/LaunchAgents/io.vectorize.hindsight.api.plist` with:
- `ProgramArguments` pointing to the dedicated venv binary: `~/.hindsight/venv311/bin/hindsight-api --host 127.0.0.1 --port 9100`
- `KeepAlive: true` — auto-restarts on crash
- `RunAtLoad: true` — starts on login
- `ThrottleInterval: 10` — prevents crash-loop spam
- `EnvironmentVariables` — all required env vars (including `HINDSIGHT_API_SKIP_LLM_VERIFICATION=true`), plus a `PATH` that starts with `/Users/creator/.hindsight/venv311/bin`
- Logs: `~/.hindsight/logs/launchd-out.log` and `launchd-err.log`

**Useful commands:**
```bash
PLIST=~/Library/LaunchAgents/io.vectorize.hindsight.api.plist
plutil -replace ProgramArguments -json '["/Users/creator/.hindsight/venv311/bin/hindsight-api","--host","127.0.0.1","--port","9100"]' "$PLIST"
plutil -replace EnvironmentVariables.PATH -string "/Users/creator/.hindsight/venv311/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" "$PLIST"
plutil -lint "$PLIST"
launchctl bootout gui/$(id -u) "$PLIST" 2>/dev/null || launchctl unload "$PLIST" 2>/dev/null || true
launchctl bootstrap gui/$(id -u) "$PLIST"
launchctl kickstart -k gui/$(id -u)/io.vectorize.hindsight.api
sleep 30
curl -sS http://localhost:9100/health
```

## Known Pitfalls

1. **`pip install hindsight` will fail** — use `hindsight-all`
2. **The server must be running** for Hermes to connect — start `hindsight serve` before using the agent
3. **LLM calls for synthesis** — `hindsight_reflect` adds latency and uses API tokens. Not an issue for recall, but for synthesis it costs tokens.
4. **Profile isolation** — Hindsight respects `HERMES_HOME` profiles, so data is isolated per profile.
5. **Launchd override problem (macOS):** If Hindsight runs as a launch agent (`io.vectorize.hindsight.api`), changes to `~/.hermes/.env` **do NOT take effect** because the launchd plist (`~/Library/LaunchAgents/io.vectorize.hindsight.api.plist`) has hardcoded `EnvironmentVariables` that override env files. To change model, API key, or any env var:
   ```bash
   # Update the plist values
   plutil -replace EnvironmentVariables.HINDSIGHT_API_LLM_MODEL -string "openai/gpt-4o-mini" ~/Library/LaunchAgents/io.vectorize.hindsight.api.plist
   plutil -replace EnvironmentVariables.HINDSIGHT_API_LLM_API_KEY -string "sk-or-v1-your-key" ~/Library/LaunchAgents/io.vectorize.hindsight.api.plist
   
   # Verify
   plutil -extract EnvironmentVariables xml1 -o - ~/Library/LaunchAgents/io.vectorize.hindsight.api.plist
   
   # Reload
   launchctl unload ~/Library/LaunchAgents/io.vectorize.hindsight.api.plist
   launchctl load ~/Library/LaunchAgents/io.vectorize.hindsight.api.plist
   ```
6. **Separate API key recommended:** Use a dedicated OpenRouter key for Hindsight (via `HINDSIGHT_API_LLM_API_KEY`) separate from your main agent key. This provides rate limit isolation and cost tracking. Hindsight makes background LLM calls on every turn (reranking, entity extraction) which can compete with your main agent calls.
