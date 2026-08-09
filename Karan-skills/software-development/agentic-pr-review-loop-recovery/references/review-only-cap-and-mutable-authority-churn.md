# Review-Only Cap Preservation and Mutable-Authority Churn

Use this reference after a user-authorized exception repair when the next exact-head pass must be **review-only**, and when reviewers discover a repeated class of live client-side authority leaks.

## Build a truthful review-only state

A terminal PR-Prover journal cannot be run again. Review it, verify no lane is alive, and reset/remove it through the shipped command. Then create the fresh current-schema state through the repository's `RunState` writer with:

- the current exact PR head;
- `attempt=2` (or the truthful cumulative consumed count);
- idle phase;
- no terminal outcome or stale classification.

Load the new state through the shipped parser before launch. This preserves the global repair cap: gates and A → B → Integration can run, while a blocker cannot open an unapproved repair cycle.

Do **not** simulate review-only mode by starting a fresh `attempt=0` state and replacing the builder executable with `/usr/bin/false`. That changes the configured control plane, hides the consumed count, and can still produce a misleading new-run lifecycle. The attempt cap belongs in validated state, not in a deliberately broken adapter.

## Reconcile historical artifacts before spending lanes

Resetting loses run-owned artifact identity. Before launch, inventory all conversation comments/reviews/threads and create evidence-bound pure ACK posts for historical builder/reviewer artifacts that the fresh run must clear. Run the repository's own reconciliation locally with no retained artifacts and require zero unresolved feedback before starting expensive reviewer lanes.

A post-triad `human-feedback` stop and a substantive exact-head fail verdict are separate facts. Preserve and report the blocker ledger even when strict feedback reconciliation also stops the run.

## Mutable client authorities: the recurring false-pass class

Any object used both for introspection and runtime admission is a security boundary. In browser analytics and similar clients, probe every page-reachable object that influences payloads:

- config and activation flags;
- factories or constructors that accept overrides;
- event taxonomies and parameter schemas;
- enum arrays;
- route/content manifests;
- registries and generated data globals;
- debug buffers if runtime later trusts them.

A frozen-by-convention comment is not protection. `const`, closure scope, and committed generated data do not stop mutation when the page receives the same object by reference.

Required former-red probes:

1. Mutate every published array/object and try to transmit a PII value.
2. Append a PII-bearing route/slug/registry record and exercise normal boot/emit behavior.
3. Confirm the clean checker fails on the vulnerable mutation and passes only after runtime authorities are private immutable snapshots or public copies are never consulted.
4. Verify state/introspection methods return defensive copies.
5. Repeat against the actual served API, not only a detached test factory.

Prefer private admitted snapshots over `Object.freeze` alone: hostile page code can replace a mutable global even if the original object is frozen. Snapshot after deterministic validation, then have runtime classification consult only that private snapshot.

## Stop patch churn

One narrow exception authorizes one repair. If the fresh triad finds another blocker, do not automatically reinterpret the original exception as renewable.

When successive heads expose the same architectural class—test/introspection seams becoming live authority, validators proving only untouched defaults, or safety depending on mutable page globals—recommend closing the PR unmerged and redesigning around a smaller private runtime surface. Mechanical `CLEAN`/`MERGEABLE` state and green hosted checks do not outweigh a reproduced no-PII or activation bypass.
