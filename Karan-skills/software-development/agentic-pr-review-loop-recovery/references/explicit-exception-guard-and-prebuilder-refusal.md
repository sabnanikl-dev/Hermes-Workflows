# Explicit exceptional-cycle guard and pre-builder refusal recovery

Use when the normal PR Prover cap is exhausted, Karan approves exactly one blocker-scoped exception, and the exception must remain mechanically incapable of opening another repair.

## Bind the exception outside automatic state

Record a local contract outside every repo/worktree with the approving human, approval evidence, repo/PR/branch/base/exact head, exact blocker IDs, `max_additional_fix_cycles: 1`, allowed files/surfaces, required proofs, forbidden scope, and terminal stop condition. Preserve the capped run state as history; use fresh state, lock, and worktree-root paths.

Do not patch the tool's normal attempt constant or call a fresh attempt-0 run ordinary authority. The exception is separate, explicit authority.

## Guard the official builder adapter

Keep the full run inside `pr-prover`. Configure a small external builder guard that:

1. accepts only attempt 1 / initial mode;
2. validates the live repo, PR, branch, base, and head against the approval contract;
3. requires the frozen blocker IDs to equal the approved set exactly;
4. injects allowed surfaces, proofs, and stop conditions into a copied blocker file;
5. delegates to the repository-owned Claude builder adapter;
6. emits a conforming failure marker for attempt 2, renamed blockers, extra blockers, or wider scope.

The guard is an authority boundary, not a replacement implementation lane.

## Empty `next_instructions` is a valid reviewer-ledger shape

A frozen file may contain a complete classified `blockers` array while `next_instructions` is empty. Reviewer findings are not always accompanied by generated failure records.

Do not reject that shape. If and only if the frozen blocker IDs exactly match the approved set, synthesize one narrow instruction per blocker from its frozen `id`, `summary`, `origins`, and exact head, then append the approved file boundary, proof commands, and escalation condition. Reject duplicate, malformed, unknown, or extra instruction IDs.

## Preflight the guard

Test with a stub Claude executable and a realistic fixture containing the approved blockers plus `next_instructions: []`:

- attempt 1 reaches the official adapter and the copied file contains one bounded instruction per blocker;
- attempt 2 returns a valid builder-failure marker;
- a changed blocker set is refused;
- shell syntax and `pr-prover check-config` pass;
- live PR head and commit-list tail still equal the approved starting head.

A cooperative fixture containing pre-populated instructions does not prove the empty-array path and can hide a guard false rejection.

## Decide whether a refused launch consumed the exception

Use evidence, not the journal attempt number alone. A pre-builder guard rejection leaves the substantive exception unused only when all are verified:

- the real Claude adapter never launched;
- lane duration/output identifies the guard refusal;
- no signed builder comment appeared;
- no commit or push occurred;
- PR head and remote commit-list tail are unchanged;
- the retained worktree has no builder mutation.

If all hold, repair the guard and replay the still-unused substantive exception in fresh state. If Claude launched or the head moved, the exception was consumed.

A replay uses a fresh journal, so its prior review artifacts are no longer run-owned. Review those artifacts, publish a pure canonical ACK bridge, read it back, bind its body evidence, and add the exact pin before spending another triad. Never acknowledge genuine unresolved human feedback.

## Separate a later proof-only cleanup from the product repair

A successful blocker-scoped product repair can expose a narrower deterministic-proof bypass or authoritative-document mismatch on the final exact head. Do not smuggle that work into the spent exception merely because the product bytes are already correct.

Classify the findings before requesting authority:

- **product defect:** shipped behavior on the exact head is wrong;
- **focused proof bypass:** a small hostile mutation defeats a frozen acceptance check even though the shipped product currently behaves correctly;
- **authoritative-doc drift:** command/count/contract prose disagrees with the executable gate;
- **broader framework hardening:** hypothetical evidence/checker expansion beyond the frozen product contract.

If the frozen reviewer rubric treats the focused proof bypass or authoritative-doc drift as blocking, require fresh explicit approval for a **proof-only** cycle. Freeze product/runtime bytes at the approved head, allow only the named checker and authoritative docs, prohibit evidence-inventory/schema/screenshot expansion, add only the former-red mutation, make every documented count match the resulting executable count, and run the existing full gates plus one final exact-head triad. Audit the pushed diff against that allowlist and verify product/runtime hashes did not change.

Do not turn broader framework hardening into an endless sequence of exceptional cycles. If the proof-only triad introduces another blocker class or demands wider evidence architecture, stop for Karan and consider the product-first replacement rule instead of silently widening the checker.

## Terminal rule

After the one substantive builder push, require five-way push agreement, signed fix-comment readback, fresh exact-head gates, and A → B → Integration Auditor. Any remaining or new valid blocker stops for Karan; no further repair is authorized.
