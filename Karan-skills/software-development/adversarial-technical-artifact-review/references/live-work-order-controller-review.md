# Live work-order controller review pattern

Use this reference when a deterministic controller selects work from a mutable issue tracker and closure depends on a live bootstrap contract.

## Independent evidence lanes

Review three surfaces separately:

1. **Contract:** the live bootstrap issue, acceptance criteria, and explicit closeout prohibitions.
2. **Implementation:** skill instructions, controller source, queries, marker parsers, and result-state logic.
3. **Reality:** a direct tracker query of current states, relations, comments, and evidence—not only the controller's own report.

A controller agreeing with itself is not an independent verification.

## Closure deadlock check

Model the closeout sequence before issuing a close verdict. A material blocker exists when all of these are true:

- bootstrap completion requires a downstream dogfood run;
- the bootstrap issue currently blocks that downstream issue;
- one-active-lane policy prevents both from being executable;
- the controller therefore cannot select the downstream issue while bootstrap remains active.

Do not close bootstrap merely to manufacture eligibility. Require a human-approved contract/state/relation handoff, such as an explicit paused state or split follow-up ownership, then re-read live state.

## Fail-open probes

Passing fixture tests are only the baseline. Probe at least:

- unauthorized approval author with a correct body digest;
- missing required marker fields;
- duplicate current claims with different run IDs or lanes;
- non-allowlisted root;
- later Ready work when an earlier ordered item is incomplete and a dependency may be missing;
- active out-of-scope descendant;
- pagination truncation hiding a child, blocker, or newer marker.

For approval, validate both marker identity and actual comment author. For claims, reject ambiguity rather than trusting only the newest marker. For bounded API connections, paginate fully or fail closed when `hasNextPage` is true.

## Mutable-artifact stability

Hash the contract artifact, implementation, and tests before review. Re-hash after tests and immediately before verdict. If hashes drift because another process edits the files:

1. invalidate earlier review conclusions;
2. reread every changed artifact;
3. rerun the full suite and all adversarial probes;
4. bind the final verdict to stable final hashes;
5. mention the concurrent drift without attributing it to the reviewer.

For read-only Python reviews, use `PYTHONDONTWRITEBYTECODE=1` so executing tests does not create `__pycache__` artifacts.

## Proposed-status transition probe

When the question is whether an active bootstrap/controller issue may move to review, do not treat the current-state inspection as sufficient. Deep-copy the live hierarchy in memory, change the issue and every duplicated relation-state snapshot to the proposed workflow state, and rerun the selector without performing a tracker mutation. Verify that:

- a review state whose tracker type is still `started` remains the sole active issue;
- the revision-bound claim remains valid;
- dependents remain blocked until the issue reaches a terminal state;
- no later work becomes selectable and no new warning/conflict appears.

Update both the direct child and relation snapshots in the fixture. Changing only the direct child can produce internally inconsistent probe output even though the selector still blocks correctly.

Keep the verdict scope explicit: `In Review` requires stable outputs and no P0/P1 review blocker; `Done` separately requires every acceptance criterion and closeout-evidence readback. A green review transition is not approval to close the issue.

## Conformance observations

Probe undocumented auxiliary commands as well as the main inspector. If a root allowlist protects selection but a read-only helper can fetch arbitrary identifiers, report the mismatch. Classify it by consequence: it is P1 when it crosses a confidentiality/authority boundary or can influence selection/approval; it may remain P2 when it is a read-only documentation/canonicalization gap with no effect on controller state. Likewise, distinguish semantic digest equality from canonical marker grammar (for example, accepting uppercase hexadecimal after normalization).

## Verdict rule

- Green tests do not override an unmet live acceptance criterion.
- A fail-open authority, concurrency, dependency, or pagination defect is normally P1.
- Report exact commands, compact reproduction output, live state, final hashes, and whether moving to review versus closing is safe.
