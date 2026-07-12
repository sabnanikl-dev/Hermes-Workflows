---
name: creative-html-visual-artifacts
description: "Use when producing browser-rendered visual artifacts: HTML mockups, diagrams, Excalidraw, p5.js/pretext sketches, DESIGN.md tokens, popular design-system recreations, and one-off visual prototypes."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [creative, html, diagrams, prototype, p5js, excalidraw, design]
    related_skills: [claude-design, local-web-preview]
---

# Creative HTML / Visual Artifacts

## Overview
This umbrella covers browser-rendered creative artifacts and design prototypes. Use it for one-off HTML reports, landing pages, visual diagrams, design tokens, Excalidraw JSON, p5.js/pretext sketches, and design-system-inspired mockups.

## When to Use
- Generate architecture/cloud/infra diagrams as HTML/SVG.
- Build throwaway or polished HTML mockups, reports, decks, or prototype pages.
- Produce Excalidraw-style diagrams or hand-drawn visual systems.
- Write p5.js or pretext generative/typographic sketches.
- Create or validate DESIGN.md token specs.
- Borrow patterns from known web design systems.

## Subworkflows

### Diagrams and Excalidraw
Start from the message's architecture/flow, choose the representation (SVG/HTML vs Excalidraw JSON), and verify the artifact renders locally.

### HTML mockups and reports
Make complete standalone files with inline CSS/JS unless the user asks for a framework. Use `local-web-preview` for realistic rendering and screenshot verification.

For research/report artifacts synthesized from repo dives, NotebookLM, or subagent findings:
1. Build a real standalone `.html` file with navigable sections, executive summary, evidence/caveats, and concrete next actions — not just prose dumped into HTML.
For research/report artifacts synthesized from repo dives or subagent findings:
1. Build a real standalone `.html` file with navigable sections, executive summary, evidence/caveats, and concrete next actions — not just prose dumped into HTML.
2. Verify the file exists and contains the required sections before previewing.
3. If direct `file://` browser navigation is blocked, serve the containing directory with a temporary local HTTP server and open `http://127.0.0.1:<port>/<file>`.
4. Run visual QA with a screenshot/browser vision pass for layout, legibility, cards/tables/diagrams, and responsive plausibility.
5. Check the browser console for JavaScript/render errors.
6. For high-stakes operational plans, use the iterative source-feedback + adversarial-review loop in `references/iterative-plan-artifact-review-loop.md`: send a compact plan summary back to source notebooks/research systems, patch the artifact, run separate adversarial reviewer lenses, patch again, then re-render/verify.
7. Stop the temporary preview server before final handoff.
8. In the final response, give the artifact path plus what was actually verified.

### p5.js / pretext sketches
Prefer single-file demos. Include controls only when useful. Verify in-browser rendering and animation behavior.

### Design tokens and design systems
For DESIGN.md, validate structure and token semantics. For popular design systems, copy principles, not copyrighted assets.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/`.

## Client-facing HTML slide decks delivered over chat
Use this pattern when the user asks for a polished standalone deck/report and wants the file sent directly in Telegram or another chat channel.

1. Build a single self-contained `.html` artifact unless the user explicitly asks for a framework or repo integration.
2. Embed required brand assets and approved real photos as data URIs when practical so the file travels cleanly without a folder of dependencies.
3. Include deck controls that work without external libraries: next/previous buttons, keyboard navigation, slide count, and print CSS.
4. Use real brand tokens and known client constraints from the relevant client skill; do not invent client claims or use stock/AI imagery when the client requires real assets.
5. For diagrams, favor visually clear layperson flows over technical completeness: named nodes, one-sentence purpose text, arrows, and owner-safe language.
6. Verify structure with deterministic checks: file exists, byte size, slide count, required topic terms, embedded asset count, keyboard/print CSS presence.
7. Render via local HTTP server when possible. If browser automation is unavailable on macOS, `qlmanage -t -s 1400 -o <preview-dir> <artifact.html>` is a useful thumbnail QA fallback; inspect it with vision for clipped text, legibility, logo rendering, and obvious layout issues.
8. If QA reveals clipping, fix layout immediately before final delivery: reduce hero font/logo size, tighten gaps, or add a cover-specific CSS override rather than shipping a visually broken first slide.
9. Stop any temporary preview server before final handoff.
10. Deliver the actual file using `MEDIA:/absolute/path/to/file` and briefly state what was verified.

## Verification Checklist
- [ ] Produce a real artifact file, not just a description.
- [ ] Render it in a browser/local preview when possible.
- [ ] Check visual requirements: layout, colors, responsive behavior, and legibility.
- [ ] For standalone decks/reports, verify slide/section count, embedded assets, navigation, and print CSS.
- [ ] Preserve any source package support files under `references/absorbed/` when consolidating.
