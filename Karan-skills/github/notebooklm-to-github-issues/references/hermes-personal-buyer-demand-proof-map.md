# Hermes Personal Buyer Demand Proof Map Pattern

Use this when Product 001 or another passive-revenue product has clearer packaging but still lacks direct buyer-demand proof.

## Trigger

A scout run should prefer this pattern when:

- repo/harness validators are green;
- buyer-facing copy and product artifacts are cleaner than before;
- adversarial review or the source map still says direct buyer voice is missing;
- the next tempting move would be launch approval, listing polish, checkout setup, or more self-scored packaging progress.

## Pattern

Create a repo-local proof map rather than more sales copy:

```text
products/<slug>/buyer-demand-proof-map.md
products/<slug>/experiments/<date>-buyer-demand-proof-map.md
products/<slug>/experiment-ledger.tsv  # one row
```

The proof map should:

1. name the primary buyer under test;
2. name the buyer job under test;
3. summarize NotebookLM/product-scout consensus without copying raw NotebookLM output;
4. separate passed gates from not-passed gates;
5. map the main buyer objections or sales friction to existing kit artifacts;
6. label proof confidence honestly (`High`, `Medium`, `Low`);
7. state the exact pass condition for the next proof gate;
8. explicitly block public listing/checkout/launch approval while direct buyer proof is missing.

## Good metric

Use `objection coverage` as the primary metric when the artifact maps launch objections to deliverables.

A useful row looks like:

```text
date	experiment_id	surface	variant	primary_metric	baseline	result	decision	notes
2026-07-04	20260704-buyer-demand-proof-map	product format	buyer demand proof map	objection coverage	no standalone artifact-to-objection proof map; direct buyer-voice gate 0/3 passed	5/5 P0 launch objections mapped to kit artifacts, but direct buyer-voice proof remains not passed	hold	NotebookLM-grounded proof discipline artifact; public launch remains blocked pending accessible freelancer/agency buyer voice.
```

## Decision rule

Use `hold`, not `promote`, when the artifact improves discipline but does not resolve the direct buyer-demand gate. This prevents the ledger from becoming a wall of self-scored `promote` rows that can be misread as market validation.

## Source handling

Search snippets, blocked Reddit pages, vendor guides, and single-author narratives are useful leads, but they are not enough to pass direct buyer voice. The pass condition should require accessible public sources with:

1. a verifiable URL;
2. a quote or close paraphrase from the product-pack buyer segment;
3. a sales/discovery/proof/pricing/objection pain that maps to one kit artifact;
4. a caveat explaining source bias.

Do not quote or use the proof map externally without Karan approval and a fresh source check.
