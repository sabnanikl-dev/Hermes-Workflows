---
name: brand-website-from-inspiration
description: Build a complete branded HTML website from inspiration site reference and brand guidelines. Uses vision AI to analyze design inspiration, then creates production-ready HTML with brand colors, typography, and layout.
version: 1.0.0
category: creative
---

# Build Branded Website from Inspiration

Use when a client wants a website and has provided an inspiration URL + brand guidelines.

## Umbrella Scope: Inspiration-Driven Website Builds

This skill now covers both multi-section branded sites and single-page landing pages built from an inspiration URL. Treat `single-page-website-from-inspiration` as an absorbed subsection rather than a separate trigger: first analyze the inspiration site's layout, color blocking, typography, section rhythm, and UX patterns; then map those patterns onto the client's exact brand assets and guidelines.

Single-page landing page specifics:
- Build a complete responsive HTML/CSS deliverable, not a loose mockup.
- Preserve brand accuracy over copying the inspiration site literally.
- Use local HTTP preview for SVG/images; `file://` can hide SVG-loading problems.
- For problematic SVG logos, inspect and tighten the `viewBox` around actual path bounds.
- Batch visual feedback into coherent design passes instead of micro-adjusting one CSS value at a time.

Full historical notes are preserved in `references/single-page-website-from-inspiration.md`.

## Steps

### 1. Analyze Inspiration Site
Navigate to the inspiration URL, then use `browser_vision()` to capture:
- Color palette and section backgrounds
- Typography style (serif, sans-serif, script combinations)
- Layout structure (hero, cards, testimonials, footer)
- Navigation style and CTA placement
- Visual hierarchy and whitespace usage
- Special elements (image carousels, color blocks, animations)

### 2. Extract Brand Assets
If the user has brand files locally:
- Find the color palette (use vision AI if it's an image)
- Note logo files, brand guidelines PDFs
- Get the brand voice/tone profile

### 3. Create Project Structure
```
~/projects/{business-name}/website/
  index.html
```

For multi-page sites, create separate HTML files.

### 4. Build Single-Page Website
Create a complete HTML file with:
- **CSS Variables** for brand colors (named clearly)
- **Google Fonts** for brand typography
- **Semantic HTML** (nav, main, sections, footer)
- **Responsive design** with mobile breakpoints
- **Smooth scroll** and hover animations
- **Brand voice** in all copy
- **Placeholder images** with clear labels like `[ Photo ]`

### 5. Review with Vision AI
Open the file in browser (`file:///path/to/index.html`), use `browser_vision()` to verify:
- Colors match brand palette
- Typography is properly applied
- Layout flows well on all sections
- All sections are visible and properly structured

## Brand Integration

### Color Mapping
Map brand hex codes to CSS variables:
```css
:root {
  --brand-primary: #7f165b;
  --brand-secondary: #ddadbc;
  --brand-background: #fdf8ea;
  --brand-text: #3f0d2a;
}
```

### Typography Choices
- **Logo/Headlines**: Elegant serif (Playfair Display, Cormorant Garamond)
- **Body Text**: Clean sans-serif (Lato, Montserrat)
- **Accents**: Script font if needed (Parisienne for coquette aesthetic)

### Copy Guidelines
- Match the brand voice profile (casual-polished, warm-creative, etc.)
- Use brand-appropriate language in CTAs and descriptions
- Include real client examples if available

## Pitfalls
- Image placeholders are expected — client will swap in real photos later
- Single-page is best for initial builds — multi-page can be added later
- Keep it responsive from the start — test both desktop and mobile views
- Use `browser_vision()` to verify the final output matches expectations