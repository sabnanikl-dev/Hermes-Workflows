# Replacement-pin cumulative feedback reconciliation

Use this when a shared-publisher PR Prover run repeatedly exits `needs-karan / human-feedback` after technically green A/B/Auditor lanes, and each replacement acknowledgement pin reveals another historical batch.

## Core model

An operator pin grants acknowledgement authority to one exact post body. It is not cumulative across prior pins. When a replacement pin takes over:

- the old pinned post's ACK lines lose authority;
- targets cleared only by those lines become unresolved again;
- the old post itself can become unresolved residual prose because its now-ineffective ACK lines remain;
- the report describes only a bounded prefix. Read `actual` and `unresolved_not_described`; ten displayed IDs can hide a much larger set.

The safe target set is therefore **not** “whatever the latest report displayed” and not a hand-union of prior batches. It is the full reconciliation result with all operator pins removed.

## Procedure

1. Preserve the exact-head state file's truthful attempt count and `verified_artifacts`. Retained verified artifacts must stay run-owned so current reviewer outputs are not reclassified as human feedback.
2. Fetch the complete live comments, reviews, and inline threads.
3. Run the repository's own `feedback.reconcile` using:
   - the live complete `FeedbackSurfaces`;
   - retained `verified_artifacts`;
   - the configured publisher login set;
   - `operator_acknowledgements={}`.
4. Build one pure cumulative body with one canonical line for every eligible unresolved prose item, in reconciliation order:

   `PR-PROVER: ACKNOWLEDGED <immutable-id>`

5. Before POSTing, append a synthetic strictly-later comment carrying that body, pin the synthetic ID to `publication_evidence(synthetic)`, and require a second reconciliation to return zero unresolved items. This catches duplicate/already-cleared/self/premature targets before another expensive triad.
6. Publish once, read the real comment back by immutable ID, compute canonical evidence over the API-returned body and review state, and pin only that exact `{id, body_evidence}`.
7. Re-run live reconciliation and require zero unresolved items before replaying Reviewer A → B → Auditor.
8. If resetting a terminal review-only state is the governed continuation, clear only the finished outcome needed to permit replay. Preserve exact head, attempt cap, classification, and verified artifact ownership so no builder cycle silently reopens.

## Minimal shape

```python
without_pins = RunArtifacts(
    verified=state["verified_artifacts"],
    publishers=frozenset(configured_publishers),
    operator_acknowledgements={},
)
result = reconcile(live_surfaces, artifacts=without_pins)
body = "".join(
    f"PR-PROVER: ACKNOWLEDGED {item.identifier}\n"
    for item in result.unresolved
)
```

Use complete surfaces. Omitting reviews or threads is acceptable only when the live governed run already proves both counts are zero.

## Pitfalls

- A ten-ID report can be only the bounded display window, not the full unresolved set.
- Do not acknowledge decisive `CHANGES_REQUESTED` reviews or live threads in prose; clear those through GitHub-native state.
- Do not include explanation in the ACK post. Any residual prose becomes feedback.
- Do not let a run-owned artifact acknowledge feedback, even if edited later.
- Do not compute evidence over pre-POST bytes and assume GitHub preserved them; read back first.
- Do not keep rerunning all three expensive reviewer lanes to discover historical feedback ten items at a time. Prove the replacement pin reaches zero locally first.
- This is control-plane reconciliation only. Exact-head gates, technical findings, and the frozen stopping rule remain independently load-bearing.
