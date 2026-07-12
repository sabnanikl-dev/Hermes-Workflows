# Hermes Personal Direction Traffic-Light Gate

Use this reference when a Hermes Personal passive-revenue/product scout is at risk of continuing artifact polish while the decisive buyer/value/WTP blocker remains unresolved.

## Trigger

Apply this pattern when all or most of the following are true:

- Product copy/artifacts have already improved materially.
- The experiment ledger has many `promote` rows based on repo-local proxy metrics such as buyer-clarity score, objection coverage, internal-term scans, or artifact readiness.
- An adversarial reviewer or the repo state says the current blocker is buyer/WTP/pivot evidence, not another title/hero/listing/export polish pass.
- NotebookLM is rate-limited/rejected after required attempts, but existing repo state and reviewer input are enough to make one safe repo-local move.
- The active product has multiple possible futures: paid launch, private/internal asset, free lead magnet, buyer pivot, kill/hold, or Karan override.

## Pattern

Create a single product-direction experiment that changes only the `product direction` surface and measures one metric, usually `observed-WTP sufficiency`.

The artifact should install a traffic-light decision checkpoint:

| Path | Status | Meaning |
|---|---|---|
| Current paid public launch | Red | Do not request listing, checkout, waitlist, outreach, approval packet activation, or public-live approval while the proof gate is below pass condition. |
| Private/internal use | Yellow | Useful as an operating artifact, but private usefulness is not market proof. Preserve it without further polish unless it directly supports the proof gate. |
| Free lead magnet | Yellow / approval-required | May be a lower-friction path if paid WTP is unresolved, but any public distribution/form/listing still requires Karan approval. |
| Exact buyer WTP evidence pass | Green | Safe repo-local move when it directly addresses the blocker. |
| Explicit buyer pivot scorecard | Green | Safe repo-local move when a different buyer has stronger evidenced pain/budget but needs support-risk scoring. |
| Karan override/direction | Green only when repo-local moves are exhausted | Ask for a buyer/path decision, not a publish approval request. |

## Files to update

Typical one-run file set:

```text
products/<slug>/experiments/<date>-direction-traffic-light.md
products/<slug>/experiment-ledger.tsv
products/<slug>/experiment-governor.md
```

This is still one move because it changes one surface: product direction.

## Ledger row guidance

Use `hold` unless the gate actually passes or Karan has explicitly approved a path.

Example fields:

```text
surface: product direction
variant: traffic-light hold/pivot/lead-magnet gate
primary_metric: observed-WTP sufficiency
baseline: 0/3 clean exact target-buyer WTP sources; paid/current-buyer direction on hold but scattered across proof/governor docs
result: 0/3 exact WTP remains; public paid launch red, private/free lead-magnet path yellow approval-required, WTP evidence or buyer pivot green
decision: hold
```

## Pitfalls

- Do not treat the traffic-light gate as public launch approval.
- Do not create new buyer-facing copy, pricing, exports, listing drafts, or checkout/setup work in the same move.
- Do not ask Karan to approve publishing while the red paid-launch gate remains red; if asking later, ask for a path/buyer decision unless he has already cleared the proof blocker.
- If NotebookLM rate-limits, record the blocker honestly in the experiment/ledger and continue only with a repo-local move grounded in existing repo/adversarial evidence.

## Verification

Run the repo's standard validators and check:

- the new experiment file states baseline, variant, metric, result, decision, and approval boundary;
- exactly one ledger row was appended;
- `experiment-governor.md` lists allowed/disallowed next moves consistently;
- no public-live action, credentials, payment, outreach, or account mutation happened;
- remote HEAD matches local HEAD after push when committing directly to `main`.
