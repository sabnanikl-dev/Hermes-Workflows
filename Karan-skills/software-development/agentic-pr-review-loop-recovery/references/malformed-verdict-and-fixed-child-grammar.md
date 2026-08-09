# Malformed verdict vs substantive triad, and fixed child-owned command grammars

Use this reference when an exact-head Prover run exits code 2 around an isolated browser/provider seam. It separates control-plane failure from product failure and captures the finite repair pattern for a pre-init first-port race.

## 1. Classify the run before touching code

Exit code 2 is never a verdict by itself. Read the persisted JSON report, state, retained lane output, and live GitHub artifacts together.

### Transport/control-plane failure

Treat the stop as infrastructure—not a repair cycle—when all of these hold:

- report outcome/reason is control-plane shaped (for example `needs-karan` + `malformed-verdict`);
- the reviewer lane exited without a parseable terminal marker/artifact;
- `reviewers` is empty or the affected role has no parsed verdict;
- no reviewer artifact was published/read back;
- the raw lane output shows provider/model refusal, truncation, or malformed formatting rather than a canonical blocking finding;
- the PR head and product bytes did not change.

Preserve the failed report. Rephrase the reviewer focus to ask for the same frozen review through existing deterministic checks, without inviting broad exploit generation, then rerun at the same head. Do not call this a product pass and do not consume a fix cycle.

### Malformed transport with a reproducible candidate defect

A malformed lane can contain detailed candidate reasoning before moderation, truncation, or a missing terminal marker prevents a canonical verdict. Keep the two claims separate:

- the ordered review transport is incomplete and the raw prose is **not** a published reviewer artifact;
- a product defect may still be independently knowable if the operator reproduces it against the unchanged shipped head.

Build the smallest deterministic reproduction from the candidate input, execute it against the exact shipped bytes, and record the observed value/type and process exit. If it reproduces, classify the transport as malformed **and** the product as blocked; never claim Reviewer B formally passed/failed or that the triad completed. If the repair cap is exhausted, stop the PR and return continuation to Karan rather than hiding another patch inside transport recovery. If it does not reproduce, retain the raw output only as control-plane diagnostics.

### Substantive triad

Treat the stop as product evidence when:

- Reviewer A, Reviewer B, and Integration Auditor each have parsed exact-head verdicts;
- canonical `FINDING:` records exist;
- transport is complete for each role (prepared, published, direct readback verified);
- independent roles converge on a reproducible blocker.

A later wrapper/transport issue does not erase those findings. If the configured repair budget permits one repair, that repair consumes the cycle. If the cap is exhausted, stop—do not disguise another repair as review-only recovery.

## 2. Opaque realm does not imply secret initialization authority

A closed shadow root and opaque sandbox protect the child realm after initialization, but earlier same-page code can wrap `document.createElement`, retain the iframe, register a `load` listener first, and win an unauthenticated first-port handshake. If the child accepts arbitrary arrays and forwards them with `gtag.apply`, opaque storage still permits arbitrary event names and PII-bearing payloads.

Do not try to prove that an interceptable port is secret. Make the privacy boundary survive port capture:

1. Parent sends only compact numeric signals.
2. Child owns the event-name table, placement enum, page-kind enum, fixed URL/referrer, consent defaults, config options, and bounded numeric ranges.
3. Child rejects raw provider commands, strings where numeric codes are required, unknown codes, extra fields, mutable payload objects, free text, PII, and out-of-range positions.
4. Child constructs the final provider commands and payloads itself.
5. Document the honest residual: captured page code may suppress or replay already-approved signals, much as it may synthesize approved DOM interactions, but it cannot widen privacy/payload authority.

This is finite product hardening, not a generalized command-validation framework.

### Array lookup must be own-index/range checked

A numeric protocol is not fixed merely because the intended values are numbers. JavaScript arrays inherit prototype keys, so truthiness checks such as `if (!places[value]) return` admit inputs like `"__proto__"` or `"constructor"`; the lookup can yield an object rather than an approved enum string. This can widen a supposedly child-owned payload even when the event name remains fixed.

