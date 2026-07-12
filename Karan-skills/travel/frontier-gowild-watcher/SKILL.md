---
name: frontier-gowild-watcher
description: Use when checking Frontier GoWild public booking-data availability for explicit routes/dates, especially before creating cron alerts with price, nonstop, or max-stop filters.
version: 1.0.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [travel, frontier, gowild, flights, cron, alerts]
    related_skills: [research-workflow]
---

# Frontier GoWild Watcher

## Overview

This skill provides a conservative local watcher for Frontier GoWild availability using Frontier's public booking-page data for explicit routes and dates. It is intended for personal route/date checks and future cron alerts, not mass scraping or automated booking.

The bundled script renders a human Markdown summary and includes safety limits so automated jobs do not fan out across Frontier's network by accident.

**Important:** Results are public booking-data indicators only. Always manually verify while logged into the passholder's Frontier/GoWild account before booking. The script does not log in, book flights, or automate checkout.

## When to Use

Use this skill when Karan asks to:

- Check GoWild availability for specific Frontier routes/dates.
- Create or test a cron job that watches requested destinations and dates.
- Filter GoWild results by displayed price, nonstop-only, or maximum stops.
- Generate a quick Markdown digest suitable for Telegram/Discord delivery.

Do **not** use this for:

- Broad network scans.
- Automated booking or checkout.
- Credential-heavy workflows without explicit approval.
- Commercial/public scraping services.

## Safety Defaults

The script enforces:

- Max **10 destinations** per run.
- Max **7 dates** per run.
- Required explicit destinations and dates.
- Random delay between route/date checks; default **2–5 seconds**.
- Browser cookies are **off by default**.

Browser-cookie mode exists as an optional flag for later experimentation, but do not use it unless Karan explicitly approves. If used, it reads local Chrome cookies via `browsercookie` and sends them only to Frontier requests.

## Script Location

```bash
~/.hermes/skills/travel/frontier-gowild-watcher/scripts/gowild_watch.py
```

## Setup

Create/use a venv before running manually:

```bash
cd ~/.hermes/skills/travel/frontier-gowild-watcher
python3 -m venv .venv
source .venv/bin/activate
pip install requests beautifulsoup4 browsercookie pytest
```

## Basic Usage

### Check explicit routes for tomorrow

```bash
python scripts/gowild_watch.py \
  --origin ATL \
  --destinations DEN,MCO,LAS \
  --dates +1
```

### Check specific calendar dates

```bash
python scripts/gowild_watch.py \
  --origin ATL \
  --destinations DEN,LAS \
  --dates 2026-05-21,2026-05-23
```

### Nonstop-only under a displayed price

```bash
python scripts/gowild_watch.py \
  --origin ATL \
  --destinations DEN,MCO,LAS \
  --dates +1 \
  --nonstop-only \
  --max-price 100
```

### Max one stop

```bash
python scripts/gowild_watch.py \
  --origin ATL \
  --destinations DEN,MCO,LAS \
  --dates +1,+2,+3 \
  --max-stops 1
```

## CLI Options

- `--origin ATL` — required origin IATA code.
- `--destinations DEN,MCO,LAS` — required comma-separated destination IATA codes; max 10.
- `--dates 2026-05-21,+1,+3` — required dates as `YYYY-MM-DD` or day offsets; max 7.
- `--max-price 100` — only show GoWild fares at or below the displayed price.
- `--nonstop-only` — only show nonstop flights.
- `--max-stops 1` — only show flights with N stops or fewer.
- `--min-delay 2 --max-delay 5` — throttle between route/date checks.
- `--use-browser-cookies` — optional Chrome-cookie mode; default off and approval-required.
- `--hide-warnings` — suppress warning lines for clean Discord cron output.

## Cron / Alert Pattern

For recurring GoWild alerts, prefer a **script-only cron** (`no_agent=true`) because the watcher already prints human Markdown and does not need LLM reasoning. For Discord alerts, Karan prefers clean, actionable messages: suppress repeated caveat/warning lines with `--hide-warnings`, include booking links, and use a change-only wrapper so unchanged searches produce empty stdout and do not post again.

See `references/cron-watch-pattern.md` for the wrapper-script pattern, bounded repeat-count calculation, Discord delivery example, warning suppression, and SHA256 state-file change detection.

See `references/http-503-retry-and-urgent-return.md` for the 503 retry/backoff pattern and the fallback workflow when GoWild is no longer enough because the user has a firm arrival deadline.

When creating an LLM-driven cron job instead, use a prompt like:

```text
Run the Frontier GoWild watcher skill for explicit routes only.
Use script: ~/.hermes/skills/travel/frontier-gowild-watcher/scripts/gowild_watch.py
Command:
python scripts/gowild_watch.py --origin ATL --destinations DEN,LAS --dates +1 --nonstop-only --max-price 100
Return the Markdown output exactly, plus a one-sentence reminder to verify manually on Frontier before booking.
Do not use browser cookies. Do not book anything.
```

