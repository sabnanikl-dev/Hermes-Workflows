# Mixed control-lines and prose: negative-space review

Use this reference when a deterministic parser treats human text as both prose and a small line-oriented control protocol, such as acknowledgement markers in PR comments.

## Core invariant

A control-looking line is removable bookkeeping **only after that exact line passes every semantic check**. Never strip all lines sharing a prefix merely because another line in the same post was valid.

Fail-closed behavior:

- a valid acknowledgement may clear only its proven earlier target;
- malformed, unknown-target, self-referencing, premature, equal-time, unparsable-time, or unauthorized acknowledgement-like lines remain unresolved prose;
- ordinary prose beside a valid acknowledgement remains unresolved;
- a pure valid acknowledgement-only post may remain a non-finding.

Dangerous shape:

```python
if post_has_any_valid_control_line:
    residual = remove_every_line_starting_with_control_prefix(post.body)
```

Counterexample:

```text
PR-PROVER: ACKNOWLEDGED 10
PR-PROVER: ACKNOWLEDGED missing-target DO NOT MERGE
```

The first line may legitimately clear comment `10`. The second clears nothing and must remain feedback. Prefix stripping converts the post to an empty residual and creates false success.

Prefer carrying validated line identities or spans from parsing into residual-prose construction. Remove only those exact validated spans; do not re-infer validity from a prefix in a later phase.

## Required adversarial matrix

Test both false-pass and positive-control directions:

1. one valid control line only;
2. several valid control lines only;
3. valid control plus ordinary prose before/after it;
4. valid control plus malformed control-prefixed substantive prose;
5. valid control plus unknown target;
6. valid control plus self-reference;
7. valid control plus premature/equal/unparsable chronology;
8. valid control plus a line from an unauthorized agent/publishing identity;
9. invalid-only control-looking post;
10. mutation test restoring broad prefix stripping so the new tests demonstrably go red.

Test target clearing and source-post findings separately. Proving that an older target was cleared does not prove the acknowledging post was classified safely.

## Exact-head reviewer reconciliation

When independent reviewers disagree, require the integration lane to reproduce the exact input through the shipped seam. Do not use majority vote. Bind all artifacts to the same full SHA and preserve the disagreement in the review record.

If the false pass appears after the final authorized exception/fix cycle, finish the required exact-head review sequence, publish and verify the blocker, and stop for human authorization rather than silently launching another repair.

## Supporting mission-contract fan-out

For a substantial bounded repair, Hermes may dispatch three independent read-only exact-head audits after push verification:

1. mission/spec compliance;
2. architecture proportionality and scope discipline;
3. tests/docs/state/config parity plus negative-space drift.

Give every subagent exact base/head SHAs, governing contract paths, changed-file allowlist, frozen blocker classes, and a strict no-mutation boundary. These audits are supporting evidence only; they do not replace the formal Reviewer A, Reviewer B, and Integration Auditor sequence.
