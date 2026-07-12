#!/usr/bin/env bash
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
GENERATOR="$HERMES_HOME/scripts/closeout_dream_report.py"
APPROVED_DIR="$HERMES_HOME/cache/documents/closeout-dream-report-daily"
APPROVED_ZIP="$HERMES_HOME/cache/documents/closeout-dream-report-daily.zip"
LOG_DIR="$HERMES_HOME/reports/closeout-dream"
mkdir -p "$APPROVED_DIR" "$LOG_DIR"

if [[ ! -x "$GENERATOR" ]]; then
  chmod +x "$GENERATOR"
fi

RUN_JSON="$($GENERATOR --since 7d --dry-run --update-history)"

HTML_PATH="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["html"])' <<<"$RUN_JSON")"
JSON_PATH="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["json"])' <<<"$RUN_JSON")"
SUMMARY="$(python3 -c 'import json,sys; d=json.load(sys.stdin)["summary"]; print("{sessions_seen} sessions · {github_seen} PRs · {linear_seen} Linear items · {candidate_count} candidates · {promote_count} ready · {stage_count} staged · {ignore_count} ignored".format(**{k:d.get(k,0) for k in ["sessions_seen","github_seen","linear_seen","candidate_count","promote_count","stage_count","ignore_count"]}))' <<<"$RUN_JSON")"
STAMP="$(date +%Y%m%d-%H%M%S)"
SAFE_HTML="$APPROVED_DIR/Hermes Closeout Dream Report $STAMP.html"
SAFE_JSON="$APPROVED_DIR/closeout-dream-report-$STAMP.raw.json"

cp "$HTML_PATH" "$SAFE_HTML"
cp "$JSON_PATH" "$SAFE_JSON"
rm -f "$APPROVED_ZIP"
(
  cd "$HERMES_HOME/cache/documents"
  zip -q -r "$APPROVED_ZIP" "closeout-dream-report-daily"
)

# Verify nonzero artifacts before emitting MEDIA lines.
python3 - <<PY
from pathlib import Path
for p in [Path('$SAFE_HTML'), Path('$SAFE_JSON'), Path('$APPROVED_ZIP')]:
    if not p.exists() or p.stat().st_size <= 0:
        raise SystemExit(f'Missing or empty artifact: {p}')
PY

cat <<EOF
Daily Closeout Dream Report prototype complete.

$SUMMARY

No durable memory/Hindsight/Obsidian/skill writes were performed. One-off observations remain staged low; recommendations mature only after repeated dream patterns.

MEDIA:$SAFE_HTML

MEDIA:$APPROVED_ZIP
EOF
