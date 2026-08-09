# Fail-closed client analytics repairs

Use when an exact-head PR review finds a browser analytics/privacy failure that appears only after a future activation gate or under hostile browser storage behavior.

## Review destination authority, not only ID syntax

A regex-shaped Measurement ID is not proof it is reviewed. Keep the production ID centralized in immutable/default configuration. Treat activation as membership in a small reviewed set: configuration may select from that set but cannot extend it. Drive production and controlled-debug seams with placeholder/unreviewed IDs, before and after explicit consent, and assert no loader, data layer, provider config/page-view, or event. Retain a reviewed-ID positive control.

## Treat browser globals as mutable input, not analytics authority

A page-global configuration or generated-data object is not a trustworthy authority boundary. For static analytics wrappers:

1. Keep production enablement, host, measurement ID, loader URL, consent keys, and debug-host allowlist in source-owned constants. A page config may only enter a deliberately bounded debug seam and select from a reviewed ID set; it must not expand production authority.
2. On wrapper load, validate and capture route data into an internal immutable representation. Do not read a mutable `window` manifest at event-dispatch time, and do not expose mutable live taxonomy/parameter objects through the public API.
3. If a future issue owns campaign-registry publication, ignore every preloaded/reassigned page-global campaign registry until that issue's owner-reviewed generated artifact exists. A syntactically valid unreviewed tuple is still untrusted.
4. Treat `document.referrer` as a separate PII surface. Set `page_referrer` explicitly to an allowlisted safe value (often empty) on both config and explicit `page_view`; sanitizing `page_location` alone is insufficient.
5. Prove these boundaries behaviorally: mutate config, the exported API, taxonomy, route manifest, and a shape-valid campaign registry after load; inject referrer query/hash data; then assert no authority expansion or PII reaches any queued payload. Include a controlled-debug positive control so a no-op wrapper cannot pass.

Before the first exact-head review, scan the living spec, non-goals, contracts, and generated-blog documentation for stale claims such as “no analytics” or “no runtime ships”. Runtime + static/generated blog wiring must be reconciled in every document that claims current implementation state.

## Make consent revocation independent of storage persistence

A failed storage write must never keep current-page collection alive:

1. Emit a denied-consent update only when an already-active tag can receive it; an inactive decline must not create a loader/data layer.
2. Tear down in-memory enabled/initialized state before persisting.
3. Keep an in-memory revocation that outranks a still-readable prior grant for that document. It may only withhold consent, never manufacture it.
4. Persist afterwards; a boolean return must truthfully describe persistence, not whether collection was stopped.
5. Allow re-grant only after the new grant successfully persists. Keep no-duplicate-loader lifecycle behavior.

## Required deterministic fixture

Use storage whose `getItem()` returns a prior `granted` value while `setItem()` throws. Begin from eligible active state, decline, then prove denied update, disabled state, refused `send()`/`init()`/DOM events, unchanged loader/event count, failed re-grant inertness, and a silent inactive-state decline. Mutation-test restoration of persistence-first order and removal of only the in-memory revocation.

## Repair-cap discipline

A privacy/security blocker found after nominal final proof is substantive despite green suites. Never waive it through acknowledgements. With the normal cap exhausted, request a new explicit single-finding Karan exception, enumerate allowed surfaces and prohibited adjacent changes, and require a fresh exact-head triad. Do not silently authorize a further repair if that review finds another issue.
