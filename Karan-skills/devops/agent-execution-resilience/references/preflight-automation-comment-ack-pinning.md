# Pure ACK and exact-post pin preflight for automation comments

Use before an expensive PR-Prover run when a fresh PR already contains a Vercel/deployment/linkback bot comment and the operator login is also a configured reviewer/builder publisher.

1. Read paginated conversation comments, reviews, inline comments, and GraphQL review threads before launch.
2. Acknowledge only inspected automation/status noise, never a human blocker or failed deployment relevant to acceptance.
3. Post a pure bookkeeping body with no explanation: `PR-PROVER: ACKNOWLEDGED <earlier-comment-database-id>`.
4. Read the ACK post back by immutable database ID and verify author, exact body, timestamp, and URL.
5. For a conversation comment, compute `body_evidence` exactly as `sha256(json.dumps([body, ""], ensure_ascii=False).encode("utf-8"))`.
6. Pin the ACK post—not the original bot post—in `operator_acknowledgements` as `{id, body_evidence}`.
7. Run `check-config` and confirm it prints the pinned ID before launching gates.

Do not mix ACK lines with prose: the residual prose becomes a new unresolved feedback item. If posting was ambiguous, inspect live comments before retrying. An ACK reconciles known noise; it does not waive content or authority boundaries.
