# Credential-bearing network gate origin binding

## Trigger

Use before launching an autonomous review when a preview, deployment, browser, or API gate attaches a secret header, cookie, token, or bypass credential to requests made against an operator-supplied URL. Credential egress is an independent safety boundary even when the requested repair concerns parsers, SEO, redirects, or another narrow subsystem.

## Core risk

A wrapper may correctly bind deployment ID → commit → immutable URL while the lower-level repository CLI still accepts an arbitrary origin and attaches the credential before functional checks can fail. A failure after the first request is too late.

Trace the full path: URL argument/environment → URL parser → client/observer construction → request headers → every redirect/manual hop.

## Required contract

- Bind a credential-bearing run to one exact trusted origin derived from the deployment-binding trust root.
- HTTPS alone is insufficient.
- Shared-host suffixes such as `*.vercel.app` are insufficient because unrelated tenants can own matching hosts.
- Do not trust a second unconstrained copy of the same caller-controlled base URL.
- Attach the credential only when each request origin exactly matches the bound origin.
- Never forward the credential off-origin, including manually observed redirects.
- Preserve no-secret immutable-production runs.
- Never print, commit, fixture, packetize, or expose the real secret to builder/reviewer lanes.

## Atomic capability implementation pattern

When the repository CLI must consume both the credential and its authorized origin, prefer one strict atomic value rather than a standalone secret plus an independently caller-controlled origin. A validated pattern is:

```json
{"origin":"https://exact-immutable-deployment.example","secret":"<memory-only>"}
```

The trusted deployment-binding wrapper mints this value only after proving deployment ID → expected commit → immutable URL. The CLI then:

1. accepts a JSON object with exactly `origin` and non-empty `secret`;
2. parses `origin` through the same bare-HTTPS-origin parser used for the requested base;
3. requires exact origin equality before constructing the credential-bearing observer;
4. rejects legacy standalone-secret inputs before the first request;
5. has the observer independently refuse any credential-bearing off-origin request before the injected/real fetch call;
6. never includes the raw capability in parse errors, observations, summaries, fixtures, comments, or logs;
7. preserves credential-free production runs.

This is capability binding, not hostile-owner containment: a process that already controls and can read the secret can always disclose it. The contract prevents base-only injection, operator mismatch, unrelated shared-platform tenants, and future off-origin request paths from receiving the credential accidentally or through an untrusted URL argument. Do not widen this into cryptographic signing, a proxy, or a new authentication architecture unless the mission threat model explicitly requires those.

Credential-free repository gates and dry runs should scrub all preview-capability and legacy-secret variables from their subprocess environment. The protected-preview gate should load the real secret only after deployment binding, mint the atomic capability in memory, clear legacy inputs, and launch the network check without printing the value.

## Safe deterministic probe

Use an injected fetch/client and a fake sentinel, with no external request. Prove both whether the parser accepts the candidate origin and whether the request adapter attaches the sentinel. An arbitrary accepted origin plus `sentinelForwarded: true` is a blocking credential-exfiltration path even if every later functional check fails.

Require permanent no-network negatives for:

- arbitrary external HTTPS origin;
- unrelated tenant on the same hosting suffix;
- mismatch between bound origin and requested base;
- off-origin redirect/manual hop;
- exact bound-origin success;
- no-secret production success.

## PR Prover use

When any baseline gate uses protected-preview credentials, include origin and redirect egress explicitly in Reviewer A, Reviewer B, and Integration Auditor focus from the first run. Bind deployment ID, status, commit, immutable URL, and gate result in the evidence packet, but never the credential.

If a final bounded repair clears its authorized findings and a fresh triad discovers a credential-boundary blocker outside that authorization, stop mutation. Report the exact head and sentinel reproduction, keep the PR unmerged, and request a separate trust-contract decision; prior repair approval is not authority for another security change.
