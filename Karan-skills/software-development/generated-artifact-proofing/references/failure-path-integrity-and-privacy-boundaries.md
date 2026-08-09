# Failure-Path Integrity and Privacy-Boundary Probes

Use this reference when a workflow, automation, importer, or reconciliation job produces a human-readable report. It captures adversarial probes that ordinary fixture suites commonly miss.

## 1. Failure-closure invariant

For each producer stage—discovery, normalization, planning, import/create, update/restore, archive, and guard/abort—prove that every counted failure reaches the report.

Required invariant:

```text
reported aggregate failures
= attributable file-level rows
+ explicitly classified non-file/anonymous failures
```

Never allow `counts.failed > 0` while the artifact says “No file-level failures recorded” unless the report visibly explains the non-file failure class and provides an actionable next step.

Probe the actual committed producer code, not only a hand-authored fixture. Execute each stage’s real node/function body with a stage-specific failure and feed its emitted payload directly into the report consumer.

Minimum matrix:

| Producer stage | Probe | Required report behavior |
|---|---|---|
| normalization/planning | missing required metadata for a named file | failure count and safe filename/actionable row survive |
| import/create | asset/doc write fails | continued/aborted outcome is truthful |
| update/restore | patch fails | existing item remains attributable |
| archive | archive patch fails | item remains public/preserved; reason/counts reconcile |
| guard | protective stop before mutation | no file mutation is implied; stop is explicit |

## 2. Reason-attribution integrity

Do not force totals to reconcile by inventing which reason failed.

Bad fallback:

```text
failure reason missing → decrement the first nonzero planned reason
```

That creates coherent but false evidence. Instead choose one explicit contract:

1. carry the authoritative reason through the failure path and subtract that exact bucket;
2. emit planned and successfully-applied reason structures separately; or
3. mark reason attribution unknown/unattributed and fail closed when exact applied-reason reporting is required.

Adversarial cases:

- missing reason;
- unknown reason;
- reason not present in planned totals;
- multiple nonzero planned reasons with one unattributed failure;
- duplicate failures for one item;
- failed count greater than planned count for a reason.

Assert that input permutation does not change attribution.

## 3. Owner-safe privacy matrix

Token scans that split only on whitespace are insufficient. Inject the same secret/PII into every dynamic field and syntax shape:

- unquoted assignment: `token=private-value`;
- quoted JSON: `{"access_token":"private-value"}`;
- nested/escaped JSON and arrays;
- dotted, slashed, colon-, query-, bracket-, and hyphen-delimited IDs;
- URL credentials and query parameters;
- email addresses;
- phone forms: `(404) 555-1234`, `404-555-1234`, `+1 404 555 1234`;
- filenames containing emails, IDs, URLs, traversal, or secret-like labels;
- status/environment/trigger badges, headings, error summaries, recommended actions, labels, and link text.

The final leak scan must be independent of the normal scrubber. A test that invokes the same detector twice proves only self-consistency, not coverage. Keep explicit raw-marker assertions for representative values.

Operator links require URL parsing before interpolation. Allow only intended schemes (normally `http:`/`https:`), a real host, and no embedded credentials. Invalid values render non-clickable or are withheld.

## 4. Contradictory-state probes

Validate closed status values and cross-field coherence:

- success + `failed > 0`;
- success + file-level rows;
- success + fired guard;
- guard-aborted + guard explicitly not fired;
- arbitrary status string;
- negative/fractional/string/NaN reason counts;
- compensated negative reason totals that still sum correctly;
- missing values defaulting to success/zero.

## 5. Independent proof rule

A large passing validator count is evidence, not completeness. Before final approval, an independent reviewer must:

1. read the real producer and all failure collectors;
2. derive at least one novel probe not already named by the builder;
3. execute it against the exact head;
4. compare aggregate counts, detailed rows, reason attribution, and rendered prose;
5. record whether the validator would have caught the mutation.

If a novel probe finds a blocker after the allowed fix-cycle cap, freeze code mutations and escalate; do not weaken the invariant to make the suite green.
