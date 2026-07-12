#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SKILL_DIR"
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -q requests beautifulsoup4 browsercookie
else
  . .venv/bin/activate
fi
python scripts/gowild_watch.py "$@"
