<!-- Archived source skill consolidated into `brand-website-from-inspiration` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: single-page-website-from-inspiration
description: Build a complete, branded, responsive HTML landing page from a client's brand assets and an inspiration website URL. Uses vision to analyze the inspiration site's layout, color blocking, and typography, and maps it to the client's exact brand guidelines.
version: 1.0.0
author: Hermes
license: MIT
category: web-dev
---

# Build a Single-Page Website from Inspiration

Use this skill when you need to draft a production-ready HTML/CSS landing page based on a client's brand assets and a reference URL.

## Steps

1. **Analyze the inspiration site**:
   - Open the URL with `browser_navigate`.
   - Use `browser_vision` (with `annotate=true`) to capture the layout, color blocking, typography style, section rhythm, and UX patterns.
   - Scroll down and capture below-the-fold sections similarly.

2. **Extract brand assets**:
   - If the client provides logo images, use `vision_analyze` to confirm exact details.
   - If they provide a color palette image, extract the exact hex codes (e.g., `#ddadbc dusty rose`) and map them to clear CSS variables (e.g., `--dusty-rose`, `--deep-plum`).

3. **Set up project structure**:
   - Create a clean directory (e.g., `~/projects/<client>/website/`).
   - Copy logos and assets into the website folder for easy relative referencing.

4. **Draft `index.html`**:
   - Write a single, self-contained file with embedded `<style>` and minimal `<script>` at the bottom.
   - **CSS Variables**: Map the exact brand hex codes to `:root` variables.
   - **Typography**: Load appropriate Google Fonts (usually a serif for display/headings, sans-serif for body).
   - **Layout**: Mirror the inspiration site's structure (hero, color block, services, about, testimonials, CTA, footer).
   - **Images/Logos**: Use `<img>` tags with relative paths to the copied assets. 
     - *Warning*: `.svg` files often fail to render over the `file://` protocol. Prefer `.png` for local previews, or inline the raw `<svg>` directly into the HTML if it's small (<10KB).

6. **Review & QA**:
   - Open the file via a local HTTP server, not `file://`.
   - Use `browser_vision` to verify the visual output and ensure colors, spacing, and layout match the inspiration + brand.
   - If the user gives copy constraints such as forbidden brand names, banned terms, or punctuation rules, verify them mechanically with a script before finalizing. Example: scan the entire HTML for forbidden strings like `Papi`, `AI`, `—`, or `–`.
   - Check a narrow mobile viewport with Playwright or browser tooling, usually 390px wide, and verify `document.documentElement.scrollWidth <= innerWidth` so the mobile-first layout has no horizontal overflow.
   - Check browser console errors. Add an inline favicon if the only error is a missing `/favicon.ico`.
   - Offer a summary of deployed sections and what needs real content (photos, real copy).

## Key Pitfalls & Lessons Learned

### SVG files don't load reliably on `file://` protocol
SVG images often show as broken/paperclip icons when viewing HTML files directly from the local filesystem. **Always serve via a local HTTP server** (e.g., `python3 -m http.server 8000`). This also allows `browser_navigate` to load all assets correctly.

### SVG viewBox whitespace
SVGs exported from design tools (Figma, Canva, etc.) often have massive empty transparent space in their viewBox. The SVG may be 144 units tall but the actual text content is only 22 units — **85% wasted whitespace**. If a logo looks tiny or the nav bar feels too tall, check and crop the SVG viewBox:
```python
# Parse SVG path data to find actual content bounds, then set a tight viewBox
new_viewbox = "75.6 55.3 104.3 28.2"  # x y width height, cropped to text
```

### Design iteration through text is painful
Don't try to iterate on visual design by tweaking one CSS value at a time through text messages. Use the **Design Mode toolkit** (`design-mode-toolkit`) — drop `design-mode.js` into the site, press `Cmd+Shift+D`, and let the user drag sliders for real-time tweaks. This saves 8-12 rounds of "make it bigger/smaller" back-and-forth.

### Batch feedback beats micro-adjustments
When iterating, ask the user to: (1) sit with the page for 2-3 minutes, (2) use Design Mode to find values they like, (3) send all feedback in one message. You bake in the values and move on.

## Key Principles
- **Color mapping**: Always use the client's EXACT hex codes for accents, buttons, and backgrounds.
- **Generous whitespace**: Inspiration sites usually rely on padding, margins, and section dividers (color blocks).
- **Mobile-first responsiveness**: Use CSS Grid, Flexbox, and `clamp()` for fluid typography.
- **Always serve via HTTP, not file://**: `python3 -m http.server 8000` — avoids CORS, SVG rendering, and font loading issues.