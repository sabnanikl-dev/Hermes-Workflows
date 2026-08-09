# Staged deployment proof and exact-head rebinding

Use this reference when a PR must be proven on a protected preview, while final indexability can only be tested on a production deployment after merge and before DNS cutover.

## Contract split

Do not remove a platform's preview `noindex` merely to make a production-oriented checker pass. Make the stage an explicit CLI/API input; a networked run with a missing or unknown stage must fail before any request.

| Stage | Exact state | What it proves | Noindex rule |
|---|---|---|---|
| `preview` | immutable deployment bound to the open PR head | routes, canonicalization, redirects, sitemap, robots, branded 404, transport completeness | require a broad/unscoped platform header safeguard; reject page-owned meta noindex |
| `production` | immutable deployment bound to the merge commit, after merge and before DNS cutover | the same finite matrix plus final indexability | reject any header noindex and any meta noindex on expected indexable routes |

A preview PASS is technical PR evidence, not migration/cutover authority. A production PASS is still evidence, not authorization to change DNS.

A useful negative boundary probe is to run production mode against the protected preview and require only the expected indexability rows to fail. Record it as boundary proof, never as production evidence.

## Head-changing repair loops

Every builder push invalidates all of these:

- deployment ID and status ID;
- immutable URL;
- live check output;
- Reviewer A/B/Auditor artifacts;
- PR-body claims naming the old head.

A common trap is a Prover config that pins the initial deployment ID/URL while allowing a builder cycle. The next gate receives the new `{head}` but still checks the old deployment, so a correct repair is guaranteed to fail for stale evidence.

### Safe gate shape

For a mutation-capable run, the trusted live-gate wrapper should accept `{repo}` and `{head}` and:

1. verify its checkout is exactly `{head}` and clean;
2. query deployments filtered by the full SHA, not by branch alias;
3. require the expected environment and select the newest unambiguous candidate;
4. bounded-poll deployment statuses until success, explicit failure, or timeout;
5. require the successful status's immutable `environment_url` and re-check deployment SHA/ref equality;
6. load any bypass secret locally, pass it only to the checker child, and never print or serialize it;
7. run the explicit preview stage and require the complete finite matrix;
8. verify HEAD and worktree cleanliness again.

Preflight deployment readiness before the first Prover launch. If a repaired head's deployment never becomes ready, classify that as infrastructure/control-plane failure and pause/resume without spending another code-repair cycle. Never send a deployment-pending or stale-binding failure to the builder as a code defect.

A static deployment ID/URL is acceptable only for a review-only run where no builder can change the head.

## Evidence ledger

Record and read back:

- local, remote branch, and PR head SHA equality;
- deployment ID, deployment status ID, environment, deployment SHA/ref, and immutable URL;
- checker stage and exact check counts;
- preview safeguard presence on every expected route;
- expected negative-boundary result, if run;
- post-merge production gate owner and before-DNS stop condition;
- current reviewer artifacts and whether they bind the same head.

Prefer the PR body or a repository-owned proof document for the contract. Keep bot/status comments reconciled with an exact, body-evidence-bound acknowledgement when the Prover requires it.

## Former-red probes for live-checker soundness

A happy-path 63/63-style matrix does not prove that its predicates are sound. Keep deterministic former-red tests for these classes:

### Inbound query preservation

Append a two-parameter sentinel query to every redirect probe and require the observed `Location` destination to preserve it exactly. The source request must contain the query; a test that starts queryless and rejects an unexpectedly added query proves the opposite direction. If manifest sources/destinations already contain queries and merge semantics are not explicit, fail plan construction rather than guess.

### Complete evidence on every hop

Check observation completeness immediately after every request, before status or header assertions. Do not enforce completeness only inside a body/media-type helper used by terminal HTML responses; redirect and canonical first hops can otherwise pass after timeout, truncation, decode failure, or read error.

### Global versus crawler-scoped directives

Parse `X-Robots-Tag` into directive groups with crawler scope retained. Keep two predicates:

- **any noindex** — conservative production failure if any crawler is denied;
- **site-wide noindex** — preview safeguard proof only when an unscoped directive applies broadly.

`bingbot: noindex` or `googlebot: noindex` must not prove a site-wide preview safeguard, even though either should still make production indexability fail conservatively.

For each repair, revert the production change temporarily and confirm the new test goes red. This guards against adding a test that never exercised the former false pass.

## Closeout language

Report these separately:

- deterministic exact-head suite;
- exact-head immutable preview proof;
- Prover lane state (`active`, `complete`, or `blocked`);
- technical merge recommendation;
- outstanding post-merge immutable-production indexability proof;
- human merge and DNS authority.

Never collapse “merge-ready code” into “migration-ready site.”
