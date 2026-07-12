# Mobile carousel smooth-scroll control QA

Use this reference when QAing mobile card carousels with both native swipe/scroll and prev/next buttons.

## Durable lesson

A carousel can pass normal one-click navigation but still feel broken when repeated button taps happen during an in-progress smooth scroll. If button handlers compute the next target from the instantaneous physical `scrollLeft`, rapid taps can be swallowed because the scroll position has not advanced yet.

## Reproduction pattern

1. Serve or open the target page in a mobile-width viewport, e.g. `390x844`.
2. Navigate to a middle card using the right/next button.
3. Press the left/previous button several times at normal quick human speed, without waiting for the smooth animation to finish.
4. Compare intended taps vs final active/centered card.
5. Repeat with native swipe/scroll and verify button disabled states resync after manual scrolling.

## Evidence to capture

For each state, capture:

- viewport width/height;
- `scrollLeft`, `clientWidth`, `scrollWidth`;
- active/nearest card index;
- prev/next disabled states;
- whether controls are hidden;
- whether cards use centered or start `scroll-snap-align`.

Example failure signature:

```text
at_index_2: nearestIndex=2, prevDisabled=false
immediate_after_prev_1: nearestIndex=2
immediate_after_prev_2_50ms: nearestIndex=2
immediate_after_prev_3_100ms: nearestIndex=2
after_1s: nearestIndex=1
```

Interpretation: several repeated previous-button taps from the middle only produced one card of movement after the smooth scroll settled.

## Likely implementation fix to suggest in issues

Prefer an intended/active card index for button navigation:

- update the intended index immediately on button click;
- scroll to the intended card;
- sync the index back from native swipe/manual scroll after `scrollend` or a debounced scroll settle;
- keep `prefers-reduced-motion` behavior intact;
- keep native swipe first-class rather than replacing it with click-only navigation.
