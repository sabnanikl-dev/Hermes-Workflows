# Hermes Personal: competitor WTP proxy map pattern

Use this when Product 001 / a passive-revenue scout is blocked on direct buyer proof but NotebookLM or reviewer input points toward competitor willingness-to-pay evidence.

## Durable lesson

Competitor/product-market evidence can improve product confidence, pricing anchors, and artifact shape, but it is **proxy proof**, not direct buyer voice. Do not let paid marketplace examples or seller-authored pages silently clear the direct buyer-voice gate.

## Pattern

1. Query the required NotebookLM notebooks separately and synthesize outside NotebookLM.
2. If the AI-money notebook recommends validating category demand through paid alternatives, run a bounded public search for comparable products.
3. Prefer accessible pages that show at least one of:
   - price or pay-what-you-want model;
   - ratings/reviews/testimonials;
   - concrete deliverables such as discovery decks, scripts, proposal templates, calculators, playbooks, or workflow blueprints;
   - a buyer/problem similar to the product under test.
4. Classify sources honestly:
   - **Direct buyer voice**: quote-level language from the exact buyer segment in their own words. Counts toward the direct proof gate.
   - **Competitor WTP proxy**: paid products, ratings, reviews, or marketplace pages for adjacent buyers/formats. Useful for price/category/artifact support, but does not pass the direct buyer-voice gate by itself.
   - **Seller-authored claim**: competitor page copy about outcomes, ROI, scarcity, revenue, or client acquisition. Use only as category/positioning signal; do not copy claims.
   - **Free/PWYW lead magnet**: supports distribution/format thinking, but weakens paid-demand certainty.
5. Create a repo-local artifact such as `competitor-wtp-proxy-map.md` that maps:
   - source URL;
   - observed price/rating/product format;
   - buyer/problem signal;
   - relevance to the active kit;
   - caveat;
   - which current kit artifact it supports.
6. Log exactly one experiment row. Use `hold` when proxy evidence improves the map but direct buyer voice remains incomplete.

## Example metric

Primary metric: `source-map support count`

Result wording:

```text
4 accessible paid/proxy products and 10 proxy review/voice snippets mapped to 5 kit artifact groups; direct buyer-voice gate still 0/3 passed.
```

Decision: `hold`

## Pitfalls

- Do not treat Gumroad/Etsy/Payhip result counts as sales proof.
- Do not use competitor income, ROI, conversion, client, guarantee, scarcity, or savings claims in buyer-facing copy.
- Do not request public listing/checkout approval because proxy WTP improved; keep launch blocked until the actual approval criteria pass.
- Do not rebuild/export public-facing artifacts just because the proof map improved; artifact rebuild is a separate surface.
- Do not over-collect sources in one run. Keep the search budget bounded and report when more research is needed.
