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

## PR-bus workflow

1. If Karan expresses the visual preference in chat, post a concise PR comment first so the PR remains the coordination bus.
2. Send Claude Code a pointer-first fix prompt: read the live PR comments/reviews/issues, fix only the requested accordion conversion, preserve JSON-LD parity, update stale PR body text, run verification, commit/push, and post a signed fix comment.
3. Verify the pushed commit via `gh pr view --json headRefOid,commits` against local `git rev-parse HEAD`.
4. Run deterministic checks:
   - repo checks (`npm test`, `npm run check`, `npm run check:seo` for JMD-like static harnesses)
   - targeted DOM/static parser: each changed page has 5 `<details>` items, one `<h1>`, `BreadcrumbList` + `FAQPage`, non-empty answer text in static HTML, and exact FAQPage ↔ visible summary/answer parity.
5. Browser QA one changed page with at least one accordion opened. Native `<details>` may show only questions in accessibility snapshots while collapsed; use `textContent`/static parser to prove answer crawlability and open one item for visual proof.
6. Re-run A/B reviewers on the new current head. Old approvals on the pre-accordion commit no longer count.

## Acceptance notes

- `innerText` for a collapsed answer can be empty even when `textContent` and static HTML contain the answer. Use `textContent` or source parsing for crawlability/parity checks.
- If a human review preference changes markup semantics, update the PR body so it no longer describes the stale implementation (for example, `<dl>` after converting to `<details>`).
- Keep copy/deploy gates explicit; an engineering-mergeable FAQ PR may still be blocked by Lucky/Danny/Karan approval.