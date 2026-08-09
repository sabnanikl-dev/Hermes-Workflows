# Protected Vercel Preview Evidence for PR-Prover

Use this when a PR's acceptance criteria require HTTP evidence from a Vercel preview, but the preview is protected by Vercel Authentication, password protection, or trusted-network controls.

## Goal

Prove the exact deployed PR head without weakening production protection or putting credentials into the repository, PR body/comments, run configuration, terminal output, or chat.

## Preferred access path

1. Prefer **Vercel Protection Bypass for Automation** scoped to preview verification. Do not disable deployment protection broadly just to make a test pass.
2. Keep the secret only in the owner-controlled Hermes environment file (`~/.hermes/.env`, mode `600`) under `VERCEL_AUTOMATION_BYPASS_SECRET`.
3. Do not request the secret in chat. Verify only its presence, for example with a boolean/non-empty check that never prints the value.
4. Send the bypass on every verification request using `x-vercel-protection-bypass`. The PR-Prover launcher inheriting the environment does **not** automatically make an HTTP probe send that header; the probe itself must do so.

## Shell-boundary pitfall

An `export` made in a user-visible desktop/embedded terminal affects only that shell and its children. It may not reach a Hermes tool-runner shell or a background PR-Prover process.

For repeatable runs, use a local launcher that reads **only** the one expected `KEY=value` entry from the Hermes env file and exports it to PR-Prover. Do not blindly `source ~/.hermes/.env`: a general-purpose env file can contain values intended for other consumers that are not valid shell syntax.

The launcher must reject a missing secret with a value-free error, never enable shell tracing, keep the secret outside the repo and PR-Prover JSON config, and pass it only to children that need it.

## Resolve the immutable preview URL through GitHub

Do not assume the Vercel bot's `Preview` link is immutable: it is often a branch alias that advances on the next push. When GitHub carries the Vercel deployment, derive the exact deployment from the PR head and then read its successful deployment status:

```bash
HEAD="$(gh pr view "$PR" --repo "$REPO" --json headRefOid --jq .headRefOid)"
gh api "repos/$REPO/deployments?sha=$HEAD&per_page=100"
gh api "repos/$REPO/deployments/$DEPLOYMENT_ID/statuses"
```

Require all of the following before using the URL as evidence:

- the deployment object's full `sha` equals the current PR `headRefOid`;
- its environment is the intended preview environment;
- the selected deployment status is `success`;
- the status supplies a non-empty `environment_url`/`target_url`;
- local HEAD, remote branch, and GitHub PR head still equal that same SHA.

The successful status's `environment_url` is the immutable HTTP target. Record the deployment id, status id, exact SHA, and URL together. A Vercel dashboard URL proves where to inspect a deployment, and a branch preview alias proves convenience access; neither substitutes for the status-bound immutable URL.

This path is useful when the public Vercel deployment API requires a separate token: GitHub already owns the SHA-to-deployment association needed for the proof. Keep the automation bypass secret independent of this metadata lookup.

## Exact-head HTTP matrix

Bind the deployment URL to the PR's current head first. Then collect machine-readable evidence for:

- each literal redirect source: required `301` and `Location`, then terminal target `200` with no extra redirect;
- representative wildcard/fallback routes;
- trailing-slash/canonicalization behavior where configured;
- intentional retired/legal and unrelated unknown paths: actual HTTP `404` plus a stable branded-page body marker;
- no external/off-site locations or redirect chains.

Treat a Vercel “Ready” check as deployment availability only — it does not prove path matching or response status.

When the frozen acceptance contract requires indexability, a platform-injected `X-Robots-Tag: noindex` on the exact deployment is a real failed gate, not harmless preview metadata. Preserve the checker result, do not rerun against a mutable alias to manufacture a pass, and do not route the failure to a builder who can only weaken the guard. Report the PR blocked until an exact-head controlled deployment satisfies the contract or Karan explicitly changes the contract. This records the proven diagnosis; it does not claim a Vercel configuration repair was performed.

## Route-specific browser and visual evidence

A sitemap-derived HTTP matrix may deliberately omit a new `noindex` route. In that case, a green matrix proves the unchanged migration surface but not the changed page. Add a separate exact-head browser gate for the route itself.

Use request routing rather than context-wide extra headers:

1. Compare every request's `URL.origin` with the immutable Preview origin.
2. Add `x-vercel-protection-bypass` only in the exact same-origin branch.
3. Refuse or separately allowlist off-origin requests without the bypass header. Never let the capability ride to a CDN, analytics host, or another Vercel tenant.
4. Record attempted URLs with any secret material redacted, plus storage, cookies, analytics globals, console/page errors, title, heading, canonical, page-owned robots metadata, footer traversal, overflow, and keyboard focus.

Capture desktop and mobile screenshots in two states: normal screenshots **before** keyboard interaction, and separate focus-state screenshots after `Tab`. Otherwise an exposed skip link can make the only screenshot look clipped even though it is correct focus behavior.

The configured visual gate should re-read the report and validate semantic fields, exact head/base binding, expected viewport labels, PNG format/dimensions, and artifact hashes. Do not accept a `PASS` string or screenshot existence alone. Pair that deterministic gate with human inspection of the normal images for hierarchy, typography, clipping, and taste.

This yields two complementary proofs:

- deployment-bound HTTP behavior for the finite migration matrix; and
- route-specific rendered behavior for the changed page.

Neither builder-local screenshots nor a green platform check substitutes for protected exact-head Preview evidence.

## Review and relay

Attach the exact-head matrix where the PR reviewer packet can read it (usually a PR comment), and record any required cross-issue inventory/handoff separately. Rerun PR-Prover only after the evidence is attached.

If PR-Prover reports a relay/transport failure, distinguish it from the reviewer verdict: inspect the retained reviewer artifact and GitHub readback before describing the code as blocked or approved.
