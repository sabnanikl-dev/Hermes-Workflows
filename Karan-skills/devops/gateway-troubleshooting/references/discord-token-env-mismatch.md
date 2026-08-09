# Discord token env mismatch reference

## Symptom
- `hermes gateway status` shows service loaded/running.
- `~/.hermes/gateway_state.json` may contain stale Discord `connected` from an older run, but recent logs show only Telegram starting.
- Recent `~/.hermes/logs/gateway.log` shows `Gateway running with 1 platform(s)` after startup.
- `hermes status` shows `Discord ✗ not configured` even though `discord.token` exists in `~/.hermes/config.yaml`.

## Root cause
Hermes Discord platform detection expects `DISCORD_BOT_TOKEN`. A local `.env` may contain only `DISCORD_TOKEN`, or a valid token may exist only at `discord.token` in config YAML. If the config loader does not bridge `discord.token` to `DISCORD_BOT_TOKEN`, Discord is silently skipped.

## Durable fix pattern
1. Do not print the token. Copy the existing `discord.token` from config to `.env` as `DISCORD_BOT_TOKEN` using a script.
2. Patch `gateway/config.py` in the Discord config block:

```python
discord_cfg = yaml_cfg.get("discord", {})
if isinstance(discord_cfg, dict):
    if "token" in discord_cfg and not os.getenv("DISCORD_BOT_TOKEN"):
        os.environ["DISCORD_BOT_TOKEN"] = str(discord_cfg["token"]).strip()
```

3. Add regression coverage in `tests/gateway/test_config.py`:
- `discord.token` bridges to `DISCORD_BOT_TOKEN`
- `DISCORD_BOT_TOKEN` env var takes precedence over config YAML

4. Run:
```bash
python -m pytest tests/gateway/test_config.py -q -o 'addopts='
hermes status | sed -n '/Messaging Platforms/,+20p'
python -m json.tool ~/.hermes/gateway_state.json
```

## Verification lines
Expected after gateway restart:
```text
✓ telegram connected
✓ discord connected
Gateway running with 2 platform(s)
```

## Pitfall
`hermes gateway restart` from inside a gateway-handled conversation can enter `draining` until the current turn finishes. Re-check after the response completes instead of assuming the restart failed.