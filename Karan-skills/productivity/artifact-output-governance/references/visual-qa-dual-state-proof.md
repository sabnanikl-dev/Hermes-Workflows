# Dual-state visual proof for human QA

Use this recipe when a frontend change needs human visual or copy approval and the changed surface is below the fold or obscured by ordinary first-visit UI such as a consent dialog.

## Evidence contract

Produce both states from the same exact reviewed revision:

1. **Default-state full page** — preserve what a first-time visitor actually sees, including consent/banner chrome.
2. **Focused review state** — dismiss only non-destructive local chrome, scroll the changed element into a stable visible position, and capture one viewport image at every required responsive width.

Never alter source code, persistence defaults, production data, or live configuration just to make the focused screenshot prettier. Label the focused state explicitly, such as `Consent dismissed only for focused view`. Label local renders as local/preview evidence rather than production.

## Capture sequence

1. Prove local checkout = remote branch = live PR head; require a clean source worktree.
2. Serve that exact checkout over local HTTP, never `file://`.
3. Capture full-page default-state images at the material widths, commonly 375, 768, and 1440 pixels.
4. In a fresh page for each width:
   - dismiss only the local consent/banner control;
   - locate the changed element by stable selector or exact expected text;
   - call `scrollIntoView({block: 'center', inline: 'nearest'})`;
   - wait briefly for layout to settle;
   - capture the viewport, not another full page.
5. Record compact DOM evidence:
   - expected text/state is present;
   - rejected text/state is absent;
   - target bounding box is non-zero and inside the viewport;
   - `document.documentElement.scrollWidth === clientWidth`;
   - console errors and page errors are empty.
6. Store final images outside disposable worktrees so chat attachments survive cleanup.

## Presentation

- Build a labeled responsive comparison sheet from the focused captures for fast scanning.
- Preserve native viewport pixels when practical; avoid shrinking mobile text into illegibility.
- Include exact revision, local/preview provenance, viewport labels, and any dismissed-state note in the sheet.
- Visually inspect the sheet itself for clipping, overlap, unreadable labels, and misleading scaling.
- Keep and deliver the individual focused and full-page images for zooming; the sheet is an index, not a substitute.
- On media-capable chat platforms, attach each artifact through the real media mechanism (for example one `MEDIA:/absolute/path.png` line per file). A prose path list is not delivery.

## Failure modes

- **One full-page screenshot only:** the changed text is too small or hidden by first-visit chrome.
- **Focused screenshot only:** it conceals the authentic first-visit experience.
- **Consent dismissed without a label:** the evidence implies a state visitors do not initially see.
- **Successful screenshot command treated as proof:** blank, cropped, or placeholder-filled images escape review.
- **Contact sheet only:** the reviewer cannot zoom the original pixels.
