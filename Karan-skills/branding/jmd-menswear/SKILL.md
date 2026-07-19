---
name: jmd-menswear
description: JMD Menswear client engagement — owners, systems, pricing, status, and attack plan reference. Active engagement started 2026-04-28.
tags: [jmd, client, menswear, conyers-ga]
triggers:
  - "jmd"
  - "jmd menswear"
  - "lucky"
  - "danny"
---

# JMD Menswear — Client Profile

## Business
- Specialty men's formal wear store, Conyers, GA
- One-of-a-kind pieces, one size per style. "When it's gone, it's gone."
- Suits, tuxedos, shoes, accessories — retail + prom/wedding/quinceañera rentals
- Owners: Lucky (brand personality, content face) + Danny (inventory, purchasing, cautious)

## Pricing (Performance-Based)
- $500 setup + $750/mo + 10% performance share
- Guaranteed: $2,750 over 90 days

## Systems
- POS: Comcash (weekly CSV export → Google Sheet)
- SMS: Trumpia (review requests, inventory alerts)
- Website: GoDaddy registrar; DNS currently delegated to HostGator nameservers; emergency holding page should use HostGator/cPanel unless it blocks launch
- CMS: Sanity project `yjaks0cn` for JMD Studio/backend work; verify dataset before deploy or writes
- GBP: Karan has manager access; GBP API application case ID 7-0941000040185
- Social: Instagram/Facebook — need creds from Lucky

## Key Constraints
- NO AI-generated content. Everything must sound like Lucky.
- Danny cautious about e-commerce. Online = showroom, not warehouse.
- Real photos only. No stock images. No AI images.
- Karan confirms Lucky’s answers are sufficient stakeholder approval for JMD website copy and commerce-adjacent made-to-order handoff details.
- Lucky approval required before any content goes out.
- Client-facing reports/presentations for JMD should speak directly to Lucky and Danny, not read like a generic agency audit. Lead with what is working, then exact fixes, then owner-specific approvals. Tie recommendations to calls, directions, store visits, trust, and customer confidence.

## Access Status (as of 2026-04-28)
- ✅ GoDaddy domain access
- ❌ GBP access (need to claim)
- ⚠️ Store photos (a few, need more)
- ❌ Comcash export capability
- ❌ Trumpia account
- ❌ Instagram/Facebook creds

## Build Approach
- Multi-agent: Hermes orchestrates → Claude Code builds → Codex reviews
- Repo: clone sabnanikl-dev/agentic-harness-template → populate spec.md
- Project brain: execution in repo docs/, knowledge in Obsidian wiki

## Attack Plan
Full 12-week plan at: ~/projects/consultancy/JMD-Menswear/plans/
- week-1-technical-plan.md (471 lines)
- week-2-technical-plan.md (414 lines)
- weeks-3-4-technical-plan.md (636 lines)
- weeks-5-8-technical-plan.md (312 lines)
- weeks-9-12-technical-plan.md (494 lines)
- jmd-operating-model.md (387 lines)

## Wiki Pages
- ~/obsidian-vault/hermes-brain/wiki/consultancy/clients/JMD/Client JMD Menswear.md
- ~/obsidian-vault/hermes-brain/wiki/consultancy/research/JMD Competitor Landscape.md
- JMD Visibility issue closeout rule: `references/jmd-visibility-durable-knowledge-closeout.md`. Every active/future JMD Visibility issue must either promote source-backed durable JMD knowledge to the canonical client/topic wiki with exact path + readback evidence in Linear, or explicitly state that no durable knowledge was produced; never mirror task state or transient metrics into Obsidian.

## Week 1 (starts 2026-04-28)
- GBP audit + claim
- Website holding page via HostGator/cPanel first; avoid nameserver change unless needed
- Baseline metrics capture
- Karan visiting store in person for content (hybrid approach)

