# Deterministic visual-evidence fixtures

Use this when a CLI/orchestrator PR claims to prove browser or screenshot evidence without itself changing a rendered UI.

## False-positive pattern

A fixture that scripts `captured 3 screenshots for <head>` and asserts only successful exit, an expected-head substring, and argv/worktree binding proves execution and head binding—but **not screenshot evidence**. Replace the message with arbitrary head-bearing text as a mutation probe. If the test still passes, the screenshot-evidence claim is vacuous.

## Minimum non-vacuous fixture

Keep the repair fixture-local unless the product contract separately requires production artifact storage.

1. Have the deterministic visual-gate double create one or more valid image files outside its disposable lane worktree.
2. Emit or create a manifest binding each image to the full head SHA, viewport/dimensions, path, and content hash when practical.
3. Validate with standard-library probes where possible: existence/non-empty, recognized image signature, declared dimensions, exact-head association, and evidence-path lifetime outside a checkout that will be removed.
4. Add negative cases for missing image, invalid/truncated image, and wrong-head manifest.
5. Re-run the arbitrary-success-text mutation and require it to fail.

A tiny deterministic PNG is sufficient for a proof fixture. Do not add Pillow, Playwright, a browser service, production screenshot storage, changed-file inference, or a generalized artifact subsystem unless the governing contract explicitly requires them.

## Claim discipline

Keep these separate:

- **gate selection/head binding** — the command ran at the expected head;
- **evidence retention** — output or a manifest survived into the result;
- **screenshot evidence** — a valid head-bound image artifact was produced and validated;
- **human visual approval** — a human inspected the rendered result.

README, PR-body, and proof-map language must not collapse one into another. Recompute executable test counts and remove stale limitations after a fixture repair.
