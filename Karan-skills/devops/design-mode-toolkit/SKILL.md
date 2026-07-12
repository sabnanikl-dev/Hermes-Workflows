---
name: design-mode-toolkit
description: V5 in-browser design panel with global sliders + click-to-select element editing. Delta-only exports. Toggle with Cmd+Shift+D. Undo/redo/reset built in. Zero dependencies — drop into any HTML site.
tags: ["design", "html", "css", "website", "dev-tools", "frontend", "iteration"]
---

# Design Mode Toolkit v5

A reusable JavaScript panel that adds live CSS controls to **any** HTML website.

## Umbrella Scope: In-Browser Design Panels

This is the class-level skill for the reusable design-mode panel/toolkit pattern. The older `design-mode-panel` skill is absorbed here as implementation history: global sliders, click-to-select per-element editing, dirty/baseline tracking, delta-only exports, transform handling, and inline-style element adjustments all belong under this toolkit.

Keep the master implementation in a shared location such as `~/projects/_shared/design-mode.js`, copy it into the target site, load it before `</body>`, serve the site over HTTP, then use `Cmd+Shift+D` to toggle visual controls. Preserve full old implementation notes in `references/design-mode-panel.md`. Two modes:
1. **Global sliders** for site-wide values (fonts, spacing, logo sizes)
2. **Click any element** to get position/margin/size/padding controls for that specific element

## When to Use

- Iteratively adjusting visual design of an HTML website
- Getting precise feedback from non-technical users who want to "see it bigger" or "move it left" without guessing CSS values
- Fine-tuning spacing, font sizes, border radius, and individual element positioning
- Any site where the client wants visual control but you're building the code

## Setup

### 1. Drop the file in your project

Copy `design-mode.js` into the website's root directory.

### 2. Add to HTML

Add the script tag before your closing `</body>` tag:

```html
<script src="design-mode.js"></script>
<script>
  // Optional: Add a visible toggle button
  const dmBtn = document.createElement('div');
  dmBtn.innerHTML = '<button style="position:fixed;bottom:20px;right:20px;z-index:999999;background:#1a1a2e;color:#a0a0ff;border:2px solid #a0a0ff;border-radius:50%;width:44px;height:44px;font-size:18px;cursor:pointer;box-shadow:0 4px 15px rgba(0,0,0,0.3);" title="Toggle Design Mode (Cmd+Shift+D)">⚙</button>';
  document.body.appendChild(dmBtn);
  dmBtn.querySelector('button').addEventListener('click', () => {
    if (window.DesignMode) window.DesignMode.toggle();
  });
</script>
```

### 3. Serve via HTTP

Always use a local HTTP server, not `file://`:
```bash
cd your-website-folder
python3 -m http.server 8000
```

## Usage

**Toggle panel:** `Cmd+Shift+D` (Mac) / `Ctrl+Shift+D` (Windows), or the gear ⚙ button.

### Global Mode (always available)
Pre-defined sliders for nav logo size, hero heading, section padding, button sizes, etc.

### Element Selection Mode
1. Click the **"SELECT"** button in the panel header (turns red)
2. **Hover any element** on the page — blue outline shows selection target
3. **Click** — element gets orange highlight, element-specific controls appear below
4. Adjust position X/Y, margin, padding, width, height, font-size, border-radius, opacity, etc.
5. Press **Esc** or click "✕ Deselect" to exit

### Undo / Redo / Reset
- ↩ / ↪ buttons in panel header, or Cmd+Z / Cmd+Shift+Z
- **Reset** snaps everything back to the hardcoded defaults

## Adding Custom Global Controls

Edit the `CONTROLS` array at the top of `design-mode.js`:

```javascript
const CONTROLS = [
  {
    id: "my-control",         // Unique ID
    label: "My Control",       // Display label
    selector: ".my-element",   // CSS selector(s), comma-separated
    cssProp: "padding-top",    // CSS property (kebab-case)
    unit: "px",                // CSS unit
    defaultVal: 0,             // MUST match what's in the CSS
    min: -100, max: 200, step: 5  // Slider range
  },
  // ... more controls
];
```

**CRITICAL: `defaultVal` must exactly match the CSS value on the page.** If a slider's default doesn't match the coded value, the page "jumps" when Design Mode opens. This was the #1 bug — always verify defaultVal against the actual CSS.

