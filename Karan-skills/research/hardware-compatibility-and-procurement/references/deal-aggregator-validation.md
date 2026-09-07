# Deal-Aggregator and Affiliate-Roundup Validation

Use this reference when a laptop, desktop, component, or other hardware search begins from a deal index, affiliate roundup, shopping feed, or dynamic “all configurations” catalog.

## Role of the aggregator

Treat the aggregator as a **candidate-discovery and price-history source**, not as the compatibility authority or the final purchase surface. Its editorial testing can be useful, but its product taxonomy, filters, prices, configuration records, and affiliate redirects may update independently.

A strong outcome is not “the site lists many products.” It is a small set of candidates that survives exact-SKU verification.

## Catalog-to-shortlist workflow

1. Recover the user’s current hard gates before browsing. Examples: replaceable RAM, two physical slots, existing-memory reuse, delivered budget, weight, chassis, exact display quality, Linux support, CUDA, ports, warranty, or immediate availability.
2. Inspect the complete catalog or relevant category pages rather than only featured/top-pick cards. Count and deduplicate records programmatically when extracting many configurations.
3. Apply coarse numeric filters only for discovery. Reject obvious sentinel or placeholder prices such as `$0`, `$1`, impossible discounts, missing currency, or prices far below every other offer.
4. Separate candidates into bounded lanes such as best complete value, portable performance, business/Linux/upgradeable, and specialized GPU value.
5. Fetch the candidate’s product-detail record and exact retailer destination. Do not stop at the catalog card.
6. Reconcile aggregator, retailer, and manufacturer/service-document data. The exact retailer SKU and manufacturer documentation govern compatibility; the live retailer page governs price, stock, returns, and warranty.
7. Re-read the candidate set after verification and remove failed hard-gate items before ranking.

## Do not trust filter labels blindly

A checked “Upgradeable RAM,” “Linux ready,” “metal,” “bright display,” or similar filter is a hypothesis, not proof. Deal sites may:

- Store the tag at a product-family level while the selected configuration differs
- Map a UI filter to the wrong field
- Retain a stale tag after a model refresh
- Treat upgradeable storage as upgradeable memory
- Return unfiltered results because the UI state is not included in the server request

For RAM, independently confirm memory type, soldered versus socketed status, physical slot count, maximum capacity, and whether the user’s existing modules match. A single SO-DIMM, soldered-plus-slot layout, and two replaceable SO-DIMMs are materially different.

## Price and inventory integrity

Record both the aggregator price and the direct retailer price with a check time. If they disagree, use the later verified direct retailer price and label the aggregator record stale or unresolved. Price-history badges such as “best ever” do not prove the current checkout price.

Before calling an offer live:

- Resolve the affiliate redirect to the intended retailer item or use a canonical direct retailer URL
- Confirm the item title/SKU matches the candidate
- Confirm a live purchase control or explicit in-stock state
- Check shipping, taxes/import exposure, seller identity, returns, and warranty
- Detect regional variants and third-party marketplace sellers

If the retailer cannot be read directly, present the item as a lead or watch item—not a verified buy-now link.

## Configuration-conflict gate

Reject or preserve as unresolved any case where the aggregator and retailer disagree on CPU, GPU, RAM, storage, display, model year, or SKU. Do not silently choose the more favorable value.

Common warning patterns:

- Catalog says 1 TB while the retailer title says 512 GB
- Product family is tagged as upgradeable while the detailed configuration says soldered memory
- Model year and exact CPU generation do not plausibly align
- “Aluminum design” resolves to an aluminum lid with a plastic deck/base
- A price changes while the research is in progress

## Recommendation format

For each surviving candidate report:

- Exact model/SKU and direct purchase link
- Aggregator price versus verified retailer price
- CPU/GPU lane
- Installed memory and exact replaceability/slot layout
- Storage and expansion
- Display resolution, brightness, gamut, refresh, and finish
- Weight and verified chassis materials
- Ports, charging, Linux support, battery expectations
- Returns/warranty
- Decisive fit and disqualifying caveat

End with one primary recommendation, one budget alternative, and one specialized option only if justified. Explicitly identify tempting products rejected by a hard gate when that helps explain why the shortlist is small.

## Sanity checks for extracted catalogs

When programmatically processing a large feed:

- Verify collected count against the feed’s declared total
- Deduplicate by stable configuration ID and canonical URL
- Flag nonpositive or implausibly low prices
- Compare record price with the selected affiliate offer price
- Preserve exact product slugs, configuration IDs, and retailer SKUs
- Re-query shortlisted records immediately before finalizing because dynamic catalogs can change during research

Do not preserve private action tokens, transient internal endpoint identifiers, or brittle implementation details in durable notes. Preserve the validation pattern, not a single site’s temporary internals.
