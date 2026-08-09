# Test Sensitivity and Bookkeeping-Line Boundaries

Use this reference when a fix changes how a validator or classifier exempts bookkeeping syntax from ordinary user prose.

## Mutation-sensitivity method

A green suite is not sufficient. In a temporary copy outside the repository:

1. Restore the exact former false-success behavior with the smallest mutation.
2. Run the focused defect tests and require them to fail.
3. Preserve positive controls and require them to remain green on the real head.
4. Mutate adjacent load-bearing invariants independently—for example, make an artifact digest constant or bypass an authoritative commit binding—and identify the exact test that fails.
5. Run the unmodified full suite on every supported runtime.

A mutation that survives the suite is an uncovered proof obligation, even when the implementation currently looks correct.

## Bookkeeping-line negative space

When one post may contain both control syntax and human prose, do not exempt the whole post merely because one valid control line exists. Also do not remove every line sharing a prefix.

Adversarial matrix:

- one valid bookkeeping line and nothing else;
- valid line plus prose above or below it;
- several valid lines and no prose;
- one valid line plus a malformed control-like line;
- one valid line plus a control-like line carrying trailing human text;
- guessed, unknown, self-referential, premature, equal-time, missing-time, and unauthorized control lines.

The consumer should remove only the exact lines that were independently validated as successful bookkeeping. Malformed or unsuccessful control-like lines remain ordinary input. Otherwise a post such as:

```text
ACK <valid-existing-id>
ACK <unknown-id> -- do not merge
```

can clear the first target and silently discard the stop on the second line.

## State and documentation parity

For persisted ownership evidence:

- combine restart and head-move behavior in at least one direct probe;
- verify unchanged evidence stays owned and edited evidence becomes visible again;
- test body, state, author, and authoritative remote binding independently;
- document whether incompatible prior state migrates or fails closed;
- note schema-version reuse when the serialized shape changes, even if fail-closed behavior makes it non-blocking.

Documentation claiming “remaining text stays feedback” must be checked against malformed control-like lines, not only ordinary prose lines.