Before **every** array lookup, require all three predicates:

```js
Number.isInteger(value) && value >= 0 && value < list.length
```

Do not use `value in list`, truthiness, coercion, or an upper-bound check alone. Exercise at least these former-red classes through the captured first port:

- `"__proto__"` and `"constructor"`;
- numeric strings and arbitrary strings;
- objects and arrays;
- fractions, `NaN`, and infinities;
- negative and out-of-range integers.

Keep position/range arguments separate from enum indices so a value invalid for one field is not accidentally valid for another. In the literal fixture, assert exact surviving event count plus primitive enum equality—not only absence of the original PII string. In Playwright, assert invalid captured-port inputs emit zero events and only the expected child-owned fixed config survives at every required viewport.

## 3. Prove the former-red ordering twice

### Literal runtime fixture

Model multiple `load` listeners in registration order. Have earlier page code retain the actual iframe, install the first listener, transfer its own port, receive the ready marker, submit a raw PII-bearing provider command, then submit only a valid fixed initialization signal. Assert:

- the captured port ordering actually ran;
- arbitrary event name and PII never enter child provider calls;
- only child-owned fixed commands are recorded;
- fixed grammar, URL, page-kind, placement, and position checks still pass;
- one loader maximum remains true.

A post-init fake global/currentScript probe is not a substitute for this ordering.

### Trusted Playwright producer

Inject earlier page code immediately before the shipped runtime. It wraps iframe creation, registers the first load listener, transfers its port, and sends the same raw command. Instrument only the trusted laboratory copy inside the child so copied provider calls can be observed without exposing a live queue in shipped bytes. Assert both desktop and mobile execute the capture, reject raw PII/event data, record only the expected child-owned fixed config, and make zero real provider egress.

Keep this case inside an existing required scenario when possible so the frozen scenario inventory does not churn merely to prove an additional observation.

## 4. Repair exact-head evidence in two commits

When runtime bytes change:

1. Run syntax, literal checker, diagnostic browser QA, and diff hygiene.
2. Run all non-evidence repository gates.
3. Commit implementation/runtime/checker/producer/docs first.
4. Run non-diagnostic browser QA so the report binds to the exact runtime commit and hash.
5. Run the narrow evidence binder and inspect result, empty problems, path, bytes, hash, commit, required labels/viewports, screenshots, and zero egress.
6. Commit only the archived report/screenshots.
7. Run the full repository suite and binder on the final evidence head.
8. Push, then independently verify local HEAD = remote branch = PR head and confirm both commits through the live PR commit list.
9. Update the PR body with the final bytes/hash/runtime commit/evidence head and the honest repair-cycle count.

A diagnostic report may intentionally lack a committed runtime binding or screenshots. Do not interpret its binder failure as a product regression; replace it with the final committed run before the full suite.

## 5. Treat executable status prose as contract surface

A green validator that prints “no runtime ships” after the PR starts shipping a production-disabled runtime is a real harness/documentation blocker. Search executable success text, docs, PR claims, and package scripts together. Correct the stale status claim in the same bounded repair; do not dismiss it because the validator logic itself passes.

## 6. Final review recovery details

- A head change invalidates every old reviewer artifact and restarts A → B → Integration Auditor.
- Pin any operator acknowledgement to the new exact head and the exact API-read body evidence. The canonical digest is over JSON `[body, state]`, not raw body SHA-256; use the repository's `publication_evidence` implementation rather than hand-rolling it.
- Preserve the truthful consumed attempt count with the repository's state writer/API. Never fake “no more fixes” by replacing the builder adapter with `/usr/bin/false` or by resetting to `attempt=0`.
- Old `CHANGES_REQUESTED` state must be cleared by fresh native review state on the final head; prose acknowledgement cannot clear it.
- If the final triad blocks after the sole repair, stop the replacement and preserve a terminal blocker ledger. Karan remains sole merge authority.