## Per-Element Controls (Built-in)

The element mode auto-generates sliders for:
- Position X, Position Y
- Margin top/bottom/left/right
- Padding top/bottom/left/right
- Width, Height, Max Width
- Font Size, Line Height, Font Weight
- Letter Spacing, Word Spacing
- Text Align (dropdown)
- Opacity, Border Radius

No configuration needed — these work on any element.

## How It Works

**Global changes:** Inject a shared `<style>` tag with `!important` CSS rules matching each control's selector.

**Element changes:** Apply styles **directly via `element.style.setProperty(prop, val, 'important')`** (inline with `!important`). Never generate CSS selectors for individual elements — tried it, specificity conflicts are unavoidable.

**Baseline tracking:** When you select an element, `captureComputedValues()` reads every CSS property from `getComputedStyle()` and saves it as the baseline. Sliders start at these real values. The export only includes properties you actually dragged, not the baseline.

**Dirty tracking:** A `dirtyElements` map tracks exactly which props the user modified. The export only includes deltas — zero noise.

**Transform (Position X/Y):** Merge translateX and translateY into a single `transform: translate(tx, ty)`. Always set both together to avoid one overwriting the other.

**Undo/redo:** Snapshots are taken on slider `change` event (drag-end), NOT on `input` (every tick). Each drag = one undo step. Default debounce is 500ms for rapid adjustments.

## Export Workflow (Safe)

The **Export** button copies clean JSON — **not CSS** — to the clipboard. This JSON contains:

1. **Global deltas:** Only sliders that differ from their `defaultVal`
2. **Element deltas:** Only props the user actually dragged (tracked via `dirtyElements`)

Example output:
```json
{
  "type": "design-mode-export",
  "version": 5,
  "global": {
    "nav-logo-size": { "value": 58, "unit": "px", "property": "height", "selector": "nav .nav-logo img", "default": 42 }
  },
  "elements": {
    "ul.nav-links:eq1": {
      "selector": "nav > div.nav-container > ul.nav-links",
      "values": { "translateX": 200, "translateY": -10 }
    }
  }
}
```

**The agent applies changes by editing the actual source files**, not by injecting CSS overrides. This means:
- Source CSS is updated in-place
- No `!important` layers or overrides pile up
- `git checkout` can always revert
- The export is safe no matter how many times you use it

## Known Pitfalls

### defaultVal mismatches
If the page looks different when you open Design Mode, your `defaultVal` doesn't match the coded CSS. Check units (`px` vs `rem`) and numeric values carefully.

### Transform conflicts
If an element already has a `transform` in CSS (rotate, scale, etc.), setting `translate` via Design Mode will **overwrite** it. For elements with complex transforms (like the logo's `rotate(-3deg)`), handle specially or skip positioning.

### SVG viewBox issues
Navigation logos that use SVGs often have massive empty padding inside the SVG file. Fix the SVG `viewBox` first, then add a Design Mode slider for its height/width.

### file:// protocol
SVGs and some assets won't load via `file://` due to browser security. Always use `python3 -m http.server 8000`.

### Selecting wrong elements
In a dense layout, hovering might pick up a child element. Click deliberately on the visual target. The blue hover preview shows exactly what will be selected.

### Element-specific controls are ALL-capture, delta-export
When you select an element, `captureComputedValues` reads ALL properties (20+). But the export only shows what you changed. This is by design — the user sees real values from the start, but only sends deltas back.

## API

```javascript
window.DesignMode.toggle()    // Toggle panel open/closed
window.DesignMode.show()      // Open panel
window.DesignMode.hide()      // Close panel
window.DesignMode.addControl(ctrl)  // Add a global control at runtime
window.DesignMode.select(el)  // Programmatically select an element
```

## File Locations

- **Master copy:** `~/projects/_shared/design-mode.js` — this is the single source of truth
- **Project copies:** Drop into any website folder and reference via `<script src="design-mode.js">`
- For existing projects: `~/projects/femme-events/website/design-mode.js`

## Workflow for Client Iteration

1. Build initial HTML/CSS
2. Drop `design-mode.js` in, add script tag + gear button
3. Open in browser at `localhost`
4. Client uses sliders to adjust spacing, typography, positioning
5. Client selects individual elements to fine-tune placement
6. Export CSS or tell you values, bake them into code
7. Remove/hide Design Mode for production