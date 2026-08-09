# Product-first replacement after verification-framework churn

Use this recovery pattern when repeated reviewer fixes have shifted from proving the shipped product into hardening a saved evidence report as though it were hostile runtime input.

## Stop signal

Stop repairing the current PR when the checker or evidence validator has become the moving target and repeated fixes no longer change the shipped runtime contract. Do not merge with an exception and do not keep patching the same verifier.

Keep the stopped PR open only as a temporary implementation/evidence reference. Close it as superseded only after the replacement PR exists, its live `headRefOid` matches the pushed replacement head, and its closing linkage matches the issue contract. Then read the stopped PR back through REST and verify `merged: false`; a successful close command alone is not proof that it remained unmerged.

## Freeze the recovery contract before rebuilding

Amend the authoritative issue before any replacement builder starts. State explicitly:

- the shipped runtime is the product;
- browser QA is a trusted exact-head execution performed by the reviewed generator;
- saved JSON/screenshots are an archived execution report, not hostile runtime input;
- binding means exact runtime path/hash/commit plus a successful QA outcome;
- no generalized closed-schema parser or standalone verification framework is required;
- unknown report fields block only when they can hide failure, alter binding, or contradict a specifically required observation;
- hardening ideas outside the finite contract become follow-up proposals;
- the replacement has a fixed repair budget, normally one fix cycle.

The amendment is a prerequisite barrier. Dispatching a builder first recreates the ambiguity that caused the churn.

## Rebuild from the current default branch

Create a fresh branch/worktree from current `main`; do not clean up the stopped PR in place. Reuse only independently verified product artifacts:

- shipped runtime bytes, or a deliberately smaller equivalent;
- required product wiring;
- browser-QA scenario knowledge.

Do not carry over the oversized generalized checker wholesale.

## Separate proof layers

1. **Runtime checker:** execute the shipped runtime against fresh literal fixtures and prove only the product contract.
2. **Browser-QA producer:** run exact-head desktop/mobile browser QA with prohibited network destinations intercepted; process exit is authoritative for that run.
3. **Narrow evidence binder:** verify successful outcome, empty problems, runtime path/hash/commit, required scenarios/viewports, screenshot existence, and required high-level no-egress/event observations.

The binder is not a hostile-input parser. Extra metadata is non-blocking unless it can falsify one of those finite observations or bindings.

## Freeze reviewer authority

Before review, list the blocker classes reviewers may use. Typical allowed blockers are:

- real runtime privacy/authority bypass;
- prohibited network egress;
- failed or missing required scenario;
- runtime/evidence binding mismatch;
- false success hiding an actual failed run;
- unmet acceptance criterion.

A hypothetical extra field in an otherwise valid archived report is follow-up hardening, not a blocker, unless the issue explicitly says otherwise.

Run reviewers sequentially on one unchanged head. Any fix invalidates the ordered triad and consumes one repair cycle. When the frozen budget is exhausted, stop for the owner rather than broadening the checker.

## Claim discipline

Prefer: “The committed report records a successful exact-head browser-QA run and is bound to the runtime hash/commit it exercised.”

Avoid claims that the report is an executable universal gate, has an exact closed schema, or is fail-closed against arbitrary mutation unless that behavior is genuinely part of the frozen product contract.

## Binder and lifecycle implementation details

- “Required labels/viewports are present” should normally be implemented as a required-subset check. Harmless additional metadata or viewport labels must not fail merely because they are additional.
- Duplicate **required** scenario labels may block because they can hide which result counts; duplicate unrelated extra labels are not automatically a contract failure.
- Commit the runtime before browser evidence production so the producer can bind a real commit. Generate evidence against that runtime commit, then commit the report/screenshots separately.
- Re-run the binder and full repository suite after the evidence commit.
- Preflight local HEAD = remote branch = PR `headRefOid` = final PR commit before spending reviewer lanes.
- Verify structured `closingIssuesReferences`; a visible `Closes #N` string alone is not lifecycle proof.
- After every push, read the PR commit list/head back from GitHub. After closing the superseded PR, verify `merged: false` through REST.
