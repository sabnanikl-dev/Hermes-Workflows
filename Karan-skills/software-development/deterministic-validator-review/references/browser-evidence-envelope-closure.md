# Browser-evidence envelope closure and scenario identity

Use this when a committed browser-QA artifact is treated as an executable merge gate. Provider-call closure alone is insufficient: the artifact can retain valid payload tuples while lying about which route ran, what was intercepted, or what public API surface existed.

## Exact scenario identity

Bind each scenario label to its exact expected browser inputs and observations, not merely to an origin prefix and expected event list.

For every scenario, pin as contract-relevant:

- exact URL or an explicitly parsed finite URL schema;
- exact origin/hostname comparison (`new URL(url).origin === expectedOrigin`), never `startsWith`/`indexOf(0)`;
- required hostile query/fragment/referrer inputs for privacy probes;
- expected HTTP status and route facts;
- exact navigation-entry/location relationship for History API probes.

Independent false-pass mutations:

1. Change a served-article scenario URL to `/` or `/about/` while retaining its label and article payload.
2. Remove the hostile query/fragment from a privacy scenario.
3. Replace the origin with a look-alike host such as `https://expected.example.evil.test/`.
4. Swap two scenario URLs while keeping labels and all claimed outcomes.

Each must fail through the public checker.

## Interception and no-egress evidence

Requiring `aborted`, `fulfilled`, `placeholders`, or `notFound` to be arrays proves almost nothing. Define exact element shapes and reconcile them with the scenario's request inventory.

At minimum:

- require every entry to be a valid URL/string of the documented kind;
- pin expected counts or exact multisets where the harness is deterministic;
- distinguish aborted, locally fulfilled, expected 404, and forbidden/unhandled requests;
- reject unknown hosts and malformed entries;
- reconcile aggregate counts with detail rows;
- prove that clearing or fabricating interception arrays fails.

If the claim is “no real egress,” the artifact must represent every outbound request disposition, and the checker must reject any unclassified request. A source-code assertion that routing calls `abort()` is not readback proof of what a recorded run observed.

## Public-surface closure

When the contract permits only a narrow API seam, validate the browser-recorded surface against an exact scenario-specific allowlist or exact delta from a known baseline. Name-pattern rejection is insufficient: a rule that rejects only keys containing `analytics` still accepts forbidden generic APIs such as `track`, `emit`, `send`, or `configure`.

Also bind related types and values:

- exact allowed namespace keys;
- function arity where contracted;
- `gtag` presence/type;
- `dataLayer` presence/type for disabled and eligible paths;
- absence of config/event registries and debug collections.

Mutate the evidence by adding each explicitly forbidden generic API and by contradicting recorded types. Each must fail even when runtime source checks independently pass.

## Envelope and run-field closure

Reject unknown fields where they can carry provider diagnostics, public state, route facts, request data, or privacy-sensitive material. JSON cannot preserve inherited JavaScript properties, but probe dangerous own keys such as `__proto__`, `constructor`, and `prototype` at every object boundary consumed by downstream code. Exact payload closure does not imply exact run/envelope closure.

## Reporting

Separate:

1. current committed evidence correctness;
2. checker soundness under artifact mutation;
3. honesty of docs/PR claims such as “exact matrix,” “interception counts,” “public surface,” and “no real egress.”

A clean current artifact does not close a false-pass in the executable gate.
