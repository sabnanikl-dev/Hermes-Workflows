# Identity-bound relay and contract-conflict split

Use this reference when a PR-Prover run has completed gates but loses transport readback, or when the final A → B → Integration triad discovers a real acceptance-contract conflict after the repair cap.

## Relay identity is part of the proof

A lane can produce a complete review and still fail `read_back` when its relay posts through the operator's default GitHub identity instead of the lane's configured `artifact_author`.

1. Inspect the transport record: `prepared` and `published` do **not** prove `read_back` or `complete`.
2. Re-read the published artifact directly. Verify its author, exact PR head, role signature, and canonical `FINDING:` lines.
3. Bind the relay to the configured lane identity explicitly (for example by exporting the GitHub token for that identity before `gh api`), rather than inheriting the operator's ambient `gh` login.
4. Re-run `check-config`, reset only governed state, and rerun the full ordered triad. Do not treat a transport identity mismatch as reviewer success.

## Acknowledgement bridge discipline

A fresh journal does not own earlier builder/reviewer artifacts. Before another expensive triad:

- inventory every still-unresolved historical comment and formal review;
- read each one before posting a bridge;
- post a **pure canonical** acknowledgement containing only exact `PR-PROVER: ACKNOWLEDGED <id>` lines required by the configured reconciliation grammar;
- read the acknowledgement body back through the API, derive the canonical body/review-state evidence hash, and pin that exact `{id, body_evidence}` record;
- run local reconciliation before spending reviewer lanes.

Explanatory prose belongs in a separate human status update, not inside the ACK post, because it can become residual feedback.

## Converged contract conflicts after the repair cap

When independent A, B, and Integration lanes reproduce the same conflict (for example a safe closed allowlist protects PII but contradicts a requirement to preserve unknown-but-legitimate acquisition values), do not open a hidden third implementation cycle.

- Report the competing requirements and exact-source counterexamples.
- Keep the PR blocked at the reviewed SHA.
- Ask Karan for a product/privacy scope decision.
- If Karan chooses a split, create and read back a focused design issue that links the PR and each current-head reviewer artifact, defines approval/ownership gates, and explicitly defers implementation to a follow-up slice.
- The design issue must not authorize merge, deployment, analytics activation, account changes, or policy publication.

## Final proof surfaces

- all lane transport rows: `complete`, `published`, and `read_back` true;
- `state.json` preserves blocker provenance from all three lanes;
- live PR head equals reviewed SHA and remains unmerged;
- split issue is open and re-read after creation.
