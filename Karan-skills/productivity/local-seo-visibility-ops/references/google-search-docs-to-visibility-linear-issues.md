# Google Search docs -> visibility Linear issues

Use this when Karan asks to read Google Search Central documentation and turn lessons into Femme/Papi visibility work.

## Source pages captured in this pattern

- SEO Starter Guide: `https://developers.google.com/search/docs/fundamentals/seo-starter-guide?hl=en`
- AI optimization guide: `https://developers.google.com/search/docs/fundamentals/ai-optimization-guide?hl=en`
- Search appearance overview: `https://developers.google.com/search/docs/appearance?hl=en`

## Translation pattern

Create or enrich Linear issues that turn documentation guidance into concrete local-visibility work, not generic SEO reading notes.

Good issue classes:

1. Crawlability and render parity
   - Googlebot should see critical content/resources as users do.
   - For JS sites, include robots, sitemap, noindex, canonical, route status, and Search Console URL Inspection when access exists.
   - Implementation belongs in GitHub branch/PR flow.

2. Search-result snippet readiness
   - Service-page specs should include unique title links, meta descriptions/snippet-supporting visible content, descriptive URLs, canonicals, duplicate-content guardrails, and internal links with meaningful anchor text.

3. People-first / non-commodity content standard
   - Convert Google's helpful-content and AI guidance into a review checklist.
   - For Femme, prioritize real coordination experience, local Atlanta context, approved proof, package-fit clarity, and practical planning decisions.
   - Reject generic listicles, keyword stuffing, AI-only rewrites, unsupported claims, and scaled page/content sprawl.

4. Proof/media and alt text mapping
   - High-quality images/videos should sit near relevant text.
   - Draft descriptive alt text that explains the image's relationship to the page.
   - Preserve permission, credit, privacy, and approval status.

5. GBP/local business detail alignment
   - GBP fields and local business details can support Search/AI visibility, but every recommendation must trace to the approved source of truth or approval ledger.
   - No GBP mutation without explicit approval.

6. Search appearance / structured data eligibility matrix
   - Evaluate site name, favicon, title links, snippets, sitelinks, images, videos, business details, AI readiness, and structured data.
   - Mark each opportunity implement now / defer / avoid / approval-needed.
   - For Femme, likely candidates are Organization, LocalBusiness, Breadcrumb, FAQ only if visible FAQs exist, Event only for real public events if approved, and Image metadata only when licensing/credits are ready.
   - Explicitly reject irrelevant/unsafe rich-result types such as Product, employer ratings, aggregate ratings/review stars without compliant data, job posting, forums, courses, etc.

7. SEO anti-pattern guardrail
   - Document what not to chase: meta keywords, keyword stuffing, magical word counts, keywords-in-domain/path as a ranking lever, llms.txt/special AI markup, chunking just for AI, AI-only rewrites, inauthentic mentions, overbuilt schema, and scaled content abuse.
   - Pair each rejection with what to do instead: crawlability, source-of-truth consistency, helpful content, proof, local details, Search Console measurement, reviews, and real promotion.

8. Agent-friendly inquiry path / accessibility smoke test
   - AI/agentic guidance maps practically to DOM/accessibility-tree clarity.
   - Test homepage, service paths, CTAs, and canonical inquiry URL through human, mobile, screen-reader/accessibility-tree, and browser-agent style inspection.

## Linear execution notes

- Prefer creating/enriching issues in the existing Femme Events Visibility project instead of creating a separate tracker.
- Put issues in `Ready` when they have goal, scope, acceptance criteria, approval boundary, and verification plan.
- Parent issues under the relevant phase/child: Search Console/crawlability under baseline; service-page snippets and inquiry-path tests under service-page spec phase; content/proof/schema/anti-pattern work under durable ops/content phase; GBP local details under the GBP audit.
- Include exact Google source URLs in every issue body for traceability.
- Verify after creation by re-querying the project and confirming title, parent, state, labels, and source links.
- If Karan adds more documentation URLs mid-task, pause before mutation, scrape/read the additional page, merge its lessons into the same issue set, then run the bulk creation/update once.

## Approval boundaries

Allowed: read docs, draft specs, create Linear issues, enrich issue descriptions, create internal matrices/checklists.

Blocked without explicit approval: website code changes/deploys, Search Console submissions, GBP edits, public profile changes, directory submissions, social/GBP posts, review replies/requests, schema that asserts unapproved facts, or public claims not in the source of truth.