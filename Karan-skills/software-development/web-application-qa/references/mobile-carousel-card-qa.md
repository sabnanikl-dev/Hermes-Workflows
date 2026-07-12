# Mobile carousel/card QA checklist

Use this when a web QA task includes mobile carousels, snap-scroll cards, service/package cards, timeline/process carousels, testimonial sliders, or any horizontally scrollable card row.

## Why this exists
A carousel can pass basic functional checks while still failing visual QA. In one Femme Events audit, the services carousel dots and CTA routing worked, but the longest `The Full Femme` service card clipped the top of its bullet list. A separate `What Happens Next` carousel had unintended vertical scroll because its horizontal scroll container also had vertical overflow.

## Required checks

1. Test every slide/card, not just the first one or one representative slide.
   - Navigate via dots/buttons.
   - Swipe/scroll horizontally if possible.
   - Inspect the longest-content card separately.

2. Check internal clipping inside each card.
   - Confirm the first visible content is not above the card top.
   - Confirm the last visible content/CTA is not below the card bottom.
   - Bounding-box rule of thumb: child top >= card top and child bottom <= card bottom.

3. Check vertical gesture containment on mobile.
   - A horizontal carousel should not have internal vertical scroll unless intentionally designed.
   - Probe `scrollHeight > clientHeight` and try a vertical wheel/touch gesture over the carousel.
   - If the carousel gets `scrollTop > 0`, file it as a mobile carousel bug.

4. Check CTA visibility and tapability per slide.
   - Buttons should remain visible and tappable after swiping/dot navigation.
   - Verify the longest card still shows its CTA.

5. Check animation side effects.
   - Entry animations like `initial={{ y: 30 }}` can create extra scroll height inside horizontal containers.
   - Tailwind `overflow-x-auto` may compute `overflow-y` as auto/scroll; explicitly test vertical overflow.

6. For centered snap carousels, verify navigation math, not only initial centering.
   - A first card can be visually centered while `Next` still re-selects card 0 if the JS compares `scrollLeft` to card left offsets from an older start-aligned design.
   - Measure active cards using the same anchor as CSS: center deltas for `scroll-snap-align: center`, left deltas for `scroll-snap-align: start`.
   - Required smoke: at narrow mobile widths (e.g. 320 and 390), first card center delta ≈ 0, no document overflow, initial Prev disabled / Next enabled, Next moves active card 0 → 1, and Prev moves 1 → 0.
   - If desktop/tablet intentionally uses start snapping, test the breakpoint boundary too (e.g. 699/700): the wider-screen reset must win in the cascade, with track gutters and `scroll-padding` reset after later mobile-first base rules.

## Evidence to collect
- Screenshot at the exact slide state, not only a full-page screenshot.
- Bounding-box measurements for card rect and first/last children.
- Carousel container measurements: `clientHeight`, `scrollHeight`, `scrollTop`, `overflowX`, `overflowY`.
- Source files/components likely responsible.

## Common recommended fixes
- For centered mobile cards, use symmetric inline gutters and `scroll-snap-align: center`; keep card width viewport-based but bounded (for example, `calc(100vw - <gutter>)` with a max width).
- Update carousel controls to scroll by the current card's center when snap alignment is centered; use start offsets only when computed `scroll-snap-align` is start.
- Put desktop/tablet reset rules after the mobile-first carousel base rules, or otherwise ensure the wider media query wins in cascade order.
- Use `overflow-x-auto overflow-y-hidden` for horizontal-only mobile carousels.
- Remove/reduce vertical `y` animations on mobile carousel children.
- Increase card height or switch to content-aware/min-height for long cards.
- Compact spacing/type for the longest card.
- Move full detail content into an expandable/modal detail view while keeping card summaries concise.