## About Page Content Intake
- Detailed reference: `references/about-page-content-intake.md`
- For a dedicated JMD About page, collect Lucky/Danny source material through a structured client email rather than writing generic copy from assumptions. Ask for a real approved photo of Lucky and Danny in the store, owner-role answers, showroom-experience language, local Conyers connection, limited-floor wording, anonymized customer stories, tone preference, and explicit claims to avoid. Include a fill-in-the-blank shortcut so Lucky can respond quickly.
- SEO lens for About page: branded/local trust (`JMD Menswear`, `JMD Menswear Conyers`, `men's formalwear store Conyers GA`) plus natural event/service context (suits, tuxedos, formalwear, prom, weddings, quinceañeras, special events). Preserve Lucky's voice; do not invent facts, dates, service claims, or inventory/availability language.

## About / Website Copy Response Ingestion
- Detailed reference: `references/about-page-response-ingestion.md`
- When Lucky/Danny respond to the About-page or general website-copy intake and Karan asks to synthesize it into the repo, create a repo-local `docs/content/` source document first, then update/comment existing issues and create granular implementation issues. Prefer a clean worktree from `origin/main` if the main checkout has unrelated local changes.
- Treat the email as source material, not final public copy: preserve client facts/phrases, synthesize draft-only copy blocks, and mark blocked inputs such as missing approved owner photos. Even if Lucky casually says a customer story can be made up, do not fabricate one by default; require Karan/Lucky approval for any composite/anonymized story.
- After creating the docs PR/issues, verify the pushed branch SHA, PR commit list, and issue bodies/comments before reporting success.

## Landing Page Approved Copy Data
- 2026-05-12 JMD email approval for rentals/product cards:
  - Public rental copy should mention **tuxedo rentals only**; do not describe suit rentals unless separately approved.
  - Rental ensemble includes tuxedo, shirt, vest, and bowtie.
  - Approved starting price wording: `$209.99 and up`.
  - Wedding groups **prefer appointments** and typically need a **minimum of 3–4 weeks**. Do not turn this into a stricter “appointments required” or weaker “usually 3–4 weeks” claim.
  - Single rentals such as prom are welcome as walk-ins.
  - Product cards should stay general until JMD chooses exact garments and agrees who maintains details; avoid hard product prices, size runs, stock counts, live availability, or urgency claims by default.
- Copy-fidelity pitfall: for JMD stakeholder-approved wording, preserve modal verbs and qualifiers exactly (`prefer`, `minimum`, `and up`). A reviewer caught “should schedule” and missing “minimum” as blockers because they changed the approved meaning.

## GBP Client Report + Follow-Up Lessons
- Detailed reference: `references/gbp-client-report-and-followups.md`
- Testimonials/reviews population workflow: `references/testimonials-gbp-to-sanity-curation.md`. For JMD homepage testimonials, use Google review candidates as inputs to Sanity `testimonial` records and require Karan/Lucky approval before making them visible on the website. Current live behavior after GitHub #139: `/api/testimonials` is the ordinary Sanity-backed read path for approved published testimonials, with `site/assets/js/testimonials.data.js` as fallback/offline snapshot only; do not tell builders to regenerate the static artifact after every Sanity change. Current implementation still has a confusing second gate (`testimonial.status == "published"`) in addition to Sanity's native Publish state; GitHub #145 tracks removing/deprecating that custom status gate so normal Sanity Publish controls visibility. Until #145 lands, if a testimonial is missing from non-prod, check both: (1) the document is Sanity-published under `perspective: "published"`, and (2) the custom `status` field is `published`, plus quote/rating/source validation. If adding or reviewing server-side Sanity reads, keep `@sanity/client` in runtime `dependencies` (not dev-only), keep `SANITY_READ_TOKEN` server-side only, and preserve no deploy/content mutation boundaries unless explicitly approved.
- Client-facing GBP reports for JMD should speak directly to Lucky/Danny as owners: what is working, what needs fixing, what needs owner approval, and how fixes increase calls/directions/website clicks/store visits.
- Use one combined owner approval checklist unless the user explicitly asks to split Lucky vs Danny responsibilities.
- Be specific about evidence: YellowPages is the known source of the hours inconsistency from JMD-2; do not describe it vaguely as "one directory" when client-facing.
- Do not overstate review response work; JMD had only a few unanswered reviews, so frame it as light trust cleanup.
- 2026 Q&A strategy: traditional GBP Q&A is no longer the primary play after Google's Q&A API shutdown; improve GBP answer sources, website FAQs/FAQ schema, specific reviews, and Ask Maps/AI answer monitoring.
- GBP growth planning should track action rates from profile views: website click rate, direction request rate, call rate, and combined action rate. Use UTM-tagged GBP links and mobile landing pages with call/directions above the fold.

