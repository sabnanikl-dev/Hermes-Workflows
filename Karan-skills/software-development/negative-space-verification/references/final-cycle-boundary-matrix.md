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

## Exact-head lifecycle and unknown-live-head probes

When a workflow persists review/classification evidence across builder execution, distinguish:

- observed live PR head;
- bound/work head;
- classification head;
- recorded pre-interruption head;
- unknown live head when no current remote read exists.

Exercise every supported terminal window:

| Window | Required result |
|---|---|
| Same-head stop after a live read | classification may render as current for that exact head |
| Terminal freshness observes B after classifying A | report B; mark A historical or clear it |
| Push reaches B but comment/readback fails | report observed B; mark pre-push A evidence historical or clear it |
| Restart with an in-flight attempt before any remote read | live head is unknown; never promote recorded A to verified-current merely because `head == classification_head` |
| Successful rebind to B | invalidate A classification |

For the restart probe, construct valid persisted state on A with a complete classification and an in-flight attempt marker, while a remote double is on B. If the documented safety policy intentionally stops before GitHub reads, assert zero PR/comment/commit reads and then inspect **both JSON and Markdown**:

- the stop must be fail-closed/needs-human;
- A may remain available as recorded evidence;
- A must be explicitly unverified/historical, current/live head must be unknown, or the classification must be cleared;
- no machine field documented as current head may silently fall back to recorded A;
- nearby failure prose does not repair misleading structured fields.

A fallback such as `observed_head or recorded_head` is unsafe whenever the destination field or heading means current PR head. Green tests and mechanical `MERGEABLE/CLEAN` status do not override a reproduced false-current evidence path.

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
