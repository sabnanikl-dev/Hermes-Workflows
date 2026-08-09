# Implementation completion vs rollout proof

Use this when a tracker combines a repository implementation with separately approved real data, content publication, deployment, activation, migration, or cutover.

## Evidence matrix

| Surface | What proves it | What it does not prove |
| --- | --- | --- |
| Capability exists | Merged exact-head PR, current default-branch files, deterministic tests | Real source data exists or the path was operated |
| Contract behavior | Fresh fixture/live-shaped tests, former-red mutations, generated-output checks | Production network/account behavior |
| Source readiness | Read-only query of the original source (CMS, tracker, account, feed) | Generated output was committed or deployed |
| Deployment state | Inspect the actual deployed URL/artifact and identify generated markers/content | Source approval or backend correctness by itself |
| Cutover/activation | Separately approved account/config change plus post-change proof | Anything inferred from a repository flag or laboratory eligible mode |

## Policy/approval child variant

Use this variant when a decision issue defines the rules for later code and production operations, but its body has accumulated wording that also mentions the downstream control, deployment, or activation proof.

Classify the surfaces separately:

| Surface | Completion evidence | Residual owner |
| --- | --- | --- |
| Policy decision | Named human approval, exact rules recorded, no unresolved decision checkbox | Policy child |
| Durable/public source | Owner-approved copy or contract merged at a stable route/schema; deterministic checks pass | Policy child or linked implementation issue |
| Control implementation | Reviewed code/UI that consumes the policy without widening authority | Verified coding successor |
| Production publication/account state | Direct readback from the live URL/account after separately approved mutation | Operations/cutover successor |
| Activation | Explicit activation approval plus network/provider proof | Operations/cutover successor |

Close the policy child only in this order:

1. prove the policy decisions and durable source are complete;
2. identify every implementation or live-operation claim that is still false;
3. create and read back a narrow successor for missing code/control work;
4. transfer deployment, account, network, and activation proof to the existing downstream operations issue and read it back;
5. reconcile the policy criterion to state what was actually approved or merged, with an explicit pointer to the residual owner—never check the old live-behavior wording unchanged;
6. promote and read back durable business knowledge when the tracker contract requires it;
7. move the policy child to a completed state, add a stable-ID closeout comment, and explicitly list what did not happen.

A direct user instruction to finish or close the policy child authorizes this tracker reconciliation when the issue's title, authority boundaries, and existing downstream structure already separate policy from activation. It does **not** authorize deployment, account mutation, or activation. If that separation is not already supported by the live contract, ask rather than redefining scope after the fact.

## Decision procedure

1. Read the live issue body, especially acceptance criteria, manual/suggested verification, and out-of-scope sections. Do not infer closure from the PR title or issue number.
2. Re-query linked PRs and require the expected merge state and exact merge commit. Inspect final review surfaces for unresolved blockers.
3. Verify the implementation on the current default branch with the issue's required checks; do not rely only on old PR comments.
4. Inspect the original external source before using tracker/session history as evidence. For a CMS-backed path, query the actual dataset read-only and count eligible records.
5. Inspect the actual deployed/public surface. Distinguish hand-authored fallback from generated output using stable markers or source-owned attributes when available.
6. Classify every unchecked/manual item:
   - **In-scope missing gate:** keep the issue open.
   - **Capability proven; operation explicitly out of scope:** create and verify a rollout successor, reconcile the implementation issue, then close it as implementation-complete.
   - **Ambiguous wording:** do not silently reinterpret. Ask the owner whether to close as implementation-only or keep the original end-to-end gate.
7. In the closeout note, say explicitly what did **not** happen: no real content published, no deploy, no account mutation, no activation, or no cutover proof, as applicable.

## Successor pattern

A rollout successor should own only the real-world step, for example:

- approve/select the first real source record;
- run the gated live generator or migration command;
- review the generated diff/output;
- deploy under explicit authority;
- perform desktop/mobile and lifecycle smoke tests;
- record rollback and source-of-truth evidence.

Link the successor from the completed implementation issue before closure. Do not let the successor become a second implementation issue, and do not reopen the completed implementation merely because rollout remains pending.

## Pitfalls

- Treating zero eligible source records as a failed implementation when real content creation was explicitly out of scope.
- Treating green fixture tests as proof that a real record rendered publicly.
- Leaving an implementation issue open forever for a separately authorized deploy while no successor owns that deploy.
- Closing without reconciling unchecked boxes or explaining that suggested manual smoke moved to the successor.
- Creating the successor after closing, which leaves a temporary gap in ownership and evidence.
