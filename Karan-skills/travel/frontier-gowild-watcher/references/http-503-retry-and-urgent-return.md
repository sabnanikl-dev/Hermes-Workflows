# Frontier HTTP 503 + urgent-return fallback

## Durable lesson

Frontier's public booking endpoints can return transient `HTTP 503` for route/date checks. Treat 503 as an indeterminate watcher failure, not as evidence of no GoWild availability and not as a flight-market result.

## Recommended watcher behavior

- Retry `HTTP 503` with short exponential backoff/jitter before surfacing an alert.
- Alert only after repeated failures, and label the state as indeterminate.
- Do not let one transient 503 overwrite or suppress a prior valid positive result without making the failure explicit.
- For script-only cron alerts, prefer posting serious watcher errors only after retry exhaustion so users are not spammed by CDN hiccups.

## Urgent travel fallback pattern

When the user says they need to be home by a deadline, stop treating GoWild as the only path:

1. Keep checking GoWild if useful, but frame it as a discount/backup path.
2. Immediately search regular cash fares across NYC-area airports when relevant (`LGA`, `JFK`, `EWR`) and destination (`ATL`).
3. Sort by the actual constraint: arrival deadline first, nonstop/reliability second, price third.
4. Separate "cheapest" from "safest/recommended" options.
5. Prefer booking direct with the airline when prices are close, especially under deadline pressure.

## Example user-facing framing

- "503 means Frontier's site/CDN failed the public request; it is not a no-flights signal."
- "Because you need to be home by Friday afternoon, I’m treating GoWild as a bonus and checking cash fares now."
- "My recommendation is the earlier mainline nonstop with arrival cushion; the cheaper late Frontier option is riskier if delays matter."
