# Post-deploy consent, network, and GA4 proof

Use this after an approved analytics merge/deploy. Repository tests and a successful deployment are prerequisites, not evidence that GA4 is collecting.

## Evidence ladder

Keep these layers separate and require each applicable layer to pass:

1. **Revision/deployment binding**
   - Verify the merged commit and deployment status.
   - For a squash merge, prove the production tree equals the reviewed PR-head tree.
2. **Public transport and byte identity**
   - Probe the canonical page, privacy page, and analytics runtime from more than one external location.
   - Record HTTP status, serving platform, authorized TLS, body hash/size, and deployment timestamp/header where available.
   - Compare the shipped runtime's relevant immutable configuration with the reviewed source. A reachable `200` is not enough.
3. **Negative consent controls**
   - In isolated browser contexts, prove absent, declined, dismissed, malformed/unreadable, and post-revocation revisit states produce zero Google Tag Manager, Analytics, Ads, and DoubleClick requests.
4. **Positive collection control**
   - Prove Allow and persisted grant attempt/load the expected tag exactly once and produce the expected initial collection request.
   - Repeated wake-ups must not duplicate loader/config/page-view behavior.
   - A provider mount, iframe, queue, DOM marker, or stored `granted` value is only an intermediate state. It is **not** collection proof.
5. **Event contract**
   - Trigger each required event through real page interactions where present.
   - Record only allowlisted metadata: request host/path, status, measurement ID, event name, fixed page kind/location/referrer, and bounded enum parameters.
   - Do not archive full request URLs or client identifiers when a reduced evidence record suffices.
6. **GA4 readback**
   - Verify Realtime/DebugView or the Analytics Data API receives the exact bounded events.
   - Keep browser-network proof and GA4-side readback as separate claims; neither substitutes for the other.
7. **Attribution**
   - Test only owner-approved campaign tuples. Query transport surviving redirects does not prove the runtime is authorized to emit campaign dimensions.
8. **Closeout**
   - Reconcile every tracker checkbox and preserve the distinction between repository evidence, deployment evidence, browser evidence, GA4 evidence, and durable wiki knowledge.

## Remote-browser/CDP pattern

When the operator machine has local TLS interception or cannot reach the canonical site reliably:

- Use an external HTTP probe for canonical transport and byte identity.
- Use a real remote Chromium session for JavaScript/consent behavior.
- If the remote browser exposes a CDP endpoint, connect with Playwright and subscribe to `request`, `response`, and `requestfailed` before navigation/action.
- Start each scenario with fresh storage/cookies or a new context. Do not let one consent decision contaminate another.
- Capture a positive-control request to a known Google endpoint if browser policy is in doubt. Without that control, zero requests after grant is ambiguous between browser policy and application failure.

## Decision rules

- **Negative states zero, positive state sends expected traffic:** consent gating is behaving; continue to GA4 readback and event checks.
- **Negative states send traffic:** privacy blocker; stop and assess rollback immediately.
- **Negative states zero, positive state mounts provider but sends zero traffic:** fail closed, but activation is not complete. Do not close the issue or claim collection. Diagnose provider startup/network delivery with fresh request-failure and child-frame evidence.
- **Browser shows delivery, GA4 readback is empty:** preserve browser proof, then investigate property/stream/filter/debug/reporting latency without rewriting the runtime prematurely.

## Analytics Data API service-disabled boundary

`runRealtimeReport` requires `analyticsdata.googleapis.com` on the OAuth consumer project. A `403 SERVICE_DISABLED` means the reporting API is disabled for that Cloud project; it does not mean the GA4 property, stream, or tag is missing.

Enabling the API is a Google Cloud account mutation and needs explicit approval. Until approved, use authenticated GA4 Realtime/DebugView UI evidence rather than silently enabling it or treating the 403 as a collection failure.

## JMD-specific durable notes

- JMD's real campaign registry is intentionally separate from the consent-gated runtime activation. Synthetic/non-emittable fixture tuples are test data, not authority for live campaign attribution.
- JMD-54 must remain open until positive network collection, required event delivery, GA4-side readback, and attribution-policy disposition are all evidenced.