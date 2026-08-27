---
name: generated-artifact-proofing
description: "Prove generated HTML, PDF, reports, SOPs, and other derived artifacts across producer/consumer schema seams, privacy boundaries, unknown-state behavior, fixture provenance, responsive semantics, print completeness, and exact-head parity."
version: 1.4.2
author: Hermes Agent
metadata:
  hermes:
    tags: [generated-artifacts, reports, pdf, html, security, responsive, verification]
    related_skills: [autonomous-pr-prover, integration-audit-review, artifact-output-governance, web-application-qa]
---

# Generated Artifact Proofing

## Purpose

Use this skill when code generates an owner-facing or operator-facing artifact such as:

- HTML run reports or dashboards;
- printable SOPs and handoff packets;
- PDFs or browser-print exports;
- generated samples committed to a repository;
- automation summaries transformed into human-readable output;
- public-safe versus operator/internal report modes.

The goal is not merely to prove that generation exits `0`. It is to prove that the artifact faithfully represents the real producer data, remains safe under adversarial input, handles unknown state honestly, preserves meaning at mobile/print boundaries, and matches the exact code head under review.

Load this alongside `autonomous-pr-prover` for an existing PR, `integration-audit-review` for cross-surface auditing, and `artifact-output-governance` when deciding where evidence should live.

## Core Invariants

1. **Test the real seam.** At least one regression probe must feed the consumer the actual producer-shaped payload—not only a hand-authored convenience schema.
2. **Safe by construction.** Owner/public-safe modes need an allowlisted projection or centralized redaction boundary over every rendered field. HTML escaping is not secrecy.
3. **Unknown stays unknown.** Missing fields must render `N/A`/unknown or fail validation; they must not silently become success, zero, or “guard did not fire.”
4. **One fixture, one truth.** A sample attributed to a real execution must represent one coherent source-backed run. Synthetic samples must be labeled synthetic and must not borrow real execution identity.
5. **Responsive meaning, not only fit.** No-overflow screenshots are insufficient when mobile tables lose column meaning.
6. **Print content, not only pages.** A nonblank PDF does not prove required content printed; closed disclosure widgets may output headings without bodies.
7. **Head-bound evidence with bounded inheritance.** Tests and reviewer verdicts bind to the final immutable head. Generated artifacts/screenshots/PDFs may be preserved across a later harmless head change only when the complete controlling input set is proven byte-identical, the shipped binder still passes, and the packet names the original evidence head instead of calling the artifact newly captured.
8. **Failure closure.** Every producer failure class—including discovery, normalization, and planning before item-routing—must reconcile from aggregate counts into an attributable row or an explicit non-file failure class. `failed > 0` plus “no failures recorded” is a blocker.
9. **Never invent attribution.** If a failed item’s reason is missing or invalid, do not decrement an arbitrary nonzero reason merely to make totals reconcile. Preserve planned versus applied values separately, carry the authoritative reason, or mark attribution unknown/fail closed.
10. **Independent probes outrank test volume.** A large green validator count is not proof of risk-model completeness. Final review must derive and execute at least one adversarial case not named by the builder.
11. **Screenshot claims require image evidence.** Head-bearing stdout that says screenshots were captured proves neither image existence nor visual evidence. A deterministic proof fixture must produce and validate a real head-bound image/manifest, and an arbitrary-success-text mutation must fail.
12. **Diff-derived inventories require location-level closure.** For owner-facing copy-review artifacts, reconcile the multiset of reader-facing unified-diff edit-run locations against unique artifact-card locations; displayed totals and DOM-card counts alone do not prove completeness or exact-once representation.
13. **Interactive review state must be portable and semantically explicit.** Browser-local persistence is not a file handoff. If checkboxes represent owner decisions, state what checked and unchecked mean, provide a self-contained export that embeds those decisions, and prove restoration from the exported file in isolated browser storage.

## Procedure

### 1. Inventory the surfaces

Record:

- producer and its exact emitted schema;
- adapter/normalizer, if any;
- generator/template;
- owner-safe and operator/internal modes;
- fixtures and committed generated samples;
- responsive breakpoints and print styles;
- docs/SOP claims about current operational state;
- repo validation/build scripts.

Treat workflow JSON, automation code, schema docs, fixtures, generator, samples, README/SOP, and PR claims as one contract family.

