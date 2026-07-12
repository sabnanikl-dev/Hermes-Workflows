# Frontier GoWild Availability Research Notes

Use when researching or prototyping personal Frontier Airlines GoWild Pass availability checks.

## Official API reality

- Frontier has an official NDC developer portal at `developer.flyfrontier.com`.
- It is partner/enterprise-style access, not a simple consumer API:
  - IATA NDC 21.3 schema.
  - Flows include AirShopping, OfferPrice, SeatAvailability, OrderCreate/Retrieve/Reshop, Schedule.
  - Auth requires IP whitelisting, API key, token generation, and certification/go-live approval.
- Do not assume NDC exposes a personal GoWild passholder's consumer inventory or logged-in eligibility.

## Consumer/public options found

- WildFares: GoWild-focused search, cached/live modes, route builder, day trips, alerts/limits.
- The 1491 Club: forward/inbound search, calendar, blackout/window awareness, paid availability/pricing tier.
- GoWilder: outbound/inbound search, login-gated search UX.
- SearchGWP: app/site; reviews and privacy disclosures looked weaker than WildFares/1491.

Prefer testing existing tools against the user's logged-in Frontier account before building a custom watcher.

## Legal/account-risk framing

Frontier Terms of Use explicitly prohibit website/data/screen scraping. Treat automation as risk-tiered:

- Low risk: manually using Frontier app/site; existing tools as discovery aids; verify/book on Frontier manually.
- Medium risk: low-frequency personal browser-assisted checks, no credential storage, no checkout automation.
- High risk: anti-bot bypass, mobile API reverse engineering, mass route/date scanning, commercial/public service, storing Frontier credentials.

Do not automate booking/payment. Ask before running any live Frontier endpoint probes.

## GWsearch repo test findings

Repo: `fly-metothemoon/GWsearch`.

Core behavior:

- Calls Frontier web booking endpoints, not NDC and not signed mobile API:
  - `https://booking.flyfrontier.com/Flight/RetrieveSchedule?...`
  - `https://booking.flyfrontier.com/Flight/InternalSelect?o1=ATL&d1=DEN&dd1=May%2021,%202026&ADT=1&mon=true&promo=`
- Parses embedded page data and looks for fields such as:
  - `isGoWildFareEnabled`
  - `goWildFare`
  - `goWildFareSeatsRemaining`
  - `journeys[0].flights`

Controlled test shape that worked:

- Clone to temp directory.
- Create venv and install `requests beautifulsoup4 browsercookie`.
- Do not use `-c` / browser cookies initially.
- Temporarily restrict `all_destinations` to a tiny test set (e.g. `ATL`, `DEN`, `MCO`, `LAS`) to avoid broad scraping.
- Run small probes only, e.g. `python gowild_scraper.py -o ATL -d 1`.

Repo issues discovered:

1. Parser stale: current Frontier response includes many unrelated scripts before the flight data. The original `soup.find("script", type="text/javascript")` can parse the wrong script and fail with `JSONDecodeError`.
2. Current flight data was embedded in a script assignment like `FlightData = '{&quot;calendarLink&quot;: ... &quot;journeys&quot;: ... }';`. A temporary fix is to scan all scripts for both `FlightData` and `journeys`, HTML-unescape, then parse the JSON object between the first `{` and last `}`.
3. Roundtrip bug: `if(roundtrip == 1 & orgin_success):` has Python operator-precedence problems. Use `if (roundtrip == 1 and orgin_success):`.
4. Hardcoded destination list is stale and causes issues when the origin is not present during roundtrip lookup. For tiny tests, include the origin in `all_destinations`; for a real tool, derive/maintain routes separately.
5. Output is human text only; a production personal watcher should emit JSON/CSV/Markdown and include filters/warnings.

Important interpretation:

- A positive result means Frontier's public booking response has `isGoWildFareEnabled: true`; it does not prove the user's logged-in pass can select/book it.
- Manual logged-in Frontier verification is required for any positive result.

## Recommended personal watcher design

If building from the idea, rebuild a guarded local tool rather than running the community script raw:

- Inputs: explicit `--origin`, `--dest DEN,MCO,LAS`, and absolute `--date YYYY-MM-DD` instead of date-offset only.
- Filters: max stops, nonstop-only, max duration, avoid overnight layovers, seat-count display.
- Safety: fixed low rate limit, tiny configured route list, no cookies by default, no credential storage.
- Policy: no checkout/payment automation.
- Output: JSON plus concise Telegram/Markdown digest with direct Frontier search links.
- Warnings: GoWild booking windows, blackout dates, and "manual verification required" on positives.
