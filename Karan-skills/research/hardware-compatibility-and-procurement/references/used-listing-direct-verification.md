# Used-listing direct verification

Use this after discovery and before presenting any exact purchase URL.

## Minimum evidence record

For every candidate, retain:

```json
{
  "item_id": "provider item identifier",
  "url": "canonical exact listing URL",
  "title": "live page title",
  "active_purchase": true,
  "quantity_or_stock": "visible state or null",
  "price": "item price and currency",
  "shipping": "amount/method",
  "import_fees": "known, none, or unknown",
  "condition": "live listing condition",
  "returns": "window and who pays",
  "warranty": "provider and term or none",
  "cpu": "exact processor",
  "memory_layout": "slots/type; authoritative source",
  "storage": "capacity, interface, and physical length",
  "display": "resolution, brightness, gamut, touch; exactness level",
  "seller_notes": "defects and omissions",
  "compatibility_status": "confirmed, conditional, or reject",
  "rejection_reason": null
}
```

## Evidence precedence

1. Manufacturer PSREF/service manual/QuickSpecs for platform compatibility.
2. Exact machine type or SKU for factory configuration.
3. Live listing item specifics and seller description for the unit being sold.
4. Listing title.
5. Search result, shopping snippet, or related-item card only for discovery.

A lower-precedence source cannot silently override a contradiction above it. Resolve the conflict or reject the listing.

## Sparse shared links and Marketplace listings

A short share URL or public preview may reveal only a title, seller description, canonical item ID, and one image. Use that to identify a **lead**, not to certify the machine.

1. Resolve the share URL to the canonical listing/item ID and preserve it verbatim.
2. Treat public Open Graph title, description, and image metadata as discovery evidence only. Vague claims such as “brand new,” “RTX 4050,” “16 GB,” and “500 GB” do not establish CPU, machine type, panel, memory layout, warranty, or active status.
3. Use photos to narrow the model family, but require the exact bottom-label machine type/MTM or serial before applying manufacturer RAM, storage, display, chassis, or weight specifications. Family resemblance is not configuration proof.
4. Re-run every original whole-system gate. A gaming laptop with two SO-DIMM slots can still be an immediate reject for a light, metal, quiet, or battery-focused request.
5. For a local/no-return purchase, compare against current retailer and refurbished pricing. The seller must provide enough discount to compensate for missing return protection; a merely fair retail-equivalent price is not a buy-now recommendation.
6. Request a clear bottom-label photo, Task Manager/System Information CPU-Memory-GPU screenshots, manufacturer warranty status, battery cycle/health evidence, original charger confirmation, and BIOS/management-lock disclosure.
7. When those fields remain unresolved, give a conditional price ceiling by configuration and ask for the missing evidence. Do not invent the most favorable CPU or SKU from the chassis photo.

## Mandatory rejection rules

Reject from the recommended set when:

- The exact URL resolves to a different product or recycled item ID.
- No live purchase control or explicit in-stock state is visible.
- Title and item specifics disagree on CPU, storage, model, or display.
- Seller notes disclose screen tint, dead pixels, missing battery, remote management, or another defect not acceptable to the user.
- Required RAM compatibility depends on unresolved ECC/non-ECC behavior.
- The SSD slot’s physical length is incompatible with the reusable drive.
- Price/location/active state is hidden behind a marketplace login and cannot be verified.
- Return or lock risk exceeds the user’s stated tolerance.

Do not convert a rejected listing into a recommendation with a footnote. Replace it.

## Display verification labels

- **Exact:** machine type/SKU or seller specifics prove resolution, brightness, and gamut.
- **Partial:** exact resolution/touch is known, but brightness or gamut is not.
- **Family maximum only:** manufacturer says “up to”; this is not evidence for the listed unit.

State the label honestly. “FHD IPS” is not equivalent to a good panel.

## Final aggregation

Before answering a request for N options:

- Dedupe by canonical URL/item ID.
- Verify the collected count equals N programmatically.
- Require every final row to pass exact-URL and active-purchase checks.
- Rank on whole-system fit, not CPU alone: screen, weight, returns, battery, charger, locks, storage, and price all matter.
