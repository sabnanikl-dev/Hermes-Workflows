# Static-site responsive visual QA with a temporary browser harness

Use this pattern when a static HTML/CSS PR needs screenshot/geometry proof across viewports but the repo does not include Playwright/Puppeteer as project dependencies, or when you want a quick operator-level visual check without adding test dependencies.

## When it applies

- Static site repo with plain `site/` assets.
- Frontend/layout PR where acceptance criteria mention specific widths (for example 375px, 768px, 1440px).
- Canonical verification is still repo tests/checkers, but human-facing proof needs a rendered page.
- You must not commit visual-QA scratch files.

## Pattern

1. Run canonical repo checks first or in parallel (`npm test`, focused validator, build/no-op command).
2. Create a temporary HTML harness under the served static root, e.g. `site/__hermes-visual-qa-<issue>.html`, containing labeled iframes that point to the target route and set explicit iframe widths.
3. Start a local static server from the static root:

```bash
cd site
python3 -m http.server 8848 --bind 127.0.0.1
```

4. Open the harness with browser automation.
5. Use browser DOM geometry to verify layout invariants, not just screenshots:

```js
Array.from(document.querySelectorAll('iframe')).map((frame, i) => {
  const doc = frame.contentDocument;
  const win = frame.contentWindow;
  const photo = doc.querySelector('[data-owner-photo-carousel]');
  const text = doc.querySelector('.about-split-text');
  const split = doc.querySelector('.about-split');
  const pr = photo.getBoundingClientRect();
  const tr = text.getBoundingClientRect();
  return {
    case: [375, 768, 1440][i],
    innerWidth: win.innerWidth,
    scrollWidth: doc.documentElement.scrollWidth,
    horizontalOverflow: doc.documentElement.scrollWidth > win.innerWidth + 1,
    photoBeforeTextVertically: pr.top < tr.top,
    photoRightOfText: pr.left > tr.left,
    gridColumns: win.getComputedStyle(split).gridTemplateColumns,
    photoGridColumn: win.getComputedStyle(photo).gridColumnStart,
    textGridColumn: win.getComputedStyle(text).gridColumnStart,
  };
});
```

6. Take a visual screenshot/inspection after the geometry check. If the important section is below the fold, scroll or make the harness frame height/route anchor show the changed component; do not treat a screenshot of only the hero/header as proof of the changed component.
7. Remove the temporary harness file and verify `git status` is clean except intended PR files.
8. Stop the local server.

## Reporting

Report both forms of evidence:

- Deterministic geometry: e.g. `375/768 photoBeforeTextVertically=true`, no horizontal overflow, `1440 photoRightOfText=true`.
- Visual inspection: the rendered section shows the changed component in the expected order/layout with no obvious clipping/overlap.

## Pitfalls

- If a screenshot does not actually show the affected component, it is not proof. Use DOM geometry, scroll, or route anchors to verify the component directly.
- Keep scratch harness files out of the commit. Delete them before final `git status` and before reviewers run.
- Do not add Playwright/Puppeteer dependencies to the project just for an operator smoke unless the issue explicitly asks for committed browser tests.
- Browser visual QA complements but does not replace canonical repo validators and the A/B reviewer loop.
