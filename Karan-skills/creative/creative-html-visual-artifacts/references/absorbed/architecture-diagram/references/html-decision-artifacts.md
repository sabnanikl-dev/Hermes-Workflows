# Visual HTML decision artifacts

Use this when a planning/report/review artifact should be more useful as HTML than Markdown — especially for Karan's substantial plans, reports, reviews, design explorations, client/internal explainers, and automation architecture docs.

## Core lesson

A strong HTML artifact should not just be a prettier Markdown document. It should become a decision + execution interface:

- spatial structure that is hard to express in Markdown;
- visual hierarchy for fast scanning;
- diagrams and cards that reduce mental load;
- audience-specific views;
- copy/export blocks that feed Linear, GitHub, PRs, SOPs, or builder handoffs.

## Recommended V2 structure

1. Hero with artifact status and source IDs.
2. Sticky decision/navigation bar.
3. "What needs approval first" cards near the top.
4. Executive summary with before/after mental model.
5. Parent/child issue map.
6. Interactive SVG/process diagram with detail panels.
7. Audience tabs, e.g. owner/client, Karan/operator, builder, reviewer.
8. Inputs/outputs and backend/data model.
9. Visual roadmap/timeline.
10. Risk register with severity styling and guardrails.
11. Tools/secrets/access table.
12. Option comparison matrix.
13. Non-goals wall.
14. Copy/export blocks for tracker comments, builder handoff, reviewer checklist, SOP starter.
15. Definition of done and artifact metadata footer.

## Interaction patterns

- SVG steps can use `data-step` attributes and JS to reveal matching detail panels.
- Audience tabs should swap content without hiding the artifact's main decision path.
- Copy buttons should read text from adjacent `<pre>` blocks and use `navigator.clipboard.writeText`.
- Keep interactions lightweight and self-contained; avoid frameworks unless the project already uses one.

## CSS/layout pitfalls

- Roadmaps with fixed many-column grids can clip on desktop. Prefer `repeat(auto-fit, minmax(210px, 1fr))` unless horizontal scrolling is intentionally signposted.
- Export/code blocks often look clipped if `pre` keeps long lines. For prose exports, use `white-space: pre-wrap; overflow-x: hidden`.
- Dense SVG diagrams are okay on desktop, but add a mobile HTML-card fallback or reading-order list.
- If using a sticky bar, verify it does not cover important diagram labels while scrolling.

## Verification pattern

1. Parse HTML with Python `html.parser`.
2. Assert key strings/classes exist: decision bar, approval cards, interactive SVG markers, tabs, exports, roadmap, risk register, non-goals.
3. Serve through local HTTP, not `file://`, for JS/assets behavior.
4. Use browser snapshot/console to verify tab and diagram-click behavior.
5. Use browser vision to catch layout issues like clipped roadmaps or export blocks.
6. Stop the local server.
