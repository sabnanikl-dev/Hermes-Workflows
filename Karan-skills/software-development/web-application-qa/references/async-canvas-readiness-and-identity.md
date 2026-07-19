# Async canvas/WebGL readiness and identity QA

Use this playbook when a configurator, visualization, editor, map, game-like UI, or other canvas/WebGL application appears stuck, login-gated, blank, or identity-unprovable during automated browser QA.

## Core diagnostic principle

Do not classify the rendering technology itself as the outcome. A canvas or WebGL context is neither success nor failure. Classify the **active user-visible state after a bounded readiness wait**.

A common false-negative pattern is:

1. Navigate with `waitUntil: "domcontentloaded"`.
2. Sleep a fixed short interval.
3. Observe a loader, zero-size canvas, or generic shell.
4. Treat `hasWebglCanvas` as equivalent to an active login/error gate.

Heavy vendor applications may finish well after DOMContentLoaded. Fixed sleeps make results dependent on network, cache, GPU startup, and concurrent asset loading.

## Readiness before classification

Prefer a bounded readiness predicate over a fixed sleep. Wait until either a positive state or a terminal negative state becomes observable, with an overall timeout.

Positive readiness can require a conjunction such as:

- Expected title or identity label is visibly rendered.
- Primary canvas has a non-zero backing size and non-zero visible rectangle.
- Flow-specific controls are visible (materials, colors, layers, parts, save/order controls, etc.).
- Loading overlay/progress indicator is absent or hidden.
- No active blocking modal is visible.

Terminal negative states can include:

- Visible login, consent, permission, maintenance, generic-catalog, no-results, or error state.
- Navigation failure or bounded timeout.
- Loaded-but-wrong identity.

Capture state transitions when timing is uncertain: immediately after DOMContentLoaded, at the historical sample point, and at the final bounded timeout. This distinguishes a genuinely stuck app from one sampled too early.

## Visible state versus dormant markup

Do not search the entire HTML or generic text blob for words such as `login`, `consent`, or `error` without checking visibility and context. Vendor templates often ship dormant login/admin panels, fallback WebGL warnings, and error templates in hidden DOM.

A gate is active only when supported by visible UI or current application state. Conversely, do not rely on accessibility snapshots alone for canvas apps: pair them with screenshots, computed visibility, canvas geometry, DOM text, and console/network evidence.

## Identity proof for opaque deep links

Canvas pixels may not expose a numeric product/model ID, and titles may repeat. Bind identity through multiple independent signals:

1. Exact approved destination URL and host.
2. Parsed or decoded deep-link token/UUID correlated with the approved source tuple.
3. Expected visible title or label.
4. Flow-specific controls proving the correct application state.
5. Visible non-zero canvas when rendering is part of the product.
6. Absence of competing identity signals.

Do not accept a repeated title alone when it is non-unique. If an opaque Customize token decodes to an order/design UUID, verify that UUID matches the approved Order URL or source contract before treating the title as exact identity evidence.

## Network and console triage

Collect failed requests, HTTP errors, and console output, but distinguish **fatal blockers** from **non-fatal vendor noise**.

A 404 for an optional translation, icon, texture, or fallback asset is not automatically the root cause if the expected product and controls render correctly. Report it as fragility only after correlating it with user-visible impact. Conversely, a missing identity/configuration payload is suspicious even if a fallback model renders; verify the approved token/title tuple rather than assuming the visible object is exact.

## Classifier design

Keep readiness and classification separate:

1. Observe until positive readiness, terminal negative state, or timeout.
2. Capture the resulting evidence.
3. Classify from that evidence.

Avoid logically self-fulfilling gates such as:

```js
if (hasWebglCanvas && (looksLoginGate || hasWebglCanvas)) fail();
```

This makes every WebGL application fail by construction. Instead, fail only when the **active gate** is proven or required identity/readiness signals are missing.

## Verification matrix

For each required model/flow, cover every required viewport independently. Record:

- Final URL and approved tuple/token match.
- Expected title/identity signals.
- Canvas backing and visible dimensions.
- Required visible controls.
- Active blocking-state result.
- Time to readiness.
- Screenshot.
- Failed requests and relevant console errors.

Before approving a fix, mutation-test or negative-test the classifier with:

- Slow-but-successful load.
- Permanent loader timeout.
- Hidden login markup but successful visible app.
- Active visible login gate.
- Correct title with wrong token/UUID.
- Repeated title without exact tuple proof.
- Non-zero canvas with wrong identity.
- Correct identity and controls in both desktop and mobile viewports.
