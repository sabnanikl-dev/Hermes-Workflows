# Hermes Personal local-owner pivot scorecard pattern

Use this reference for Product 001 passive-revenue scout runs when adversarial/user feedback says the current agency/freelancer buyer may be thin and the local-service owner/operator might have stronger pain or budget.

## When to use

Trigger when the active product is held behind buyer/WTP uncertainty and the next useful move is an audience-segment decision, not more copy, artifact, price, or launch polish.

Good signals:

- adversarial reviewer flags the selected buyer as low-WTP or meta;
- exact target-buyer WTP remains unresolved;
- local-service owners have clearer underlying pain and budget, but support/compliance burden is risky;
- the experiment governor allows a local-owner pivot scorecard.

## Pattern

Run exactly one product experiment with:

- Surface: `audience segment`
- Primary metric: `buyer-segment evidence score plus low-fulfillment fit`
- Decision: usually `hold` unless the owner path clearly beats the current buyer and stays low-fulfillment.

Score the owner/operator as the **paid product buyer**, not merely as the beneficiary of the workflow.

Suggested criteria:

| Criterion | Scoring question |
|---|---|
| Evidenced pain | Do public sources show repeated, urgent owner pain? |
| Budget / WTP evidence | Do owners pay for this kind of decision aid, not only for software/services? |
| Channel / accessibility | Can the owner buyer be reached without unapproved outreach or paid setup? |
| Low-fulfillment digital-pack fit | Can the product avoid implementation, software selection, compliance advice, and support expectations? |

## Decision rules

- If owner pain/budget is strong but low-fulfillment fit is weak, log `hold`, not `pivot`.
- A pivot needs evidence for owner self-audit/checklist/decision-worksheet demand, not just evidence that missed calls hurt businesses.
- Keep public-live gates closed: no post, listing, checkout, waitlist, outreach, owner interview, or approval request unless Karan explicitly approves.

## Artifacts to update

For Hermes Personal Product 001, a complete run should update:

- `products/local-service-missed-call-recovery-pack/experiments/<date>-local-owner-pivot-scorecard.md`
- `products/local-service-missed-call-recovery-pack/value-clarity-reset.md`
- `products/local-service-missed-call-recovery-pack/experiment-governor.md`
- `products/local-service-missed-call-recovery-pack/experiment-ledger.tsv`

Append exactly one ledger row. Do not also polish copy, rebuild dist artifacts, change price, draft launch approval, or do platform setup in the same run.

## Verification

Run the repo's full cron validation set before committing:

```bash
python3 scripts/validate_repo.py
git diff --check
python3 scripts/local_skill_audit.py --min-score 80
python3 scripts/market_viability_audit.py --min-score 80
python3 scripts/product_experiment_audit.py --min-score 80
python3 scripts/loop_audit.py --min-score 80
python3 scripts/four_cs_audit.py --min-score 80
```

If committing direct to main under the scheduled sprint authority, push and verify local `HEAD` equals `origin/main` with `git ls-remote` before reporting success.
