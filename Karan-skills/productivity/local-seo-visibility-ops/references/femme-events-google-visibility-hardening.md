# Femme Events Google Visibility Plan Hardening Notes

Session artifact distilled for future local SEO / Google visibility work. Do not treat this as a task log; use it as a pattern bank.

## Context

The plan reviewed was an HTML master plan for Femme Events Google visibility. It already included a good operating model: website/code lane, lightweight ops/API lane, ops harness lane, web-marketer profile, approval gates, and verification rules.

The hardening pass found that the plan was operationally disciplined but too governance-heavy. It needed stronger local SEO strategy, competitor pattern capture, automation/human split, and concrete decision rules.

## What was preserved

- Three execution lanes: website/code, lightweight ops/API, ops harness.
- No public/account mutations without approval.
- GBP completeness check should be lightweight, not a harness audit.
- Standard GitHub workflow for website changes.
- Verification rules after pushes, merges, deploys, and account/reporting changes.
- First batch should stay small and prove the system.

## What was added to harden the plan

### Strategy spine

- Technical foundation first: robots, sitemap, metadata, canonicals, OG image, schema, Search Console, production route checks.
- GBP completeness plus optimization: categories, services, photos, reviews, Q&A, UTM links, response workflow.
- Primary page before page sprawl: launch one strong local SEO conversion page first.
- Reviews before blog volume.
- Selective directory authority over generic citation spam.

### Scrutiny section

Flagged as unnecessary work:

- Huge upfront content calendars before proof/data exists.
- Seven-agent chains for minor website tasks.
- Directory submissions everywhere.
- Harnesses for simple GBP/API/dashboard checks.
- Weekly draft generation without approvals.

Flagged as oversimplified:

- GBP completeness.
- Search Console baseline.
- Service pages as one-and-done assets.
- Review acquisition.
- Photo/proof asset handling.

### Source-of-truth and proof readiness

Added tasks for:

- Local SEO Source of Truth.
- Review Compliance Policy.
- Photo/Proof Inventory.
- Approved and disallowed claims.

### Competitor patterns checked

Sources reviewed included:

- WeddingWire Atlanta planner directory.
- Zola Atlanta planner directory.
- PartySlate Atlanta planner directory.
- Peachy Keen package/service page.
- Engaged Atlanta planner cost article.
- Peerspace Atlanta planner roundup.
- House of BASH search result/site availability check.
- Laura Burchfield Events homepage extraction.

Patterns to copy/adapt:

- Directory profiles surface review counts, awards, starting prices, response time, photos, service tags, and location filters.
- Zola and PartySlate emphasize service filters such as day-of/month-of, partial planning, full service, awards, pricing, and location.
- Some competitors publish package names, timelines, inclusions, meeting counts, coverage hours, and prices or starting prices.
- Roundups reward visible portfolios, reviews across neutral platforms, certifications/awards, venue familiarity, and strong photos.

Recommended additions:

- Directory-specific asset packets instead of treating all citations equally.
- Service comparison content: full planning vs partial planning vs month-of/day-of coordination.
- Pricing clarity if approved; otherwise investment-starts-at or consultation-led scope clarity.
- Real wedding/case-study template once proof is approved.
- Venue/vendor credit workflow and local authority/backlink workflow.

### Automation vs human split

Good automation:

- Monthly GSC + GBP report.
- GBP completeness drift snapshot.
- Production indexability checks.
- Review monitoring and draft replies.
- Content repurposing drafts.
- Directory tracker checks.

Human-only/approval-gated:

- Review requests and follow-up.
- Review replies.
- GBP edits, posts, Q&A, media uploads.
- Photo selection/permission/credit/privacy.
- Directory accounts, paid listings, public submissions.
- Claims and brand voice decisions.

### Claude/Codex leverage

Claude Code is best for:

- Page brief stress tests.
- Brand voice and proof-claim review.
- Schema/content critique.
- Competitor pattern synthesis.
- Client-facing narrative/report language.

Codex is best for:

- Scoped website implementation branches/worktrees.
- QA scripts for production routes, robots, sitemap, canonicals, noindex, OG image MIME, schema JSON-LD, broken links, accessibility basics.
- Directory tracker tooling.
- Before/after regression checks.

Hermes remains final integrator and approval gate.

## Verification pattern used

After editing the HTML plan in place, verification included:

- Serving the file locally over HTTP.
- Loading it in browser.
- Checking page title.
- Checking all nav anchors resolve to sections.
- Checking no horizontal overflow.
- Confirming key new sections exist.
- Checking browser console for JS errors.

This is a reusable pattern for local HTML strategy artifacts.
