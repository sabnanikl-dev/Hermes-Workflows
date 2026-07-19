# Exact-head responsive proof with lazy images and contract-drift closeout

Use this for frontend PRs where merge-readiness requires screenshot proof across responsive widths and the page contains lazy-loaded remote images.

## Why the normal screenshot path can lie

- A raw Chrome `--window-size=375,...` screenshot may be misleading on macOS/headless Chrome because the browser can enforce a wider minimum layout viewport and crop the bitmap to 375px. Apparent right-edge clipping is not proof of real overflow.
- A one-shot Playwright `--full-page` screenshot may capture lazy images before they have entered the viewport, leaving intentional fallback colors where real images should appear.
- A screenshot from the initial PR commit is stale after even a docs-only follow-up commit. Final proof must be labeled with and rendered from the current `headRefOid`.

## Reliable capture sequence

1. Verify the live PR `headRefOid` and fast-forward the isolated PR worktree to it.
2. Serve that exact worktree over local HTTP; never use `file://`.
3. Use a real Playwright browser context with an explicit viewport, not raw Chrome `--window-size` cropping.
4. For each lazy image in the changed component:
   - `scrollIntoViewIfNeeded()`;
   - wait briefly for loading/decoding;
   - assert `complete && naturalWidth > 0`.
5. Scroll back to the top, then collect deterministic metrics before capture:
   - `innerWidth`;
   - `document.documentElement.scrollWidth`;
   - `overflow = scrollWidth > innerWidth`;
   - changed-component count;
   - image `naturalWidth` / `naturalHeight`;
   - CTA count or other issue-specific DOM invariants.
6. Capture fresh full-page screenshots at the issue-required widths (commonly 375, 768, and 1440).
7. Visually inspect the actual files. Do not deliver navy/blank fallback cards as final proof when the requirement is to show real imagery.
8. Store final screenshots outside the temporary worktree and include the exact PR head in filenames/captions.

## Minimal Playwright pattern

```js
const page = await browser.newPage({ viewport: { width: 375, height: 900 } });
await page.goto(url, { waitUntil: 'networkidle' });
const images = page.locator('.changed-component img[loading="lazy"]');
for (let i = 0; i < await images.count(); i++) {
  await images.nth(i).scrollIntoViewIfNeeded();
  await page.waitForTimeout(350);
}
await page.waitForFunction(() =>
  [...document.querySelectorAll('.changed-component img')]
    .every(img => img.complete && img.naturalWidth > 0)
);
await page.evaluate(() => window.scrollTo(0, 0));
const metrics = await page.evaluate(() => ({
  innerWidth,
  scrollWidth: document.documentElement.scrollWidth,
  overflow: document.documentElement.scrollWidth > innerWidth,
}));
if (metrics.overflow) throw new Error(JSON.stringify(metrics));
await page.screenshot({ path, fullPage: true });
```

## Review/fix-loop closeout

When a reviewer flags stale harness documentation after a feature lands, do not update only `docs/spec.md`. Search every source-of-truth artifact that future work consumes:

- source packets and allowlists;
- consumer/status sections;
- build plans and future-tense handoff notes;
- issue-boundary docs naming the next owner.

Preserve historical truth (for example, “issue #166 itself built no page”) while adding the current delivered state and the next-issue boundary. After any follow-up commit—even docs-only—refresh exact-head screenshots and rerun both reviewer roles, because old-head approvals are not current-head evidence.
