# NotebookLM MCP/CLI selection notes

Use when Karan wants Hermes to use Google NotebookLM as a research workspace or "research brain."

## Current package distinction

Two active unofficial projects can look interchangeable but differ in shape:

- `teng-lin/notebooklm-py`: broader automation substrate — Python API, CLI, notes, sources, artifacts, profiles, and documented research-brain patterns. Prefer this when Hermes should orchestrate NotebookLM as a durable research workspace.
- `jacob-bd/notebooklm-mcp-cli`: strong immediate CLI + MCP bridge. Prefer this when the main need is a ready MCP server now.

Both use undocumented/internal Google NotebookLM APIs and browser/session-cookie auth, so treat them as local trusted tooling, not a public service.

## Verification before MCP wiring

Do not assume README/docs on `main` match the latest PyPI release. Verify the installed package exposes the MCP extra and entrypoint before adding Hermes MCP config:

```bash
uv tool install "notebooklm-py[browser,mcp]"
uv tool list | grep -i notebooklm
command -v notebooklm
command -v notebooklm-mcp || true
notebooklm --version
python3 - <<'PY'
import json, urllib.request
with urllib.request.urlopen('https://pypi.org/pypi/notebooklm-py/json') as r:
    info=json.load(r)['info']
print(info['version'])
print(info.get('provides_extra'))
PY
```

If PyPI lacks the `mcp` extra / `notebooklm-mcp` entrypoint, use the CLI first and wait for a stable release rather than installing from `main` unless the user explicitly accepts instability.

## Auth workflow

`notebooklm-py` auth does not produce a portable phone/device-code link. It opens a local browser and saves Google session cookies to the Mac profile, so the user must complete login on the machine or via remote desktop.

```bash
/Users/creator/.local/bin/notebooklm login
/Users/creator/.local/bin/notebooklm auth check --test --json
```

Require `"status": "ok"` and `"checks.token_fetch": true`; a local cookie parse alone is not enough.

If switching accounts, use a fresh login or targeted browser-cookie import:

```bash
/Users/creator/.local/bin/notebooklm login --fresh
/Users/creator/.local/bin/notebooklm login --browser-cookies chrome --account <email>
```

## Research-brain architecture

NotebookLM should be the grounded reading/research workspace, not the only durable memory layer. Promote final decisions, stable summaries, and reusable procedures into Hermes Brain / Obsidian, Hindsight, memory, or skills as appropriate.