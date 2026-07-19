# Human design review after agent approval: restart the loop, then re-prove

Use this when Karan leaves a PR comment after the builder and A/B reviewers have already approved a frontend/UI PR.

## Lesson

A human PR review comment is new source-of-truth input, not a casual note and not merge approval. Even when the PR is already green/approved, treat Karan's visual/design comment as a requested revision unless the wording clearly says “merge”.

## Required workflow

1. Read all PR review surfaces again: conversation comments, formal reviews, inline comments, and review threads.
2. Classify the human comment:
   - **design/taste revision**: send to builder/fix lane, then visually QA and re-review.
   - **blocking correctness issue**: send to builder/fix lane and require targeted verification.
   - **merge approval**: only proceed if the wording explicitly approves merge and repo gates are still green.
3. Prompt the builder/fix lane with PR number, branch, issue number, and instruction to read the live PR comment directly. Do not paraphrase away the human’s visual intent; include the referenced URL/design direction when relevant.
4. After the fix commit lands, verify the PR head and rerun visual QA at the exact new head.
5. Rerun A/B reviewers on the new `headRefOid`. Prior approvals on the old head do not prove the new design/fix.
6. Read back current-head review objects and review threads before reporting merge readiness.

## Entry-point copy correction pattern

When the human removes a negative operational caveat from a teaser, feature block, card, or homepage entry point:

1. Preserve the approved positive proposition and CTA instead of replacing the removed caveat with a synonym. For example, keep “made to order” while removing stock/availability language entirely when that is the direction.
2. Scope the change to the named entry surface. Do not silently rewrite the destination page, catalog, FAQ, historical issue context, or another surface where fuller operational detail remains accurate.
3. Sweep all **present-tense current-state claims** that describe the changed surface: implementation, durable spec/docs, PR body, acceptance-criteria checklist, and signed fix summary. Do not leave metadata claiming the visible copy still contains the removed statement.
4. Preserve historical provenance only when clearly labeled as history; otherwise rewrite it as the new current state. Avoid repeating the unwanted customer-facing phrase in the visible implementation merely to explain its absence.
5. Add a focused rendered-text/DOM assertion for the exact entry surface: required positive wording present, CTA/destination intact, and the whole banned semantic family absent (for example stock, inventory, in-store availability, inspection). This is stronger than checking one exact deleted sentence.
6. Re-run responsive visual QA because shorter copy can change vertical balance, CTA spacing, and media alignment even when HTML/CSS are unchanged.
7. Push through current-head A/B re-review. Old approvals are stale after even a copy-only human design correction.

## Visual inspiration adaptation guardrails

When Karan references a visual inspiration component:

- Inspect the inspiration visually and extract mechanics, not code or brand styling.
- Preserve the target brand system; do not copy colors/framework/dependencies literally.
- For static sites, adapt with static HTML/CSS unless the issue explicitly authorizes runtime dependencies.
- Keep honesty constraints explicit: if exact location/coordinates are unverified, a “map” can be a stylized locator, but it must not invent street names, routes, landmarks, pins, or coordinates.
- Label only verified facts, and document why any remaining geometry is decorative.

## Responsive CSS pitfall from PR #158

`aspect-ratio` plus `min-height` can create an unintended intrinsic minimum width. Example:

```css
.map-locator {
  aspect-ratio: 5 / 4;
  min-height: 220px; /* implies 275px min width */
}
```

On a narrow mobile card, that minimum width can propagate up through a grid/flex item and create horizontal page overflow. Prefer width-driven sizing for decorative cards that must shrink:

```css
.map-locator {
  width: 100%;
  min-width: 0;
  aspect-ratio: 5 / 4;
}
```

Then verify at 320/360/375px with DOM measurements:

```js
{
  viewport: innerWidth,
  scrollWidth: document.documentElement.scrollWidth,
  overflow: document.documentElement.scrollWidth > innerWidth,
  locator: document.querySelector('.map-locator').getBoundingClientRect()
}
```

Also verify labels fit within the component bounds when the component is label-heavy.

## Good closeout evidence

- PR `headRefOid` matches local `HEAD`.
- `npm test` or repo canonical tests pass.
- Targeted DOM check proves no horizontal overflow at narrow mobile.
- Browser screenshot/render proof shows the changed component at the current head.
- A/B reviewers approve the current head after the human-requested change and any follow-up blocker fixes.
