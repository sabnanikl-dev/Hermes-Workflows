# JMD custom-shoes WordPress → static-site migration pattern

Use when JMD custom-shoe / shoes-section work comes up during the WordPress/WooCommerce → static Vercel migration.

## Durable sequence

1. **Capture/source packet first**
   - Treat the live WordPress/WooCommerce shoes catalog as source material, not approved static-site copy.
   - Create or update a repo-visible source packet before building the public page.
   - Record product names, source URLs, image counts, CTA URL shape, asset provenance, and approval status.
   - Classify every price, sale price, delivery-window claim, material/manufacturing claim, and made-to-order CTA as approved / inspiration-only / needs Karan-Danny approval / do-not-migrate.

2. **Then build the crawlable showroom-safe page**
   - Preferred route from the July 2026 analysis: `/custom-shoes-conyers-ga/`.
   - Keep it as a showroom/customization page, not ecommerce.
   - No cart/account UI, sale badges, stock/in-stock copy, size runs, live availability, checkout language, Product/Merchant schema, or unapproved prices.
   - Made-to-order links, if used, must be product-specific, tested, approved, and `rel="noopener"`.
   - Do **not** reuse the stale nav-level made-to-order URL `http://jmdmenswear.made-to-order.com/getinspired/#`; it resolved to a 404 during analysis.

3. **Fold legacy URL coverage into migration issues**
   - Do not create duplicate redirect trackers if the WordPress → Vercel migration redirect/preflight issues already exist.
   - Fold shoes category/product URL coverage into the existing redirect map and preflight work.
   - The key legacy cluster includes `/product-cat/shoes/`, `/product-cat/shoes/page/1/`, `/product-cat/shoes/page/2/`, `/product-cat/shoes/custom-made-shoes/`, empty child categories, and individual `/product/<shoe-slug>/` URLs.
   - Redirect rows should point directly to a published target; avoid redirecting to a future page that does not exist yet.

## PR hygiene pitfall

If committing an analysis report after follow-up GitHub issues/comments have already been filed, re-read the report before committing. Update wording from "Proposed issue" / "no issue found" to reflect the current reality, e.g. "Filed GitHub Issue Draft (#166/#167)" and notes that redirect/preflight coverage was folded into #162/#163. This prevents repo evidence from contradicting the live tracker state.

## Boundaries

This workflow does not authorize public deploys, DNS/hosting changes, WordPress mutations, made-to-order account changes, or client-facing publication. Keep all such actions separately approval-gated.
