---
name: local-seo-visibility-ops
description: Harden and execute local SEO / Google visibility plans for small service businesses without overbuilding the operating system.
tags: [local-seo, google-business-profile, search-console, service-pages, reviews, citations, content-ops, competitor-analysis]
triggers:
  - local SEO plan
  - Google visibility plan
  - Google Business Profile optimization
  - Search Console visibility
  - service area business SEO
  - citation strategy
  - wedding planner SEO
  - directory visibility
  - review workflow
---

# Local SEO Visibility Ops

## Repo-backed artifact handoff discipline

When local SEO / visibility work creates or updates a GitHub-backed docs package, git state is part of the deliverable. In the Femme visibility repo specifically, do **not** move a Linear issue to **Done** while the satisfying repo changes exist only as uncommitted local files: commit the exact artifacts first, then mark Done. If push/PR is approved or required for the handoff, push the commit and verify it exists on the remote (`git ls-remote`, GitHub contents/commits API) before reporting completion. If push/PR is approval-gated, keep that gate explicit in Linear instead of closing as if GitHub is updated. See `references/repo-backed-visibility-artifacts-remote-handoff.md` for the full checklist and handoff language.

Use this for local visibility plans for service businesses such as Femme Events, JMD Menswear, or similar client/owned brands. The goal is to turn Google/GBP/Search Console/content/directory work into measurable visibility without creating unnecessary agent ceremony.

## Core Principle

Build the local search engine without overbuilding the operating system.

A good plan balances:

- **Visibility mechanics:** indexability, GBP relevance, reviews, service pages, directories, local authority.
- **Operational discipline:** approval gates, ownership, verification, reporting, durable source-of-truth.
- **Lean execution:** small first batch, scoped issues, automation after baseline, no harness for simple checks.

## First Pass Review Checklist

When reviewing or hardening a local SEO plan, explicitly answer:

1. **What will work?** Preserve practical foundations: technical SEO, Search Console, GBP baseline, service pages, reviews, selective directories.
2. **What creates more work than value?** Flag giant upfront content calendars, agent handoff chains for tiny tasks, directory spam, weekly draft busywork, and harness use for simple API/dashboard checks.
3. **What is overengineered?** Watch for using Kanban/profile/harness/PM-spec ceremony where a scoped issue or lightweight report is enough.
4. **What is oversimplified?** Expand vague items like “GBP completeness,” “Search Console baseline,” “content calendar,” and “citations” into concrete fields, checks, owners, and decision rules.
5. **What needs human work?** Reviews, relationship-sensitive follow-up, photo permissions, proof/claims, brand voice, public profile edits, paid listings, external outreach.
6. **What can be automated?** Read-only reports, drift checks, route/indexability checks, review monitoring, draft generation, tracker validation.
7. **What are competitors doing?** Compare directory presence, review volume, pricing/package clarity, proof assets, service filters, venue/local authority, FAQs, and conversion cues.

## Recommended Hardened Sequence

### Phase 0 — Source of truth and guardrails

Create these before directory submissions, page sprawl, or broad AI content generation:

- **Local SEO Source of Truth:** NAP, website, inquiry URL, service area, address/privacy posture, primary/secondary categories, descriptions, services, hours, socials, UTM standards, approved assets, approved claims, disallowed claims.
- **Review Compliance Policy:** no fake reviews, no AI-written customer reviews, no review gating, no pressure, no incentives unless compliant and explicitly approved.
- **Photo/Proof Inventory:** photo permission, photographer credit, venue/vendor credit, channel permissions, file name, alt text, and approved usage.
- **Claims Guardrails:** document what can and cannot be said. Do not invent awards, review counts, venue relationships, luxury positioning, event volume, or “top-rated/best” claims.

When filling a source-of-truth artifact, do a read-only public-source pass before asking the user for missing fields:

1. Extract the live website homepage and any obvious contact/about/inquiry routes.
2. Capture visible NAP/contact fields, canonical URL, inquiry URL/anchor, CTA language, live package/service names, meta title/description, JSON-LD basics, and visible asset URLs/alt text.
3. Reconcile live website terminology against older business-plan/wiki terms instead of blindly preserving legacy names; mark conflicts explicitly for human decision.
4. If given a GBP share/search link, record the link and any redirect-derived stable IDs/query text, but do not infer profile fields from a blocked/anti-bot page. Mark GBP fields as needing read-only API/dashboard verification.
5. Treat public website facts as “observed” but still approval-gated for GBP/directories; public edits remain explicit-approval actions.

When Phase 0 becomes executable work, package it as a small operating system rather than a loose note:

1. Keep the private/sensitive canonical source-of-truth in the wiki or knowledge base.
2. Link that source-of-truth from the relevant tracker issue before moving the issue to active execution.
3. Add a repo-facing docs package with the source-of-truth, an approval ledger, and reuse notes.
4. If the docs package lives in a visibility-ops repo, add a lightweight `AGENTS.md` so future agents can orient and maintain it safely. Keep it around ~100 lines, table-of-contents style, and explicit that the repo is not a coding harness. Apply harness-engineering principles only as lean operating rules: progressive disclosure, one artifact/one reviewable change, separate drafting from evaluation, define done before editing, and no performative scaffolding.
4. If the docs package lives in a visibility-ops repo, add a lightweight `AGENTS.md` so future agents can orient and maintain it safely. Keep it around ~100 lines, table-of-contents style, and explicit that the repo is not a coding harness. Apply harness-engineering principles only as lean operating rules: progressive disclosure, one artifact/one reviewable change, separate drafting from evaluation, define done before editing, and no performative scaffolding.
5. Add a short `docs/spec.md` or equivalent project-goal document that reflects the Linear project description in plain language. It should explain what the visibility project is, what the repo is/is not, the operating model across Linear/repo/wiki/website repo, success criteria, and approval boundaries. When the user wants future-client leverage, make the goal dual-purpose: improve the current brand's digital reach while building reusable Papi/client visibility systems.
6. Add repo-local Linear issue/status guidance when the repo will be maintained by multiple agents. Do not let `README.md` become a moving task tracker; link the Linear project and put issue links in artifact headers instead of maintaining a single mutable `Current issue` pointer.
7. Put unresolved human decisions in the approval ledger, not hidden inside prose.
7. Use a named branch/commit for the docs package, but do not push or open PRs until the user explicitly approves external repo mutation.
8. After any approved push, verify the remote branch/commit before reporting success.

When Phase 0 work is waiting on Karan/Amanda input, reflect ownership in Linear instead of leaving the parent issue ambiguously active: move the parent to **In Review**, create/assign a child human review issue with a checkable decision checklist and comment-answer format, then wait. After the child is **Done**, move the parent back to **In Progress**, apply the decisions to wiki/repo artifacts, verify consistency, comment the finalization summary, and move the parent back to **In Review** for final owner closeout.

If the user asks to break Phase 0 / Step 1 into smaller steps before choosing an execution lane, do not immediately run the lane. First produce a compact lane-ready breakdown: micro-step, outcome, owner/lane, approval boundary, and recommended lane. Keep this first response short enough for the user to pick a lane. See `references/phase-0-step-1-execution-lanes.md` for the reusable breakdown and lane picker.

See `references/local-seo-source-of-truth-operationalization.md` for the issue/wiki/repo packaging pattern.

### Phase 1 — Technical and measurement foundation