## Inventory Backend + Drive Automation Plan
- Detailed reference: `references/inventory-backend-automation-plan.md`
- Canonical tracker home for the May 14 / JMD website photo-automation plan is **Linear JMD-23**, with child issues under that packet.
- Supporting local repo research doc: `~/projects/consultancy/JMD-Menswear/deliverables/JMD-Website/docs/research/inventory-backend-automation-plan.md`.
- The local doc may be an earlier/supporting draft; when Karan asks where the plan is, point to **JMD-23 first**, then cite the repo doc as supporting material.
- Recommended architecture: Google Drive intake → approval ledger → Sanity CMS/assets → scheduled publish/archive automation → website showroom section.
- Safety rule: do not publish raw Drive uploads directly to the public website; human approval is required before anything goes live.
- When Karan says to “work on JMD-23” or “open a PR” for this packet, start with the first reviewable child slice unless he names another child: JMD-24 architecture/docs is the safe first PR. Do not jump straight to live n8n credentials, Drive folders, Sanity writes, deployment, DNS, or public website mutations. Keep the parent in progress, move the child to review after PR, and comment back in Linear/GitHub with the PR URL and no-live-change boundary.

## Photo Automation Direction
- JMD showroom photo automation direction: Google Drive approved folder = source of truth; if Lucky/Danny place images there, v1 treats them as approved. Use n8n scheduled reconciliation as deterministic workflow layer, Sanity as CMS/image CDN, and website queries Sanity only. Archive, do not hard-delete. Keep showroom language only: no e-commerce, checkout, exact live availability, prices, quantities, stock counts, AI images, or stock photos. Use `n8n-deterministic-workflows` skill for implementation/review details.
- Client backend explainer deck guidance: `references/client-backend-explainer-decks.md`. For Lucky/Danny-facing slide decks about Drive → n8n → Sanity → frontend, default to a concise 6–8 slide deck, use actual current website/Sanity feed photos from `site/assets/js/on-the-floor.data.js`, include timing/counts (sync cadence, current feed count, live cap, age window, min-live, archive-not-delete, archive safety threshold), and visually QA key slides for clipping/legibility before handoff.
- Client-facing description pitfall: do **not** describe the showroom photo system as a future/hypothetical “we can set up a system” if the repo/non-prod site already has it wired. Before drafting client email or sales copy about this feature, inspect the JMD website repo/current non-prod state and describe what is real now: the non-prod `On the Floor` section, Sanity-sourced public-safe photo feed, n8n/Drive→Sanity managed pipeline, and any remaining gated steps such as schedule activation or live archive/restore mutation. Translate verified implementation into layperson value-prop language.
- Client-facing wording preference for Lucky/Danny: keep the showroom automation explanation casual and concrete. Say it starts with a **regular Google Drive folder** they can use like any normal upload/drag-and-drop folder, then the system picks up approved photos, prepares/stores them in the backend, and makes them available for the website. Avoid prefacing with “in plain English” or similarly tutorial-ish phrasing; Karan found that too staged. Emphasize usefulness: keeps the showroom section fresh without manual website rebuilds, while avoiding e-commerce/live-inventory implications like prices, sizes, stock counts, or checkout.
- When grooming or implementing JMD Sanity Studio work, do not leave the scope at “wire project ID.” The expected backend slice is: deploy a Studio connected to project `yjaks0cn` after dataset verification, add/register blog CMS schemas for the website blog section, and confirm/refine the `showroomPhoto` backend for n8n-dropped approved images. Acceptance criteria should include Studio build/schema validation, deployment evidence/URL when approved, no committed secrets, no live content publishing, and no n8n schedule activation unless explicitly approved.
- Verification/test-credential details: `references/showroom-n8n-test-verification.md`. For JMD-34/JMD-35-style required Hermes verification, report real test output and boundaries separately: workflow export validation, inactive workflow state, no committed credentials/secrets, test-only Drive folder/credential scope, no Sanity writes, no schedule activation, no deploy, and Linear comment verification. If OAuth2 is used because n8n's local Google Drive credential type is OAuth2-only, be honest that containment is operational/config-based unless a true least-privilege service-account setup is available.
- Run reporting / owner-safe SOP contract: `references/showroom-run-report-sop-contract.md`. For JMD-29/GitHub #66-style work, the deliverable should be a beautiful branded HTML report matching JMD navy/midnight/gold/cotton styling, plus plain-English owner SOP and separate operator diagnostics. Fold in current JMD-23 child outcomes (25-node n8n graph, nested-folder source, import/touch/archive/restore, schedule evidence, Sanity-only website feed), but keep hard gates explicit: no credential/account mutation, schedule change, deploy, live data mutation, or owner-facing delivery without approval. Reporting fixtures must not fossilize stale counts; sync/rebase against current main and distinguish report-generated time from actual run/execution time.
- Showroom photo timing / client-safe explanation: `references/showroom-photo-timing-explanation.md`. When explaining “when photos appear” or “how long they stay,” separate Drive→Sanity sync timing from Sanity→static-site feed rebuild/deploy timing. Verify current schedule, active runner, latest trigger-mode execution, archive policy env values, and whether the site is still static before making live/client-facing claims.

