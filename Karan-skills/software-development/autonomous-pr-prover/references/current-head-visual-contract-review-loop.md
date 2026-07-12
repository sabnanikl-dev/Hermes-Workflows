# Current-head visual contract review loop

Use this reference when an already-open static/site PR gets a human visual-contract follow-up mid-review (for example: “make this map/card/layout true to the actual source, not generic”).

## Pattern that worked

1. Treat the human PR comment as a live blocking contract surface even if the PR was previously approved.
2. Send the change back through the builder lane with a pointer-first prompt to read the live PR comments/reviews.
3. Preserve prior accepted fixes explicitly in the builder prompt (for example: no visible TODO copy, no mobile overflow regression, no geo/coordinate claims).
4. Require both deterministic suite verification and a targeted contract probe:
   - required labels/content present;
   - no forbidden claims/metadata introduced;
   - layout invariant preserved (for example `scrollWidth <= innerWidth` at 320px).
5. If the local worktree does not have Playwright/Chrome available, do not stop at a static text check when Hermes browser tools are available. Start a local HTTP server and use `browser_console` to inject a 320px iframe, then read `documentElement.scrollWidth`, map/component bounding boxes, and DOM/SVG text labels from inside the iframe.
6. Pair the DOM probe with visual inspection (`browser_vision`) for changed visual components. For anchored sections, scroll the target into view and offset for sticky nav; if an anchor capture is misleading, use a taller full-page/section view plus DOM assertions.
7. Re-run A/B reviewers on the new current head. If a broad re-review times out after doing useful reads but does not emit a final marker, rerun a narrower targeted re-review that only inspects the previous blocker and the new diff. Do not count a timed-out reviewer as a pass.
8. Post reviewer artifacts under the reviewer identity on GitHub for the current head. Same-account approval limitations may mean one lane comments and another approves; what matters is current-head artifacts with explicit `DONE: STATUS=pass BLOCKING=0 HEAD=<sha>` markers.
9. Re-query the PR after posting reviews. Confirm remote head equals local head, checks are green, review decision is approved, review threads are empty, and the human blocking comment has a later fix/comment response.

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
- If `reviewDecision` remains `CHANGES_REQUESTED` after a fix, check whether a current-head approving/comment review exists under the reviewer identity; post/obtain a current-head approval where permissions allow, then re-query the PR.
