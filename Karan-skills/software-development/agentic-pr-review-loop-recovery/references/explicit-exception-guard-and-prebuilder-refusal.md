# Explicit exceptional-cycle guard and pre-builder refusal recovery

Use when the normal repair cap is exhausted, Karan approves exactly one blocker-scoped exception, and the exception must remain mechanically incapable of opening another repair. Preserve the already-selected execution mode: Full Prover uses its official adapter/journal; risk-proportional orchestration uses its scoped launcher and parallel reviewer lifecycle. An exception is not a reason to adopt a larger orchestration framework.

## Bind the exception outside automatic state

Record a local contract outside every repo/worktree with the approving human, approval evidence, repo/PR/branch/base/exact head, exact blocker IDs, `max_additional_fix_cycles: 1`, allowed files/surfaces, required proofs, forbidden scope, and terminal stop condition. Preserve the capped run state as history; use fresh state, lock, and worktree-root paths.

Do not patch the tool's normal attempt constant or call a fresh attempt-0 run ordinary authority. The exception is separate, explicit authority.

## Risk-proportional launcher path

For an existing non-Prover High-tier run, reuse the established scoped Claude launcher rather than manufacturing a Prover journal:

1. Recover the full approval proposal if the reply quote is clipped. Inspect live PR/base/head/commit tail, all review surfaces, local/remote equality, clean task checkout, and real worker processes. Do not launch a duplicate or disturb the original dirty checkout.
2. Preserve the old terminal checkpoint. Put the new exception contract, launcher settings, and one-build lock outside worker-writable paths. Keep normal cycles consumed and exceptional cycles started in separate fields; distinguish launcher PID from actual Claude PID.
3. Give a credential-free worker a disclosed frozen-source fallback only when direct GitHub reading is intentionally unavailable. Fetch complete paginated conversation/review/inline surfaces and check thread pagination; save exact final reviewer bodies with immutable IDs/URLs/readbacks and a hash manifest. Name the exact readable filenames in the prompt, not only the packet directory. Freeze inputs separately from mutable process bookkeeping.
4. Before implementation dispatch, guard repo/branch/base/starting head, PR open/draft state, PR commit tail, remote head, worktree cleanliness, approved blocker set, and packet hashes. Use an exclusive create (`open(..., 'x')` or equivalent) for a one-build lock so a repeated launch refuses. A lock alone does not prove the worker launched or that a repair commit exists; preserve those facts separately.
5. Run the harmless strict-sandbox probe first. Verify actual tool-result records for authorized read/write and denied private/control access and disallowed egress, not merely the model's final summary. A mixed JSONL stream may include non-JSON diagnostics: retain the raw stream, parse valid JSON records, and require the expected successful tool-result records rather than accepting an empty parse. Probe success is not product proof.
6. Launch with completion notification, verify the actual child PID and initial model/tool header once, then record ACTIVE accurately. If GitHub transport is within the approved envelope, publish/read back the bounded exception and retain prior blocking verdicts until fresh proof closes them.
7. After the worker exits, independently inspect the entire changed-path set against the frozen allowance. Verify any commit/push through local, remote, PR head and commit-list readback, then run required native/integration/browser gates. Run fresh Codex A/B in parallel and the dependent integration audit afterward. No additional repair is authorized by an agent's completion marker or by passing tests.

This path was exercised through a guarded sandboxed builder launch and verified authorization publication. It does not establish that the subsequent product repair, gates, or final reviews passed.

## Full Prover: guard the official builder adapter

For an already-selected Full Prover run, keep the full run inside `pr-prover`. Configure a small external builder guard that:

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

After the one substantive builder push, require remote/PR/commit agreement, the workflow's required fix-artifact publication/readback, fresh exact-head gates, and fresh review in the selected mode: parallel A/B then dependent Integration Auditor for risk-proportional High tier; the official ordered A → B → Integration Auditor lifecycle for Full Prover. Any remaining or new valid blocker stops for Karan; no further repair is authorized. Never describe a verified launcher start as a verified product fix.
