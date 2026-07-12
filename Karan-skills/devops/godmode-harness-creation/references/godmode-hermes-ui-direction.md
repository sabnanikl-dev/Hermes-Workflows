# GodMode Hermes UI Direction

Use this reference when a GodMode dashboard/renderer PR risks looking like a direct clone of QuadWork or a generic neon terminal dashboard.

## Baseline judgment

- Keep the **dense split-pane operator cockpit**: role panes, harness chat, GitHub/PR state, run/review controls, and manual merge gate.
- Use QuadWork/tmux as **layout/workflow inspiration only**, not visual identity.
- The durable product feel should be **GodMode by Hermes**.

## Hermes visual cues

- Primary palette: cobalt/ultramarine blue with ink/white surfaces.
- Secondary accents: small magenta/cyan glitch accents.
- Green should be status-only (verified/pass/running), not the dominant brand accent.
- Motifs: wing-like linework, angular motion trails, etched/circuit strokes, cyber-classical geometry.
- Mood: precise, intelligent, local command cockpit; slightly mythic rather than generic Matrix-style terminal.

## Copy/labels

Prefer terms like:

- `Hermes command cockpit`
- `Agent workspace`
- `mock GitHub state` / `Demo Batch` until data-backed
- `<selected-project>` for project placeholders

Avoid:

- `Q` as the workspace identity
- unlabeled mock PR/issue/check data
- hardcoded local paths like `/Users/.../projects/godmode`
- implying GitHub/run success before real `gh`/git verification exists

## Review checklist

For UI PRs, verify:

- The layout still supports local, tmux-style human-in-loop operation.
- The visual system is distinct from QuadWork.
- Mock/demo state is explicitly labeled until live data replaces it.
- The manual merge gate remains visible.
- Role language stays role-first and BYOA-friendly.
- Short viewports do not cause footers/buttons to overlap issue/PR/blocker rows or clip controls behind the command bar.

## Issue update pattern

When a UI direction change lands in a PR, update open implementation issues with a concise `### UI direction from PR #N` section so future builders inherit the direction from GitHub issue source of truth, not just chat/PR comments. Tailor each issue's note to its scope, then re-query issues to verify the section landed everywhere intended.
