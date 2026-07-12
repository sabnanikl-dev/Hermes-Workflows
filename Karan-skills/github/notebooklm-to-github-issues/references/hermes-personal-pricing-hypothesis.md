# Hermes Personal Product 001 Pricing Hypothesis Pattern

Use this when a passive-revenue product scout needs to revisit price after buyer/usefulness clarity improves, but before public listing/checkout approval exists.

## Trigger

- Active product has clearer buyer/use case than before.
- Prior price is stale or was only a launch assumption.
- Exact-kit willingness-to-pay is still unproven.
- Public listing, checkout, waitlist, outreach, and payment activation remain approval-gated.

## Pattern

1. Treat price as the single experiment surface.
2. Build a repo-local `pricing-hypothesis.md` rather than editing public copy or asking for launch approval.
3. Use bounded public-source anchors, separated by evidence type:
   - free substitutes/templates;
   - adjacent low-ticket template or agency product ranges;
   - broader playbook/course prices;
   - underlying workflow software/tool prices;
   - higher-touch service/substitute spend.
4. Pick a conservative private validation price when direct willingness-to-pay is weak.
5. Keep higher prices explicitly conditional on stronger proof, polished previews, testimonials/reviews, or approved public exposure.
6. Log exactly one ledger row with:
   - `surface`: `price`
   - `primary_metric`: `source-map support count`
   - `decision`: usually `hold` unless real public market data exists.
7. Update readiness/approval docs only to reflect the private hypothesis and closed approval gate; do not turn a price hypothesis into a public ask.

## Useful wording

- “No public price approved.”
- “Current private hypothesis: `$X` early validation / `$Y` first public-listing candidate after approval.”
- “This is not an approved public price, listing, checkout, preorder, or waitlist.”
- “Hold until Karan approves external exposure and a platform-specific draft exists.”

## Pitfalls

- Do not revive an old price because it appeared in a previous launch packet.
- Do not borrow broad playbook/course pricing for a narrow kit without exact-buyer proof.
- Do not treat software/service spend as direct willingness-to-pay for the digital pack.
- Do not make revenue, ROI, savings, booked-job, legal, or compliance claims.
- Do not request paid-listing approval while a value-clarity blocker remains open.

## Verification

Run the normal Hermes Personal validation set before commit/push:

```bash
python3 scripts/validate_repo.py
git diff --check
python3 scripts/local_skill_audit.py --min-score 80
python3 scripts/market_viability_audit.py --min-score 80
python3 scripts/product_experiment_audit.py --min-score 80
python3 scripts/loop_audit.py --min-score 80
python3 scripts/four_cs_audit.py --min-score 80
```
