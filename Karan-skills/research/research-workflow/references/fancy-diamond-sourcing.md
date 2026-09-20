# Fancy-shape lab diamond sourcing

Use for user-constrained oval/moval or other fancy-shape searches. Read-only public research is not approval for seller outreach, reservations or purchases.

## Evidence hierarchy
- Separate fixed constraints (shape, length/width ratio, origin) from preferred carat and flexible setting details. Treat total ring budget as distinct from stone budget; reserve setting/tax without inventing a local tax rate.
- Search actual inventory, not only generic configurable product pages or indexed snippets. Preserve stock number, vendor-specific listing URL, lab report number, price and retrieval date in a project-local evidence JSON; dedupe by report number.
- Verify primary IGI/GIA report and compute ratio from measurements with Decimal. Distinguish exact dimensions yielding 2.00 from values merely rounded to 2.00. Do not quietly broaden locked ratios. Near matches stay separate.
- Check shape AND cutting style. Moval brilliant, step-cut moval, old-mine style and pointed marquise are not interchangeable.
- A retailer's Ideal/Excellent cut label may not exist on the lab report. Excellent polish/symmetry, D color or VVS clarity do not establish high light return. Inspect what the actual report grades, not a generic claim about all fancy reports.
- Open actual stone rotating media and inspect multiple views. Describe sampled observations narrowly; oblique studio views do not establish face-up brilliance in normal lighting. No unearned best-brilliance rankings or guarantees. Useful next evidence: multi-light face-up rocking videos, ASET/Ideal-Scope, independent inspection within the return window. Some dynamic dark contrast is normal.
- Read the detailed loose-stone return policy, not generic ring banners. Check window start, previous-setting exclusions, once-per-customer returns, price-match/final-sale exclusions and custom-setting consequences before recommending an order.

## Dynamic storefront pitfalls
- Visible number-input changes may not update the actual app filter state. Read back active filter labels and actual result measurements; never assume the filter applied.
- Public page scripts/DOM can expose read-only filter functions and inventory objects. Use them to retrieve the same public inventory safely; do not invoke cart/product-creation functions or leak irrelevant supplier internals into reports.
- Clairamor (observed September 2026): DIAMOND_PLP_SETTING.config and callBeforeDiamond() drive public inventory filters; matching stone objects are rendered in textarea[id$=textarea]. Collect only relevant public stone fields. Direct product routes require stone-stock and vendorId, with stone_shape.
- Stienhardt (observed September 2026): public filters persist shape, caratMin/caratMax, lwMin/lwMax, priceMax in URL. Wait for actual results, not just the page shell. Extracted product pages can include unrelated default/template diamonds and hidden unavailable messages; use rendered state and matching report identity before asserting stock.
- Primary PDF extraction may work even when a direct binary HTTP download returns 403. Preserve verified report links/text and disclose if the binary was not archived; do not fabricate a saved PDF.

## Closeout
Return a short ranked-by-stated-basis shortlist, exact links/report IDs, price and budget limitations, optical evidence status and next verification gate. 'Spec-matching candidates found, brilliance not yet verified' is an honest bounded outcome. Keep transient prices in project research files rather than durable memory. Personal vault edits remain approval-gated; reusable method belongs here.