## Content Engine / Video Automation Direction
- Detailed reference: `references/content-engine-video-automation-research.md`
- For JMD short-form social, default to a human-approved deterministic pipeline: Lucky/Danny phone footage → Drive/Dropbox/Telegram intake → tracker → FFmpeg/Whisper processing → OpusClip/`opus-skills` or transcript rules for candidate clips → Hyperframes/Remotion for branded captions/lower thirds/end cards → Lucky/Karan approval → manual/native posting first, API publishing later via Ayrshare or Meta/TikTok only after the workflow is stable.
- Avoid AI-generated/avatar-video tools as the core workflow because JMD requires real footage only. AI is acceptable for assistive transcription, caption drafts, clip suggestions, titles/hooks, and file routing when reviewed.
- CapCut CLI is a useful human-review bridge into CapCut drafts, but treat it as optional and backup-sensitive because it relies on CapCut/JianYing draft schema behavior.

## GA4 Analytics + Hosting Cutover
- Detailed reference: `references/ga4-cutover-operations.md`.
- JMD analytics direction is GA4 via the direct Google tag (`gtag.js`), with Google Tag Manager deferred until multiple approved destinations justify it. Keep coding in GitHub and non-coding account/privacy/legacy-Ads/cutover/monitoring work in the JMD Visibility Linear project. Never silently migrate or remove the live legacy Ads/phone-conversion configuration; verify ownership/activity and record an owner-approved preserve/replace/retire decision first.

## Canonical URL + Social Metadata
- Detailed reference: `references/canonical-social-metadata.md`
- For repo SEO/social metadata, current evidence supports HTTPS apex canonical: `https://jmdmenswear.com/`; `www` redirects to apex. Verify live redirect behavior again before changing canonical fields.
- Keep canonical URL, `og:url`, JSON-LD `url`, `robots.txt` sitemap directive, and `sitemap.xml` `<loc>` consistent. For Open Graph images, use only real JMD design/brand assets; prefer a verified 1200×630 optimized JPEG and record source path, dimensions, bytes, SHA-256, and approval caveats in repo docs/evidence.
- Metadata PRs do not authorize deployment or DNS/HostGator/GoDaddy/Vercel/SSL/email changes.

