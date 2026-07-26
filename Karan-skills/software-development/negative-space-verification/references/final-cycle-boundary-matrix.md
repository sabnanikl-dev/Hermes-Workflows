# Final-Cycle Boundary Matrix

Use this checklist before launching reviewers on the last normal remediation cycle, and again when the final Integration Auditor adjudicates their findings.

## Privacy / projection probes

| Class | Example | Required behavior |
|---|---|---|
| Unquoted assignment | `token=private-value` | redact or reject |
| Quoted JSON assignment | `{"access_token":"private-value"}` | redact or reject |
| Punctuation-bound ID | `record.<opaque-id>`, `folder/<opaque-id>` | redact or reject |
| Phone variants | `404-555-1212`, `(404) 555-1212` | redact or reject |
| Person-name prose | `Customer Jane Doe called…` | withhold or safely generalize |
| Person-name filename | `Jane Doe prom fitting.jpg` | require trusted safe-name provenance or withhold |
| Raw upstream error | arbitrary provider/API text | map to allowlisted stage/action + safe summary |
| Unsafe URL | `javascript:…`, credentials-in-URL | non-clickable/withheld |

The final scan must use broader, independent detection—not the exact same recognizer as field scrubbing.

## Producer → consumer completeness

Enumerate all failure-producing stages:

```text
listing/discovery
normalization/planning
guards
import/create
touch/restore
archive/remove
post-run verification
```

For each stage:

1. execute actual committed producer code;
2. create one failure;
3. verify aggregate counts;
4. verify row-level evidence reaches the consumer;
5. verify the owner-safe rendering is actionable without leaking private IDs/PII.

Required relationship:

```text
aggregate failure count = actionable file rows + explicit global/non-file failures
```

## Attribution probes

Use at least two nonzero reason buckets and test:

- known reason;
- missing reason;
- invalid reason;
- duplicate/multiple failures;
- reason total after partial success.

Fail the review if missing attribution is assigned to a bucket by precedence or convenience. Balanced arithmetic with fabricated provenance is still wrong.

## State-coherence probes

For each status, construct:

- required evidence present;
- required evidence absent;
- contradictory evidence present;
- positive side effects under a claimed pre-side-effect stop.

For `guard-aborted`, require fired guard evidence and zero mutation counters. Inspect rendered copy as well as model validation.

## Objective visual probes

For every small or muted text role:

1. obtain foreground/background colors;
2. obtain computed font size and weight;
3. calculate WCAG contrast;
4. inspect screen and print overrides;
5. include mobile-generated labels and list numerals.

Do not waive low contrast because screenshots are geometrically clean.

## Final-cycle closeout

If blockers remain after the configured cycle cap:

- stop builder/code changes;
- publish exact-head A/B blocker artifacts and read them back;
- run/publish the Integration Auditor after A/B are durable;
- record consolidated blockers and passing surfaces in the ledger;
- mark the disposition `HUMAN_ESCALATION / NO-GO`;
- leave PR and tracker open unless the human decides otherwise;
- ask the human to choose: exceptional scoped cycle, defer, or close/replace.

An exceptional cycle is a new authority decision, not an automatic continuation.
