# Static FAQ accordion + GEO PR-loop pattern

Use when a static-site SEO/GEO FAQ PR changes from fully visible answers to an accordion/dropdown after human visual review.

## Key decision

A conservative accordion can remain GEO/crawler-friendly if it is native/static:

- Use `<details class="faq-item">` with `<summary class="faq-q">Question</summary>` and a real answer element such as `<p class="faq-a">Answer</p>` inside the same `<details>`.
- Keep answer text in the initial HTML/DOM. Do **not** fetch, inject, or reveal schema-only answers after click.
- Keep `FAQPage` JSON-LD only if it mirrors the visible/dropdown Q&A text verbatim.
- Keep questions visible when collapsed.
- Avoid JS-only accordion behavior for FAQ content whose value is AI-citation/GEO extractability.

Google's mobile-first guidance permits different mobile UX such as accordions/tabs as long as the content remains equivalent and accessible on the mobile page. Treat this as support for static/native accordions, not a license to hide primary content behind interaction-loaded JavaScript.

## Workflow notes

1. A preference expressed in chat is not yet part of the current-head contract. It has to become PR-visible evidence before anything can be proved against it; `pr-prover` owns that transport.
2. Scope the conversion narrowly: the requested accordion change, JSON-LD parity preserved, and any stale PR body text describing the old markup corrected.
3. Run deterministic checks:
   - repo checks (`npm test`, `npm run check`, `npm run check:seo` for JMD-like static harnesses)
   - targeted DOM/static parser: each changed page has 5 `<details>` items, one `<h1>`, `BreadcrumbList` + `FAQPage`, non-empty answer text in static HTML, and exact FAQPage ↔ visible summary/answer parity.
4. Browser QA one changed page with at least one accordion opened. Native `<details>` may show only questions in accessibility snapshots while collapsed; use `textContent`/static parser to prove answer crawlability and open one item for visual proof.
5. A markup conversion is a new exact head. Passes recorded against the pre-accordion head no longer count for anything.

## Acceptance notes

- `innerText` for a collapsed answer can be empty even when `textContent` and static HTML contain the answer. Use `textContent` or source parsing for crawlability/parity checks.
- A human review preference that changes markup semantics leaves any PR body text describing the old markup stale (for example, `<dl>` after converting to `<details>`). A stale contract surface is a real blocker, not cosmetic.
- Keep copy/deploy gates explicit; an engineering-mergeable FAQ PR may still be blocked by Lucky/Danny/Karan approval.