- robots.txt, sitemap.xml, metadata, canonicals, OG image, direct route loading.
- For SPA/Vite/React Router sites, do not treat “route returns 200” as sufficient sitemap readiness. If `/about`, `/journal`, or service routes are listed in `sitemap.xml`, verify each route has route-specific canonical/OG URL/title/description, or keep only truly self-canonicalizing URLs in the sitemap until prerender/SSR/runtime head management is in place.
- If metadata advertises an OG image size such as `1200×630`, the repo verification script should enforce actual PNG dimensions, not only existence, extension, or file size.
- Schema with one consistent business `@id`; visible FAQ schema only; no fake aggregate rating markup.
- Search Console property and sitemap submission after deploy.
- When Search Console access is newly enabled, use the blocker ladder before reporting metrics status: OAuth scope → API enablement/propagation for the OAuth client project → property access → metrics pull. See `references/search-console-baseline-blocker-ladder.md`.
- After Search Console access is resolved, capture a read-only post-access baseline before any mutation: property/permission, 90-day Search Analytics, optional 16-month no-row back-check, sitemap list/get, URL Inspection for canonical and alternate homepage URLs, and production robots/sitemap fetches. Treat HTTP 200 Search Analytics responses with no rows as a valid zero/no-recorded-performance baseline, not a renewed blocker. Keep sitemap submission approval-gated and split it into a follow-up issue if needed. See `references/search-console-post-access-baseline.md`.
- Analytics/conversion posture: form submissions, phone/email clicks, CTA clicks.
- Analytics/conversion posture: form submissions, phone/email clicks, CTA clicks.
- Analytics/conversion posture: form submissions, phone/email clicks, CTA clicks.
- UTM conventions for GBP and directory links where appropriate.

### Phase 2 — GBP baseline and optimization

Do a lightweight read-only check first; no harness unless multiple evidence-heavy deliverables are needed.

When a phase combines GBP and Search Console baseline work, package it as a "Google surfaces baseline" rather than treating partial access as failure: write a read-only GBP baseline, a human-readable GBP completeness audit, a Search Console baseline/blocker note, a parent summary, and folder index updates; move Linear issues to In Review with exact blockers and approval gates. See `references/google-surfaces-baseline-package.md`.

Check:

- Primary category and secondary categories.
- Service area and address/privacy posture.
- Website URL and UTM plan.
- Phone, hours, opening date if available.
- Business description.
- Services with useful descriptions.
- Attributes, Q&A availability, messaging readiness.
- Photos/media, review count/rating, unanswered reviews, recent themes.
- Booking/contact/inquiry links.
- Profile status and Google updates.

Split work into: completeness, optimization recommendations, photo/media workflow, review/reply workflow, LocalPost workflow, monthly performance report.

#### GBP API read-only audit pattern

When dashboard/API access exists, collect a read-only baseline before recommending or making edits:

1. Use OAuth user consent with `https://www.googleapis.com/auth/business.manage`; for GBP-only work, prefer a dedicated token such as `~/.hermes/google_gbp_token.json` instead of adding `business.manage` to the general Gmail/Drive/Calendar token.
2. Include `openid` + `https://www.googleapis.com/auth/userinfo.email` scopes when practical so the signed-in Google identity can be verified without Gmail/People access. Prefer the canonical `userinfo.email` scope over short `email`; Google may canonicalize `email` during token exchange and strict OAuth libraries can fail on the apparent scope change.
3. **Verify the signed-in Google identity before any GBP/Gmail/Drive/Calendar API work.** Compare the token/profile email to the intended workspace/agent account for the task; if it is the wrong account, stop, quarantine/remove the active token, and reauthorize the correct account before continuing. Do not treat “token exists” as sufficient.
4. Smoke test Account Management with `GET https://mybusinessaccountmanagement.googleapis.com/v1/accounts` to discover account parents.
5. Use Business Information `accounts.locations.list` with an explicit `readMask` for fields such as `title`, `websiteUri`, `phoneNumbers`, `categories`, `regularHours`, `openInfo`, `profile`, `serviceArea`, `serviceItems`, `storefrontAddress`, `latlng`, `metadata`, and `labels`.
6. If API calls return insufficient scopes, reauthorize the existing Google OAuth flow rather than creating a second credential stack — but only after confirming the existing token belongs to the intended account.
7. If calls return API disabled or quota is `0`, verify the OAuth client belongs to the Google Cloud project that actually has GBP API approval/quota, not merely that the signed-in email is an approved/test user. A valid user token still fails if the OAuth client project is unapproved or has the API disabled.
8. If account discovery succeeds but the target business/location is missing, treat it as a GBP access/role issue: the signed-in account likely needs Manager/Owner access to the business profile or parent account before API-derived fields can be populated.
9. Write API-derived values into the private source-of-truth as “observed/API-derived,” keep unresolved approval gates, and do not patch GBP fields unless explicitly approved.

