# Live preview evidence, access controls, and transport stops

## Use when

A PR's governing issue requires real hosted behavior — redirects, final status codes, 404 fallthrough, authorization, cache headers, or browser behavior — and an autonomous review/prover loop stops before the complete A → B → Auditor lifecycle.

## Exact-head live-preflight procedure

1. Read the live PR head SHA and bind the preview/deployment to that SHA. A Ready deployment is not behavior evidence.
2. Build the test matrix from the acceptance criteria: every literal source, representative pattern/fallback inputs, final target status, slash canonicalization, intentional retirements, and one unrelated unknown path.
3. Capture both the initial response and terminal response. For redirects, prove the first status + exact `Location`, then follow it and prove terminal `200`/`404`; this distinguishes a single hop from chains or soft 404s.
4. If an adjacent preflight/tracker issue owns recording the inventory, publish an exact-head handoff: PR URL + SHA, manifest path, grouped counts, intentional retirements, expected matrix, and authorization boundary. Read the tracker post back by immutable ID.

## When preview access intercepts the request

If the preview returns an SSO/login/access-control redirect before the application responds:

- classify it as **needs-Karan**: no route behavior has been observed;
- do not disable protection, alter project settings, recover/reuse a bypass secret, or try to evade the control;
- retain a sanitized observation: status code plus safe destination host/path category; do not preserve nonce/query credentials;
- request one explicit authorized next action: authenticated access for the designated preflight runner, or an approved preview-access change; then rerun the full matrix at the same exact head.

Do not treat green repository checks, a Ready deployment, or a handoff to a neighboring issue as a substitute for a governing issue's live criterion. Do not weaken the issue wording just to make a prover pass.

## PR Prover relay failure

A `needs-karan` report with `reason: relay-failure` is **two separate facts**:

1. the local reviewer artifact may contain a substantive technical verdict; inspect its retained path and report the blocker IDs faithfully;
2. `transport_complete: false` means reviewer publication/readback did not complete, so the PR has not received a valid ordered review lifecycle.

Do not hand-post a substitute reviewer artifact merely to make the PR look reviewed. That bypasses artifact identity, sanitization, and immutable-ID readback barriers. Preserve the run paths/state, fix or authorize the prerequisite, then launch a fresh exact-head Prover run.

## Evidence skeleton

```text
Head: <40-char SHA>
Preview: <safe host or URL>
Direct routes: <N>/<N> initial status + location + terminal status
Fallbacks: <representative sources> -> expected final status
Canonicalization: <slashless route> -> <slash route> + expected status
Retirements: <all listed paths> branded 404
Unknown path: <path> branded 404
Tracker handoff: <comment ID/URL read back>
Access state: <authenticated / needs-Karan; sanitized observation>
```
