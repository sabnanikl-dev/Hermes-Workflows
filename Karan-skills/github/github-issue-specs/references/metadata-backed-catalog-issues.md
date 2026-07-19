# Metadata-backed catalog issue specs

Use this reference when a user wants to turn a large metadata source into a browseable catalog, carousel/gallery, or product-detail modal/drawer.

## 1. Recover the real product intent

Do not assume an initial curated subset is the full desired catalog. Reconstruct the distinction between:

- the currently shipped sample/featured set;
- the complete source dataset;
- the deterministic launch subset;
- future individual routes versus one category page with client-side detail views.

Search existing issues and prior decisions for intentionally deferred catalog work. If no tracker item exists, say that the future lane is missing rather than silently treating the sample count as final.

## 2. Quantify candidate membership before specifying scope

Run deterministic source analysis and report:

- total records;
- counts under each plausible filter;
- exact taxonomy-field counts versus loose “term appears anywhere” counts;
- unique IDs and missing IDs;
- distinct titles and duplicate-title pressure;
- required-field completeness;
- image counts per record and total image references;
- exact image/link domains;
- sanitized payload size;
- forbidden fields that must be removed from the public projection.

Prefer an explicit taxonomy-field rule such as `subtitle contains X` over a loose any-field match. Use stable IDs—not titles—as identity when titles repeat.

## 3. Adapt inspiration patterns, not implementation stacks

Inspect both the inspiration and the target repo. Separate:

- **Pattern to adapt:** image hierarchy, thumbnail navigation, information grouping, dialog/drawer behavior, action hierarchy.
- **Pattern to omit:** marketplace-only pricing, seller profiles, ratings, favorite/share controls, shipping, recommendations, cart/checkout signals.
- **Implementation constraint:** if the target is static HTML/CSS/vanilla JS, do not copy React/Tailwind/Framer code. Reimplement the interaction using the target repo’s primitives and design tokens.

## 4. Prevent large-gallery performance traps

Do not specify “put every image in one carousel” literally when the source has hundreds of records or thousands of images.

A strong catalog contract usually requires:

- one primary thumbnail per browse card;
- a bounded initial batch or windowed/paginated rendering;
- no autoplay for a large product set;
- alternate images added/requested only when that record’s detail view opens;
- search/filter/result counts for reachability;
- card-level broken-image degradation;
- a useful no-JavaScript or data-failure fallback;
- network/DOM acceptance criteria proving the initial page does not request the entire image corpus.

## 5. Specify accessible detail state

For a modal/drawer detail experience, require observable behavior for:

- pointer and Enter/Space activation;
- accessible dialog naming;
- focus entry, focus trap, Escape/backdrop/close-button dismissal, and exact focus return;
- background scroll lock and cleanup;
- desktop two-column and mobile nearly full-screen layouts;
- thumbnail/previous-next/swipe/keyboard image synchronization;
- reduced-motion behavior;
- repeated open/close cycles without duplicate listeners or history entries;
- optional shareable query state, Back/Forward behavior, invalid-ID handling, stable canonical, and no sitemap pollution.

## 6. Keep catalog UI separate from commerce handoff authority

Metadata containing an order/customize URL does not automatically authorize rendering it.

For commerce-adjacent external destinations:

- preserve candidate URLs in a source/provenance contract;
- expose actionable links only after exact allowlist and browser-QA gates pass;
- omit buttons for missing, stale, failed, future-dated, or mismatched rows;
- keep the descriptive catalog usable when actions are disabled;
- never fall back to an unlisted generic URL;
- use exact approved labels, HTTPS, `target="_blank"`, and `rel="noopener"`;
- retain a clear external-payment/delivery disclosure;
- prohibit order submission, payment, customer data, or account mutation during QA.

If destination verification is a separate risk surface, keep it in an adjacent issue rather than weakening the gate inside the catalog UI issue.

## 7. Recommended issue split

A reviewable split is often:

1. **Catalog projection + browse/detail UI:** deterministic sanitized data, bounded loading, filters/search, accessible detail dialog, conditional action seam.
2. **External destination QA + enablement:** browser-verifies candidate destinations and enables only passing rows.
3. **Legacy redirects:** remains separate from destination-page UX and external configurator handoffs.

The UI issue may include enabled/disabled fixtures so reviewers can verify both states without authorizing live links.

## 8. Acceptance-criteria checklist

Include pass/fail criteria for:

- exact filter membership and count;
- unique stable identity;
- forbidden-field stripping and safe text rendering;
- deterministic generation/check mode;
- initial card/image-request bound;
- filter/search/empty/reset behavior;
- broken-image isolation;
- full detail-dialog accessibility lifecycle;
- deep-link and browser-history behavior;
- enabled versus disabled external actions;
- no price/inventory/cart/checkout/schema leakage;
- no-JavaScript/data-failure fallback;
- responsive widths and longest/shortest image-set fixtures;
- project tests plus a manual network/browser smoke.
