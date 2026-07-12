# Boutique / Lifestyle Hotel Shortlist Reports

Use this reference when a lodging request is not just “find hotels under budget,” but asks for a specific **vibe** or inspiration property: bungalow-style, Alaya Tulum-like, old-Tulum, boutique, glamping, palapa, design hotel, romantic, beachfront, etc.

## Trigger

- User asks for a hotel shortlist plus polished report.
- User names an inspiration property or aesthetic style.
- User cares about photos, amenities, breakfast, pool, location, and price details.
- User may steer mid-turn with a vibe correction like “look for bungalow style hotels like Alaya Tulum.” Treat that as a first-class requirement and revise the shortlist/report accordingly.

## Workflow

1. **Lock assumptions up front inside the report**
   - Dates, location/neighborhood, occupancy, currency, and whether the budget is base nightly or all-in.
   - If occupancy is omitted, use a reasonable default such as 2 adults / 1 room and state it.

2. **Search the exact neighborhood first**
   - Use hotel search pages with date, occupancy, currency, and neighborhood filters.
   - For Tulum-style requests, filter for `Zona Hotelera` / Hotel Zone, then scan both hotel and bungalow/glamping/cabana-style listings.

3. **Check the inspiration property directly**
   - Search the named property for the requested dates.
   - Record whether it is available and whether it fits the budget.
   - If unavailable or over budget, include a brief “reality check” explaining that the shortlist optimizes for the same feel instead.

4. **Turn the vibe into explicit selection criteria**
   - Example Alaya/Tulum criteria: beachfront or private beach, thatched roofs, cabanas/bungalows, boutique scale, natural materials, jungle/palapa visuals, yoga/spa/glamping energy, Hotel Zone location.
   - Prefer a smaller, better-fit shortlist over a generic cheapest-results dump.

5. **Capture structured fields for each property**
   - Name and booking/official links.
   - Neighborhood/address and map link.
   - Displayed total and nightly calculation.
   - Whether breakfast is included, paid, or unclear.
   - Whether pool access exists; distinguish shared pool, private/plunge-pool imagery, or “no pool listed.”
   - Review score and review count where available.
   - Why it matches the vibe and any caveat.
   - At least one high-quality image URL, ideally from a property/gallery page rather than a tiny search thumbnail.

6. **Verify prices with arithmetic, not mental math**
   - Use terminal/Python for nightly totals and keep base-rate vs excluded taxes clear.
   - Common caveat: Booking.com often excludes VAT, city tax, environmental fees, and service charges from displayed prices.

7. **Build the HTML report as a real artifact**
   - Include hero, quick verdict, inspiration-property reality check, hotel cards with images, comparison table, booking order, and sources/caveats.
   - For user-friendly travel reports, prioritize visual scanning over long prose: cards, badges, tables, and concise caveats.

8. **Preview and verify**
   - Serve with a local HTTP server, not `file://`.
   - Confirm HTTP 200, file size, expected card/image counts, and no console errors.
   - Visually inspect at least the top/card layout. If an image looks wrong or low-quality, replace it with a better gallery image and re-verify.
   - Stop the preview server before final handoff unless the user asked for a live localhost link.

## Output shape

Recommended sections:

- Hero: destination + date/budget/occupancy chips.
- Quick verdict: top 3 picks by use case.
- Inspiration property reality check: available? over budget? why alternatives were chosen.
- Shortlist cards: photo, score, price, breakfast, pool, location, caveat, links.
- Comparison table: hotel / fit / base price / breakfast / pool / risk.
- Booking order: practical ranking.
- Sources & caveats: rate source, tax caveats, photo sources, “no booking made.”

## Pitfalls

- Do not treat “under $250/night” as all-in unless the user says so. Label it as base nightly when taxes/fees are excluded.
- Do not keep the first generic hotel shortlist if the user clarifies an aesthetic mid-turn; update the search and report to match the vibe.
- Do not rely only on search thumbnails for a polished report; open property pages for better gallery images.
- Avoid overclaiming pool/breakfast: use `included`, `available/paid`, `not shown included`, `no pool listed`, or `confirm access` when the source is ambiguous.
- Do not make bookings or external reservations without explicit approval.