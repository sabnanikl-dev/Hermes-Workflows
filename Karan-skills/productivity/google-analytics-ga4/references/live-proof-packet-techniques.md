# Live GA4 proof packet techniques

Use this companion to `post-deploy-consent-network-proof.md` when executing a production consent/collection smoke and preparing evidence for tracker closeout.

## Privacy-safe network reduction

Live GA4 requests may contain client identifiers, cookie-derived values, page URLs, and batched payloads. Derive a reduced record in memory and persist only:

- Google host and path;
- response status and request-failure status;
- Measurement ID;
- event names admitted by a closed grammar/allowlist;
- parameter-key names admitted by a closed grammar/allowlist.

Parse both URL parameters and POST bodies; GA4 can batch newline-separated rows. Never persist cookie values, client/session IDs, arbitrary parameter values, form values, raw query strings, or full request URLs when reduced evidence suffices.

## Bounded remote-browser scenarios

Create fresh contexts and install request/response/failure listeners before navigation. Split a large matrix into bounded runs:

1. absent/dismissed/declined/malformed consent;
2. first and persisted grant;
3. revocation and post-reload zero state;
4. representative events;
5. redirect transport and payload privacy.

Combine the reduced artifacts afterward and explicitly stop remote sessions. One oversized browser evaluation can time out and discard an otherwise valid packet.

## Mixed beacon signals

A GA beacon may receive HTTP 204 while the browser also reports `requestfailed` / `net::ERR_ABORTED`. Preserve both observations. Do not call delivery from either alone; require GA4 Realtime/DebugView receipt and disclose the mixed browser signal.

For revocation, distinguish earlier-document traffic from the reloaded denied document. The defensible claim is that the **new document** creates no Google state or requests. Revocation cannot undo traffic already transmitted.

## Realtime API limits

Check the Realtime schema before selecting dimensions; it is narrower than standard `runReport`. Unsupported dimensions such as acquisition/source fields can return `INVALID_ARGUMENT` without implying a collection failure.

Use `eventName` and `eventCount` for receipt inventory when available. Prove redirect transport, canonical page fields, UTM admission/omission, and query/fragment suppression in browser/network evidence unless the exact dimension is supported. Realtime event receipt does not expose raw event parameters and therefore cannot independently prove payload privacy.

## Empty campaign-registry disposition

When no owner-approved campaign tuple exists:

1. use synthetic, non-sensitive values to prove HTTP/HTTPS, host, and legacy-route transport;
2. prove separately that the runtime omits that unapproved tuple from emitted page fields;
3. report **fail-closed attribution disposition**, not successful live campaign attribution.

## Durable packet before tracker mutation

Before changing tracker checkboxes or states, create and validate:

- a human-readable report organized by evidence layer;
- a machine-readable JSON packet with reduced scenario outputs, GA4 readback, immutable revision/deployment/public-asset binding, timestamps, source hashes, and evidence boundaries.

Parse JSON after writing and hash final artifacts before linking them. Temporary browser files are inputs; keep the final report/JSON in the approved durable artifact location.

Reconcile implementation and rollout trackers independently. A merged implementation PR can coexist with an open rollout issue, and passing rollout proof does not automatically close an implementation issue without a verified closing relation or separately reconciled acceptance contract.