#### Bind negative-source claims to captured evidence

A report may say that no change, incident, definition update, or historical event was found only when the searched source corpus is reconstructable. Require an immutable locator or captured artifact for each source-specific negative claim such as “the captured changelog documents no change.” A metric-definition page is not interchangeable with a changelog, and cautious qualifiers such as “not ruled out” do not cure invented provenance. If no captured search artifact exists, narrow the statement to what the available evidence directly supports—for example, differentiated series behavior may argue against a whole-pipeline loss while leaving a component-specific reporting change untested.

For fresh-session reconstruction, verify both directions:

- every cited evidence artifact exists and hashes to the claimed identity;
- every source-specific factual clause can be traced to one of those artifacts rather than merely sounding compatible with the conclusion.

#### Protect exact candidate bytes during review

Hash the candidate before running any generator, validator, or helper. Determine whether each command is a read-only binder or a producer that rewrites timestamps, generated reports, evidence sidecars, or status readbacks. Run producers only in a disposable copy/designated evidence worktree unless regeneration is explicitly in scope. After every command that could write, re-hash the candidate and inspect worktree changes before continuing.

If a review command causes incidental churn in the canonical checkout, restore only review-induced paths without touching pre-existing user changes, reconstruct the exact candidate bytes when necessary, and require the original digest before issuing the verdict. A validator exit `0` is not enough if the command changed the artifact under review. See `references/negative-claim-provenance-and-review-byte-preservation.md` for the claim matrix and recovery sequence.

### 2. Run a producer-shaped probe

Extract or reconstruct representative payloads in the producer’s actual shape. Feed them directly to the consumer and verify that required identity, counts, reasons, failures, guards, and timestamps survive.

A required field being nonempty is not proof that its provenance survived. For every safety- or decision-bearing normalized field, independently derive the expected value from the raw request/response and compare semantic equality row by row. Pay special attention to fields that legitimately vary across a panel—geography, requested/used location, coordinates, query, device, method, and timestamp—because a hardcoded plausible default can make every schema assertion pass while falsifying most observations. Include a cross-row variation probe: when raw rows contain multiple distinct values, normalized rows must preserve the corresponding distinctions rather than collapse them to one repeated label. Treat semantic provenance mismatches as blockers when the governing contract requires accurate per-observation evidence.

Do not stop at the post-routing collectors. Enumerate and execute every real failure-producing stage: discovery/listing, normalization, planning, import/create, update/restore, archive, and guard/abort. Reconcile aggregate failure counts against detailed rows or an explicitly rendered non-file failure class. A flat producer feeding a nested-only consumer is a blocker even when nested fixture tests pass; so is a producer that counts planning failures but omits them from `runtimeFailures` or the equivalent detail surface.

For reasoned totals, test missing, invalid, duplicated, and unattributed failure reasons with multiple nonzero planned buckets. Never use fixed-precedence decrementing to manufacture a successful-reason breakdown. Carry the authoritative reason, separate planned from applied totals, or mark attribution unknown/fail closed. Fix with a deterministic normalizer or align the schemas; retain regression fixtures that execute the actual committed producer code.

### 3. Run the privacy/adversarial matrix

Inject sensitive values into every owner-visible dynamic surface and syntax shape:

- bearer/API-token-like strings;
- unquoted assignments such as `token=private-value`;
- quoted/nested/escaped JSON such as `{"access_token":"private-value"}`;
- raw folder, file, workflow, credential, and execution IDs at whitespace, dotted, slashed, colon-, query-, bracket-, and hyphen boundaries;
- email addresses and customer-like PII;
- phone formats including parenthesized, dashed, spaced, and international forms;
- URL credentials and sensitive query parameters;
- filenames containing PII, opaque IDs, URLs, traversal, or secret-like labels;
- status/environment/trigger badges, headings, labels, names, errors, recommended actions, and link text.

Verify owner-safe output contains none of them while operator mode preserves only intentional diagnostics. Test an execution ID with no explicitly safe display label. The final leak scan should be independent of the normal scrubber; calling the same detector twice proves self-consistency, not coverage. Keep direct raw-marker assertions for representative values. Parse operator links before interpolation and allow only intended schemes/hosts without embedded credentials.

### 4. Run unknown/inconsistent-state probes

