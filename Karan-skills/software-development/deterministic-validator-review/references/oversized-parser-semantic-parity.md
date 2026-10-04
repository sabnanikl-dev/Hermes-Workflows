# Oversized-input parser semantic parity

A verified failure involved a parser recognizing every decoded `utm_` prefix as campaign-shaped while its oversized-query fallback skipped long raw keys before decoding. The fallback assumed only short known keys mattered; raw substring scanning missed an encoded prefix.

Paired reproduction:

```js
const key = '?%75tm_' + 'x'.repeat(130) + '=other';
const oversized = key + '&pad=' + 'x'.repeat(2100);
```

The short query was `unsupported`; the padded query became `none`. After granting consent on a valid GBP arrival, navigating to the padded query retained stale GBP attribution. All 121 committed logic tests still passed. This is a verified diagnosis, not a validated implementation fix.

## Reusable probe matrix

Derive current bounds and semantics from the repository:
- Query size and key size: below, at and above each branch threshold.
- Key families: approved exact keys, unknown governed-prefix keys, unrelated controls.
- Encoding: raw, once-encoded prefix, fully encoded known key, malformed/double-encoded controls according to policy.
- State: absent, valid prior attribution, revoked/expired attribution.
- Navigation: forward/history wherever classification is required.

Assert classification and downstream stored/emitted attribution. Unrelated padding must not weaken rejection. An oversized approved tuple may be rejected by policy; unrelated inputs should retain their documented behavior. Fake-provider assertions do not prove real-provider effects.

Keep remediation bounded to consistency across existing parsing branches. Preserve the independent counterexample and positive controls for re-verification. A green builder suite does not close the finding. If the authorized repair budget is exhausted, report the residual rather than implicitly starting another cycle.
