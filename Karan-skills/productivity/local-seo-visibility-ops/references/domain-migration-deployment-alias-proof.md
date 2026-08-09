# Domain Migration: Deployment, Alias, and Redirect Proof

Use this when a static-site migration is validated on a provider such as Vercel before DNS cutover.

## Separate the three identities

Do not collapse these into one “production URL”:

1. **Deployment identity** — immutable deployment ID plus source commit SHA.
2. **Generated deployment URL** — provider-generated hostname for that deployment. Platforms may intentionally attach `X-Robots-Tag: noindex` to preview or outdated/generated deployment URLs.
3. **Domain-assigned alias** — project alias or custom domain that serves the current production deployment. This can be indexable but is mutable.

A generated URL failing a production noindex assertion can be a target-selection failure rather than a site defect. Check provider-documented header behavior before changing settings.

## Safe proof contract

Require two independent bindings:

- provider/GitHub deployment record: deployment ID → exact commit SHA;
- provider alias metadata: tested alias → that deployment ID.

Then run the production migration matrix against the domain-assigned alias. Never call the alias immutable merely because its content currently matches an immutable deployment.

If alias metadata cannot be read back, exact byte hashes for authority files (homepage, `robots.txt`, `sitemap.xml`) plus full live-route behavior are useful narrow evidence, not a substitute for alias→deployment-ID proof. State the limitation explicitly and rerun the production matrix immediately before DNS cutover because aliases move.

## Noindex pitfall

Do **not** disable a project-wide automatic noindex header merely to make a generated deployment URL pass. That can remove the protection from every Preview deployment. Prefer a domain-assigned production target and keep Preview noindex checks intact.

After cutover, retire, unassign, or 301 any publicly crawlable non-production project alias to the canonical domain so it does not remain a duplicate-content surface.

## Redirect completeness from Search Console evidence

A green declared redirect matrix proves configured rules behave; it does not prove the legacy inventory is complete. Before DNS:

1. Compare the map with the legacy sitemap, URL Inspection sample, and performance data.
2. Preserve indexed/ranking taxonomy URLs when a relevant replacement exists.
3. Choose pattern redirects only when the whole namespace shares a truthful destination; avoid relevance-mismatched redirects that search engines may treat as soft 404s.
4. Query-only legacy URLs may need no path rule when the destination path already resolves correctly.

For a new wildcard/pattern redirect in a fail-closed repository, expect a contract change across:

- deployment configuration;
- shared pattern allowlist/namespace probe definition;
- redirect manifest and project specification;
- agent/process documentation that pins permitted patterns or counts;
- exact-list/cardinality tests and live migration matrix counts;
- a nested namespace probe with inbound-query preservation.

A matrix count increase caused by one newly approved fallback probe is expected contract evolution, not accidental drift. Prove the new total in offline/self-tests, Preview, and domain-assigned production checks.

## Preparation is not mutation authority

Keep T-24/T-1h preparation read-only unless Karan has separately approved a specific live action. In particular, a mutable alias rebind is a provider mutation, not a harmless verification step.

- Before GO: read and record the alias's current deployment binding; prepare the exact rebind plan if it is stale.
- After an explicit GO bound to the window and deployment: rebind if needed, record before/after deployment IDs, then rerun the complete production matrix.
- If exact alias metadata requires an authenticated provider UI, say so. A successful GitHub deployment record proves deployment ID → commit, and a green public-alias matrix proves current route behavior, but neither alone proves alias → deployment ID.
- A generated deployment URL that renders a provider login/protection page from an unauthenticated client is not comparable to the public alias by body hash. Treat it as an authentication boundary, not a content mismatch, and obtain authenticated alias metadata before GO.

## Custom-domain preparation before DNS

After authenticated deployment/alias proof, treat provider-side custom-domain setup as a separate mutation class from public DNS. With explicit approval, it can be prepared before the cutover window while the public site remains on the old host.

1. Attach both apex and `www`, then read back both provider domain rows individually. Multi-domain dialogs can leave only one requested hostname attached; never infer the second row exists from form input alone.
2. Expect `Invalid Configuration` or equivalent while public DNS still targets the old host. This is a prepared-not-live state, not proof of a bad deployment.
3. Read repository canonicals, sitemap hosts, and existing public behavior before accepting a provider's suggested apex/`www` redirect direction. If HTTPS apex is canonical, keep apex→`www` off and configure `www` as a permanent 308 redirect to apex.
4. Record the provider's current, project-specific apex and `www` DNS targets. Do not reuse remembered Vercel values; target IP ranges and CNAMEs can change.
5. Verify the saved row itself (redirect status and destination), not only the pre-save form.
6. Immediately re-read public NS, apex, `www`, MX, `mail`, SPF/DKIM/TXT after provider-side setup. State **prepared, not live** until authoritative DNS actually changes.

For authenticated browser work, an `unverifiable` background click requires a fresh capture before any retry so Add/Save is not submitted twice. For custom Chrome dropdowns, open the menu, capture current accessibility options, select by the exposed item, and read back the final label/row.

## Mail continuity before a website-only cutover

Do not assume a domain-looking cPanel sender identity is a real inbound mailbox. A cPanel **System** account may send successfully while replies fail with `550 No Such User Here` because no normal domain mailbox exists.

- Distinguish the System account from normal mailboxes in cPanel; do not delete or repurpose the System account.
- If the customer-facing mailbox must be created, obtain approval, then test external sender → mailbox and mailbox → external recipient/reply.
- Diagnose recipient-recognition failures separately from SPF/DMARC posture.
- Preserve nameservers, MX, `mail` A, SPF, DKIM, DMARC/TXT, and verification records when only apex/`www` web traffic moves.

## Deterministic DNS windows and rollback

A checklist is not operationally safe when it says only “watch propagation” or “roll back after prolonged failure.” Before scheduling, bind the plan to the current web-record TTL and define:

1. window start/end and the latest time DNS mutation may begin;
2. polling interval and named authoritative/public resolvers;
3. acceptable mixed-resolution state during TTL;
4. numeric availability-failure trigger (for example, consecutive failures a fixed number of minutes apart from two independent networks);
5. latest continue/rollback decision time with enough window remaining to execute and verify rollback;
6. named operator, rollback owner, and—when mail continuity matters—a real mailbox send/receive validator.

A cached old web target during TTL is expected and is not by itself a rollback trigger. A practical mixed-resolution threshold can require all authoritative nameservers to return the approved new target, at least two of three named public resolvers to return it, and no resolver to return an unexplained third target. State that the window is monitoring time, not a promise that every downstream cache will expire.

Use tiered rollback instead of treating every failure as a DNS failure:

- **Application/analytics-only rollback:** redeploy the last safe production-disabled or known-good revision while leaving healthy website DNS unchanged.
- **Website/DNS rollback:** restore only the approved web records when TLS/canonical/preflight/availability or email-continuity hard gates fail; preserve nameservers, MX, mail host, SPF, DKIM, and verification TXT records.

## Ordered cutover barrier

1. Bind deployment ID to source commit.
2. Bind domain-assigned alias to deployment ID.
3. Run full production matrix against the alias.
4. Resolve evidence-backed redirect inventory gaps.
5. Rerun the alias matrix immediately before DNS.
6. Record deterministic window, resolver, rollback, operator, and validator bounds.
7. Change DNS only with explicit approval.
8. From a clean network/CI, verify HTTP→HTTPS, apex/www consolidation, live redirects, canonicals, indexability, and any preserved email path.
9. Submit the canonical sitemap and re-inspect priority URLs in Search Console.
10. Retire or redirect the temporary project alias.
