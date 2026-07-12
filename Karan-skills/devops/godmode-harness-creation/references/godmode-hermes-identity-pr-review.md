# GodMode Hermes Identity PR Review Notes

Use these notes when reviewing GodMode UI/dashboard PRs that reference QuadWork/tmux inspiration.

## Core judgment

The layout may be inspired by QuadWork/tmux, but the visual identity should read as **GodMode by Hermes**, not a QuadWork clone or generic neon terminal dashboard.

Approve the general split-pane/operator cockpit layout when it preserves:
- dense multi-pane agent workspace,
- harness chat/control surface,
- role-bound head/builder/reviewer panes,
- visible GitHub/PR/review-loop state,
- manual merge gate,
- local-first operator framing.

Push back when the styling feels like a direct QuadWork reskin or an undifferentiated green terminal UI.

## Hermes aesthetic cues

Prefer:
- electric cobalt / ultramarine as the primary brand accent,
- white/ink contrast and deep navy/black surfaces,
- green used mainly as a status/success color, not the dominant brand color,
- small cyan/magenta glitch accents,
- Hermes/messenger motifs: wing-like linework, motion trails, angular geometry,
- cyber-classical mood: precise, intelligent, slightly mythic,
- subtle engraved/circuit/line-art texture rather than only rectangular neon borders.

Avoid:
- obvious QuadWork color/layout mimicry beyond the broad split-pane workflow,
- generic Matrix-green terminal dashboard styling,
- copy that keeps saying QuadWork once the design is meant to stand on its own,
- static UI facts that look verified when they are mock/demo state.

## Review comments that worked

Useful phrasing:

> Keep the split-pane cockpit layout — it is working. The follow-up should make the surface feel like GodMode by Hermes rather than a QuadWork reskin.

> Use QuadWork as workflow/layout inspiration only. Brand separation should come from palette, motifs, copy, iconography, and decorative system.

> Cobalt/ultramarine should carry the brand; green should become status-only.

## Follow-up verification checklist

When re-reviewing after a design-direction comment:
1. Confirm new commits appear on the PR.
2. Re-read `AGENTS.md` / `docs/spec.md` if workflow rules changed.
3. Inspect the changed renderer files.
4. Run `npm run build`.
5. Load the dev UI and visually check:
   - brand feel is Hermes-distinct,
   - mock/demo state is labeled,
   - hardcoded local paths are gone or clearly placeholders,
   - short-window clipping/overlap does not hide important controls.
6. Post a re-review comment with: verdict, verified items, what improved, remaining follow-ups.
