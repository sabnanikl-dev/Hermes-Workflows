# Internal baseline → external benchmark → approved mutation

Use this pattern when a local-visibility decline spans three adjacent work classes:

1. an owned-profile diagnosis;
2. an external market/competitor benchmark;
3. an approval-gated live profile change.

It prevents circular dependencies, unfocused paid research, and competitor observations from becoming unsupported client-account mutations.

## Ownership boundaries

### Internal diagnosis issue

Owns:

- first-party performance recomputation;
- current owned-profile fields and activity surfaces;
- comparison with dated prior audits;
- the initial hypothesis ledger;
- selection of the fixed query panel and candidate competitors;
- final synthesis and mutation-candidate handoff.

Source hierarchy:

1. owned first-party API/dashboard evidence and dated business confirmations;
2. public first-party surfaces and official platform documentation;
3. external provider evidence returned by the benchmark issue.

External observations may corroborate displacement or identify a follow-up question. They must not overwrite first-party profile state or manufacture a historical change timeline.

### External benchmark issue

Owns:

- localized Search, local-pack, and Maps observations;
- query × geography panel execution;
- competitor profile/review observations;
- provider selection, cost ceiling, raw response preservation, retry policy, and actual cost reporting;
- the market-wide-versus-business-specific conclusion.

It does not own internal profile completeness or live mutations.

### Mutation issue

Owns only exact separately approved changes. It is an execution lane, not a diagnosis lane.

A competitor pattern can justify a question or bounded test. It does not prove that a category, service, product, offer, or claim is true for the business.

## Sequencing

1. **Internal Phase A first.** Recompute the baseline, capture current profile state, freeze the first hypothesis ledger, and select the primary queries and candidate competitors.
2. **Start the bounded external panel.** Run it while remaining internal read-only analysis continues.
3. **Finish synthesis.** Consume external results by immutable evidence ID, or explicitly record `pending external test` / `insufficient evidence`.
4. **Route mutation candidates.** Send only complete, evidence-backed rows to the execution issue.
5. **Execute approved rows.** Separate batches by risk and directly read back every write before continuing.

A pre-existing deterministic one-field consistency fix may proceed earlier only if it has its own exact before/after contract, fresh preflight, separate approval, direct readback, and no bundling with other fields.

## Bounded paid-data packet

Before paid execution:

- search by capability, not vendor name;
- record required input fit, observed reliability/sample size, price, last-success recency, and intended evidence ID;
- use owned/free sources where they already answer the question;
- obtain explicit approval for one cost ceiling covering the bounded packet;
- stop at the ceiling and report actual settled cost per call and total spend.

Preserve immutable raw responses separately from normalized comparison tables. Each observation should retain:

- query;
- requested and resolved geography or coordinates;
- language/country;
- device/OS or disclosed context;
- timestamp;
- provider, capability/endpoint, and version when available;
- actual cost;
- evidence ID.

Use one primary method consistently across the full panel. A second provider is a bounded cross-check, not a value to average into the first provider's ranks. Exact rank is a timestamped method/location/device observation, never a timeless fact or proof of historical causation.

Retry rules:

- `4xx`: treat as an input/contract failure; fix the request and do not fan out paid retries.
- `429`, `5xx`, timeout: switch to the next suitable provider only within the approved ceiling and record the switch.
- Lost response after a potentially billed call: reuse the same idempotency key only for the genuine retry.

## Mutation approval ledger

Every candidate row should include:

- field or surface;
- exact current state;
- exact proposed state or asset;
- evidence IDs and source class;
- rationale and expected benefit;
- risk;
- owner confirmation needed;
- rollback/reversal method;
- human approver and date;
- execution/readback status.

Risk-separate batches:

1. deterministic consistency fixes;
2. owner-approved copy, hours, and real assets;
3. discovery-sensitive categories, attributes, services, and products after business truth and platform eligibility are verified.

Stop the batch if the before-state drifted, the platform rejects or rewrites a value, readback is ambiguous, or rollback is unclear. Do not improvise compensating edits.

## Acceptance checks

- The internal Phase A checkpoint exists before paid external execution.
- Queries, geographies, and competitor candidates are frozen before collection.
- Paid calls remain within an approved ceiling and actual costs are recorded.
- Raw evidence and normalized tables remain separate and traceable by evidence ID.
- Findings identify their source class.
- External observations do not become direct mutations.
- Every mutation candidate has exact before/proposed state, provenance, risk, rollback, owner confirmation, and approval status.
- Every live write receives direct readback before the next write begins.
- Final artifacts are saved in the canonical project location and linked from the tracker; chat-only evidence is insufficient.
