# Safety-Critical Migration Plan Review

Use this reference for filesystem cleanup, data migration, installer/archive, control-plane, or other stateful operational plans where a documentation defect can become a destructive execution defect.

## Core review model

Treat the plan as code. Extract a state-transition table before judging prose:

| State | Producer | Allowed next action | Recovery after crash/expiry | Must never allow |
|---|---|---|---|---|
| bootstrap/staging | initial creation | validate and atomically publish | same-run journal reconciliation | adopting unknown partial state |
| awaiting execution | approved immutable batch | consume nonce and enter preflight | reapproval only if unconsumed and no intent | stale/newest-run lookup |
| preflight in progress | nonce-consuming CAS | snapshot/drill or recovery | reconcile durable intent only | new side effect after expiry |
| execution in progress | verified preflight | one approved operation or recovery | finish/rollback exact durable intent | next operation under ambiguous state |
| post-processing pending | committed operations | exact map/report/review finalization | finalization-only re-entry | reopening source mutation |
| complete | final attestation | read-only reporting | none | further mutation under old approval |

**Blocker test:** every state named anywhere in the plan must appear in the table with a safe consumer. The AIOS review caught a real dead end because `executed_pending_map` and `executed_pending_review` were writable but initially rejected on re-entry.

## Approval boundary checklist

Approval should bind exact immutable bytes or hashes for:
- run/attempt/batch identity and ordered operations;
- source, destination, parent, volume, provider/materialization, and collision facts;
- rubric, schemas, validator, fixtures, executor, and tests;
- rollback/recovery manifest;
- review package plus deterministic privacy projections;
- expected mutable-control-file preimages;
- exact journal, temp, revision, evidence, report, and post-review paths;
- nonce, issue/expiry timestamps, approver evidence, rollback authorization, and command class.

Do not let the validator, rubric, executor, or projection algorithm change after review without rebuilding the control bundle, review, and approval.

## Side-effect ordering

1. Perform side-effect-free validation.
2. Acquire a real kernel/process lock; a persistent lock file is only an anchor.
3. Re-read and revalidate while locked.
4. Atomically consume the nonce before the first approved mutation.
5. Journal intent and fsync before each non-idempotent side effect.
6. Recheck expiry immediately before every new snapshot, drill, or real-operation intent.
7. After expiry, allow only reconciliation/verification of already-durable intent or explicitly approved rollback.

For bootstrap, define a genesis protocol because the journal cannot pre-journal its own creation and a ledger cannot safely hash itself. Specify empty-staging, journal-only, partial-ledger, and post-publish/pre-verify recovery.

## Filesystem-specific gates

- Same-volume no-replace rename only for a first pilot; no implicit copy/delete fallback.
- Descriptor-relative exclusive rename where available; generic `mv` is not an exclusive primitive.
- Revalidate source **and destination** ancestry, identity, provider/sync state, materialization, volume, case behavior, and Unicode/casefold collisions immediately before mutation.
- A local snapshot is same-device recovery depth, not an independent backup. Track count/age/free space and never silently prune.
- Keep the first execution batch tiny and homogeneous; route directories, repos/worktrees, secrets, synced paths, hardlinks, and unsupported metadata to dedicated procedures.

## Privacy-bound external review

A reviewer should not receive raw sensitive paths merely to make review “independent.” Instead:
1. Use a versioned deterministic canonical projection.
2. Tokenize only declared roots; reject unknown roots.
3. Preserve operation ids/order and all safety-relevant non-path fields.
4. Record raw artifact hashes, projection hashes, and one-to-one operation mapping.
5. Hash the exact review-package bytes.
6. Require the attestation to bind the package hash, projection map, raw hashes, lane identity, findings, timestamp, and verdict.

## Blocker-only adversarial prompt

```text
Review these migration artifacts as an executable safety state machine.
Return only concrete P0/P1 defects that can cause data loss, unapproved mutation,
privacy leakage, replay, stale execution, unrecoverable crash state, or an
unexecutable recovery dead end. For each finding give the exact artifact/state
and minimal fix. Do not suggest optional defense-in-depth. If none remain,
return VERDICT: PASS.
```

After each fix, narrow the next prompt to the patched blocker. This avoids both premature acceptance and endless optional hardening.

## Verification pattern for plan artifacts

When no project test suite exists, run a fresh temporary verifier that checks:
- every standalone goal starts with its required command/prefix;
- required safety invariants are present;
- stale unsafe wording is absent;
- embedded HTML/preformatted goal mirrors decode byte-for-byte to source Markdown;
- UTF-8, trailing whitespace, duplicate HTML ids, section/pre counts, and parser completion;
- expected files only and cryptographic hashes for final reporting.

Also render the plan through a local HTTP server and inspect the browser console, duplicate ids, horizontal overflow, and updated recovery wording. Remove the verifier and stop the preview server afterward. Preserve originals before patching when the directory is not under git.
