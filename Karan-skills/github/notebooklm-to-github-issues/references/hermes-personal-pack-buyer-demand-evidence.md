# Hermes Personal Product 001 — Pack-Buyer Demand Evidence Pattern

Use this reference during Hermes Personal passive-revenue scout runs when Product 001 has buyer/value clarity work and the unresolved gap is evidence that the **pack buyer** exists or will pay.

## Trigger

Apply this when an adversarial review, Karan feedback, or source-map caveat says the product has evidence for the end customer's operational pain but lacks evidence for the digital-product buyer's pain.

For Product 001, distinguish:

- **End business pain:** local service businesses miss calls, voicemail, forms, after-hours inquiries, or follow-up tasks.
- **Pack buyer pain:** AI automation freelancers/tiny agencies need discovery-call assets, safe objection handling, positioning, and proof that a narrow workflow is worth testing.

Do not let strong end-business pain automatically count as proof that freelancers/agencies will buy a pack.

## One-run artifact pattern

A strong repo-local move is a dedicated source-map section named like:

```md
## Pack-buyer demand / willingness-to-pay signals
```

Include a table with:

```md
| Source | Buyer signal | What it supports | Caveat |
|---|---|---|---|
```

Good signal types:

- marketplace results for agency-side AI automation assets, templates, playbooks, or workflow packs;
- visible product prices and ratings when public and accessible;
- public methodology sources that support using buyer pain language before launch;
- comparable product formats that prove willingness to pay for packaged workflow judgment.

Do **not** overstate marketplace counts. They are market-adjacent, not proof of sales for this exact product.

## Preserve the direct buyer-voice gate

If only marketplace/product-pack signals are found, record the experiment decision as `hold`, not `promote`, and keep an explicit unchecked gate such as:

```md
- [ ] 3+ direct buyer-voice sources from freelancer/agency communities showing discovery-call or sales-objection pain in the buyer's own words.
```

Suggested wording for the conclusion:

```md
Current conclusion: market-adjacent evidence improved, but the P0 caveat remains open. The product should stay at `narrow` until direct freelancer/agency buyer-voice sources show the discovery-call or sales-objection pain in the buyer's own words.
```

## Experiment ledger pattern

Surface: `product format`

Primary metric: `source-map support count`

Example ledger result:

```text
6 market-adjacent pack-buyer signals added; direct buyer-voice gate remains unchecked
```

Decision:

- `hold` when market-adjacent evidence improved but direct buyer-voice proof is still missing;
- `promote` only if the run adds enough direct buyer-voice sources and they map clearly to product artifacts;
- `blocked` if public research is unavailable and no repo-local evidence can be added honestly.

## Boundaries

Do not use this evidence to request public launch approval by itself. Public posts, marketplace listings, checkout/payment links, waitlists, outreach, paid setup, ROI/revenue/legal/compliance claims, and direct buyer contact still require Karan's explicit approval.
