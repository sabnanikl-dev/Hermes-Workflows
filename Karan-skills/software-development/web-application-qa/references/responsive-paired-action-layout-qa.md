# Responsive paired-action layout QA

Use this when the product contract explicitly requires two related actions to remain in one row at supported mobile and desktop widths. Do not apply it automatically: stacking can be the better mobile design unless the human/product contract says otherwise.

## Why wrapping flex rows regress

A wrapping flex container can look like one row at wide widths but silently stack when long labels plus button padding exceed the available content column. A screenshot at one desktop width does not prove the contract.

For a strict two-column contract, prefer:

```css
.paired-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--existing-gap-token);
}

.paired-actions > .action {
  min-width: 0;
  white-space: normal;
  text-align: center;
}
```

`minmax(0, 1fr)` lets both tracks shrink below their intrinsic text width. `min-width: 0` and `white-space: normal` make labels wrap *inside* the buttons instead of forcing the second control onto another row or creating overflow. Preserve the project’s existing button min-height/tap-target rule.

## Deterministic browser assertions

At minimum test 375, 768, and 1440 CSS-pixel widths. For each width, open a real enabled state without navigating the external actions and assert:

1. Exactly two expected actions are visible and labels are readable.
2. Their top and bottom coordinates match within a small rendering tolerance (for example 2px): this proves one row rather than merely `display:grid` in source.
3. The first action is left of the second and their rectangles do not overlap.
4. Both rectangles stay inside the dialog/container bounds.
5. Each action preserves the project tap-target minimum (commonly 44–48px).
6. `document.documentElement.scrollWidth - clientWidth <= 1`.
7. A non-enabled control model renders no item-level actions, preventing leakage.
8. URL/target/rel assertions inspect attributes only; do not click consequential external destinations during layout QA.

Add a fast source-level contract guard when the CSS rule is critical, but keep real geometry assertions as the authority. Mutation-check the guard once: temporarily restore the wrapping layout and verify the narrow-width “not stacked” assertion fails.

## Evidence

Capture fresh exact-head desktop and mobile screenshots showing the affected dialog/component—not only the surrounding page or PR status. Pair screenshots with geometry output because screenshots alone do not prove all supported widths or overflow bounds.
