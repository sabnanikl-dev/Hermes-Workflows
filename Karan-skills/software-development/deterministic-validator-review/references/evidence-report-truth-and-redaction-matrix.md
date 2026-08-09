# Evidence report truth and redaction matrix

Use this reference when a deterministic generator adapts workflow/run evidence into owner-safe or operator-facing HTML, Markdown, or JSON. The dangerous false pass is a polished report that is internally contradictory, silently drops producer fields, leaks sensitive values, or presents synthetic fixture data as a real execution.

## Proof layers

Keep five layers separate:

1. **Producer shape** — what the real workflow/runtime actually emits.
2. **Adapter semantics** — how that shape becomes the report model.
3. **Truth invariants** — which states/counts/details may coexist.
4. **Rendering/redaction** — what leaves the trusted boundary.
5. **Attribution** — whether an execution ID, timestamp, and counts all describe one source-backed event.

A green curated-fixture suite normally proves only layers 2 and 4 for the examples the builder chose.

## Producer-to-adapter contract

Capture one payload directly from the real producer code or a byte-faithful fixture. Probe that shape through the public generator entry point.

Require:

- every issue-required field survives or is explicitly unavailable;
- unknown/missing evidence renders as `unknown`, `not recorded`, or `N/A`, never a reassuring default;
- the adapter does not derive success solely because absent nested fields default to zero;
- failure rows, guard state, source IDs/names, archive reasons, and execution metadata come from fields the producer actually carries.

If the governing contract requires file-level failure detail or guard disposition but the producer does not emit it, an adapter warning is not a complete fix. Change the producer schema or narrow/defer the acceptance contract with explicit authority. Do not let presentation code manufacture missing evidence.

## Truth-coherence mutation matrix

Run each mutation independently against the public generator. A rejection must exit non-zero and write no success-looking artifact.

| Mutation | Expected result |
|---|---|
| empty object / unrecognized shape | reject; no output |
| missing or unknown status | reject, unless status is deterministically derived from complete evidence |
| `status=success`, `failed>0` | reject |
| `failed=0` with one or more runtime failure rows | reject |
| `failed>0` with no itemized rows | reject when the issue requires debuggable file-level detail; otherwise label the gap explicitly and never claim complete reporting |
| guard fired with imported/touched/archived mutations | reject |
| guard state absent | render unknown, not “guard did not fire” |
| negative, fractional, string, or non-finite counts | reject |
| archive-reason totals exceed applied archives | reject |
| archive-reason totals are lower than applied archives | expose unattributed remainder; do not assign it to a guessed reason |
| report generation time before run time | reject |
| execution URL with `javascript:` or another non-allowlisted scheme | render non-clickable or reject |

Also test honest controls: success with zero failures, warning/failure with coherent rows, a guard-aborted zero-mutation run, and a flat producer payload with all supported counts.

## Owner-safe redaction families

Builder-authored probes often cover only obvious `token: value`, Bearer, email, and phone examples. Add independent variants from each family:

- env/assignment forms: `SANITY_AUTH_TOKEN=...`, `API_KEY = ...`, quoted JSON keys such as `"access_token":"..."`;
- authorization forms: Basic credentials, Bearer tokens, provider-prefixed keys, JWT-shaped values;
- contact data: mixed-case emails, punctuated/parenthesized phone numbers;
- identifiers: short and long opaque IDs after path, dot, query, and JSON boundaries;
- filenames: title-case, lowercase, hyphenated, underscored, and possessive person-bearing names;
- URLs: credentials/query secrets and disallowed schemes.

Use two barriers:

1. field-profiled redaction before rendering;
2. a final scan of the completed owner-safe bytes that aborts the write if a sensitive pattern survives.

The final scan must cover the same families as redaction; a scanner that omits assignment secrets, opaque IDs, or filenames only certifies its blind spots. Add valid controls to prevent over-redacting brand/workflow names and ordinary non-secret numbers.

## Real execution vs synthetic fixture attribution

A fixture may be synthetic or source-backed, but not both.

- A synthetic fixture must use a clearly synthetic ID/label and say it is fixture-rendered.
- A fixture named for a real execution must match that execution's timestamp, trigger mode, counts, failure rows, guard state, and archive reasons from one authoritative source.
- Do not combine event deltas with a later system snapshot. For example, “archived this run = 0” and “currently archived total = 32” are different facts and need different fields/labels.
- If source evidence is partial, remove the real execution attribution or mark the sample partial; never fill missing fields from a different run.

Regression-test both the values and the provenance label. A green suite that requires a real execution ID beside invented counts is enforcing misinformation.

## Documentation truth: artifact state vs live instance state

Repository exports and production instances can legitimately differ. Document both explicitly:

- **tracked artifact state:** sanitized, credential-free, often `active=false`, safe to import;
- **live operational history:** whether a production instance was activated, what execution evidence exists, and what follow-up durability caveats remain.

Do not turn “the committed export remains inactive by design” into “production activation is still gated.” Likewise, a fixture-rendered sample is not evidence that the live schedule ran. Cross-check operational claims against the authoritative tracker/live source before accepting them.

## Review sequence

1. Preserve a clean exact-head checkout; run write-producing probes in a scratch copy.
2. Read the governing issue and list report fields that are mandatory, optional, or explicitly deferred.
3. Inspect the real producer code before the adapter.
4. Run the truth-coherence and redaction matrices with at least one independent case per family not present in builder tests.
5. Compare every real execution attribution to its authoritative source.
6. Re-run the full suite, deterministic sample regeneration, syntax checks, and worktree-cleanliness check.
7. Report separately: current committed sample correctness, generator/validator soundness, owner-safe boundary safety, and documentation/attribution honesty.

## Stop rules

- One reproduced owner-safe leak is blocking for an owner-safe report.
- One success report that visibly contains failure evidence is blocking.
- Missing producer fields required by the issue cannot be waived by adapter prose.
- A real execution label attached to contradictory counts is blocking documentation/evidence drift.
- At the repair-cycle cap, preserve these as terminal exact-head findings; do not keep expanding regexes or silently open another builder cycle.
