# External Evidence Packet Exact-Byte Audit

Use this recipe for read-only audits of paid-provider or third-party evidence packets containing frozen requests, raw responses, normalized rows, reports, and a hash manifest.

## 1. Freeze and independently bind every byte

- Compute SHA-256 for the report, normalized artifact, generator, and manifest.
- Parse the manifest and independently re-hash every listed file; reconcile entry count, per-file bytes, and total bytes.
- Treat older packets and review hashes as superseded. Never combine findings from different byte sets.
- Confirm the proposed packet excludes unrelated untracked files.

A manifest that hashes correctly is necessary but not sufficient: it proves byte identity, not semantic truth.

## 2. Reconstruct semantics without trusting the normalizer

Build an independent verifier from the frozen requests and raw provider responses:

- **Grid observations:** derive query, geography from the frozen coordinate map, device/OS, provider status, result count, cost, exact identity match, and provider-returned rank.
- **Search observations:** derive query, requested location, used location, normalized geography, observed coordinates, device/language/country, local-pack presence, visible count, answer surfaces, organic presence, and business presence.
- **Review observations:** derive target identity, requested geography, rating, review count, newest/oldest sample timestamps, sample depth, replies, and recurrence from raw grid identities.
- Compare expected and normalized records field-by-field and report every mismatch. Also assert cross-row variation: distinct raw locations must remain distinct after normalization.

Do not merely check that fields are nonempty. A plausible repeated default can satisfy schema checks while falsifying provenance.

## 3. Prove identity across provider representations

Google and other providers may expose different identifiers on different surfaces, such as a `ChIJ...` Place ID on Maps and a decimal CID on Search.

- Freeze the exact canonical identifier for each provider surface.
- Match only the provider's canonical identifier; do not fall back to title substrings.
- Run three adversarial controls through the real matcher:
  1. correct ID with a changed title must pass;
  2. wrong ID with the expected title must fail;
  3. missing ID with the expected title must fail.

Current rows being correct does not cure an unsound identity guard.

## 4. Reconcile spend and provider incidents

- Recompute spend from raw settled task costs, including recovery tasks.
- Reconcile the total against the final provider balance when available.
- Distinguish uncharged contract/input failures from charged observations; preserve statuses such as `No Search Results` rather than converting them to ordinary rank absence.
- Record provider incidents, retry/failover behavior, and cost effects separately.

## 5. Judge unavailable fields honestly

A benchmark should disclose unavailable attributes, services/products, post recency, landing-page analysis, or similar fields rather than infer them.

Do not automatically make every unavailable field a blocker. Read the governing contract as a whole:

- Block when the field is indispensable to the decision or explicitly requires successful capture.
- Accept an explicit unavailable disclosure when the contract permits unavailable evidence or safe alternatives, the bounded packet still answers the decision, no extra spend is authorized, and the report does not infer the missing value.
- State the limitation and route any future collection through a separately approved packet.

## 6. Evaluate callback locators at the real boundary

Callback/webhook URLs in immutable raw evidence require contextual severity, not reflexive rewriting:

- Count every raw/request file containing the locator.
- Verify the report and normalized/public surfaces do not expose it.
- Verify repository/storage visibility and intended audience.
- Verify the endpoint is deleted, expired, or otherwise no longer a live capability using direct readback where possible.
- Preserve original raw provider bytes when immutability is part of the evidence contract; do not silently redact or rewrite them.

A dead locator confined to private immutable raw evidence is normally advisory, with a rule to redact/exclude before broader distribution. A live capability, public exposure, or secret-bearing normalized/report surface is blocking.

## 7. Prove deterministic relocation

A same-directory rerun is not enough. Copy the complete manifest packet to a randomly named temporary root and run the generator there.

Require:

- successful execution;
- exact report and normalized hashes;
- repo-relative evidence locators inside rendered artifacts;
- no dependency on the original checkout's absolute path.

Absolute paths printed only in transient stdout are acceptable if they do not alter artifact bytes or handoff locators.

## 8. Close claims and routing

- Map every material conclusion, limitation, recommendation, and hypothesis to concrete evidence IDs—not just table rows.
- Verify the report separates provider surfaces and avoids timeless rank, market-share, and historical-causation claims.
- Verify downstream routing preserves authority: synthesis, monitoring, and approval-gated mutation lanes must remain distinct.
- Record explicit `mutationsPerformed: []` or equivalent and corroborate with repository/remote state where relevant.
- Return a prior-blocker closure table, one-line proof for every acceptance gate, residual advisories, and an exact final marker such as `DONE: STATUS=pass P0=0 P1=0 P2=1`.
