# Configured activation negative-space probes

Use when a browser/client feature is disabled by consent, host, feature-flag, or configuration checks but can dynamically load a remote script or emit telemetry.

## Why happy-path tests miss the risk

A test that uses only the committed production value can prove that the shipped configuration is inert or that the approved debug seam works. It does **not** prove the gate rejects hostile-but-plausible runtime configuration. A broad syntax predicate (for example, `^G-[A-Z0-9]+$`) can accept placeholders, test IDs, or future unreviewed identifiers and turn a controlled debug seam into a loader/event path.

## Required probes

For every activation identifier/configuration boundary, test these independently:

| Case | Expected result |
| --- | --- |
| Committed production configuration while production remains disabled | no loader, no provider initialization, no event queue |
| Explicitly reviewed controlled-debug configuration with its separate approval gate | only the documented local/debug behavior |
| Placeholder/test identifier matching the normal syntax | fail closed: no loader, initialization, page event, or queue |
| Arbitrary syntactically valid but unreviewed identifier | same fail-closed result |
| Empty/malformed identifier | same fail-closed result |
| Review-required configuration absent (for example, no registry/manifest) | same fail-closed result |

Assert the *effects*, not merely the boolean branch: absence of inserted script, network request, provider configuration command, initial page event, and later interaction event.

## Design guidance

- Prefer an explicit finite reviewed allowlist at the activation seam over a shape-only regex when the identifier authorizes an external side effect.
- Keep a controlled debug identifier separate from production only if it is itself explicitly reviewed and tested; do not let arbitrary debug config bypass the production review boundary.
- Keep the test mutation in the existing sandbox/config-injection path where possible. Do not add a separate test-only production implementation.
- Pair each rejection with the valid reviewed debug control so hardening does not silently remove required QA coverage.

## Review handoff

Describe the blocker as an external-effect authorization defect: a syntactically valid unreviewed value can cross consent/host/debug checks and produce a loader or telemetry command. Do not call it merely a regex issue.