See `references/gbp-readonly-api-baseline.md` for a compact implementation checklist and field map.

### Phase 3 — Primary conversion page before page sprawl

Launch one strong local service page first, then iterate from data.

For a wedding/event planning brand, start with a page like `/atlanta-wedding-coordinator` before secondary pages. Brief must include:

- Target query and search intent.
- Who the service fits / does not fit.
- Package fit and timeline.
- Real proof needed.
- FAQ coverage.
- Internal links.
- Schema plan.
- CTA and inquiry path.
- Claims guardrails.

### Phase 4 — Review and directory authority

Reviews and proof usually beat blog volume early.

- Target first 5, then 10, then 25 authentic Google reviews.
- AI may draft templates and reply drafts; humans decide who to ask, when to ask, and what to post.
- Prioritize quality profiles over citation spam: Google, The Knot, WeddingWire, Zola, PartySlate, Bing Places, Apple Business Connect, Facebook/Instagram, and real venue/vendor/blog opportunities.
- Track directory URL, status, account owner, NAP match, description match, photos, reviews, last checked, and issues.

### Phase 5 — Secondary pages and content

Only expand once the primary page, GBP baseline, review workflow, and proof assets are moving.

Good next assets:

- Day-of/month-of coordinator page that honestly explains support begins before the wedding day.
- Partial planning page tied to real package scope.
- Service comparison content: full planning vs partial planning vs month-of/day-of coordination.
- Cost/when-to-hire FAQs.
- Real wedding/case-study pages once proof is approved.
- Local authority content only when there is real venue/vendor/local substance.

## Decision Rules for Reports

Monthly reports must produce decisions, not just metrics.

### GBP monthly email as a lightweight baseline

When Google sends a monthly Business Profile performance email and the user asks how to improve the numbers, extract the email's raw counts and turn them into an explicit baseline before prescribing tactics: interactions, calls, website visits, chat/message clicks, and profile views. Calculate interaction rate, website click rate, and call rate. If the action rate is strong but profile views are tiny, frame the bottleneck as discovery/trust/relevance rather than only conversion. For “order of magnitude” asks, convert each number into 10x targets so the plan has concrete goals. See `references/gbp-email-performance-report-baseline.md`.

Examples:

- If profile views are very low but interaction rate is healthy, prioritize GBP relevance/completeness, reviews, photos, directory authority, and local service-page/indexing work.
- If a page has impressions but CTR under ~1% for two months, test title/meta and SERP alignment.
- If a target page is indexed but has no impressions after 60–90 days, improve internal links, content quality, and authority signals.
- If GBP views increase but actions stay flat, improve services, photos, CTA/inquiry link, and profile copy.
- If a query repeatedly appears in Search Console and no page targets it, consider a brief.
- If reviews stagnate after completed events, revisit the human review-request workflow.
- If competitors gain directory/review/photo prominence, update the priority queue.

## Automation vs Human Work

### Automate after the first manual baseline works

- Search Console + GBP monthly report.
- GBP completeness drift snapshots.
- Production indexability checks: robots, sitemap, 200 routes, canonicals, noindex, OG image MIME, sitemap membership.
- Review monitoring and draft replies.
- Content repurposing drafts: GBP LocalPost, Instagram caption, carousel outline, FAQ candidates, title/meta options.
- Directory tracker validation.

