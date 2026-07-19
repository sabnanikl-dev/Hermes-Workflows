# Static Catalog Action Gates and Dialog History QA

Use this when a static/frontend PR expands a catalog from a small curated set to a generated browser dataset, while per-item outbound actions remain approval- or evidence-gated.

## Contract split: candidate data is not browser action state

A hidden button is not a sufficient fail-closed boundary if disabled/unapproved destination URLs are still shipped in a browser-served asset.

Use three explicit layers:

1. **Non-browser candidate contract** — repo-visible JSON under `docs/`, `data/`, or another non-served path. Contains model identity, title, exact candidate destinations, and provenance needed by generators and QA. This is the authoritative input for tuple comparison and browser-evidence tooling.
2. **Browser catalog projection** — served UI data containing only identity, copy/specification fields, image URLs, collection/filter fields, and safe provenance. It must omit disabled/unapproved action destinations.
3. **Enabled action artifact** — browser-served action state containing URLs only for rows that pass the exact allowlist + freshness + browser-QA gate. The generator enforces candidate/authority/evidence tuple equality before emission.

Verification:

- Search all served assets for candidate destination keys/hosts and prove disabled rows are absent.
- Keep a positive synthetic enabled fixture and negative disabled/missing/stale/future/mismatched fixtures.
- Verify a neighboring disabled row stays disabled when one fixture row is enabled.
- Do not mutate committed production authority/evidence merely to test the positive path.

## Producer/validator contract parity

When an earlier issue ships a browser-QA producer that advertises `--source=<catalog>`, execute it against the actual new artifact before closeout. Schema comments are not evidence of compatibility.

Required regression:

- Load the authoritative non-browser candidate contract through the real producer/parser.
- Assert the complete candidate universe and exact model/title/customize/order pairing.
- Exercise dry-run or bounded planning without contacting external destinations.
- Feed the resulting shape into the existing validator and prove resumability/fail-closed behavior.

Common failure: the producer expects JSON `products[]`, while the new catalog emits JavaScript `window.* = { records: [...] }`. Fix with one authoritative JSON contract or an explicit tested adapter; do not point tooling at an incompatible browser bundle.

## Query-state preservation

Treat a selection parameter such as `?shoe=<id>` as one field in the current URL, not as the whole URL.

- Build from `new URL(window.location.href)`.
- On open, set only the selection parameter.
- On UI close, delete only that parameter.
- Preserve all unrelated query parameters, hash, and applicable `history.state` fields.
- `popstate` must open/close without pushing another entry.
- Recheck the current URL after async catalog load so stale deep-link intent cannot reopen after Back/close.

Regression cases:

- `?utm_source=test&shoe=6034#catalog` opens correctly.
- UI close preserves `?utm_source=test#catalog`.
- Back closes, Forward reopens, and same-model open is idempotent.
- Empty, malformed, duplicate, encoded-markup, and unknown IDs leave the catalog usable.

## Dialog close/reopen timer race

Animated teardown often schedules `overlay.hidden = true` after a delay. If the dialog reopens before that callback fires, the stale timer can hide an open, scroll-locked modal.

Rules:

- Track the pending hide timer explicitly.
- Cancel and clear it at the start of every open/reopen path.
- Clear it during teardown/dispose.
- Balance scroll lock, inert/`aria-hidden`, listeners, and focus restoration across every close path.

Regression: close and immediately reopen via keyboard/history inside the transition interval; after the old delay elapses, assert the dialog remains visible, focus is inside, background state is correct, and one subsequent close fully cleans up.

## Review-loop use

If Hermes discovers one of these blockers independently:

1. Post it to the PR bus with exact file/line evidence and authoritative issue text.
2. Let independent reviewers evaluate the same current head.
3. Send Claude a pointer-first fix prompt to read all live blockers.
4. After the fix, verify remote head, rerun the real producer/validator integration and browser QA, then rerun both reviewer roles on the new head.
