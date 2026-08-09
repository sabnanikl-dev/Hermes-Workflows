# Fixture Isolation and Harness-Integrity Recovery

Use when a deterministic validator, mutation suite, or regression guard may reuse state across cases.

## Treat the finding as a proof failure

A clean committed artifact can coexist with an unsound verifier. If fresh seeds make a mutation survive that the shared suite catches, withhold merge readiness. Do not use an aggregate mutation count as evidence until isolation is proven.

## Isolation contract

- Store only declarative plain data in case definitions.
- Build new storage maps, queues, logs, DOM node arrays, event arrays, and configuration objects *inside each sandbox invocation*.
- Never retain a stateful fixture helper or mutable object in a module-level case matrix.
- Run state-sensitive cases in forward and reverse order; results must be identical.
- Repeat an individual case after a prior case writes consent-like state; it must behave as if first.
- Add a negative self-test that deliberately restores one shared object reference and proves the verifier rejects it.

## Recovery when the verifier overtakes the feature PR

1. Freeze the feature PR and preserve its exact-head review evidence. Do not merge or continue an unbounded repair loop.
2. Split a focused, synthetic-fixture-only harness-integrity issue/PR from current main. Keep it free of the pending runtime, provider, production configuration, account, deployment, and network behavior.
3. **Freeze the verifier's data model before implementation.** Prefer a closed, named-slot fixture (for example: storage backing maps, log, queue, plain config, fixed DOM nodes) over a generic graph walker or extensible sandbox framework.
4. Reject values outside that model at the seed boundary: unknown keys, functions, class instances, cycles, `Map`, `Set`, and arbitrary container shapes. Do not add support for an adjacent container merely because a reviewer finds an unwalked edge case.
5. Retain and identity-audit **every sandbox created**, including both halves of targeted state-sensitive pairs. A created-but-not-audited sandbox is a proof gap; it can carry a leak that comparison output alone will not reveal.
6. Prove fixture freshness, order independence, repeatability, and deliberately reintroduced direct-slot sharing (storage, log/queue, targeted-pair DOM/config, seed alias) in that small PR.
7. If a supposedly focused verifier starts growing into a generic framework or reviewers uncover successive container/traversal edge cases, close/supersede it rather than adding another traversal patch. Reissue a closed-shape verifier with an explicit finite acceptance envelope.
8. Merge the verifier prerequisite only after its own independent review.
9. Rebuild the feature on the new main from a fresh branch; do not revive the blocked branch or claim its prior mutation score transfers.

This split is appropriate when test-harness churn, not product behavior, dominates review. It prevents a feature PR from growing an ever-more-complex checker while its evidence remains untrustworthy.

## Do not turn the prerequisite into a product of its own

A synthetic prerequisite is justified only when its **finite interface is already a concrete dependency** of the future product checker. Before opening it, write down the exact fixture constructor/call sites that will consume it and a small acceptance envelope. If the runtime does not exist yet and the proposed harness is defining its own APIs, seed language, object-graph rules, or extensibility model, keep fixture construction local to the future runtime checker instead.

A nominally closed-shape verifier can still scope-invert when it starts defending JavaScript meta-object details that are irrelevant to its fixed call sites (for example non-enumerable or symbol own properties). The right response is not an endless admission-policy chase:

1. A first finding may justify a tightly bounded repair when it proves a missing assertion in the declared direct-slot contract.
2. If a replacement verifier then receives consecutive findings about its own framework boundaries rather than feature acceptance criteria, stop and close it unmerged.
3. Record the reset on the governing feature issue: rebuild from current main; construct literal fresh storage/log/queue/config/DOM fixtures directly inside the checker that executes the real runtime; retain and inspect those concrete objects in that test only.
4. Do not claim that a standalone synthetic verifier proves runtime behavior, consent, telemetry safety, or production readiness.

The goal is not a reusable sandbox abstraction. The goal is a small, independently reviewable proof that the actual product tests cannot inherit state.
