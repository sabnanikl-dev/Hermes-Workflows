# JMD Service/Event Landing Pages

Use this when implementing or grooming JMD website work that adds dedicated crawlable pages for local/event search intent (prom, weddings, quinceañeras, tuxedo rentals, broader formalwear).

## Durable pattern

- Build static, crawlable HTML pages under descriptive lowercase hyphenated paths, e.g.:
  - `/prom-formalwear-conyers-ga/`
  - `/wedding-tuxedo-rentals-conyers-ga/`
  - `/quinceanera-formalwear-conyers-ga/`
- Each page should have:
  - exactly one `<h1>`
  - unique `<title>`
  - unique meta description
  - self-referencing canonical URL
  - sitemap membership exactly once
  - visible breadcrumbs if `BreadcrumbList` JSON-LD is emitted
  - standard `<a href>` links from relevant homepage/About/blog locations
- Keep pages complementary to the homepage; do not replace existing showroom/homepage sections unless separately scoped.

## Copy / safety boundaries

- Preserve the JMD showroom-first boundary: call, get directions, visit the showroom, try it on in person.
- Public rental copy remains **tuxedo rentals only** unless separately approved.
- Approved rental ensemble wording: tuxedo, shirt, vest, and bowtie.
- Approved price wording when needed: `$209.99 and up`.
- Wedding groups prefer appointments and typically need a **minimum of 3–4 weeks**.
- Single rentals such as prom are welcome as walk-ins.
- Avoid suit-rental claims unless separately approved.
- Avoid Product/Merchant listing schema, ecommerce/cart/checkout language, live availability, size runs, stock counts, fake urgency, fake awards/reviews, stock imagery, and AI imagery.

## Verification pattern

Run repo tests plus browser smoke when using browser tools:

- `npm test`
- `npm run check`
- `npm run build`
- `git diff --check`
- Local static server + browser smoke for each new route at 375, 768, and 1440 px:
  - HTTP 200
  - exactly one `<h1>`
  - expected self-canonical
  - visible breadcrumb
  - no horizontal overflow
  - no console warnings/errors
  - no failed requests

## PR body checklist

Include:

- New routes and internal-link sources.
- Sitemap/canonical updates.
- Explicit no-live-change boundary.
- Rental-copy constraint: tuxedo-rentals-only.
- Verification output, including local browser smoke evidence.
