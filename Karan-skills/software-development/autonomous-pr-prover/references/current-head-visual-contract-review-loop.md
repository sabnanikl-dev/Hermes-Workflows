# Current-head visual contract review loop

Use this reference when an already-open static/site PR gets a human visual-contract follow-up mid-review (for example: “make this map/card/layout true to the actual source, not generic”).

## Pattern that worked

1. Treat the human PR comment as a live blocking contract surface even if the PR was previously approved.
2. Keep the change on the existing PR branch and scoped to that comment. Pointer-first still applies: the live PR comments and reviews are the contract, not a copied summary of them.
3. Prior accepted fixes stay accepted (for example: no visible TODO copy, no mobile overflow regression, no geo/coordinate claims). A visual follow-up is not a licence to regress them.
4. Require both deterministic suite verification and a targeted contract probe:
   - required labels/content present;
   - no forbidden claims/metadata introduced;
   - layout invariant preserved (for example `scrollWidth <= innerWidth` at 320px).
5. If the local worktree does not have Playwright/Chrome available, do not stop at a static text check when Hermes browser tools are available. Start a local HTTP server and use `browser_console` to inject a 320px iframe, then read `documentElement.scrollWidth`, map/component bounding boxes, and DOM/SVG text labels from inside the iframe.
6. Pair the DOM probe with visual inspection (`browser_vision`) for changed visual components. For anchored sections, scroll the target into view and offset for sticky nav; if an anchor capture is misleading, use a taller full-page/section view plus DOM assertions.
7. Treat the fix as a new exact head. Prior passes are historical; `pr-prover` re-runs the gates and the ordered review lifecycle, and this reference does not reassemble that closeout by hand.
8. A lane that timed out after useful reads is not a pass. Useful partial reads and a real verdict are different things, and only the second one counts; `pr-prover` owns timeouts, retries, and how the lifecycle continues.
9. Automated checks going green again is not a response to a human blocking comment. Whether a later fix commit or reply actually addresses it is exact-head evidence `pr-prover` reads back, not a closeout this reference reassembles.

## 320px iframe probe sketch

Run against a local HTTP preview for static sites:

```js
(async () => {
  const iframe = document.createElement('iframe');
  iframe.style.cssText = 'position:fixed;left:-9999px;top:0;width:320px;height:1400px;border:0;';
  iframe.src = location.href + '?mobilecheck=' + Date.now();
  document.body.appendChild(iframe);
  await Promise.race([
    new Promise(resolve => iframe.onload = resolve),
    new Promise(resolve => setTimeout(resolve, 3000))
  ]);
  await new Promise(resolve => setTimeout(resolve, 500));
  const w = iframe.contentWindow;
  const d = iframe.contentDocument;
  const component = d.querySelector('.map-locator');
  const labels = Array.from(d.querySelectorAll('.map-locator text')).map(n => n.textContent.trim());
  const r = component.getBoundingClientRect();
  const out = {
    innerWidth: w.innerWidth,
    clientWidth: d.documentElement.clientWidth,
    scrollWidth: d.documentElement.scrollWidth,
    overflow: d.documentElement.scrollWidth - w.innerWidth,
    labels,
    component: { width: r.width, height: r.height, left: r.left, right: r.right }
  };
  iframe.remove();
  return out;
})()
```

Adapt selectors and required labels to the component under review.

## Pitfalls

- Do not let old approvals on previous heads count after a human follow-up comment or fix commit.
- A comment-only blocker can still be merge-blocking when the stale comment misstates a source-of-truth or safety contract; fix docs/comments if they would mislead the next builder.
- Browser/CLI screenshot geometry can be misleading on macOS/headless contexts. Trust `scrollWidth`, bounding boxes, and DOM labels for deterministic layout facts; use screenshots for visual sanity, not as the only proof.
- A collapsed, account-level review summary is not per-lane evidence. When one account carries more than one lane, judge each artifact by its declared role, verdict, and exact head.
