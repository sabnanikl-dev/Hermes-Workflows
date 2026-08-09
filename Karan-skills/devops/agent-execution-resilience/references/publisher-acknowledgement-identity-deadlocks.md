# Publisher-Authored ACK Identity Deadlocks

## When this applies

Use this reference when a restored or successor PR-prover run cannot cross its retained-feedback barrier because every authenticated GitHub identity is also configured as a builder or reviewer publisher.

## Minimal diagnosis

Before posting reconciliation comments:

1. Inventory all retained comments, reviews, inline comments, and threads.
2. Derive the run's effective publisher set from the validated config.
3. Enumerate the authenticated identities actually available to the operator.
4. Inspect the shipped acknowledgement-candidate rule.
5. If every available identity is excluded solely because it is a publisher, classify an **identity deadlock** before running expensive gates.

A characteristic proof is:

- the live comment contains the exact canonical acknowledgement lines;
- direct API readback confirms its immutable ID, author, body, and timestamp;
- the reconciler reports `acknowledged: []`;
- the author appears in the effective publisher set;
- no eligible non-publisher operator identity exists.

Do not keep appending publisher-authored ACK comments. They cannot clear the retained artifacts under the strict rule and may enlarge the unresolved conversation.

## Safe stop rule

Do not escape the deadlock by:

- faking an author;
- swapping builder and reviewer identities;
- changing the qualification config only to make the live ACK author look independent;
- granting a publisher-login allowlist;
- patching the candidate under qualification and continuing as if the same candidate passed;
- creating a third permanent authority identity merely to satisfy the tool.

Preserve the exact failed readback, report attempt `0/N` when no builder opened, and split a bounded control-plane repair if authorized.

## Narrow repair pattern

The robust seam is **operator-pinned immutable acknowledgement post IDs**, not trusted logins.

Recommended contract:

- Add one optional, bounded config list of exact immutable GitHub post IDs.
- Absent or empty config preserves current fail-closed publisher denial.
- A publisher-authored post may participate as an ACK candidate only when its own exact ID was pinned before launch.
- Publisher login alone never grants acknowledgement authority.
- Pinning grants only permission for that post's canonical ACK lines to be evaluated. It does not exempt the post from chronology, grammar, one-transition semantics, residual prose, native thread/review resolution, or stable-read checks.
- A mixed mapped ACK may spend valid lines but remains unresolved for its residual prose; a later separately pinned pure ACK can clear that mapped post.
- Run-owned lane artifacts remain ineligible even if an ID is configured. A lane must never create an artifact during the run and use it to clear its own blockers.
- An ID that names no live post authorizes nothing.
- Unknown keys, duplicates, whitespace-bearing IDs, patterns/login-shaped rules, overlong values, and excessive list sizes fail validation without echoing untrusted malformed values.

This is an immutable-artifact authorization seam, not an approval service, capability broker, token/signature protocol, identity expansion, or semantic prose engine.

## Required proof matrix

Exercise the real config → load → loop → run-artifact → feedback path, not only a helper:

### Positive

- Two-publisher environment with no third identity.
- A pinned publisher-authored mapped ACK clears older feedback but retains its residual prose.
- A later separately pinned pure ACK clears that mapped post.
- With a blocking gate ledger, both pins permit the run to reach the fix-attempt boundary.

### Negative

- Field absent.
- Empty list.
- Either required ID omitted.
- Same publisher posts an unpinned ACK.
- Pinned body is edited so only still-valid lines can act.
- Pinned ID names no post.
- A normal lane publication or run-owned artifact attempts self-clear.
- Malformed, duplicate, self-targeting, future/non-orderable, and mixed-residual cases.

For every negative control, require:

- stop at the human-feedback barrier;
- zero builder launches and zero attempts spent when the barrier precedes fixing;
- zero reviewer relay/publication;
- no push and no `merge-ready` result;
- deterministic evidence naming the configured pinned IDs without treating them as resolved merely because they were listed.

Mutation-check the seam in at least three directions: ignore every pin, grant every publisher post authority, and remove the run-owned-artifact guard. Each mutation should make focused tests fail.

## Tracker and qualification sequencing

Keep the repair separate from the failed qualification:

1. Leave the original qualification issue terminal or paused with exact evidence.
2. Create a bounded control-plane issue/PR for the repair.
3. Wire the repair as blocking the original resume.
4. Update the parent execution train and use an additive amendment on the still-open child; do not rewrite completed child history.
5. Build and independently review the repair PR.
6. Do not claim the original target qualified until the repair is separately approved/merged and the original task explicitly adopts the new immutable candidate.

A green repair branch is not evidence that the old merged candidate passed, and an unmerged repair PR is not authority to resume target mutation unless the task contract explicitly permits pre-merge dogfooding.
