# Observed WTP Evidence Sprints

Use this note when a product/revenue validation run needs public willingness-to-pay proof before more copy/artifact polish.

## Durable pattern

1. **Start with the product's gate script or proof contract.** Run the existing governor/checker before research so the baseline is explicit.
2. **Collect candidates before promoting proof.** Keep a small machine-readable candidate table with columns like `url`, `source_title`, `buyer_class`, `paid_signal`, `artifact_mapping`, `caveat`, `pass_fail`.
3. **Search exact buyer first, comparable buyer second.** For digital products, exact-buyer marketplace pages with visible price + review/rating/sale signals are strongest; comparable solo-service/freelancer assets can pass only when the buyer class, paid signal, artifact/job mapping, and caveat are explicit.
4. **Reject aggressively.** Do not promote category pages, vendor price suggestions, free-template libraries, seller pages with no purchase/review/sales evidence, inaccessible/unavailable listings, or broad hype bundles with weak artifact mapping.
5. **Use marketplace extraction plus local text search.** Extract pages, then search cached extracts for `Price`, `stars`, `reviews`, `sales`, `buyer`, `verified buyers`, and artifact terms. This often surfaces evidence hidden below the truncated extract window.
6. **Promote only clean markers.** If a repo has a machine-readable marker shape, match it exactly and include: URL, buyer class, observed paid/purchase/review/sales signal, artifact/job mapping, and caveat/source-bias note.
7. **Re-run the governor in both report and require-pass modes.** A passing evidence governor does not approve public action; preserve external approval gates.
8. **If the baseline already passes, treat the sprint as a source-integrity recheck, not permission to polish.** Re-verify accessibility, inspect additional candidates, promote only genuinely stronger markers, and keep the decision centered on WTP/source quality rather than launch/readiness copy.
9. **Log one experiment row.** Record baseline count, final count, decision, and the fact that listing/checkout/waitlist/outreach/posting/payment/claim actions remain approval-required.
10. **Validate and commit only if the artifact actually changed.** For scheduled direct-to-main runs, follow repo validation and remote-SHA verification before reporting success. If unrelated untracked files appear, leave them untouched and commit only the intended WTP evidence files.

## Common rejected-source categories

- Marketplace search/category pages: useful for discovery, too broad for proof.
- Gumroad/Etsy pages with price but no visible review/rating/sale/purchase signal.
- Unavailable or blocked listings, even if search snippets look strong.
- Broad AI-money prompt/course bundles that are paid and reviewed but do not map to the target artifact/job.
- Implementation-template bundles when the product is a discovery/proposal/audit/sales-proof asset, unless the mapping is explicitly defensible.
- Exact-category marketplace products with visible sales/reviews but the wrong artifact job. Example: an AI-automation agency website template may prove people buy agency sales assets, but it is not a clean discovery-call/proposal/audit/calculator proof source unless the product itself maps to that job.
- Strong shop-level reputation without item-level signal. Etsy shop sales, Star Seller, or rave-review badges can support candidate notes, but do not promote them as WTP markers when the item itself has no reviews/sales/purchase evidence.
- End-buyer/operator templates when the current product buyer is a freelancer/agency. A construction-company AI proposal template may be relevant to the domain, but it fails the buyer-class requirement if the WTP contract asks for automation sellers or comparable solo service sellers.

## Source-integrity recheck pattern

When the governor already passes at baseline, do not treat the sprint as permission to polish launch assets. Run a source-integrity/candidate sweep instead:

1. Re-run the governor and capture the baseline count.
2. Re-extract or search-check existing accepted sources if cheap.
3. Inspect 10+ new candidates from exact-buyer and comparable-buyer searches.
4. Add rejected-but-informative candidates to the candidate TSV with a precise fail reason.
5. Promote no new markers unless the candidate has all required fields and improves source quality.
6. Log one ledger row with baseline count, final count, number of candidates inspected, and the preserved public-action approval gates.

## Reporting shape

Report baseline governor count, final governor count, accepted sources, rejected categories, files changed, validations, commit/remote verification, and remaining approval gates.