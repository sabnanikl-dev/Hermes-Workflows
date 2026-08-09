# Fixed-canvas HTML blueprint proof

Use this when delivering a one-page engineering schematic or infographic as standalone HTML plus a rendered PNG.

## Grounding

1. Inspect the live source and exact candidate head before drawing. For a PR blueprint, derive the flow from the changed execution seams—not from a test/status summary alone.
2. Lead with one plain-English sentence, then show inputs, trust boundaries, ordered execution, fail-closed exits, before/after behavior, proof metrics, and explicit out-of-scope boundaries.
3. Prefer module/function labels on nodes when they help reconnect the schematic to code. Keep repair history subordinate to the architecture unless the user asks for a repair ledger.

## Fixed-canvas hazard

A fixed-width sheet inside a flex body can shrink while pixel-based inner grids do not. If the sheet also uses `overflow:hidden`, right-hand lanes silently disappear on normal browser widths even though a native-width screenshot looks correct.

For a deliberately fixed blueprint, make the canvas non-shrinking:

```css
body { display:flex; justify-content:center; }
.sheet {
  flex:0 0 1800px;
  width:1800px;
  min-width:1800px;
  overflow:hidden;
}
```

Horizontal scrolling on narrow screens is safer than clipping. If responsive behavior is required, replace fixed inner tracks with proportional ones and verify each breakpoint instead.

## Render and proof recipe

1. Serve the artifact directory over HTTP on a verified free port; do not assume a familiar port belongs to this artifact.
2. Capture at or above canvas width. If Playwright is present but its bundled Chromium is absent and system Chrome is installed, use the verified fallback:

```bash
npx playwright screenshot --channel chrome \
  --viewport-size="1900,2650" --full-page \
  "http://127.0.0.1:<port>/<artifact>.html" \
  "/absolute/path/<artifact>.png"
```

3. Inspect the final PNG for header/subtitle overflow, missing side lanes, unclear arrow continuity, panel/footer collisions, empty cards, and copy that is only legible at unrealistic zoom.
4. Pair image inspection with DOM geometry. At minimum prove the rightmost lane and footer stay inside the sheet and the intended node count exists:

```js
const sheet = document.querySelector('.sheet').getBoundingClientRect();
const rightmost = document.querySelector('.lanes aside').getBoundingClientRect();
const footer = document.querySelector('footer').getBoundingClientRect();
({
  rightLaneInside: rightmost.right <= sheet.right,
  footerInside: footer.bottom <= sheet.bottom,
  nodes: document.querySelectorAll('.node').length
})
```

Run the geometry probe at a narrow viewport too. A wide PNG cannot reveal reusable-HTML flex shrink.
5. Check browser console errors, final PNG dimensions/size, and HTML existence. Stop the temporary server.
6. Deliver the PNG for immediate viewing and the standalone HTML for zooming, printing, or future edits.

## Pitfalls

- Browser-tool screenshots often show only the current narrow viewport; do not treat that crop as the full fixed canvas.
- Increasing header height can push the footer beyond a fixed sheet. Recalculate the vertical budget or enlarge the canvas, then verify footer geometry.
- `overflow:hidden` hides layout mistakes; it is not evidence that content fits.
- A transport/test summary is not sufficient architecture grounding. Read the live PR and changed source seams first.