## Website GitHub Issue Creation / UI Polish
- Post-merge owner approval gate pattern: `references/post-merge-copy-approval-gates.md`. Use it when a merged JMD website PR lands draft customer-facing copy but owner/Karan approval is still required before public/client-facing use; create and verify a Linear approval issue, then comment the boundary back on the merged PR. If Karan narrows routing to one owner (for example “forget Danny, ask Lucky”), respect that exactly: send the approval request only to the named owner, ask only for the approval class they own, and structure the reply fields so the response can be copied back into Linear/repo docs as approval evidence.
- Service/event landing page implementation guidance: `references/service-event-landing-pages.md`. Use it when adding crawlable local/event-intent pages such as prom formalwear, wedding tuxedo rentals, quinceañera formalwear, or similar high-intent JMD pages. Keep paths descriptive and hyphenated; add unique metadata, self-canonicals, sitemap entries, visible breadcrumbs if using BreadcrumbList, and standard internal links from homepage/About/blog. Preserve the showroom-first/no-ecommerce boundary and the tuxedo-rentals-only public rental constraint unless separately approved.
- Cross-page public-copy regression gate: `references/cross-page-copy-regression-gate.md`. Before opening any new public JMD page PR, audit the new diff against durable site-wide owner/team corrections—not only the task issue's local facts. In particular, issue #132 / PR #154 requires Cornell to be included (or neutral team-safe wording used) whenever new JMD-authored customer copy names Danny and Lucky together; preserve owner/tenure role accuracy and do not rewrite verbatim testimonials.
- Custom-shoes WordPress→static migration guidance: `references/custom-shoes-wordpress-to-static-migration.md`. Use it for JMD shoes/custom-shoe catalog migration work: source packet first, then `/custom-shoes-conyers-ga/`, fold legacy shoe URL coverage into existing redirect/preflight issues, and keep made-to-order/ecommerce claims source-backed.
- Two-phase custom-shoes rollout: `references/custom-shoes-two-phase-rollout.md`. Phase 1 is a crawlable **Made-to-Order inspiration/handoff page**, not an in-store sample/showroom page: the six featured shoes are not stocked at JMD, and copy must not invite visitors to come see them or discuss their leathers/lasts in-store. The exact approved collection URL is the sole page-specific conversion destination, intentionally repeatable in hero/carousel handoff/closing; no page-specific Call/Directions/visit alternatives (global nav/footer boilerplate may remain). Move model-level Customize/Order buttons into a separate real-browser-QA/allowlist follow-up, and treat that as an explicit contract change across source packet, allowlist, validator/self-tests, page copy, and PR body. Lucky's answers are sufficient stakeholder approval for this JMD work; Karan still controls public launch.
- When Karan asks to create a JMD website issue, use the website repo `sabnanikl-dev/jmd-6-holding-page-harness` unless he names another repo. Before creating, search open issues first, then broader all-state matches for overlapping wording (`navbar`, `logo`, `showroom`, `lightbox`, `modal`, etc.). Use existing labels only; `enhancement` is the safe default for small UI polish.
- For small visual polish issues, keep scope narrow and implementation-ready: state what should change, explicitly preserve surrounding layout behavior, name out-of-scope areas, and include repo verification (`npm test`) plus manual desktop/mobile checks.
- For tiny direct implementation requests that do not need a new issue (for example “make the top ticker 8% faster”), keep the PR intentionally surgical: inspect the existing CSS seam first, change only the needed declaration, and preserve surrounding layout/copy/JS behavior. For marquee/ticker speed, calculate the new animation duration as `old_duration / speed_multiplier` (8% faster = `42s / 1.08 = 38.9s`) rather than guessing a visually nice number. Confirm existing `prefers-reduced-motion` handling remains intact, and state the consulted repo-routed skills (`frontend-design`, `accessibility` when motion is touched) in the PR body per the project manifest.
- For top announcement/store-status polish, inspect the current homepage implementation before writing the issue. As of this pattern, `site/index.html` owns the live `data-store-status` text via an inline America/New_York hours script, while `.status-dot` in `site/styles.css` controls the decorative dot. Issue bodies should ask for deterministic open/closed state classes or data attributes from the existing status script, preserve status copy/timezone logic/nav layout, allow no-JS fallback to remain neutral, include `prefers-reduced-motion` if a glow/pulse is requested, and require simulated verification for closed-all-day, before-open, open-hours, and after-close cases.
- For `On the Floor` / showroom photo UX issues, preserve the showroom-only contract: no ecommerce, prices, sizes, stock counts, live availability, checkout, new content, stock images, AI images, Sanity/n8n publishing changes, deployment, DNS, hosting, credential, or live account mutation unless separately approved. If a mobile screenshot shows the static/no-JS grid instead of the carousel, do not assume missing data: inspect whether the JS loader is blocked on full-feed image probes, check image payload sizes/transforms, and require an issue/test that a slow or broken later image cannot block carousel mount.
- For enlarged image/lightbox-style issue requests, include accessibility acceptance criteria by default: visible `X`, Escape-to-close, focus moves into viewer and returns to trigger, accessible close label, background scroll lock with cleanup, desktop/mobile no clipping/overlap, and existing carousel behavior still works after close.

