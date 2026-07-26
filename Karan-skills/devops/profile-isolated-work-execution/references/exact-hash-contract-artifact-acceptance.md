# Exact-Hash Contract Artifact Acceptance

Use this reference for non-code specifications, architecture contracts, playbooks, and other durable artifacts produced by an isolated worker.

## Candidate → acceptance → promotion

1. **Freeze live source state.** Record the tracker body revision/digest, approval and claim markers, source identities by immutable account ID where authority matters, and per-connection pagination evidence (`pages`, node counts, final `hasNextPage=false` or exhausted REST links).
2. **Write to a non-canonical candidate path.** The executor must not claim the file is already reviewed, promoted, indexed, or accepted.
3. **Run deterministic checks.** Compute SHA-256, bytes, and lines; check required sections, terms, links, secret shapes, and formatting. Treat these as presence/shape checks only.
4. **Run a fresh semantic reviewer against the exact hash.** The reviewer reads the complete issue contract, candidate, and source packet. It must classify each acceptance criterion and cite line ranges.
5. **Block on P0/P1.** Keep the tracker issue active. Repair into a new candidate, compute a new hash, and re-run the semantic review. Never reuse a pass from older bytes.
6. **Protect the integrator context during repair loops.** Once repair requires repeated whole-file reads, multiple semantic-review rounds, or extended line-by-line patching, Default Hermes stops authoring directly and dispatches a task-scoped author/fixer worker. Give it a frozen packet containing the exact candidate path/hash, all blocker reports, acceptance criteria, one new allowed output path, local verification commands, and an explicit ban on tracker, canonical-artifact, messaging, and other external mutations. The worker returns a verifiable path/hash/count/check result; Default Hermes reads back and verifies those facts rather than trusting the self-report.
7. **Use a separate reviewer lane.** Send the worker's exact verified hash to a fresh reviewer that did not author or repair those bytes. Keep author/fixer → reviewer sequential because the reviewer depends on the finalized candidate; parallelize only independent evidence reads or audits. If review blocks again, issue a revised frozen repair packet to the worker instead of absorbing the full repair loop into the control-plane context. Direct Hermes edits are reserved for genuinely small one-shot fixes that will not trigger another prolonged review cycle.
8. **Route repair by role, not tracker origin.** The fact that a task originated in Linear does not make every worker a `linear-worker`. Contract/spec repair belongs to `pm-spec`; repository implementation belongs to `builder`; durable wiki publication belongs to `wiki-ops`. Use the generic Linear worker only when no role-native lane fits. If a generic worker rejects the packet before reading inputs because required launcher attestation is absent or the task is out of role, preserve that fail-closed result and relaunch through the correct sanitized specialist; never add fake grant variables or weaken the worker contract.
9. **Correlate asynchronous completions.** Record `(process-or-session ID, candidate path, candidate SHA-256, output/review path)` at dispatch. When a delayed completion notification arrives, compare all four values with the active acceptance record. A report against an older hash remains useful review history but cannot change the current candidate's state, authorize promotion, or restart a superseded repair lane.
10. **Promote unchanged.** Only a green exact-hash review permits copying those exact bytes to the canonical destination. Verify candidate and canonical hashes match.
11. **Make it discoverable.** Update the existing canonical index/log without creating a parallel tracker.
12. **Close out with a complete output inventory.** Include exact path/ID/URL, intended user/purpose, provenance, hash/readback, lifecycle, discoverability update, and approval/publication status.

### Control-plane context diet

Default Hermes retains the governing tracker revision, approval/claim evidence, worker handoff, exact candidate hash, reviewer verdict, promotion verification, and closeout inventory. Keep large drafts, repeated full reads, detailed repair reasoning, and deterministic validator iteration inside the worker lane. On Telegram, report only meaningful states: dispatched, in progress, review-ready, blocked, accepted, promoted, and done. Do not poll noisily or paste full worker transcripts into the main conversation.

### Background one-shot approval and large-file repair pattern

Use this split when a role-native specialist must repair a large local artifact but its background process cannot surface terminal approval prompts reliably:

1. **Control plane freezes and verifies the input.** Default Hermes computes the source candidate hash/bytes/lines and records the blocker report path. The specialist may rely on that frozen identity when terminal is intentionally unavailable.
2. **Pre-seed instead of rewriting.** Default Hermes copies the full verified candidate to a new writable path and verifies source/copy hashes match. This preserves all provenance, scenarios, and long-form contract sections.
3. **Launch the correct specialist with file tools only.** The packet allows targeted patch/replace operations on the pre-seeded copy, forbids whole-file replacement, names the exact blocker report, and grants no external systems or operational credentials.
4. **Keep verification outside the worker.** The specialist must not claim a hash, validator pass, acceptance, or promotion. Default Hermes computes identity and runs validators after exit.
5. **Reject structural collapse before review.** Compare line/byte counts and required-section checks with the source. A dramatic contraction or failed deterministic validator is a failed candidate, not something to send to the semantic reviewer.
6. **Review only verified bytes.** Once the patched copy passes control-plane mechanics, send its exact new hash to a fresh read-only reviewer.

Prefer this split over broad `--yolo`/approval bypass for a background specialist. A bounded bypass can still be appropriate in a purpose-built sanitized launcher, but invisible approval retries are not a repair strategy. The durable principle is separation of duties: specialist edits; Default Hermes verifies; independent reviewer accepts.

## Semantic blocker checklist

Presence validators commonly miss these contract-level defects:

- a guard that promises one terminal result but yields “checkpoint, then either A or B”;
- claim/lease recovery that depends on an unspecified store, heartbeat, expiry clock, or worker identity;
- approval that names a display name/login but omits immutable platform account identity and its configuration source;
- machine-readable queue prose without a strict versioned schema, duplicate/unknown-key policy, or explicit order field;
- scenario rows that do not map to exactly one declared step and outcome;
- “complete pagination” claims without evidence for every collection used in the decision;
- review/check reduction that is ambiguous across commits, reviewers, dismissed reviews, or duplicate checks;
- lifecycle prose that says “reviewed/promoted” before acceptance and promotion actually happened;
- a supposedly terminal repair ladder where released-lineage branches, claims spread across duplicate control objects, or malformed-but-corrected records can disappear into “no active work” and permit new selection;
- mergeability, check status/conclusion, review state, or timestamp inputs without closed vocabularies, unknown/null handling, and one canonical normalization (including fractional seconds);
- the same defect mapping to different reason codes in guard prose, reason precedence, and scenario fixtures;
- deterministic templates whose inner placeholders are specified but whose outer outcome/evidence object has no byte-exact encoding, field order, escaping, nullable-value rule, or evidence-ID ordering;
- scenario rows that accidentally contain an earlier-priority defect, so the asserted reason is unreachable; require isolated fixtures plus combined-defect precedence fixtures.

The reviewer should answer explicitly whether the downstream implementation issue can proceed **without inventing policy**.

## Tracker body normalization

After mutating a tracker description, immediately re-read the live body before posting approval or claim markers. Some APIs normalize Markdown representation (for example, unordered-list bullet characters). Compare the returned body with the intended change using only documented representation equivalences; stop on any unexpected semantic diff. Compute the approval digest from the exact live normalized body, not from the local draft.

Never continue from a mutation response alone: verify the body, digest, comment ID/author, and state via direct readback.
