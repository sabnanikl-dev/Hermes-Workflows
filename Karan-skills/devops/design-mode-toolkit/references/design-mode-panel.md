<!-- Archived source skill consolidated into `design-mode-toolkit` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: design-mode-panel
description: In-browser design panel for visual CSS tweaking - global sliders + click-to-select per-element editing. Reusable across any HTML/CSS site.
version: 1.0.0
category: devops
---

# Design Mode Panel

An in-browser design panel (like Figma/Webflow lite) that lets users visually tweak CSS without touching code. Drop `design-mode.js` into any site.

## File Location

Master copy: `~/projects/_shared/design-mode.js`

For a new project, copy it into the site folder:
```bash
cp ~/projects/_shared/design-mode.js /path/to/site/design-mode.js
```

Load it in the HTML before `</body>`:
```html
<script src="design-mode.js"></script>
```

## Features

- **Toggle**: `Cmd+Shift+D` or click the gear icon
- **Global sliders**: Site-wide controls for logo sizes, fonts, spacing, buttons, grid gap
- **Click-to-select**: Hit "Select" button → hover highlights elements in blue → click to select
- **Per-element controls**: Position X/Y, margins, padding, width/height, font size, opacity, border radius, text align
- **Undo/Redo**: `Cmd+Z` / `Cmd+Shift+Z` or buttons in panel header
- **Reset**: All sliders snap back to coded defaults
- **Export**: Clean JSON of only-changed values (delta-only, no noise)

## How the Export Workflow Works

1. User adjusts sliders in Design Mode
2. Clicks "📋 Export Changes" → copies JSON to clipboard
3. Pastes JSON to the assistant
4. **The assistant edits the actual source HTML/CSS values** — never applies CSS overrides or `!important` layers

The export ONLY contains:
- Global sliders that differ from their default
- Element properties that were actually dragged (dirty tracking — no computed value noise)

## Key Implementation Details

### Baseline vs Dirty Tracking
When a user selects an element, `captureComputedValues(el)` reads all CSS properties via `getComputedStyle()` and stores them as the **baseline**. The `elemValues` mirror this baseline. Only when the user drags a slider does the value change and get flagged in `dirtyElements`. This keeps exports clean.

### Element-Level Changes Use Inline Styles
All per-element changes apply via `el.style.setProperty()` — they always win over the original CSS. No generating CSS rules that could be overridden.

### Transform Handling
Position X/Y combine into a single `transform: translate(tx, ty)` — the tool merges both values properly.

### Global Controls
Defined in the `CONTROLS` array at the top of the file. To customize per-site, edit the selectors, default values, ranges, and step sizes.

### Per-Element Controls
Defined in `ELEM_CONTROLS`. Uses `defFromStyle: true` to read computed values from the selected element.

## Common Fixes

| Problem | Fix |
|---------|-----|
| Element sliders start at zero | Make sure `captureComputedValues` reads `getComputedStyle(el)` values on select |
| Export is bloated with defaults | Use dirty tracking — only export properties flagged in `dirtyElements` |
| Position X/Y don't work | Generate `translate(tx, ty)` syntax, not `translateX = Npx` |
| Changes get overridden by CSS | Use `el.style.setProperty(prop, val, "important")` for inline overrides |
| Panel is empty on open | Every slider needs an explicit `defaultVal` — don't rely on auto-detection |

## Workflow with the Assistant

After the user exports JSON:
1. Parse the JSON to find changed values
2. For global changes: find the property in the source CSS and update the hardcoded value
3. For element changes: apply as clean CSS properties in the source file
4. Never layer CSS overrides — always modify the source

## Adding Custom Controls

```javascript
// From outside the script (after page load)
DesignMode.addGlobal({
  id: "custom-control",
  label: "Custom Label",
  selector: ".my-element",
  cssProp: "font-size",
  unit: "px",
  defaultVal: 16,
  min: 8,
  max: 72,
  step: 1
});
```