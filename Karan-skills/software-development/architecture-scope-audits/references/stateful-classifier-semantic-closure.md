# Stateful Classifier Semantic-Closure Audit

Use this audit when a PR changes a classifier, validator, parser, ownership rule, evidence filter, or workflow state machine—especially after reviewers find repeated false-success variants in the same blocker class.

## Why this gate exists

Example-by-example repairs often pass large suites while missing stateful permutations. The common blind spot is testing one aggregate input in isolation while the implementation also depends on run-global history: previously consumed IDs, prior comments/reviews, persisted evidence, retries, or head movement.

The audit must decide not only whether the result fails closed, but whether the exact state transition is correct. Over-blocking can be semantically wrong even when it avoids false success.

## 1. Reconstruct the state axes

List the smallest complete vocabulary before judging implementation. Typical axes:

- valid vs malformed marker;
- known vs unknown target;
- earlier vs same/later target;
- authorized human vs publisher/agent author;
- unresolved vs already consumed globally;
- first use vs duplicate in the same input vs duplicate across earlier inputs;
- bookkeeping-only vs mixed ordinary prose vs malformed bookkeeping-like prose;
- fresh process vs persisted/restarted state.

Replace these with the domain's real states; do not invent speculative platform requirements.

## 2. Build a temporal transition table

For every meaningful row record:

| Prior state | Current input | Effective transition | Global state after | Unresolved evidence | Public outcome |
|---|---|---|---|---|---|

Include same-input/different-history rows. These expose post-local checks that accidentally ignore run-global state.

For acknowledgement-like workflows, representative rows include:

- unresolved A + valid ACK A;
- unresolved A + valid ACK A + ordinary prose;
- unresolved A + valid ACK A + malformed/unknown ACK-like line;
- A already cleared, B unresolved + valid ACK B + duplicate ACK A;
- unresolved A + unauthorized or non-later ACK A;
- restart with previously verified/consumed evidence.

## 3. Separate safety from transition correctness

Require reviewers to report both:

1. whether false success/merge-ready is possible;
2. exact cleared/retained/invalidated IDs and exact unresolved finding IDs.

A `blocked` result that retains two findings instead of the specified one may be safe but still violate the contract. Conversely, a valid transition must not erase adjacent ineffective evidence.

## 4. Require three proof layers

### Predicate tests

Prove each individual classification and ineffective control.

### Sequence tests

Exercise multiple inputs over time, including cross-input duplicates and restart/persistence when supported.

### Shipped-path probes

Drive the real public orchestration seam and assert:

- outcome/reason;
- exact state transition;
- exact finding IDs;
- retained evidence body/text;
- supported runtime parity.

Unit predicates do not override a shipped-path false success.

## 5. Prove sensitivity

For each former-red or transition-table row:

- show the pre-fix rule or a focused mutant fails the test;
- include controls that fail if the implementation becomes over-conservative;
- distinguish semantic paths from many syntactic variants of one path;
- report table rows proven, not only total test count.

## 6. Architecture verdict

A direct table-driven classifier or explicit transition function is usually proportionate. Repeated literal special cases without a complete state vocabulary are not.

If a same-class blocker recurs after a table-driven repair, recommend stopping the automated patch loop for human-reviewed redesign or PR decomposition. Do not endorse another narrow exception merely because the next code change appears to be one condition.

## Reviewer prompt capsule

```text
Reconstruct the finite state/transition table for this classifier. Probe same-input/different-history cases, input-local vs run-global duplication, mixed valid+invalid aggregates, restart/persistence, and the shipped public outcome. Report both safety and exact state transition. Green tests or high coverage do not clear an independently reproduced public-path false success.
```
