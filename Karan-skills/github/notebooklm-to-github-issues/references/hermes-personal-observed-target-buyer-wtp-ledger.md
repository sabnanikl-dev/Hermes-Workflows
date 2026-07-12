# Hermes Personal Observed Target-Buyer WTP Ledger Pattern

Use this reference for Product 001 / passive-revenue scout runs when the product has clear private artifacts but the public-launch blocker is exact willingness-to-pay from the selected buyer class.

## When to use

Trigger this pattern when:

- the experiment governor or adversarial reviewer says proxy-polish must stop;
- `scripts/wtp_governor.py` reports `0/3` or fewer than 3 verified observed-WTP markers;
- prior evidence includes seller-authored pages, listed prices, marketplace categories, or adjacent reviews, but not clean exact target-buyer purchase/review/would-pay proof;
- NotebookLM product/strategy grounding recommends evidence fidelity, adversarial market validation, or transaction-proxy proof.

## Single-move shape

Choose exactly one surface: `evidence / WTP gate`.

Create or update a strict internal evidence artifact such as:

```text
products/local-service-missed-call-recovery-pack/observed-target-buyer-wtp-ledger.md
```

Also create one experiment file under:

```text
products/local-service-missed-call-recovery-pack/experiments/<date>-observed-target-buyer-wtp-ledger.md
```

Append exactly one row to `experiment-ledger.tsv` with:

- primary metric: `observed-WTP verified source count`;
- decision: usually `hold` unless 3 verified markers truly pass;
- notes preserving no-public-live boundary.

## Evidence classification

Separate evidence into these buckets instead of flattening them:

1. **Exact target-buyer priced source** — AI automation freelancer/tiny agency/automation seller source with visible price but no buyer review/purchase proof. Useful, but not a verified marker by itself.
2. **Exact target-buyer purchase/review source** — exact buyer class with review/rating/sale/purchase/would-pay signal and artifact mapping. Candidate for `WTP-VERIFIED:` if caveats are present.
3. **Comparable service-seller reviewed source** — adjacent freelancer/agency/service-seller category with stronger review/rating evidence. Good transaction-proxy support, but not exact demand.
4. **Seller-authored / claim-heavy page** — useful for offer-shape clues only; never copy revenue/client/ROI claims.
5. **Search-result or blocked/404 lead** — log as discarded/lead only; do not count as proof.

## WTP-VERIFIED discipline

Do **not** add `WTP-VERIFIED:` markers unless all five components are present:

1. verifiable URL;
2. target or close-comparable buyer class;
3. paid, purchase, would-pay, review, rating, or sale signal;
4. mapping to one kit artifact or buyer job;
5. caveat/source-bias note.

If exact-category sources only show prices/listing copy and adjacent sources carry the actual reviews, keep the governor at `0/3` and log `hold`.

## Search budget

Use a bounded public search budget after required NotebookLM grounding. Five focused queries is enough for a single cron move, for example:

```text
site:gumroad.com/l "AI automation agency" "ratings" "proposal" OR "discovery"
site:gumroad.com/l "AI automation" "agency" "client acquisition" "ratings"
site:etsy.com/listing "AI automation agency" "sales scripts" "digital download"
site:payhip.com "AI automation agency" "template" "sales"
"AI automation agency" "discovery call" "Gumroad"
```

Use `web_extract` or equivalent clean extraction for candidate product pages. Treat 404s as discarded leads, not blockers.

## Product implication wording

When evidence remains below the gate, state the next decision choices explicitly:

- keep as private/internal operating asset;
- draft a free lead-magnet path for Karan approval before public exposure;
- pivot the paid product toward a broader buyer/category with stronger observed marketplace evidence;
- kill the paid-product path and preserve reusable components;
- Karan override.

Do not ask for public listing, checkout, waitlist, outreach, or paid-launch approval while the observed-WTP governor remains below pass.

## Verification

Run the normal validation suite plus the governor report:

```bash
python3 scripts/wtp_governor.py
python3 scripts/validate_repo.py
git diff --check
python3 scripts/local_skill_audit.py --min-score 80
python3 scripts/market_viability_audit.py --min-score 80
python3 scripts/product_experiment_audit.py --min-score 80
python3 scripts/loop_audit.py --min-score 80
python3 scripts/four_cs_audit.py --min-score 80
```

Expected safe outcome for a hold run: `scripts/wtp_governor.py` still reports blocked, and that is treated as honest evidence rather than failure.