#!/usr/bin/env bash
# Run the Google Workspace CLI (gws) using Hermes' existing Google OAuth token.
# This avoids a second OAuth setup for read/write operations covered by the
# token's authorized scopes. The token itself is never printed.
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
# Default to the skill directory this wrapper lives in. Older installs used
# ~/.hermes/skills/productivity/google-workspace, but this skill may be re-homed
# under umbrella/absorbed paths; a hardcoded default breaks in that layout.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="${GOOGLE_WORKSPACE_SKILL_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
SETUP_SCRIPT="$SKILL_DIR/scripts/setup.py"
TOKEN_PATH="$HERMES_HOME/google_token.json"

choose_python() {
  if [[ -n "${GOOGLE_WORKSPACE_PYTHON:-}" ]]; then
    printf '%s\n' "$GOOGLE_WORKSPACE_PYTHON"
  elif [[ -x "$HERMES_HOME/venvs/google-workspace/bin/python" ]]; then
    printf '%s\n' "$HERMES_HOME/venvs/google-workspace/bin/python"
  elif command -v python3.11 >/dev/null 2>&1; then
    command -v python3.11
  elif command -v python3 >/dev/null 2>&1; then
    command -v python3
  else
    echo "ERROR: no Python found for Google Workspace token refresh" >&2
    exit 1
  fi
}

PYTHON_BIN="$(choose_python)"
GWS_BIN="${GWS_BIN:-}"
if [[ -z "$GWS_BIN" ]]; then
  if command -v gws >/dev/null 2>&1; then
    GWS_BIN="$(command -v gws)"
  elif [[ -x "$HOME/.local/bin/gws" ]]; then
    GWS_BIN="$HOME/.local/bin/gws"
  else
    echo "ERROR: gws not found. Install from https://github.com/googleworkspace/cli/releases or run:" >&2
    echo "  npm install -g @googleworkspace/cli" >&2
    exit 1
  fi
fi

if [[ ! -f "$SETUP_SCRIPT" ]]; then
  echo "ERROR: setup.py not found at $SETUP_SCRIPT" >&2
  exit 1
fi

# Refresh token if needed. Suppress output to avoid noisy wrapper behavior.
"$PYTHON_BIN" "$SETUP_SCRIPT" --check >/dev/null

if [[ ! -f "$TOKEN_PATH" ]]; then
  echo "ERROR: no Google token at $TOKEN_PATH" >&2
  exit 1
fi

ACCESS_TOKEN="$($PYTHON_BIN - "$TOKEN_PATH" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
data = json.loads(path.read_text())
token = data.get("token") or ""
if not token:
    raise SystemExit("missing access token")
print(token)
PY
)"

export GOOGLE_WORKSPACE_CLI_TOKEN="$ACCESS_TOKEN"
exec "$GWS_BIN" "$@"
