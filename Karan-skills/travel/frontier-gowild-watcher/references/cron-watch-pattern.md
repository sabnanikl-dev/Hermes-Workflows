# Cron Watch Pattern for Frontier GoWild

Use this when Karan asks for recurring GoWild route/date checks delivered to Discord/Telegram.

## Pattern

Prefer **script-only cron** (`no_agent=true`) for deterministic watcher digests. The watcher already produces human Markdown and does not need LLM summarization.

1. Create a wrapper in `~/.hermes/scripts/` so the cron scheduler can run it directly.
2. The wrapper should:
   - `cd` into `~/.hermes/skills/travel/frontier-gowild-watcher`
   - activate/use the skill venv via `scripts/run_watch.sh`
   - pass explicit `--origin`, `--destinations`, `--dates`, and filters
   - use `--hide-warnings` for clean Discord output when Karan does not want caveats repeated
   - optionally hash the watcher body and print nothing when results are unchanged
   - set `PYTHONWARNINGS=ignore` to keep macOS urllib3/LibreSSL warnings out of user-facing digests
3. Create the cron with `no_agent=true`, `script=<wrapper filename>`, and explicit `deliver` target.
4. Verify by running the wrapper once before scheduling and then listing the cron job.

## Change-only wrapper example

For Discord channels, prefer this pattern so unchanged searches stay silent. In `no_agent=true` cron jobs, empty stdout means no message is delivered.

```bash
#!/usr/bin/env bash
set -euo pipefail
export PYTHONWARNINGS="ignore"
SKILL_DIR="$HOME/.hermes/skills/travel/frontier-gowild-watcher"
STATE_DIR="$HOME/.hermes/state/gowild-watcher"
STATE_FILE="$STATE_DIR/<watch-name>.sha256"
mkdir -p "$STATE_DIR"
cd "$SKILL_DIR"

body="$(scripts/run_watch.sh \
  --origin DEN \
  --destinations ATL \
  --dates 2026-06-01,2026-06-02,2026-06-03,2026-06-04 \
  --nonstop-only \
  --max-price 100 \
  --hide-warnings \
  --min-delay 2 \
  --max-delay 5)"

hash="$(printf '%s' "$body" | shasum -a 256 | awk '{print $1}')"
previous=""
[[ -f "$STATE_FILE" ]] && previous="$(cat "$STATE_FILE")"

if [[ "$hash" == "$previous" ]]; then
  exit 0  # silent: no Discord post for unchanged results
fi

printf '%s' "$hash" > "$STATE_FILE"
printf '## DEN → ATL GoWild Watch — changed results\n\n'
printf '%s\n' "$body"
printf '\nBooking links are included above. Verify manually in Frontier before booking.\n'
```

Seed the baseline by running the wrapper once locally without delivering to Discord. The next cron run will stay silent unless results change.

## Scheduling twice daily for a bounded window

For morning + evening checks, use cron syntax like:

```text
0 8,20 * * *
```

If the watch should end after a known date, calculate the finite repeat count rather than running forever. Example: if now is May 20 afternoon and the final desired run is June 4 at 8 PM ET, `0 8,20 * * *` has 31 future runs.

## No-match-silent alert wrappers

When Karan asks for an alert for matching flights (not a digest every run), make the wrapper silent when the watcher finds zero matches and no serious route errors. Do not hash and deliver a “no matches” baseline unless the user explicitly asks for baseline reports.

Useful pattern after `body=...`:

```bash
match_count="$(printf '%s\n' "$body" | /usr/bin/python3 -c 'import re,sys; m=re.search(r"Found \*\*(\d+)\*\*", sys.stdin.read()); print(m.group(1) if m else "0")')"
error_count="$(printf '%s\n' "$body" | grep -E '^Status: `(http-error|parse-error)`' -c || true)"
if [[ "$match_count" == "0" && "$error_count" == "0" ]]; then
  exit 0
fi
```

Treat `no-schedule` as informational for unsupported route/date pairs, not an alert-worthy error by default. Only `http-error` and `parse-error` should force non-empty output for operator attention.

## Rolling weekday date windows

For rolling “current week Thursday/Friday” alerts, compute explicit dates in the wrapper before calling the watcher. If today is Saturday/Sunday, roll to the following week so the alert always points forward:

```bash
DATES="$('/usr/bin/python3' - <<'PY'
import datetime as dt

today = dt.date.today()
week_start = today - dt.timedelta(days=today.weekday())
if today.weekday() >= 5:  # Sat/Sun -> next week
    week_start += dt.timedelta(days=7)
thu = week_start + dt.timedelta(days=3)
fri = week_start + dt.timedelta(days=4)
print(f"{thu.isoformat()},{fri.isoformat()}")
PY
)"
```

Use the computed dates in the state-file key (for example `${DATES//,/_}`) so each week has a fresh change-detection bucket.

## Notes

- `deliver` can target a Discord channel directly, e.g. `discord:<channel_id>`.
- Keep browser cookies off unless Karan explicitly approves.
- Keep the watcher within explicit routes/dates and the script safety limits.
- Include booking links by default; `gowild_watch.py` outputs a Frontier search link for each route/date.
