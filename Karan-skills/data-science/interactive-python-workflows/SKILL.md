---
name: interactive-python-workflows
description: Stateful Python, Jupyter, notebook, and REPL workflows for iterative data exploration, API probing, DataFrame inspection, and clean notebook verification.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [python, jupyter, notebook, repl, data-science, exploration, iterative, hamelnb]
---

# Interactive Python Workflows

Use this skill when the user needs iterative Python work rather than a single stateless script: exploratory data analysis, live API probing, DataFrame inspection, long-lived variables, notebook editing, or clean notebook verification.

## Tool choice

| Path | Use when |
| --- | --- |
| `execute_code` | One-shot Python that benefits from Hermes tool imports, with no persistent state. |
| `terminal` | Shell commands, installs, git, builds, process management, or scripts outside notebooks. |
| Live Jupyter kernel | You want notebook-style state across executions, variables to persist, or incremental exploration. |

Rule of thumb: if a human would open a notebook or REPL, use the live-kernel workflow.

## Live Jupyter kernel via hamelnb

### Prerequisites

1. `uv` is installed (`which uv`).
2. JupyterLab is installed (`uv tool install jupyterlab` if missing).
3. The hamelnb helper exists at:

```bash
SCRIPT="$HOME/.agent-skills/hamelnb/skills/jupyter-live-kernel/scripts/jupyter_live_kernel.py"
```

If the helper is missing:

```bash
git clone https://github.com/hamelsmu/hamelnb.git ~/.agent-skills/hamelnb
```

### Start or discover the server

```bash
uv run "$SCRIPT" servers --compact
```

If no server is running:

```bash
mkdir -p ~/notebooks
jupyter-lab --no-browser --port=8888 --notebook-dir=$HOME/notebooks \
  --IdentityProvider.token='' --ServerApp.password='' > /tmp/jupyter.log 2>&1 &
sleep 3
uv run "$SCRIPT" servers --compact
```

The tokenless server is for local agent access only.

### Create a scratch notebook/session

```bash
mkdir -p ~/notebooks
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / 'notebooks' / 'scratch.ipynb'
if not p.exists():
    p.write_text(json.dumps({
        'cells': [{'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [], 'source': []}],
        'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python'}},
        'nbformat': 4,
        'nbformat_minor': 5,
    }))
PY
curl -s -X POST http://127.0.0.1:8888/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"path":"scratch.ipynb","type":"notebook","name":"scratch.ipynb","kernel":{"name":"python3"}}'
```

### Execute iteratively

Always use `--compact`.

```bash
uv run "$SCRIPT" execute --path scratch.ipynb --code $'import pandas as pd\nprint(pd.__version__)' --compact
uv run "$SCRIPT" execute --path scratch.ipynb --code $'df.head()' --compact
```

State persists across execute calls.

### Inspect variables

```bash
uv run "$SCRIPT" variables --path scratch.ipynb list --compact
uv run "$SCRIPT" variables --path scratch.ipynb preview --name df --compact
```

Subcommand flags go before the sub-subcommand: `variables --path nb.ipynb list`, not `variables list --path nb.ipynb`.

### Edit and verify notebooks

```bash
uv run "$SCRIPT" contents --path scratch.ipynb --compact
uv run "$SCRIPT" edit --path scratch.ipynb insert --at-index 1 --cell-type code --source 'print("hello")' --compact
uv run "$SCRIPT" restart-run-all --path scratch.ipynb --save-outputs --compact
```

Use restart-and-run-all only when the user asks for clean verification or when final deliverables must run top-to-bottom.

## Pitfalls

- First execution after server start or kernel restart may timeout. Retry once before escalating.
- The kernel Python is JupyterLab's Python. Install packages into that environment, not necessarily the active Hermes shell.
- JSON output can be large without `--compact`.
- If no live session exists, start one via the Jupyter REST API before executing.
- For long-running cells, pass a larger timeout such as `--timeout 120`.
