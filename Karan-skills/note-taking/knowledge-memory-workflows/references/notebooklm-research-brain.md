# NotebookLM as a Research Brain for Hermes

Use when the user wants Hermes to read/write Google NotebookLM as a grounded research workspace.

## Recommended mental model

- **NotebookLM** = grounded research workspace: sources, citations, long-document reading, notes, generated artifacts, research runs.
- **Hermes Brain / Obsidian** = durable structured knowledge and project memory.
- **Standard memory / Hindsight** = compact cross-session recall and user/environment preferences.

Do **not** make NotebookLM the only system of record for Hermes memory. Let NotebookLM do heavy source-grounded reading, then promote stable conclusions, decisions, and reusable procedures into the existing Hermes memory layers.

## Tool selection note from June 2026 evaluation

Two active unofficial NotebookLM projects were compared:

- `teng-lin/notebooklm-py`: stronger fit for “research brain” automation because it provides a Python API, CLI, note/source/artifact workflows, profiles, auth refresh, and explicit patterns like Master Brain notebooks and `ask --save-as-note`.
- `jacob-bd/notebooklm-mcp-cli`: good MCP/CLI bridge, stronger if immediate MCP integration is the primary goal.

Preferred starting point for Karan’s goal: install `notebooklm-py` CLI first, authenticate, use Hermes terminal workflows, and only wire MCP after the stable PyPI release actually exposes the MCP extra/entrypoint.

## Stable-install verification pattern

Before configuring Hermes MCP for a rapidly moving NotebookLM package:

1. Install from PyPI or a specific tagged release, not GitHub `main`, unless the user explicitly wants unreleased behavior.
2. Verify package metadata for extras and scripts rather than trusting README text from `main`:
   - PyPI `provides_extra`
   - installed executables under the uv tool env
   - `command -v notebooklm` / `command -v notebooklm-mcp`
3. Verify CLI first:
   - `notebooklm --version`
   - `notebooklm doctor`
   - `notebooklm auth check --test --json`
4. Only add a Hermes `mcp_servers` block after the MCP executable is actually installed and callable.

## Example CLI-first workflow

```bash
uv tool install "notebooklm-py[browser]"
notebooklm login
notebooklm auth check --test --json
notebooklm create "Research Brain"
notebooklm source add "https://example.com/source"
notebooklm ask "What are the key claims and citations?" --json
notebooklm ask "Summarize durable decisions for Hermes Brain" --save-as-note
```

Then have Hermes copy/promote the final durable summary into Obsidian/Hindsight/skills as appropriate.