# Nous Portal: list available models non-interactively

`hermes model` is the supported way to pick a Nous Portal inference model, but it's an interactive TUI — unusable when you're operating through the gateway and need to fix a broken config from inside a chat session. This recipe lists available models programmatically using the cached agent key.

## Prerequisite

`~/.hermes/auth.json` must already contain a `nous` provider entry (the user must have logged in once via `hermes model` or `hermes login`). The session stores:
- `inference_base_url` — usually `https://inference-api.nousresearch.com/v1`
- `agent_key` — short-lived bearer token minted by the Portal (preferred)
- `access_token` — OAuth access token (fallback if `agent_key` absent/expired)

## List models

```python
import json, pathlib, urllib.request
auth = json.loads((pathlib.Path.home() / '.hermes' / 'auth.json').read_text())
n = auth['providers']['nous']
key = n.get('agent_key') or n.get('access_token')
url = n['inference_base_url'].rstrip('/') + '/models'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'})
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())
for m in data.get('data', []):
    print(m.get('id'))
```

The response is an OpenAI-shaped `{ "data": [ { "id": "...", ... }, ... ] }` listing — `id` is the value to put in `model.default`.

## Notes on model IDs

- Stable ids look like `anthropic/claude-opus-4.7`, `openai/gpt-5.5`, `google/gemini-3.1-flash-lite`.
- A leading `~` (e.g. `~anthropic/claude-opus-latest`) marks a rolling/alias model — fine for casual use, but pin to a versioned id (`anthropic/claude-opus-4.7`) for anything you want to be stable.
- Suffixes like `-fast` are provider-side speed variants of the same family.

## After picking a model

```bash
hermes config set model.provider nous
hermes config set model.default <id-from-listing-above>
hermes config set model.base_url https://inference-api.nousresearch.com/v1
hermes gateway restart   # ASK USER FIRST if you're messaging through the gateway
```

`hermes portal status` and `hermes config show | grep Model` should agree afterward. If `errors.log` still shows the old provider in `agent.conversation_loop` warnings, the gateway hasn't picked up the config change yet — the restart is what makes it take effect.

## Do NOT do

- Don't print the bearer key. Tokens in `auth.json` are short-lived but still credentials.
- Don't write the agent key into config.yaml or env files — it's auto-refreshed by `hermes auth` flows and pinning a stale value will break the next refresh.
- Don't restart the gateway as part of automated diagnosis when the user is on a messaging platform — surface the diagnosis and wait.
