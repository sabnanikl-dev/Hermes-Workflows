# Human visual-reference alignment in PR prover loops

Use when Karan attaches a visual reference after an automated review loop has already gone green and says the PR is **not merge-ready**.

## Durable lesson

Automated zero-blocker reviews and green checks do not satisfy a human visual contract. A chat or PR comment like “not merge ready, align with this” is a live human blocker. Treat it as a new current-head PR contract, not as optional polish.

## Recommended sequence

1. **Acknowledge the blocker by action, not prose.** Do not repeat “merge-ready.” Post a concise PR comment that turns the reference into an actionable contract.
2. **Transcribe the reference into spatial/design requirements.** For map/card/location widgets, capture relative placement: major roads, landmark positions, labels, highlighted areas, pin placement, colors, and no-go constraints.
3. **Scope the fix to the visual-alignment blocker.** Existing guardrails stay; the work stays on the existing PR branch; the reference contract, not a redesign, is the acceptance bar.
4. **Expect a long quiet stretch.** A builder lane can print nothing for 10+ minutes while editing and testing. Judge it by worktree, diff, and head evidence rather than by silence, and do not redo work that already produced a valid commit.
5. **Verify three ways before reporting back:**
   - deterministic checks: required labels/tokens present; forbidden geo/embed/dependency tokens absent; source-of-truth/ARIA contract intact;
   - browser geometry: local HTTP server plus `browser_console` 320-ish iframe probe for `scrollWidth <= innerWidth`, bounding box, and expected DOM/SVG labels;
   - visual proof: side-by-side reference/current screenshot plus mobile screenshot.
6. **Aim the new head's review at the reference.** The review lanes should compare the new exact head to the human reference contract and to the static safety guardrails above, not only to the diff.
7. **Final wording:** do not say “human-approved” or “merge-ready” until Karan visually signs off. Say “technical/reviewer checks are clean; waiting on your visual approval.”

## Static mini-map checklist

For decorative location maps based on a screenshot reference:

- Keep it static inline SVG; no map tiles, embeds, network map SDKs, or runtime dependencies.
- Keep `aria-hidden` and preserve semantic address/directions/call text as the authoritative source of truth.
- Do not add exact coordinates, lat/lon, `GeoCoordinates`, or JSON-LD `geo` unless explicitly approved.
- Use only real, verified labels from the reference/PR contract; no invented streets or businesses.
- Prove mobile no-overflow with an iframe/viewport probe, not just by eyeballing.

## Proof artifact pattern

Create two user-facing images when taste approval is the blocker:

- side-by-side **reference vs current PR component** screenshot;
- phone-width/mobile screenshot with JSON/DOM proof showing current head, labels, `innerWidth`, `scrollWidth`, overflow, and component bounds.

This makes Karan’s visual QA fast and prevents Hermes from prematurely declaring merge readiness after automated checks pass.
