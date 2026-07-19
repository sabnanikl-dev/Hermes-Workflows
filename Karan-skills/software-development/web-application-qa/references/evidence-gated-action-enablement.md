# Evidence-gated action enablement

Use this when item-level buttons or handoff links are hidden behind browser-QA evidence and a fresh audit shows the external destination now works.

## Source binding before enablement

Do not enable from a title match alone. Titles often repeat across a catalog.

For every candidate item, reconcile the owner-supplied source against the repo contracts using a compound identity:

- Stable model/item ID.
- Exact visible title.
- Exact approved Customize/deep-link URL.
- Exact approved Order/handoff URL.
- Parsed or decoded token/UUID relationship between those URLs when available.
- Presence of the matching ID/title in the rendered page/catalog source.

If the owner source lives outside the repo, stage only the minimal sanitized rows in an already-ignored agent input directory. Record non-secret provenance such as source count/hash, prohibit the builder from reading outside its worktree, and verify the staged input never enters Git history.

## Reclassify; do not force-enable

A diagnosis that the old evidence was wrong is not itself permission to flip a boolean. The committed producer must rerun every required destination × viewport slot and write fresh evidence.

Enable each item independently only when all of its required slots pass. Preserve the negative control: an unrelated/non-enabled item must remain actionless.

## Readiness and identity proof

For slow canvas/WebGL destinations:

1. Observe until a bounded positive-ready state, active terminal blocker, or timeout.
2. Require visible title/identity, visible non-zero canvas, flow-specific controls, approved token/UUID binding, and no active blocker.
3. Treat dormant hidden login/admin templates as inert markup, not a gate.
4. Treat WebGL as rendering technology, not an outcome.
5. Keep wrong token/UUID, repeated title without tuple proof, active login/consent, permanent loader, wrong identity, off-host/HTTP, malformed tuple, and timeout fixtures fail-closed.

## Contract cascade after evidence flips

When evidence changes from failed to passed, update every present-tense contract surface in the same PR:

- Browser-QA evidence artifact.
- Enablement authority/allowlist rows.
- Generated browser action artifact.
- Action-rendering tests across every scoped item.
- Non-enabled and cross-item leakage regressions.
- Specs, build plan, capture notes, friction logs, and PR verification summary.
- Desktop/mobile screenshots that visibly show the enabled buttons.

Preserve explicitly labeled historical notes, but do not leave stale present-tense language saying buttons are intentionally hidden.

## Verification gate

Before merge-ready:

- Local HEAD = remote branch = PR head.
- Full repo suite passes.
- Producer/classifier self-tests include slow success and terminal-negative cases.
- Browser UI tests prove exact labels, hrefs, `target`, `rel`, disclosure text, and no cross-dialog leakage.
- Visual proof shows the affected dialog at desktop and mobile.
- Reviewer A/B evaluate the new current head; old-head approvals do not count.
- No raw owner source or ignored staging input is committed.
