# Accordion FAQ Visual QA Proof Pattern

Use this when a PR changes visible FAQ sections into accordions/dropdowns and the user asks for screenshot proof before merge.

## Why this matters

For SEO/GEO/AEO FAQ work, a dropdown can be acceptable only when the answers remain present in the initial static DOM. Visual proof should show both:

- the collapsed accordion state (questions visible, disclosure marker visible); and
- at least one expanded answer so the user can judge spacing, typography, and readability.

## Capture pattern

1. Re-check the live PR head before previewing:

```bash
gh pr view <PR> --repo <owner>/<repo> --json headRefOid --jq .headRefOid
git rev-parse HEAD
```

2. Start the preview from the exact PR worktree over HTTP, never `file://`.

3. Navigate to the target page and use browser JS to set a deterministic visual state before the screenshot:

```js
(() => {
  document.querySelectorAll('details.faq-item').forEach((d, i) => d.open = i === 0);
  document.getElementById('faq-heading')?.scrollIntoView();
  window.scrollBy(0, -220); // offset sticky nav
  return {
    path: location.pathname,
    details: document.querySelectorAll('details.faq-item').length,
    open: document.querySelectorAll('details.faq-item[open]').length,
    firstSummary: document.querySelector('details.faq-item summary')?.textContent.trim(),
    firstAnswer: document.querySelector('details.faq-item .faq-a')?.textContent.trim(),
  };
})()
```

4. Capture with `browser_vision`, then copy the newest `~/.hermes/cache/screenshots/browser_screenshot_*.png` into stable evidence storage outside the worktree.

5. For multi-page FAQ changes, create a contact sheet plus individual screenshots. Deliver every file with `MEDIA:/absolute/path.png`.

## Verification alongside screenshots

Run a deterministic DOM/parity probe when structured data is involved:

- count `details.faq-item` per page;
- confirm one `<h1>` per page;
- confirm answer text is present in static HTML/DOM, not JS-fetched;
- confirm `BreadcrumbList` and `FAQPage` JSON-LD parse;
- confirm FAQPage questions/answers match visible `<summary>` / answer text verbatim.

## Pitfalls

- An anchored URL like `/#faq-heading` may not visually position the section correctly under sticky nav. Always scroll and offset manually before screenshot capture.
- A screenshot of only the collapsed state is not enough for visual QA; open one representative item so the answer spacing and readability are visible.
- Headless CLI screenshots can time out or produce blank/mis-cropped images while still creating a non-empty file. Inspect/capture via browser tools when proof quality matters.
- Do not claim accordion GEO safety unless answers are present in the initial DOM and any FAQPage JSON-LD mirrors the visible/dropdown content verbatim.
