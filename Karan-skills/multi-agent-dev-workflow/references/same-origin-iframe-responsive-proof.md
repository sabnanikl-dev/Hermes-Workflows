# Same-origin iframe responsive proof without a local Playwright package

Use this for static frontend PRs when exact-width browser evidence is required but the worktree does not have Playwright/Puppeteer installed. This is a fallback for responsive layout and interaction checks, not a replacement for real-device or full-browser E2E coverage when the issue requires it.

## Pattern

1. Verify and label the live PR `headRefOid`; fast-forward the isolated worktree to it.
2. Serve that exact worktree over localhost HTTP.
3. Create a clearly named, uncommitted scratch HTML file under the served root with same-origin iframes whose `width` attributes equal the required viewports (for example 375, 768, and 1440).
4. Navigate the harness with the browser tool. Because the frames are same-origin, inspect each frame programmatically:
   - `frame.contentWindow.innerWidth`
   - `frame.contentDocument.documentElement.scrollWidth`
   - `overflow = scrollWidth > innerWidth`
   - issue-specific invariants such as H1 count, CTA count, FAQ count, and mobile/desktop nav mode.
5. Visually inspect the affected component/page in the 375px and 768px frames; inspect the wide layout directly or in the 1440px frame. A harness wider than the operator browser may itself scroll horizontally; do not confuse harness clipping with overflow inside the iframe. Trust the frame-local metrics.
6. Exercise shared interactions inside the exact-width frame when relevant: open the mobile menu, verify focus moves into it, press Escape, and verify focus returns to the toggle.
7. After every follow-up commit, refresh the live PR head and rerun the proof with the new head embedded in the harness title/output. Old-head screenshots and metrics are stale even when the follow-up is docs-only.
8. Delete the scratch harness, stop the local server, and verify `git status` is clean before launching reviewers.

## Minimal metrics expression

```js
[...document.querySelectorAll('iframe')].map((frame) => {
  const doc = frame.contentDocument;
  const win = frame.contentWindow;
  return {
    width: win.innerWidth,
    scrollWidth: doc.documentElement.scrollWidth,
    overflow: doc.documentElement.scrollWidth > win.innerWidth,
    h1s: doc.querySelectorAll('h1').length,
  };
});
```

## Evidence wording

Report this honestly as exact-width, same-origin iframe browser QA. State which widths were measured, which interactions were exercised, and whether the page itself overflowed. Do not call it Playwright coverage, real-device testing, or a deployed-preview smoke.