### Keep human-only or approval-gated

- Review requests and sensitive follow-up.
- Review replies, especially negative/mixed reviews.
- GBP field edits, media uploads, Q&A, posts, and category/address/service-area changes.
- Photo selection, permission, privacy, and photographer credit.
- Directory account creation, paid listings, public submissions, and outreach.
- Brand voice and proof claims.

## Harness Rule

Use an ops harness only when at least two are true:

- Multiple external sites/accounts.
- Evidence screenshots/exports are required.
- Multiple final deliverables.
- High risk of losing state.
- Formal client-facing packet.
- Multiple approval checkpoints.

Otherwise use a scoped GitHub issue, Kanban task, lightweight script, or report.

## Cross-system tracker discipline

When the user asks to update a visibility Linear project and allows repo-side issue creation, treat Linear as the strategy/approval tracker and GitHub as the implementation/PR tracker for website-owned work.

- Read the Linear project first; update existing relevant issues before creating new ones.
- Create new Linear children for new operating work such as GBP optimization packets, UTM/conversion baseline, or review workflows.
- Mirror into GitHub only when the work needs repo-side execution, branch/PR tracking, cross-QA, or reviewable website/code artifacts.
- If an existing GitHub issue already owns the repo-side concern, comment/link it instead of creating a duplicate.
- Put Linear issue/project links in GitHub issue bodies, then comment back in Linear with the GitHub issue/comment URL.
- Preserve approval boundaries: creating Linear/GitHub issues does not approve GBP edits, review requests, directory submissions, website merges, deploys, env changes, or public/account mutations.
- Verify both sides after mutation: GitHub issue/comment contains the Linear ID and key context; Linear direct comment lookup confirms the backlink.

See `references/visibility-linear-github-issue-sync.md` for the reusable Linear ↔ GitHub issue-sync checklist.

## Claude Code and Codex Leverage

Use token budget for parallel pressure and QA, not for one bloated session.

- **Claude Code:** page brief stress tests, copy/voice review, proof-claim review, schema/content critique, competitor pattern synthesis, narrative client-facing reports.
- **Codex:** scoped implementation branches/worktrees, QA scripts, route/sitemap/schema checks, regression checks, directory tracker tooling, production verification scripts.
- **Hermes:** final integrator; enforces approval gates; verifies remote/deploy/dashboard state before reporting done.

Pattern:

1. Run parallel read-only research: competitors/directories, keyword/service intent, GBP/local-pack observations.
2. Synthesize into one prioritized brief.
3. Convert approved items into scoped issues/tasks.
4. Use Codex for implementation and Claude/reviewer for cross-QA.
5. Human approves proof, claims, voice, and public/account changes.
6. If an approval-gated Kanban task blocked itself, Hermes must actively unblock/complete/promote/dispatch after approval; comments alone do not wake an exited blocked worker.
7. Hermes verifies real state.

## Verification for docs/API-export artifacts

When a visibility-ops task changes Markdown reports, folder indexes, and structured API exports in a docs-first repo with no canonical test/lint/build command, create a focused temporary verifier instead of stopping at `git diff --check`. The verifier should check index wiring, JSON parsing, secret-marker absence, approval-boundary wording, and consistency between API-export facts and the human-readable report. Use an OS-safe `tempfile` path with a `hermes-verify-` prefix, clean it up, and report the result explicitly as **ad-hoc verification** rather than suite green.

When wiring Google/GBP/GSC credentials into a local visibility workspace, treat the credential wiring itself as a guardrail artifact: create ignored symlinks/env files, verify they are ignored and untracked, smoke-test non-secret API access, and commit only safe tracked guardrails such as `.gitignore` and `AGENTS.md`. Never copy OAuth token JSON or client-secret JSON into the repo. See `references/project-local-google-credential-wiring.md` for the combined GBP + Search Console pattern.

