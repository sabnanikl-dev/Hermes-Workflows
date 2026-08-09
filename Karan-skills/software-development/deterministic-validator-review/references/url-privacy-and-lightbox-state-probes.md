# URL privacy and lightbox state probes

Use this matrix when a deterministic test/validator claims PII-safe analytics URLs or exact UI-state analytics.

## URL-derived analytics

| Claim | Invalid probe | Expected | Valid control |
|---|---|---|---|
| Path is PII-safe | `/reset/alice@example.com/` | collapse to safe fallback path | each committed shipped route remains itself |
| UTM excludes names/free text | `utm_campaign=JaneDoe` | omit | approved campaign token survives |
| Encoding cannot bypass policy | `utm_campaign=Jane%44oe` | omit after `URLSearchParams` decoding | conventional URL-safe token survives |
| Email/phone excluded | `alice%40example.com`, `%2B17709229078` | omit | `google`, `cpc`, `summer_sale` survive if explicitly allowed |
| Arbitrary query/hash excluded | `email=...#fragment` | omit | only documented acquisition fields survive |

A regex such as `^[A-Za-z][A-Za-z0-9_-]{0,63}$` is a lexical shape check, not a free-text classifier: it accepts `JaneDoe` both literally and after percent decoding. If a policy promises no names/free text, a finite allowlist (or an equivalently non-free-text policy) is needed. Do not merely add the same permissive regex to the test.

## Lightbox/modal analytics

The analytics event must fire only after the component has committed an open dialog state—not at a document-wide click/keydown seam. Assert:

1. Genuine image click → dialog open and exactly one event.
2. `Enter`, `" "`, and legacy `"Spacebar"` → dialog open and exactly one event each.
3. Activation while already open → still one dialog, no second event.
4. Pointer down → move beyond gesture slop → pointer up → synthetic click → no dialog and no event.

### Fixture trap

Many carousel implementations deliberately skip pointer setup when there is fewer than two images. A one-image lightbox fixture can validate click/keyboard behavior but cannot validate actual swipe suppression. Use two or more items for the pointer lifecycle test; directly setting `_lastDragMoved` or a comparable private flag tests only the click branch, not the real gesture path.

## Reporting

Separate the outcomes:

- **Current artifact behavior:** what the live component/code emits.
- **Guard soundness:** which hostile values or real event sequences the validator failed to cover.
- **Claim honesty:** whether comments/docs claim PII-safe/free-text-safe behavior stronger than the implemented boundary.
