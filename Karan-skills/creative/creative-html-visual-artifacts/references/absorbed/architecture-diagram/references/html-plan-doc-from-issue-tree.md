# HTML plan doc from parent issue + sub-issues

Use this pattern when the user asks for a full HTML plan/architecture document based on a tracker parent issue and its sub-issues.

## Context-gathering pattern

1. Load the project/client skill and tracker skill(s) first.
2. Reconstruct repo context if inside a harness: `git status`, `AGENTS.md`, `docs/spec.md`, recent log.
3. Read the parent tracker issue and child issues, not just local draft docs. Tracker state may supersede older local research.
4. Search local docs for prior research or source plans and reconcile differences explicitly.

## Document shape

Create one standalone `.html` file with inline CSS and SVG. For Karan-facing substantial planning/reporting artifacts, prefer the richer V2 decision-artifact shape in `references/html-decision-artifacts.md`, not just a pretty Markdown replacement.

Include:

- Hero/executive summary.
- Sticky decision/navigation bar when the artifact supports choices or execution.
- Near-top approval/decision cards.
- Before/after mental model when explaining a new operating model.
- Parent + sub-issue map.
- Step-by-step SVG process flow diagram near the top.
- Inputs and outputs.
- Audience-specific views/tabs when stakeholders differ (Karan, owners/client, builder, reviewer).
- Detailed workflow table.
- Tools needed.
- Backend/CMS/data-model section if the plan involves a content backend.
- Pros and cons/tradeoffs.
- Option comparison matrix when alternatives matter.
- Safety/guardrail section and risk register.
- Non-goals wall for scope control.
- Open decisions.
- Implementation sequence/timeline.
- Copy/export blocks for Linear/GitHub/PR/SOP handoff text.
- Definition of done.

## SVG diagram guidance

- Use lane/boundary boxes for layers: source/owner, automation/reconciliation, backend/CMS, website/output, safety/error path.
- Make the process readable as a left-to-right or top-to-bottom flow before adding detail.
- Use color semantics consistently and include a legend.
- Put the safety/error path in a visibly different color and label abort/no-mutation behavior.

## Verification

- Parse the HTML with Python `html.parser` or equivalent.
- Check required sections with string assertions.
- Serve locally with `python3 -m http.server` and open in browser.
- Use browser vision/snapshot to confirm the page renders, the SVG is visible, and there are no obvious layout problems.
- Stop the local server after verification.

## Pitfalls

- Do not rely on stale local planning docs if Linear/GitHub has newer acceptance criteria.
- Do not turn a planning artifact into live account/workflow changes; keep external mutations approval-gated.
- Avoid `MEDIA:` tags in CLI responses; report the absolute path plainly.