See `references/ad-hoc-verification-for-visibility-docs.md` for the reusable checklist.

## Pitfalls

- Do not confuse content volume with authority. Early reviews, proof, and directory/profile completeness often matter more.
- Do not create location/service pages without real substance; thin local pages can dilute trust.
- Do not let profile setup block obvious high-value SEO work.
- Do not submit to every directory; prioritize high-signal platforms and real local/vendor links.
- Do not publish AI-drafted review replies, GBP posts, directory profiles, or outreach without approval.
- Do not report success from command output alone; verify dashboard/API/production state.

## References

- `references/project-local-google-credential-wiring.md` — local-only GBP + Search Console credential wiring for visibility repos: ignored symlinks/env files, git ignore/tracking verification, live smoke tests, and commit-only-safe-guardrails discipline.
- `references/notebooklm-seo-attacker-audit-to-github-issues.md` — source-grounded SEO attacker audit pattern: query specific Google Search/SEO NotebookLMs, inspect repo SEO surfaces, rank gaps by impact/effort, run a Codex Reviewer gate, open verified GitHub issues, and commit an `SEO-AUDIT-STATE.md` artifact when requested.
- `references/visibility-linear-github-issue-sync.md` — when visibility work is tracked in Linear but website/code implementation belongs in GitHub: mirror only repo-owned work, backlink both systems, avoid duplicate GitHub issues, and verify comments/issues after mutation.
- `references/visibility-ops-repo-operating-system.md` — repo operating-system pattern for AGENTS/spec/Linear guidance, future-client systems goals, proof-bank databases, and PR review pitfalls.
- `references/visibility-coding-pr-lane.md` — use when local SEO / visibility work becomes website code: specify Claude Code/Codex via the standard GitHub PR workflow instead of vague “builder implements” handoffs.
- `references/visibility-ops-repo-agents-guide.md` — lightweight `AGENTS.md` pattern for docs-first visibility-ops repos that should not become coding harnesses.
- `references/visibility-ops-linear-status-guidelines.md` — Linear status-management pattern for visibility-ops repos, including Ready/In Progress/In Review/Done semantics and human-review child issues.
- `references/google-surfaces-baseline-package.md` — repo/Linear handoff pattern for read-only GBP + Search Console baselines when public mutations are approval-gated and Search Console access may be blocked.
- `references/google-search-docs-to-visibility-linear-issues.md` — translate Google Search Central SEO/AI/Search appearance docs into concrete Femme/Papi Linear issues with source links, parents, approval gates, and verification.

- `references/femme-events-google-visibility-hardening.md` — session-specific notes from hardening Femme Events' master Google visibility plan, including competitor patterns and added sections.
- `references/search-console-baseline-blocker-ladder.md` — OAuth/API/property-access ladder for Search Console baselines so blockers are named accurately before metrics pulls.
- `references/search-console-post-access-baseline.md` — post-access read-only baseline pattern: no-row Search Analytics interpretation, sitemap state vs production reality, URL Inspection, and approval-gated sitemap follow-up.
- `references/local-seo-source-of-truth-public-source-pass.md` — reusable checklist for pre-filling local SEO source-of-truth artifacts from public website/GBP share-link observations while preserving approval gates.
- `references/local-seo-source-of-truth-operationalization.md` — issue/wiki/repo packaging pattern for turning Phase 0 source-of-truth work into traceable execution artifacts without prematurely mutating public profiles or remotes.
- `references/phase-0-step-1-execution-lanes.md` — compact micro-step and lane-picker pattern for breaking Phase 0 Step 1 into kick-offable chunks before execution.
- `references/web-marketer-skills-sh-install-gate.md` — profile-scoped community skills.sh install pattern, including scanner override approval boundaries and verification steps.
