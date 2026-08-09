# Semantic visual gates for generated artifacts

Use this pattern when a PR produces HTML reports, dashboards, PDFs, or other rendered artifacts and file-existence/screenshot checks can false-pass over missing semantics.

## Contract

A useful semantic visual gate proves four different things:

1. **Binding:** every artifact and the manifest name the full reviewed head.
2. **Structure:** PNGs decode at their declared dimensions; PDFs are non-empty and parseable.
3. **Semantics:** the rendered/exported surface contains the required meaning, not merely source CSS or hidden DOM.
4. **Retention:** evidence survives a failed semantic verdict so the builder and operator can inspect what failed.

## Render-first, fail-late procedure

1. Verify `git rev-parse HEAD` equals the full expected SHA.
2. Regenerate committed samples with the repository-native command before rendering. Generation must be byte-identical on a clean reviewed head; otherwise the normal worktree-contamination guard should fail.
3. Create a collision-free evidence directory **outside** the reviewed worktree, scoped by run ID, full head, timestamp, and process/nonce.
4. Render every required state at every required width (for example mobile/tablet/desktop) and generate the required print/PDF format.
5. Finish collecting artifacts and writing their hashes before returning a semantic failure. Distinguish semantic failure from infrastructure failure with separate exit codes/messages.
6. Write a machine-readable report and manifest containing full head, artifact paths, byte sizes, hashes, dimensions, each assertion, and the complete error list.

## Assertions that bite

### Print/PDF meaning

Extract text from the **PDF itself** and assert required operator-detail body fragments there. Searching the HTML or seeing a valid PDF header is insufficient: closed disclosure bodies and print CSS can disappear from the actual export while the file remains structurally valid.

Prefer several small named assertions (environment instructions, credential purpose, recent-execution checks, paused response, failure response, rotation procedure) over one vague “text present” check. Run them against every required report state.

### Collapsed mobile tables

If responsive CSS hides `<thead>`, every required data column must retain a visible or assistive field label. Record one measured label per required column and fail when:

- the expected table or header set is missing;
- row width differs from the header width;
- a collapsed cell has no `data-label`/`aria-label` (or equivalent measured accessible name);
- the label does not match its header.

If headers remain visible at mobile width, record that fact explicitly instead of demanding redundant labels.

### Small operational text contrast

Recompute WCAG contrast from the actual foreground token/value and every real background used by each small-text selector. Record selector, resolved colors, ratios, and minimum. Screenshots are useful sanity evidence but cannot prove the numeric ratio. Do not globally ban a brand color: constrain the selectors/sizes where it acts as text, allowing the same color to remain decorative elsewhere.

## Required negative proof

Before trusting a new gate, run it against a known-bad fixture/head where:

- all expected PNGs and PDFs are present and structurally valid;
- print bodies are absent, mobile labels are missing, or contrast is below the threshold;
- the gate exits nonzero and names the failed semantic assertions.

This proves the gate judges meaning rather than file existence.

## Orchestration consequence

In `pr-prover`, any baseline/visual finding skips Reviewer A/B/Integration for that head. The blocker may still go to the builder, but only if the historical-feedback barrier is clear. Preflight retained feedback before an expensive render run, and report accurately when the outcome is “gates failed, reviewers skipped, feedback prevented attempt 1.”

## Pitfalls

- Do not write screenshots/PDFs into the reviewed worktree.
- Do not stop at source inspection for print semantics.
- Do not infer mobile accessibility from a screenshot alone.
- Do not return on the first semantic defect before preserving the evidence set.
- Do not treat structurally valid artifacts as semantic pass.
- Do not reuse a prior-head manifest after any push.
