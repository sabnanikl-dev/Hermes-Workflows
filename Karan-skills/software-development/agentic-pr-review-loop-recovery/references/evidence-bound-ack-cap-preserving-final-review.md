# Evidence-bound ACKs and cap-preserving final review

Use this reference when a PR-Prover recovery run must reconcile historical publisher-authored feedback after one or more builder pushes, especially when all authenticated GitHub identities are also publishers and the normal two-cycle repair budget is already consumed.

## Why an immutable ID alone is insufficient

GitHub assigns immutable comment/review IDs, but the body and review state remain mutable. An ID-only operator pin therefore follows the post into whatever it is edited to say. A historical publisher post can be rewritten into different but still-valid `PR-PROVER: ACKNOWLEDGED <id>` grammar and inherit authority the operator never reviewed.

Keep three predicates distinct:

1. **Owned now:** ID + author + current publication evidence still match this run's recorded artifact. This may lapse after an edit so the edited post re-enters feedback.
2. **Published by this run:** immutable ID was observed being created by this run. This never lapses and permanently denies ACK authority to run-published artifacts.
3. **Operator-authorized state:** immutable historical ID + canonical body/review-state evidence match what the operator read. A same-ID evidence mismatch denies ACK authority and remains feedback.

A safe pin shape is bounded and explicit:

```json
{
  "operator_acknowledgements": [
    {
      "id": "<github-database-id>",
      "body_evidence": "<lowercase-sha256-from-the-repository-canonical-function>"
    }
  ]
}
```

Do not invent a parallel digest algorithm. Fetch the immutable artifact by ID, construct the repository's GitHub `Comment`/review value from the raw API body and state, and call the same canonical `publication_evidence()` function used for run-owned artifacts. Verify the raw API body equals the pure ACK bytes you intended to publish before retaining the digest.

## Historical-feedback bridge

1. Inventory prior-run reviewer/builder conversation artifacts that the new journal will no longer own.
2. Read and adjudicate them; never ACK material you have not actually reviewed.
3. Publish one pure bookkeeping post containing only canonical ACK lines. Residual prose creates new unresolved feedback.
4. Fetch that new post by its returned immutable ID.
5. Verify author, exact raw body, URL, and timestamp; derive canonical body evidence from the API object.
6. Pin the evidence-bound record in the next run config.
7. Immediately before launch, fetch and recompute again. Any mismatch is a stop.

Formal `CHANGES_REQUESTED` reviews are not prose comments. A later exact-head `APPROVED` or `DISMISSED` review from the same author must supersede them.

## Preserve the global repair cap in a fresh final run

A terminal journal must not be copied or edited into a new outcome. But creating a fresh `attempt=0` journal after two verified repair commits silently reopens cycle 3.

For a final **review-only** run after the cap is consumed:

- create fresh run/state/lock/worktree paths;
- initialize a current-schema `RunState` using the repository writer/API, not hand-maintained JSON;
- set the truthful cumulative attempt count (`attempt=2`), exact current PR head, idle phase, and no outcome/classification;
- do not carry old head-bound findings or terminal outcome;
- load the journal through the repository parser and verify attempt/head/phase before launch;
- run the normal gates and A → B → Integration sequence. A blocker must terminate as `blocked`; it must not invoke another builder.

Conceptual Python shape (adapt names to the repository's current API):

```python
from pathlib import Path
from pr_prover.state import RunState

state = RunState(
    repo=repo,
    pr=pr_number,
    path=Path(state_path),
    attempt=2,
    head=exact_live_head,
)
state.save()
loaded = RunState.load(Path(state_path), repo=repo, pr=pr_number)
assert loaded.attempt == 2
assert loaded.head == exact_live_head
assert loaded.phase == "idle"
assert loaded.outcome is None
assert loaded.classification is None
```

This preserves accounting; it is not permission to forge a resumed success or bypass an interrupted in-flight attempt.

## One-retry rule for an unchanged timing-gate flake

A single timing-sensitive failure is not automatically a product blocker or automatically dismissible.

Before one clean retry:

1. Confirm every changed-surface gate and the other supported-runtime full suite passed.
2. Prove the failing test file and its implementation path have no base-to-head diff.
3. Rerun the exact test/module several times on the same clean exact head and launcher mode.
4. Record the original failure and reproduction results; do not delete it from evidence.
5. Create one fresh review-only run with the identical gate commands, exact head, evidence-bound ACKs, and consumed attempt count.

Stop rather than retry again if:

- the test or implementation path changed in the PR;
- the focused reproduction fails;
- another gate fails;
- the identical clean retry fails;
- making it pass would require changing thresholds, commands, retries, timeouts, or test discovery.

Never add an internal retry to the gate or keep relaunching until green. The allowed action is one independently justified identical run, not metric gaming.
