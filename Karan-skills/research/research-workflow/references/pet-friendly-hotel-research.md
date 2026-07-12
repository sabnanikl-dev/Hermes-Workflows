# Pet-Friendly Hotel Research / HTML Reports

Use this reference when sourcing road-trip lodging with pet, bed, price, and route constraints.

## Pattern that worked

1. Verify dates first with a live date/tool when the user gives weekday + date.
2. Use Google Travel/Hotels through Playwright for current-ish hotel rate snippets:
   - Example URL pattern: `https://www.google.com/travel/search?q=<city>%20pet%20friendly%20hotels&checkin=YYYY-MM-DD&checkout=YYYY-MM-DD&adults=2&currency=USD`
   - Read `document.body.innerText` to extract hotel names, prices, ratings, amenities, and pet-friendly labels.
3. Use Serper for official/OTA/pet-policy confirmation snippets:
   - `site:brand.com <hotel> pet friendly two queen beds`
   - `<hotel> <date> rate 2 queen pet policy`
   - `<hotel> BringFido Expedia Hotels.com pet policy`
4. Use Google Places Details to verify address, phone, Google rating/review count, maps URL, and photos.
5. If making a portable HTML report, download Places photos and embed as `data:image/...;base64,...` so the report can be sent as a single file.
6. Verify the final HTML:
   - File exists and has nonzero size.
   - Expected number of hotel cards exists.
   - Expected number of embedded images exists.
   - Open via local HTTP server + Playwright if possible; ignore favicon-only 404s.

## Output conventions

- Include a clear caveat that base rates exclude taxes, parking, pet fees, and availability changes.
- Call out conflicting pet-fee snippets explicitly instead of pretending one number is authoritative.
- Prefer route-efficient neighborhoods for road trips (airport/I-40/I-70/east-side departures) over downtown glamour when the user asked for affordable route lodging.
- Give a small “best pick” section before the full hotel cards.
- Include official booking link, Google Maps link, address, phone when available, rating/review count, bed note, pet-policy note, price note, why it fits, and watch-outs.

## Common pitfalls

- Google Travel results are rendered and sparse in accessibility snapshots; `document.body.innerText` is often more useful than a shallow snapshot.
- Serper can return empty output for highly quoted queries; retry broader/unquoted queries.
- Google Places photo references are temporary; embed the downloaded image bytes if the report needs to survive after the session.
- Pet policies vary by exact property, not just brand. Confirm property-level rules whenever possible.
- “Under $200” should be framed as observed/advertised base rate, not guaranteed checkout total.
