# Bounded paid local-visibility panels

Use this procedure for fixed-budget Maps, Search/local-pack, and review panels where provider calls consume credit.

## Execution contract

1. **Freeze before spending.** Save the exact query × geography × device matrix, competitor targets, request bodies, task counts, conservative estimates, and one aggregate ceiling. Keep request construction/budget validation separate from provider execution.
2. **Capture preflight state.** Save the relevant catalog records and `treg balance`. Treat catalog schemas, batching claims, and estimated prices as guidance—not proof of live behavior.
3. **Canary each live request class.** Run one representative Maps, Search, and review request before fan-out. Parse top-level and task-level status, message, result count, and cost. HTTP 200 or CLI exit 0 alone is not success.
4. **Preserve contract mismatches.** Keep uncharged 4xx responses as provenance, correct the request shape, and retry only the same frozen target. Do not silently broaden the panel or switch providers after a parameter error.
5. **Enforce the ceiling continuously.** Recompute cumulative settled spend after each component. Count all paid recovery calls. Registry reservations may temporarily differ from settlement; closeout uses provider-reported task costs plus final ledger readback.
6. **Keep raw and normalized layers separate.** Store immutable one-response-per-call JSON. Generate normalized rows with evidence ID, provider/endpoint, exact request location/device, timestamp, task status, result count/rank/surface, and settled cost.
7. **Recover async results safely.** If task submission is exposed but retrieval is not, and the provider supports callbacks, use a unique temporary private callback for the same approved targets. Save submission task IDs and exact result packets, count recovery settlement, then delete/de-authorize the callback and retain deletion evidence.
8. **Validate completeness deterministically.** Assert exact query × geography cardinality and uniqueness, expected Search-query set, expected review-target count, successful or explicit no-result state for every observation, component cost sums, and `actual_settled_spend <= approved_ceiling`.
9. **Run independent exact-hash acceptance.** Freeze the report and normalized evidence, compute hashes, and review causal claims, provider limitations, evidence linkage, cost math, authority boundaries, and user usefulness. Record acceptance in a sidecar rather than editing accepted bytes.

## Validated provider observations (2026-08-13)

Canary these again in future runs; they are observations, not timeless guarantees.

- DataForSEO Google Maps live advanced accepted the first task from a multi-task array while returning uncharged task-level 4xx errors for the remainder despite catalog batching language. One-task-per-call succeeded for the same frozen requests. Inspect every task in a batch.
- DataForSEO Google Reviews required a valid `location_name` alongside the supplied `place_id` in the observed contract. Omitting location failed uncharged.
- TREG exposed review task submission without the matching async result endpoint. Supplying DataForSEO `postback_url` on same-target recovery tasks returned exact result packets successfully. The recovery tasks' settlements remained part of the original aggregate ceiling.
- Live review-task settlement was lower than the conservative catalog estimate. Use catalog estimates for approval and live settled values only for closeout; never spend projected savings before the ledger confirms them.

## Interpretation boundaries

- Keep Maps rankings and Search surfaces separate; do not average them.
- Distinguish local pack, organic, answer/AI, rank absence, and provider `No Search Results`.
- A one-day panel is a current observation, not historical causation, market share, or a timeless rank claim.
- Review “velocity” from newest-N samples is only a bounded cadence signal unless a complete period is collected.
- Replace non-recurring preflight competitors with profiles that actually recur in the live frozen panel, and document the replacement rule.

## Closeout evidence

- frozen request packet and budget approval;
- preflight and final ledger snapshots;
- raw request/response files and provider task IDs;
- normalized evidence with deterministic validation output;
- report plus SHA-256;
- independent exact-hash acceptance sidecar;
- tracker comment/readback with canonical paths and hashes;
- explicit statement that no GBP/public/client mutation occurred;
- temporary callback deletion/de-authorization proof.
