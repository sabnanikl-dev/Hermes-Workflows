# Conditional CTA Follow-up Browser QA

Use this when a frontend PR intentionally hides model/item-level external actions behind an evidence gate, and the human asks why expected buttons are missing or asks to enable them.

## First classify the observation

Missing buttons are not automatically a visual bug. Read the exact current-head browser action artifact, enablement authority/allowlist, and evidence record:

- If the enabled action map is empty or the selected item lacks an authority row, explain that the UI is failing closed.
- Distinguish the collection-level/global CTA from item-level actions.
- State the exact policy: for example, Customize + Order across desktop + mobile may require a complete 2×2 pass matrix.
- Do not silently change “render neither action when disabled” into disabled placeholders. That is a product-policy change and needs a human decision.

Offer a bounded choice: keep hidden, show non-clickable placeholders, test one selected item, or run a catalog-scale batch. Recommend one-item QA first when the user is reacting to one visible model.

## Safe targeted QA sequence

1. Verify the PR/current head and clean primary worktree.
2. Create a detached exact-head scratch worktree. This prevents the committed canonical evidence and already-approved PR from being overwritten by a diagnostic run.
3. Install the pinned dependencies/browser engine in the scratch worktree.
4. Run the **committed producer**, not an HTTP probe or hand-authored evidence. Typical shape:

   ```bash
   node scripts/browser-qa-custom-shoes.mjs \
     --source=docs/content/custom-shoes-candidates.json \
     --models=<MODEL_ID> \
     --concurrency=1 \
     --retries=2 \
     --force
   ```

5. Preserve GET-and-observe-only boundaries: never click actions, submit forms, log in, order, pay, create accounts, or send customer data.
6. Run the committed offline validator against the generated evidence.
7. Read back the selected item’s exact destination × viewport records, timestamps, methods, failure reasons, and summary eligibility.

`--models` selects work; it must not shrink the full declared candidate universe. The resulting checkpoint may contain one terminal model and hundreds of pending models while remaining validator-consumable.

## Decision rule

- **All required slots pass:** the item is evidence-eligible, not automatically enabled. Send the live evidence through the builder lane for a deliberate authority/allowlist edit and generated browser-action update. Verify exact URL pairing, host, labels, `target`, `rel`, and disclosure. Push verification and current-head A/B re-review are mandatory because visible/actionable frontend behavior changed.
- **Any required slot fails or remains pending:** do not enable either item-level action when the policy requires the complete matrix. A passing Order pair does not override a failing Customize pair. Report exact observed outcomes and keep the UI hidden/fail-closed.

If the item is absent from the enablement authority, passing evidence still requires a reviewed new authority row; candidate metadata alone never grants browser action authority.

## Regression design pitfalls

### Treat the model action tuple atomically

The browser-side guard must preserve the same complete-matrix policy as the evidence gate. Do not validate and append Customize and Order independently: a malformed/off-host/missing-label Customize member plus a valid Order member must render **neither** action, not an Order-only partial state.

Exercise both malformed-member directions for every scoped model:

- invalid Customize + valid Order → `[]`
- valid Customize + invalid Order → `[]`
- missing label on either member → `[]`
- HTTP/off-host/look-alike host on either member → `[]`
- exact approved pair → exactly two actions in the required order

Assert the complete rendered array (`length === 0` or the exact two-member tuple). Avoid weak checks such as `every(kind !== "customize")`, which pass vacuously for an empty array and can hide incorrect behavior.

### Injected clocks must reject non-finite values

Deterministic freshness tests may add an optional evaluation clock to gate helpers. Treat it as an API boundary and fail closed:

- Omitted clock → production `Date.now()` behavior.
- Supplied clock → require `Number.isFinite(now)` before calculating age.
- `NaN`, `Infinity`, `-Infinity`, invalid timestamps, stale timestamps, and future timestamps must not enable actions or validate evidence.
- Add invalid-clock negatives to every freshness path (for example action generation and evidence validation), not only the happy-path fixture.

JavaScript pitfall: `typeof NaN === "number"`; comparisons against `NaN` are false, so `typeof now === "number" ? now : Date.now()` can silently bypass both stale and future checks.

## Evidence and cleanup

For a failed diagnostic run that should not broaden an already-approved PR:

1. Save an audit copy outside the worktree if useful.
2. Restore the scratch evidence file.
3. Remove the scratch worktree.
4. Re-read the original PR head/review decision and confirm it remained unchanged.
5. Do not launch builder or reviewer cycles when the condition “enable only if all slots pass” evaluated false.

For a passing run, commit only the deliberate evidence/authority/action changes, synchronize PR body and docs with the new enabled state, refresh exact-head screenshots showing the actual buttons, and then rerun both reviewers.