For script-only cron jobs, put the wrapper under `~/.hermes/scripts/`, run it once manually, then create the cron with `script=<wrapper filename>` and `no_agent=true`. If Karan asks for alerts rather than every-run digests, make the wrapper change-only: hash the watcher body, compare it to a state file under `~/.hermes/state/gowild-watcher/`, and print nothing on unchanged results. In `no_agent=true` cron jobs, empty stdout is the intended silence mechanism.

## User-Facing Output Preferences

- For Discord cron alerts, avoid repeating generic caveats/warnings in every message; use `--hide-warnings` and keep the output focused on changed availability and booking links.
- Use change-only delivery for twice-daily or more frequent watches. Seed the baseline locally, then post only when the route/date result body changes.
- Keep safety limits and manual-verification assumptions enforced internally even when warning text is hidden from user-facing output.

## Verification Checklist

Before trusting a route watcher:

- [ ] Run unit tests from the skill venv: `source .venv/bin/activate && pytest -q` from the skill directory. If `.venv` is missing, run `scripts/run_watch.sh --help` once or follow Setup first so dependencies like `beautifulsoup4` are installed.
- [ ] Run one small live smoke test with 1–3 destinations.
- [ ] Confirm no `403`, `406`, or parse errors.
- [ ] Manually verify at least one positive result while logged into Frontier.
- [ ] Confirm filters work: `--nonstop-only`, `--max-price`, and/or `--max-stops`.
- [ ] Keep route/date counts within safety limits.

## Known Limitations

1. **Public data only:** `isGoWildFareEnabled` and displayed `goWildFare` are read from Frontier's public booking response. They may not equal final passholder checkout eligibility.
2. **Frontier can change page shape:** If `FlightData` disappears or changes, parsing may break.
3. **Blackout/early-booking nuance:** Public data may show GoWild-adjacent or early-booking fares even on dates that require logged-in verification.
4. **No booking automation:** This is intentional. Booking and payment remain manual.
5. **No broad exploration:** The script requires explicit destinations; use third-party tools like WildFares/1491 for broad exploration.

## Common Pitfalls

- Running too many routes/dates at once. The script blocks above 10 destinations × 7 dates.
- Treating displayed GoWild public data as final booking truth. Always verify manually.
- Enabling browser cookies casually. Keep default off unless explicitly approved.
- Forgetting that date offsets use the machine's current local date.
- When the user gives both a weekday and a calendar date, verify the date/weekday pair before scheduling. If they conflict and one is clearly emphasized (e.g. “Thursday June 5th” when June 5 is Friday), prefer the emphasized weekday only if you explicitly state the assumption in the final report; otherwise ask before scheduling long-running alerts.
- For one-date hourly watches, bound the cron repeat count through the end of the watched date instead of running forever, and state the computed repeat count/next run after listing the cron.
- When modifying an existing GoWild cron, update both layers: the wrapper script arguments/output labels/state-file key **and** the cron metadata (`name`/`prompt`/script reference if needed). Then re-list the cron job to verify the scheduler reflects the new target dates/filters.
- To verify a modified change-only wrapper without accidentally seeding/suppressing the next alert, run `bash -n` on the wrapper and smoke-test the underlying watcher command directly. Only run the wrapper itself when intentionally seeding or posting a baseline.
- When expanding a watch from one date to multiple dates, use a fresh state-file key (for example `2026-06-03_04`) so old single-date hashes do not suppress multi-date changes.
- When changing an existing rolling-window cron (for example next-2-days → next-4-days), copy the wrapper to a new descriptive script name first, patch the new copy, then update the cron `script`, `name`, and prompt to match. Avoid leaving the scheduler pointed at a stale `next2` script or accidentally converting the old wrapper in place unless the old behavior is intentionally retired.
- Verify rolling-window edits without seeding/suppressing alerts: run `bash -n` on both the new wrapper and any old wrapper you touched, compute/check the generated date list separately if needed, then `cronjob(action='list')` to confirm the scheduler points at the intended script/name/window.
- For script-only alert crons, decide explicitly whether the job should post every changed result body or only when matching flights/errors exist. If Karan asks for a flight alert, prefer silence on zero matches and hash/deliver only positive matches or serious watcher errors; see `references/cron-watch-pattern.md`.
- If Frontier returns `HTTP 503`, treat it as indeterminate/transient site or CDN failure, not as a no-flight result. Add retry/backoff before alerting and only surface the error after repeated failures; see `references/http-503-retry-and-urgent-return.md`.
- When the user has a firm travel deadline (“need to get back home by Friday afternoon”), immediately broaden from GoWild-only checking to cash fare search across practical airports. Rank by arrival deadline and reliability first, then price; GoWild becomes a bonus/backup path.
- For rolling weekday watches like “current week Thursday/Friday,” compute explicit dates inside the wrapper and use those dates in the state-file key so the watch rolls forward cleanly each week.
- Using `--nonstop-only` and thinking no results means no GoWild at all; it may only mean no nonstop matches.
