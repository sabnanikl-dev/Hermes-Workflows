# Review-state barriers and heterogeneous diagnostic seams

Use this reference for exact-head closeout after a narrow exception/hotfix, especially when the Integration Auditor must certify both implementation and reviewer state.

## Stage reviewer-state evidence before the Auditor

If the Auditor is expected to verify A/B state, do not freeze its packet before those artifacts can exist.

Preferred sequence:

1. Run Reviewer A on the exact head; wait for exit and inspect the final marker.
2. Verify the live head, relay A's signed artifact, and read it back.
3. Run Reviewer B; wait, verify, relay, and read back.
4. Refresh only the packet's live PR/review/comment/thread/check surfaces while preserving the same exact code head, diff, baseline, and machine evidence.
5. Assert that the refreshed packet contains A's formal exact-head state and B's signed exact-head verdict.
6. Launch the Integration Auditor last.

A packet frozen while A/B are still running cannot prove their absence. If parallelism is intentional, the Auditor should return an implementation/AC verdict with review-state synthesis marked pending—not manufacture a code blocker from orchestration timing. Default Hermes performs the final live reconciliation.

## Accepted-domain expansion requires a failure-path census

When a patch broadens accepted values (for example, strings to arbitrary JSON scalars), audit every downstream consumer, not just validation and matching:

- successful comparison;
- failed comparison;
- failure-message construction;
- sorting, min/max, sets, and dictionary keys;
- human rendering and JSON serialization;
- deterministic output under operand permutation;
- escaping of quotes, control characters, and Unicode.

Raw Python ordering is unsafe for heterogeneous scalars: `sorted([False, "x"])` raises `TypeError`, while Python equality also aliases `False == 0` and `True == 1`.

Use a total canonical diagnostic key such as:

```python
(json_scalar_type_rank(value), compact_canonical_json(value))
```

Keep comparison semantics separate and JSON/type-sensitive. Add end-to-end controls for every membership operator on an intentionally untyped selected field:

- validation accepts a heterogeneous scalar list;
- match and non-match paths both execute;
- failure diagnostics are non-empty, stable, and order-independent;
- boolean/integer/float/string values remain distinct;
- duplicate operands and escaped strings never crash or corrupt output.

A green happy-path corpus is not proof that an expanded input contract is closed. The diagnostic path is part of the executable contract.