## Domain/DNS Lessons from JMD-4
- Registrar: GoDaddy; current DNS provider: HostGator
- Nameservers: ns6415.hostgator.com, ns6416.hostgator.com
- Root A and mail A point to 192.254.232.174; www CNAME points to root; MX points to mail.jmdmenswear.com
- Preserve MX, SPF, DKIM, Facebook verification, and other TXT records before any web hosting move
- If cPanel/AutoSSL says SSL is secure but public HTTPS fails, treat it as a HostGator-side site/SSL health issue, not a DNS issue — unless external evidence shows the site is healthy
- Observed failure mode #1: HTTP redirects to SafeBrowse warning while HTTPS fails with TLS protocol error. Next steps are cPanel document root, .htaccess, malware/security redirect, and AutoSSL reissue checks
- Observed failure mode #2: local non-VPN path shows SafeBrowse/TLS failure, but VPN/incognito on same Wi-Fi works and external SSL/malware scanners pass. In this case, pause HostGator/WordPress/DNS changes and verify by phone cellular + another external network; likely local ISP/router/security filtering false positive
- For emergency launch, keep DNS on HostGator and upload holding page there if possible. Only move web traffic to Vercel if HostGator blocks launch
- If using Vercel later, prefer A/CNAME method over changing nameservers so email records remain intact

## Vercel Static Deploy Pitfall
- The JMD website repo is a static site served from `site/`; `npm run build` is intentionally a no-op and does not create a framework output. If a Vercel deployment of the repo root errors with a zero-duration `Builds . [0ms]` entry and logs are unavailable because it never reached READY, deploy the static directory directly instead of retrying the same root deployment.
- Safe non-DNS deploy command used before server functions existed: `npx vercel@latest deploy site --project jmd-non-prod --prod --yes --logs`. This promotes only the Vercel project alias and does not touch GoDaddy/HostGator/DNS records.
- After GitHub #139, the non-prod project includes the root-level Vercel function `api/testimonials.js`; deploy from the **repo root**, not `site/`, when the API endpoint must ship: `npx vercel@latest deploy --prod --scope sabnanikl-devs-projects --yes` from the linked repo root. The `vercel.json` `outputDirectory: "site"` still serves static assets while preserving root `api/` functions. Deploying only `site/` would omit `/api/testimonials`.
- Verification after Vercel deploy: run repo baseline (`npm test`), inspect the new deployment and confirm `status Ready`, fetch the public alias (`https://jmd-non-prod.vercel.app/`) for HTTP 200/title/H1, fetch representative static assets (`assets/js/card-carousel.js`, `assets/js/on-the-floor.data.js`, `assets/jmd-logo-full-blue.png`), and, when testimonials are in scope, verify `GET /api/testimonials` returns HTTP 200 public-safe JSON and the homepage performs a `fetch` to that endpoint. The generated deployment URL may be auth-gated while the production alias is public; verify the alias that will be shared.
