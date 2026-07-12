# Hermes Personal target-buyer WTP scan pattern

Use this pattern during Product 001 passive-revenue scout runs when the product has enough copy/artifact polish but remains blocked by buyer/WTP uncertainty.

## Trigger

- Adversarial or repo context says proxy-metric farming is the main risk.
- Existing evidence is mostly vendor/educator guidance, broad service-seller analogues, or price/category listings.
- The current product direction is blocked on whether the selected buyer class actually pays for comparable assets.
- NotebookLM is unavailable/rate-limited after the required JSON + text retries, but repo-local progress is still possible.

## One-run move

Run a bounded public-source pass focused only on the exact target-buyer class, not more product polish.

For the Missed-Call Discovery Audit Kit, the useful query family was:

```text
site:gumroad.com "AI automation agency" "discovery" "template"
site:gumroad.com "AI automation agency" "proposal" "template"
site:etsy.com "AI automation agency" "template" "clients"
"AI automation agency" "discovery call" "template" price
"AI automation agency" "proposal template" "$"
"AI automation agency" "client acquisition" "Gumroad"
```

Keep to the prompt's search budget. Prefer accessible listing/product pages with visible price, sales/review signal, buyer class, and artifact mapping.

## Evidence classification

Separate these categories explicitly:

- **Clean observed WTP / pass candidate:** buyer review, purchase evidence, named paid comparable, or stated would-pay from the target buyer class.
- **Partial WTP:** listed price, shop-level sale count, marketplace result count, or seller-authored listing for the target buyer class.
- **Category lead only:** search-result snippets, blocked pages, timed-out marketplace pages.
- **Non-pass:** vendor suggested pricing, tutorial/educator claims, free-template libraries without purchase evidence, local-service-owner pain when the current pack buyer is the agency/freelancer.

## Artifact shape

Create one evidence artifact under the product workspace, for example:

```text
products/local-service-missed-call-recovery-pack/target-buyer-wtp-scan.md
```

Include:

1. question;
2. search budget / queries used;
3. NotebookLM status if blocked;
4. evidence table with source, observed price/purchase signal, buyer/job signal, kit mapping, caveat;
5. gate readout;
6. decision (`hold` unless the pass condition truly clears);
7. product implication: continue exact-buyer evidence, pivot, lead-magnet path, or Karan override.

Also create a product experiment file and append exactly one `experiment-ledger.tsv` row:

```text
surface: evidence / WTP gate
primary_metric: observed-WTP source count
decision: hold unless 3/3 clean sources pass
```

## Pitfalls

- Do not count seller-authored listing copy as buyer voice.
- Do not count a listed price as proof of purchase unless a sale/review/purchase signal is visible.
- Do not treat marketplace search snippets as source proof; treat them as leads.
- Do not request public listing/checkout approval while exact WTP remains unresolved.
- Do not copy claim-heavy income/ROI/client-guarantee language into buyer-facing assets; record it only as category evidence with caveats.

## Verification

Run the repo's full product-scout validation set before committing:

```bash
python3 scripts/validate_repo.py
git diff --check
python3 scripts/local_skill_audit.py --min-score 80
python3 scripts/market_viability_audit.py --min-score 80
python3 scripts/product_experiment_audit.py --min-score 80
python3 scripts/loop_audit.py --min-score 80
python3 scripts/four_cs_audit.py --min-score 80
```

After pushing, verify local HEAD equals `origin/main` with `git ls-remote origin refs/heads/main`.