Render `{}` and strategically partial payloads. Verify missing fields remain unknown. Add contradictory combinations relevant to the domain, including success plus failures, success plus a fired guard, arbitrary status strings, negative/fractional/string reason counts, compensated-negative totals, count/detail mismatches, and impossible chronology.

### 5. Prove fixture provenance

For each committed sample:

- classify it as source-backed or synthetic;
- verify identity and counts come from one coherent run;
- enforce `generatedAt >= runTimestamp`;
- enforce domain count invariants;
- regenerate and compare hashes or require a clean worktree.

### 6. Prove responsive semantics

Capture the required viewports and inspect failure/guard/archive states, not only the happy path. For stacked tables, preserve a visible or assistive label for each cell, commonly with `data-label` plus a mobile pseudo-label.

Use DOM geometry checks for overflow/clipping, but also visually inspect hierarchy and field meaning. Before capturing a component or below-fold section, stabilize overlays through the artifact's real public controls. If a consent panel, coachmark, drawer, or sticky prompt obscures the target, capture that control separately when it is in scope, then dismiss/decline it through its documented UI and recapture the target. Never delete the overlay from the DOM or claim that clean geometry proves readable pixels: an element can have a valid box and zero page overflow while the screenshot is visibly covered.

For intentionally fixed-canvas HTML diagrams, do not let a flex parent shrink the sheet while inner pixel grids remain fixed: give the canvas an explicit non-shrinking basis/minimum width, then run the geometry probe at both native and narrow viewports. A native-width screenshot can look perfect while the reusable HTML silently clips its rightmost lane behind `overflow:hidden`.

### 7. Prove interactive review-state portability

For HTML artifacts with checkboxes, approvals, filters, or other mutable controls, define the decision semantics before testing. “Reviewed” is not interchangeable with “approved”; if unchecked can mean either rejected or not-yet-reviewed, use a three-state control.

Do not treat `localStorage` as a portable save. Provide a self-contained export that embeds sorted decision IDs, synchronizes live checkbox properties to literal HTML attributes, removes transient filter-hidden state, and supports both mobile file sharing and download fallback. When replacing a report already in use, retain its versioned storage key, have the user compare recovered counts in the same browser, and keep the old tab open until the exported copy is verified.

Exercise the export in a real browser: select representative early/middle/late items, download the artifact, inspect its embedded state, then reopen it in a fresh context with empty storage and verify the same decisions and counts. See `references/portable-interactive-review-state.md` for the implementation and migration recipe.

### 8. Prove print completeness

Generate the PDF using the target browser engine. Then:

1. confirm it is nonblank and has plausible pages;
2. visually inspect representative pages;
3. extract PDF text;
4. assert every required SOP/operator section body appears, not only its heading;
5. verify closed `<details>` or accordion content is exposed in print, or render a dedicated print-safe representation.

Keep deterministic DOM/text assertions in the repo when practical, but independently recapture the PDF on the final head.

### 9. Integrate current main and close parity

Inspect divergence and semantic conflicts before final proof. When package/build manifests conflict, preserve both current-main validation coverage and the feature’s new commands. Run the complete integrated suite and require clean/hash parity.

Recapture artifacts on the final head when any controlling input changed. For a later checker/docs-only repair, preserve prior browser/PDF/report evidence only after proving the complete controlling path set is byte-identical, rerunning the shipped binder, recording the original evidence head, and freezing a new current-head packet with the narrow delta. See `references/evidence-inheritance-across-harmless-head-changes.md`.

## Proof Packet

Include:

- exact head/base SHAs;
- producer-shaped input and expected mapped fields;
- adversarial and empty/partial probe results;
- fixture provenance/chronology result;
- test/build commands and exits;
- generated artifact parity result;
- mobile screenshots and geometry/label findings;
- interactive-state semantics, exported-file path, embedded decision IDs/counts, and isolated-storage restoration result;
- PDF path, page count, visual findings, and text-completeness assertions;
- unresolved blocker classes.

For reusable checklists and probe recipes:

