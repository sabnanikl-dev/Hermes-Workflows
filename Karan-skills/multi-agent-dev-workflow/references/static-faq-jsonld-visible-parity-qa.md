# Static FAQ + FAQPage JSON-LD parity QA

Use this when an issue asks for visible FAQ content plus optional `FAQPage` schema on static HTML pages.

## Pattern

1. Treat the visible FAQ as the source of truth. JSON-LD may be added only when it mirrors the visible Q&A verbatim.
2. Prefer semantic static markup (`section` with `aria-labelledby`, `h2`, `dl/dt/dd` or equivalent). Avoid JS-only accordions for GEO/snippet work unless the issue explicitly asks for interaction.
3. Keep existing page contracts intact: one `<h1>`, existing breadcrumbs/canonical/sitemap behavior, no unrelated body-copy rewrites unless the issue asks for them.
4. For approval-gated copy/fact changes, use `Refs #N` and verify `closingIssuesReferences` is empty. Do not use closing keywords in PR body or commit messages when the issue should remain open for business approval.

## Verification bundle

Run the repo checks first:

```bash
npm test
npm run check
npm run check:seo
```

Then add targeted DOM/schema checks:

- each affected page has exactly one `<h1>`;
- each affected page has the expected FAQ heading and 3–5 visible Q&As;
- each affected page still has expected existing JSON-LD (for example `BreadcrumbList`);
- if `FAQPage` was added, each JSON-LD question/answer exactly matches visible FAQ text;
- no Product/Offer/Review/inventory/live-availability claims slipped in unless explicitly approved.

Browser QA: render at the exact PR head and visually inspect at least one affected page's FAQ section for readability and spacing. If browser unsafe network evaluation is blocked, navigate each page directly and inspect the current page DOM only; don't treat the blocked cross-page fetch as evidence that browser QA is impossible.

## Review closeout

For A/B reviewer loops, verify both signed review objects/comments against the current `headRefOid`. `latestReviews` can hide a same-account `COMMENTED` review behind a later approval, so read the full reviews API as well as comments/threads before saying both lanes passed.
