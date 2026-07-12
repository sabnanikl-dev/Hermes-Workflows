# Hermes Personal: observed WTP evidence pass pattern

Use this when Product 001 / a passive-revenue scout is blocked on direct willingness-to-pay evidence but needs to determine whether comparable paid artifacts exist before choosing hold, kill, pivot, or deeper proof work.

## Trigger

Use this pattern when:

- the product copy/readiness artifacts are already polished enough;
- adversarial or human feedback says the blocker is buyer/WTP, not packaging;
- the proof map says vendor/educator/free-template/internal-score signals are non-passes;
- NotebookLM is rate-limited/rejected after the required attempts, or NotebookLM points toward WTP/proof discipline;
- a safe repo-local public-source pass can be completed within the search budget.

## Pattern

1. Query the required NotebookLM notebooks first. If they are rate-limited/rejected after compact retries, mark them blocked in the final report and continue with bounded public/repo-local evidence. Do not fabricate NotebookLM grounding.
2. Search for paid/reviewed comparable artifacts, not more advice posts. Good queries include marketplace + job terms:
   - `site:etsy.com AI automation agency proposal template discovery call price reviews`
   - `site:gumroad.com AI automation agency proposal template discovery call`
   - `"discovery call script" template price review freelancer`
3. Classify each source honestly:
   - **Exact target WTP**: target buyer class and comparable paid/purchase/review signal for the same job. Strongest.
   - **Comparable service-seller WTP**: adjacent solo/B2B service seller paying for discovery, sales-script, proposal, audit, or client-acquisition assets. Useful but not exact.
   - **Price/category only**: paid listing without visible reviews/purchase signals. Use as price/category evidence, not observed WTP.
   - **Non-pass**: vendor suggested price bands, educator claims, free-template libraries, local-service owner pain, or internal scores.
4. Create a repo-local artifact such as:
   - `products/<slug>/observed-wtp-evidence-pass.md`
   - `products/<slug>/experiments/<date>-observed-wtp-evidence-pass.md`
   - append one row to `experiment-ledger.tsv`
5. Keep the decision `hold` unless the exact gate truly passes. Comparable marketplace evidence improves the proof map but should not unlock public listing/checkout by itself.
6. Update the proof map so the next run sees the new state and does not repeat the same bounded search as if it were still `0/3`.

## Good metric

Primary metric: `observed-WTP source count`

Good result wording:

```text
5 comparable paid/reviewed service-seller assets plus 1 exact-category priced listing mapped; exact missed-call-kit WTP remains unresolved.
```

Decision: `hold`

## Pitfalls

- Do not treat marketplace result counts or listing prices alone as sales proof.
- Do not treat adjacent service-seller reviews as exact demand for the current kit.
- Do not copy competitor claims, revenue claims, or review text into buyer-facing copy.
- Do not request launch/listing/checkout approval from comparable evidence alone.
- Do not create a new proxy-polish `promote` row when the actual blocker remains exact buyer WTP.
