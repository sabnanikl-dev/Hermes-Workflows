# Exact-head static screenshot bundle

Use this when a user asks for visual proof of a static frontend PR across responsive widths.

## Workflow

1. Verify the local checkout SHA equals the live PR `headRefOid` and the worktree is clean.
2. Serve the exact worktree over local HTTP; never capture through `file://`.
3. Store final evidence outside the disposable worktree, e.g.:
   `~/projects/pr-work/<repo>-evidence/issue-<n>-pr<pr>/`
4. If Playwright is not installed in the repo but `npx playwright` is available, use the system Chrome channel without modifying project dependencies:

```bash
npx --yes playwright screenshot \
  --channel chrome \
  --viewport-size '375,900' \
  --wait-for-selector 'h1' \
  --wait-for-timeout 500 \
  --full-page \
  http://127.0.0.1:<port>/<route>/ \
  "$EVIDENCE/pr<pr>-<shortsha>-mobile-375.png"
```

Repeat for the issue-required widths (commonly `375`, `768`, and `1440`). Prefer explicit viewport sizes over raw Chrome `--window-size`, which can misrepresent the layout viewport on macOS.

5. Verify every PNG before delivery:
   - file exists and size is non-zero;
   - pixel dimensions match the requested viewport width;
   - image is not blank (pixel extrema/mean are useful mechanical checks);
   - visually inspect for crop, clipping, overlap, broken assets, CTA wrapping, spacing, and footer completeness.
6. When several long full-page captures exist, create a labeled comparison sheet for fast scanning, but keep the individual full-resolution PNGs. Give each column enough fixed label width; narrow mobile thumbnails can make labels overlap if columns shrink to image width.
7. Stop the preview server and verify the port is clear. Keep the stable evidence directory; remove only scratch harness files.
8. Deliver the contact sheet and each individual image with separate `MEDIA:` lines. Label them as local renders from the exact PR head, not production screenshots.

## Interaction proof

The screenshot CLI captures the default state. For menus, accordions, carousels, or focus behavior, pair screenshots with browser/DOM assertions. If FAQ appearance matters, capture a deterministic state with one `<details>` item open and the rest closed.

## Pitfalls

- A successful screenshot command is not proof the image is usable; inspect the pixels.
- A full-page mobile image can be extremely tall. The comparison sheet is an overview, not a substitute for the full-resolution file.
- After any follow-up commit—even docs-only—refresh the exact-head proof before final A/B re-review if the workflow requires current-head evidence.
- Watch-pattern startup notifications may arrive after a server was already stopped. Verify process/port state before reacting or reporting a leak.
