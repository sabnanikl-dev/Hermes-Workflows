# Private Third-Party Provider Queue Authority

Use this pattern when a browser runtime must integrate a third-party loader that expects a window-named queue, while the product contract forbids page code from gaining mutable event/payload authority.

## Threat model

A normal `window.dataLayer = []` is not merely debug state. Any same-page script can append a provider command, choose an event name, add free text or PII, or bypass the wrapper's fixed grammar. A zero-argument public boot seam does not make the runtime private if the provider queue remains writable.

Review the **actual shipped eligible path**, not only the committed-disabled path. Mutation probes must enable the runtime and attempt a real queue injection after boot.

## Bounded integration pattern

When the provider requires a global string key:

1. Create the queue in the runtime closure.
2. Create and retain the exact loader DOM node in the same closure.
3. Refuse startup if the chosen global key already exists; do not overwrite or trust page-owned state.
4. Define a non-enumerable, non-configurable accessor at that key.
5. Return the live queue only while `document.currentScript === loader` for that exact node.
6. Return `undefined` to ordinary page reads and ignore ordinary writes.
7. Keep the wrapper's fixed `send` function closed over the private queue.
8. Include the custom queue name in the loader URL through a fixed reviewed URL grammar.

This is capability narrowing, not secrecy by naming: page code may discover the property name, but it cannot obtain or replace the mutable queue through the accessor.

## Required proof split

### Direct runtime checker

Use fresh literal fixtures and capture the queue only by simulating the provider's exact current-script context. Then restore the normal script context and prove:

- page reads return `undefined`;
- assignment of a PII-bearing attacker queue is ignored;
- the closure queue and emitted call list are unchanged;
- a pre-existing property collision creates no loader, queue, listener, observer, or request;
- repeated boot creates at most one loader/config;
- loader URL and queue-name parameter are exact.

Add a deliberate mutant that changes the accessor to `return queue`; the public-authority probe must turn red. If duplicate-loader protection has more than one independent guard, remove all relevant guards in the duplicate-loader mutant so the probe still exercises the claimed failure class rather than surviving for the wrong reason.

### Browser-QA producer

If no-egress QA aborts every analytics/ads request, the real provider script cannot execute and must not be used as the observation channel. Instrument only the laboratory copy of the runtime with a QA-only getter that returns defensive copies of provider calls. Keep this instrumentation absent from shipped bytes.

In real browser page code, attempt the former injection through the provider key and record both:

- whether the private queue became readable;
- whether the attempted assignment changed the copied provider calls.

Both must remain false. Also verify `window.dataLayer` and `window.gtag` stay undefined unless the reviewed product contract explicitly requires otherwise.

### Compatibility boundary

An aborted-loader browser run proves runtime wiring, no egress, interactions, and the page-code authority boundary. It does **not** prove the live third-party loader will accept the conditional accessor. Treat real provider compatibility as a separately approved activation/preflight criterion; do not overclaim it from an offline stub or aborted request.

## Exact-head evidence lifecycle

Commit runtime/checker/producer changes first. Run browser QA against that commit, binding the report to runtime path, byte count, SHA-256, and commit. Commit the regenerated report separately, then run the narrow binder and full repository suite. Any later runtime or producer change invalidates the report and ordered reviewer sequence.

## Claim discipline

Prefer: "page code cannot read or widen the closure-owned provider queue; direct and browser probes reject the former injection path."

Do not claim a generalized hostile-report parser, universal same-page isolation, or live provider compatibility unless those are independently exercised and explicitly in scope.