- `references/report-sop-proof-matrix.md` — baseline report/SOP proof matrix and sample assertions.
- `references/failure-path-integrity-and-privacy-boundaries.md` — aggregate-to-detail failure closure, real producer-stage probes, fail-closed reason attribution, quoted JSON/phone/composite-ID privacy cases, and independent-review rules.
- `references/deterministic-visual-evidence-fixtures.md` — non-vacuous screenshot fixtures: real head-bound image files/manifests, format and dimension checks, missing/invalid/wrong-head negatives, and the arbitrary-success-text mutation probe.
- `references/fixed-canvas-html-blueprint-proof.md` — source-grounded engineering blueprint structure, fixed-canvas flex-shrink prevention, native-width Playwright capture, narrow-viewport DOM geometry checks, and PNG+HTML delivery verification.
- `references/exact-head-copy-review-reports.md` — exact-revision public-copy diff extraction, contiguous edit-run/card multiset accounting, surface-aware text-fidelity checks, qualifier decision hotspots, interaction/privacy probes, read-only in-memory print proof, and returned owner-decision packet ingestion with approved-item no-drift handling.
- `references/portable-interactive-review-state.md` — explicit decision semantics, local-state migration, self-contained HTML export via embedded IDs and synchronized checkbox attributes, mobile share/download fallback, and isolated-storage reopen verification.
- `references/evidence-inheritance-across-harmless-head-changes.md` — preserve expensive artifacts across checker/docs-only head changes by proving the complete controlling inputs are byte-identical, retaining original-head provenance, and freezing a fresh current-head packet.
- `references/external-evidence-packet-exact-byte-audit.md` — independently re-hash manifests, reconstruct raw/frozen provider semantics, prove cross-provider identity and geography, reconcile spend/incidents, assess dead callback locators at the actual privacy boundary, and reproduce artifacts after relocation.
- `references/negative-claim-provenance-and-review-byte-preservation.md` — require reconstructable source corpora for “no change found” claims, distinguish binders from mutating producers, and recover exact candidate bytes after incidental review churn without erasing pre-existing work.

## Pitfalls

- Treating fixture-specific secret scans as a general privacy boundary.
- Calling HTML escaping “redaction.”
- Letting absent booleans default to favorable states.
- Combining a real execution ID with counts from a later readback.
- Checking only page-level horizontal overflow at mobile widths.
- Hiding table headers without adding cell labels.
- Treating a nonblank PDF or page count as proof of print completeness.
- Trusting CSS source inspection when the browser’s print engine behaves differently.
- Running the old branch test command after a semantic conflict instead of the complete current-main suite.
- Reusing screenshots/PDFs after a head change without proving every controlling product/runtime/style/fixture/producer input is byte-identical, rerunning the binder, and retaining the original evidence-head provenance.
- Treating a high validator/check count as proof that the adversarial model is complete.
- Claiming that a captured changelog, incident history, or deployment ledger showed no relevant change when only a current definition/status page is preserved; source-type mismatch is invented provenance even when the conclusion is hedged.
- Running tracked browser/evidence producers in the canonical review checkout without immediately diffing or restoring their timestamp-, ordering-, JSON-, or screenshot churn. Producers belong in a disposable/designated evidence worktree; binders belong in read-only exact-head gates. If behavior-controlling bytes changed, intentionally regenerate and commit/rebind the artifacts. If they did not, restore producer churn before reviewer launch and do not call the output byte-reproducible merely because the binder passes.
- Testing only post-routing failures while normalization/planning failures contribute to aggregate counts but disappear from detailed rows.
- Making archive totals reconcile by decrementing the first nonzero reason when the failed item’s reason is absent or invalid.
- Scanning only whitespace-delimited or unquoted secret forms while quoted JSON, escaped values, composite IDs, or parenthesized phone PII survive.
- Calling browser-local checkbox persistence a saved handoff when the original HTML does not contain the live choices.
- Serializing `outerHTML` without synchronizing checkbox `checked` attributes or clearing transient filter-hidden classes.
- Using ambiguous “Reviewed” checkboxes when the owner needs explicit approve/reject semantics.

## Stop Conditions

Stop and classify the artifact as blocked when:

- actual producer data loses required fields;
- aggregate failure counts cannot be reconciled to attributable detail rows or an explicit non-file failure class;
- reason attribution is fabricated or depends on input/order precedence rather than source evidence;
- owner-safe adversarial input leaks secrets/PII/raw IDs;
- missing data renders a favorable invented state;
- source-backed fixture provenance is inconsistent;
- mobile output loses field meaning;
- print output omits required section bodies;
- current-main integration cannot preserve both validation surfaces;
- evidence is tied to a stale head.
