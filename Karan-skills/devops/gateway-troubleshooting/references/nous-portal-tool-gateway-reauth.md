# Nous Portal Tool Gateway reauth pattern

Use when web/search/browser/image/TTS tools are configured for `use_gateway: true` but Hermes reports Nous Portal is not logged in, or web tools fail with a message like “Log in to Nous Portal to use managed Firecrawl web tools.”

## Durable diagnosis

1. Confirm routing config without printing secrets:
   ```bash
   hermes portal status
   hermes portal info
   python3 - <<'PY'
   from pathlib import Path
   import yaml, json
   cfg = yaml.safe_load((Path.home()/'.hermes'/'config.yaml').read_text()) or {}
   for section in ['web','browser','image_gen','tts']:
       val = cfg.get(section, {})
       if isinstance(val, dict):
           safe = {k:v for k,v in val.items() if not any(s in k.lower() for s in ['key','token','secret','password'])}
           print(section, json.dumps(safe, sort_keys=True))
   PY
   ```
2. Good gateway routing for managed Firecrawl usually has:
   ```yaml
   web:
     backend: firecrawl
     use_gateway: true
   browser:
     cloud_provider: browser-use
     use_gateway: true
   ```
3. If `hermes portal status` says `Auth: not logged in`, do not add a direct Firecrawl key unless the user explicitly wants direct vendor billing. Reauth Nous Portal first.

## Reauth flow from a gateway/chat session

Use a PTY/background process so the OAuth/device flow can keep polling while you relay the link to the user:

```bash
hermes auth add nous --type oauth
```

In an agent tool call, prefer background + PTY and then poll output. The process prints a Portal URL and a `user_code`.

Tell the user:
- open the exact Portal URL from the process output;
- enter the shown code if prompted;
- reply when approved.

Do not store the code as durable memory. It is short-lived session data.

## Remote desktop/computer-use handoff

If Karan is away from the Mac and asks you to open/click the Portal link for him, first separate **opening the link** from **approving the auth**:

1. Opening the URL is safe and can be done with:
   ```bash
   open 'https://portal.nousresearch.com/manage-subscription?user_code=XXXX-XXXX'
   ```
2. Before using desktop automation to inspect/click the page, verify computer-use readiness:
   ```bash
   hermes computer-use status
   cua-driver permissions status
   ```
3. If CuaDriver is missing, the setup fix is:
   ```bash
   hermes computer-use install
   ```
4. If macOS reports Accessibility or Screen Recording is not granted for CuaDriver, stop and ask Karan to grant those permissions. Do not claim remote GUI control is available until both are granted.
5. Do not enter passwords, 2FA codes, payment details, or change subscription tiers. If the Portal shows a password, 2FA, payment, plan purchase, or subscription-change step, stop and report `BLOCKED`.

Device codes expire quickly. If the first flow times out, kill/let it exit, start a fresh `hermes auth add nous --type oauth`, and use the newly printed URL/code.

## Browser automation caveat

If you try to complete the Portal login with browser automation, Google/OAuth may show “Something went wrong” or require the user’s real browser/session. Treat that as a human-auth handoff, not a Hermes/browser failure.

## Verification after user approves

After the polling process exits, verify:

```bash
hermes portal status
hermes portal tools
hermes status | sed -n '/Nous Tool Gateway/,+12p'
```

Then run a tiny live tool smoke test from the active agent if available, e.g. a one-result `web_search` for a harmless query. Success proves Firecrawl is routed through the Nous Tool Gateway.

## Gateway restart note

Config changes may require a fresh session or gateway restart, but do not restart a live Telegram/Discord gateway conversation without explicit approval. For pure reauth, a restart is often unnecessary; verify first.
