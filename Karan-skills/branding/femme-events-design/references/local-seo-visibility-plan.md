# Femme Events Local SEO Visibility Plan Notes

Use this reference when planning Femme Events search visibility, Google Business Profile work, or SEO implementation issues.

## Priority sequence

1. Technical SEO foundation
   - Real `robots.txt` and `sitemap.xml` must return text/plain and XML, not the Vite SPA HTML fallback.
   - A real `og-image.jpg`/social image should return an image MIME type, not HTML.
   - LocalBusiness/EventPlanningService JSON-LD should use valid public contact info, service area, sameAs links, and a clean service catalog.
   - Submit sitemap and key routes through Google Search Console after deploy.

2. Google Business Profile
   - GBP is the local SEO anchor for "Atlanta wedding coordinator" and "wedding planner near me" style searches.
   - Complete category, service areas, website, phone, hours, description, services, photos, Q&A, and posts.
   - Reviews are a major moat. First target: 10 quality reviews. Next target: 25+.

3. Primary service landing pages
   - `/atlanta-wedding-coordinator` for primary local intent.
   - `/day-of-wedding-coordinator-atlanta` to capture common search language while explaining that real support starts before the day itself.
   - `/partial-wedding-planning-atlanta` for couples who have started planning but need structure.
   - Optional location/venue pages only when each page has unique local detail or real proof. Avoid thin copy-paste doorway pages.

4. Authority and distribution
   - Directory/citation profiles matter: The Knot, WeddingWire, Zola, PartySlate, Bing Places, Apple Business Connect, Facebook, and selected Atlanta wedding directories.
   - Use consistent NAP/contact details, website, service area, and short description everywhere.
   - Repurpose each useful journal post into Instagram captions, carousel ideas, stories, and GBP LocalPosts.

## Competitor patterns observed

Searches checked during the session included:
- `atlanta wedding planner`
- `atlanta wedding coordinator`
- `day of wedding coordinator atlanta`
- `best wedding planners atlanta`
- `partial wedding planner atlanta`

Patterns that ranked competitors used:
- Exact local intent in title/meta copy, e.g. "Atlanta Wedding Planner" and "Atlanta Wedding Coordinator".
- Directory dominance from PartySlate, WeddingWire, The Knot, Zola, Thumbtack, Reddit/Facebook groups, and local bridal directories.
- High Google review counts. Examples observed: Laura Burchfield Events ~90 reviews, House of BASH ~132, Emily Jordan Events ~40, W Events ~28, Events by Mesita ~28.
- Proof-heavy language: award-winning, luxury, featured, destination, full-service, published. Femme should only use claims that are true; the safer differentiator is "coordination with feeling, personality, and a plan."
- Clear service ladders: full service, partial planning, month-of/day-of coordination, destination, corporate/social events.
- Portfolio/gallery, testimonials, FAQs, investment/service pages, and blog/journal content.

## Skills.sh candidates for this class of work

If Karan approves installing third-party skills, likely useful skills from skills.sh are:
- `coreyhaines31/marketingskills/seo-audit` — systematic technical/on-page/content/authority audit.
- `coreyhaines31/marketingskills/schema-markup` — LocalBusiness, FAQPage, Article, BreadcrumbList, Service JSON-LD.
- `coreyhaines31/marketingskills/content-strategy` — content pillars, topic clusters, buyer-stage mapping.
- `coreyhaines31/marketingskills/copywriting` — conversion-focused landing page copy without robotic keyword stuffing.
- `coreyhaines31/marketingskills/social-content` — turn journal/GBP content into Instagram posts and carousels.
- `coreyhaines31/marketingskills/ai-seo` — extractable answer blocks, FAQs, citations, third-party proof for AI search visibility.
- `coreyhaines31/marketingskills/programmatic-seo` — use cautiously for location/venue pages only when unique local substance exists.
- `squirrelscan/skills/audit-website` — optional deeper audit with squirrelscan CLI.
- `vercel-labs/agent-skills/web-design-guidelines` — accessibility/design review for new SEO pages.

## Recommended agent delegation

Use this graph for implementation:

1. `researcher` refreshes SERP, Google Places, directory, and competitor findings. Workspace: read_only.
2. `pm-spec` turns findings into GitHub issues with acceptance criteria and page outlines.
3. `builder`, Claude Code, or Codex implements repo changes in a worktree branch.
4. `reviewer` checks technical SEO, schema, accessibility, mobile layout, and copy guardrails.
5. Hermes summarizes for Karan, waits for approval, merges only after approval, then verifies merge/deploy state.

Approval gates remain required for: live GBP mutations, public posts, review replies, directory submissions, deploys, PR merges, or external outreach.
