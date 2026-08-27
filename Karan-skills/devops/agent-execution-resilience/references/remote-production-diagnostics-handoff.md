# Remote production diagnostics handoff

Use this when a security- or privacy-sensitive issue requires one live production observation before implementation, but the designated builder cannot reach the custom domain from its execution network.

## Principle

A builder's inability to reach production is an evidence-collection interruption, not automatically a human blocker. The orchestrator may obtain the missing **read-only, reduced** observation through a trusted remote probe, bind it to a durable measurement handle, and return it to the same builder lane.

This never authorizes authenticated access, mutation, deployment, account changes, credential use, or real analytics delivery.

## Procedure

1. **Validate the builder stop.** Require a clean preserved worktree and a precise statement of the one observation that distinguishes competing root causes. Do not let the builder guess across a consent/privacy/security boundary.
2. **Choose a remote read-only probe.** Prefer an established external measurement service or trusted remote browser/network lane. For response-header questions, unauthenticated HTTPS requests from multiple regions are usually sufficient.
3. **Bind reduced evidence.** Preserve the measurement ID, timestamp, exact target/path, probe regions, status, resolved address, TLS authorization, and only the relevant headers. Keep raw artifacts outside the repository when useful.
4. **Prove absence explicitly.** When diagnosis depends on a missing header, enumerate both the relevant headers found and candidate headers absent across several probes. HTTP 200 alone does not prove absence.
5. **Reconcile, do not overclaim.** State which hypothesis the observation eliminates and what uncertainty remains. A header probe is not browser execution, collection, revision-binding, or deployment proof.
6. **Resume the same lane.** Give the builder the immutable measurement handle, reduced facts, optional local artifact path, and original authority boundaries. Require it to verify base/worktree state before editing.
7. **Return to the normal lifecycle.** Builder implementation, tests, push/PR readback, and exact-head independent review remain mandatory.

## CSP-versus-origin example

A sandboxed child may mount while no network request appears. Local real-browser fixtures can show both:

- document CSP can suppress inline child execution; and
- an opaque-origin child cannot use cookies or Web Storage.

Those imply materially different repairs. A multi-region production-header probe can safely determine whether document CSP is actually present. If all authorized-TLS responses omit `Content-Security-Policy`, report-only CSP, and legacy CSP headers, document CSP is eliminated as the production cause. It does **not** prove that the origin/storage boundary is the sole cause; the builder must reconcile the remaining runtime evidence before changing architecture.

## Pitfalls

- Do not encode a temporary local content filter, missing binary, or provider outage as a durable tool limitation.
- Do not ask the user to manually fetch evidence that a safe remote read-only probe can retrieve.
- Do not hand the builder a paraphrased conclusion without the measurement ID and exact reduced facts.
- Do not store cookies, client IDs, full analytics request URLs, or unrelated response bodies.
- Do not weaken a private/consent boundary merely because the easiest fixture makes traffic appear.