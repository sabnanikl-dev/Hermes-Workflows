---
name: research-workflow
description: Standard multi-source research process using Brave Search, browser, local files, and wiki.
---
# Research Workflow

## When to Use

- Vendor sourcing and vetting
- Competitor analysis
- Market research
- Technical research for client projects
- Local business, restaurant, job-fit, and productized-service research
- Deep-dive deliverables that need parallel subagents or polished reports
- Travel/lodging shortlists and polished HTML reports that need live rates, photos, route-fit, and policy verification
- Any task requiring external information gathering

## Umbrella Scope: Research and Discovery Deliverables

This is the class-level skill for external-information workflows. Narrow research skills are absorbed here as labeled subsections/reference files instead of remaining as one-off siblings.

Absorbed subsections:
- **Local business research**: verify local vendors/businesses with multiple sources and avoid search-result hallucinations.
- **Georgia small-business registration research**: separate entity formation, federal/state tax registration, and location-dependent city/county licensing; distinguish mailing, registered-agent, and physical operating addresses; treat entity-name searches as preliminary only. See `references/georgia-small-business-registration.md`.
- **Restaurant reservation research**: for date/time/party-size/ambiance constraints, check reservation platforms before generic search.
- **Resume-to-role research**: extract resume facts first, build search queries from candidate profile, prioritize direct employer pages, and verify role details.
- **Productized service reports**: combine tools/vendors, competitor analysis, economics, ICPs, GTM, and risks into an HTML business brief.
- **Market viability gates for repo-local offer/landing-page ideas**: before polishing a market-facing draft, run bounded public research and force a continue/narrow/pivot/hold/kill decision from evidence, not vibes. See `references/market-viability-gates.md`.
- **Passive-revenue digital product validation**: when Karan wants a PDF, prompt pack, NotebookLM/AI query pack, source map, checklist, marketplace-ready digital download, or revenue experiment loop, pair a specific NotebookLM query with public marketplace/web research, separate viability from marketability, create repo-local product packs/skills when appropriate, use autoresearch-style fixed-budget A/B/product experiment ledgers for title/price/CTA/product-surface tests, and treat Telegram approval + agent-owned account setup as part of the launch workflow. See `references/passive-revenue-digital-product-validation.md`.
- **Observed willingness-to-pay evidence sprints**: when a product is blocked on whether the target/comparable buyer actually pays for analogous assets, run a governor-first evidence sprint: candidate table, exact-buyer marketplace proof first, comparable seller proof second, strict rejection of weak sources, exact machine-readable markers only, then re-run the governor and preserve approval gates. See `references/observed-wtp-evidence-sprints.md`.
- **Local directory niche validation**: test broad local media/directory ideas with a wide niche scan, unfair-advantage scoring, monetization paths, and maintenance-risk checks. See `references/local-directory-niche-validation.md`.
- **Subagent research reports**: split complex topics into parallel streams, validate sources, and synthesize into a polished deliverable.
- **Notion scraping**: public Notion pages usually need browser navigation because curl returns only the shell.
- **Ontology research-to-spec**: when research turns into a reusable client ontology standard, switch from article summary mode to the `client-ontology-architecture` skill and ground the spec in wiki/project/GitHub/Linear sources.

Full historical playbooks are preserved in `references/`.

Useful support references:
Useful support references:
- `references/medium-member-article-research.md` — Medium member-only article workflow: public preview checks, RSS/archive/search workarounds, authorized email-code login, full-body browser extraction, and linked-reference follow-up.
- `references/pet-friendly-hotel-research.md` — road-trip lodging research workflow using Google Travel/Hotels, Serper, Google Places photos, and portable HTML verification.
- `references/boutique-hotel-shortlist-reports.md` — boutique/lifestyle lodging reports where the user gives a vibe/inspiration property; includes availability reality checks, aesthetic-fit scoring, image capture, breakfast/pool fields, and HTML deliverable guidance.
- `references/frontier-gowild-availability-research.md` — Frontier GoWild availability research notes: NDC API reality, existing tools, GWsearch repo test findings, scraping-risk framing, and guarded personal-watcher design.
- `references/frontier-gowild-availability-research.md` — Frontier GoWild pass availability research: official NDC API limits, third-party search tools, DIY watcher risks, and recommended validation workflow.
- `references/market-viability-gates.md` — bounded research gate for offer/landing-page ideas: evidence requirements, scoring, and continue/narrow/pivot/hold/kill decision framing.

## Step-by-Step Process

### 1. Check Existing Knowledge
```bash
# Hindsight recall for past sessions
hindsight_recall "<topic>")

# Check wiki index
cat ~/obsidian-vault/hermes-brain/index.md

# Search local projects
search_files(target="content", pattern="<keyword>", path="~/projects/")
```

### 2. Serper (Google Search API) — Primary Fast Discovery
```bash
curl -s "https://google.serper.dev/search" \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "YOUR QUERY", "num": 10}'
```
- Use for: finding businesses, vendors, competitors, checking existence, quick facts
- Google-quality results with knowledge graphs, sitelinks, and direct answers
- Returns organic results, peopleAlsoAsk, relatedSearches — richest data

### 3. Brave Search API (Backup)
```bash
curl -s "https://api.search.brave.com/res/v1/web/search?q=URL_ENCODED_QUERY&count=10" \
  -H "X-Subscription-Token: $BRAVE_API_KEY" \
  -H "Accept: application/json"
```
- Use when Serper quota is exhausted
- Rich descriptions, good for competitor analysis and pricing research

### 4. Google Places API (Business Verification)
```bash
curl -s "https://maps.googleapis.com/maps/api/place/textsearch/json?query=URL_ENCODED_QUERY&key=GOOGLE_PLACES_API_KEY"
```
- Use for: verify business exists, get real address/phone/hours/ratings/review count
- Fast alternative to visiting each site individually

### 4. Firecrawl API (Website Scraping)
```bash
curl -s -X POST "https://api.firecrawl.dev/v1/scrape" \
  -H "Authorization: Bearer FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "formats": ["markdown"]}'
```
- Use for: extract clean content from websites, especially sites that block browsers
- Gets pricing, catalogs, service details without manual browsing

### 5. Unstructured.io API (PDF/Document Extraction)
```bash
curl -s -X POST "https://api.unstructured.io/general/v0/general" \
  -H "unstructured-api-key: UNSTRUCTURED_IO_API_KEY" \
  -F "files=@path/to/document.pdf" \
  -F "strategy=auto"
```
- Use for: extract text from PDFs (contracts, vendor brochures, invoices)
- Works with: PDFs, images, Office docs, plain text

### 4b. Competitor Website Research (Bulk Analysis)
When analyzing multiple competitor websites for design patterns, pricing, or positioning:
```python
import requests, json
# 1. Serper to find URLs
# 2. Firecrawl to scrape each URL in bulk
# 3. Synthesize into competitor table + gap analysis
firecrawl_key = os.environ.get('FIRECRAWL_API_KEY', '')
for url in competitor_urls:
    r = requests.post("https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {firecrawl_key}", "Content-Type": "application/json"},
        json={"url": url, "formats": ["markdown"], "onlyMainContent": True, "waitFor": 3000})
    data = r.json()
    if data.get('success'):
        md = data['data'].get('markdown', '')
        title = data['data'].get('metadata', {}).get('title', 'N/A')
        # Extract headings, sections, keywords (pricing, testimonials, portfolio)
```
**Synthesize output as:**
- Competitor table (URL, notable design elements, how we differentiate)
- Gap analysis (what none of them do = opportunity)
- Design token recommendations for the build
- Service tier comparison with pricing intel

**Important:** Use `requests` in Python (not curl in terminal) for Firecrawl calls — it's faster when looping over multiple URLs and avoids shell escaping issues.

### 6. Browser Deep Dives
```bash
browser_navigate("https://specific-site.com")
browser_snapshot()  # Get structured content
browser_get_images()  # If visual info needed
browser_vision(question="what specific info do you need")  # For complex pages
```
- Use for: detailed pricing, contact forms, service pages, reviews, terms
- Extract: phone numbers, emails, pricing tables, service areas, reviews
- **Important: Notion pages require browser rendering** — Notion is a pure SPA that returns empty HTML to curl/urllib/requests. Always use `browser_navigate()` + `browser_snapshot()` for Notion content.

### 7. Multi-URL Batch Extraction & Synthesis
When synthesizing multiple articles or sources into a single document (e.g., best practices, comparative analysis):

**Step 1 — Batch extract with `web_extract`:**
```python
# Fetch up to 5 URLs at once
web_extract(urls=["https://source1.com", "https://source2.com", ...])
```
- Prefer `web_extract` over browser tools for articles/blog posts — it returns clean markdown
- If a URL fails, fall back to `browser_navigate()` + `browser_snapshot()`

**Step 2 — Synthesize themes, not summarize individually:**
- Read all extracted content before writing
- Identify cross-cutting themes and patterns that multiple sources agree on
- Note where sources diverge or complement each other
- Extract specific quotes, metrics, or examples that illustrate key points

**Step 3 — Structure the output:**
- Use **numbered principles** or **best practices** as the top-level structure
- Support each principle with evidence from multiple sources
- Include a **quick-reference table or checklist** at the end for copy-paste utility
- Always cite source URLs at the bottom

**Step 4 — Store in the wiki:**
- Save as a standalone page in the appropriate domain folder
- Use clear, searchable filename (e.g., `best-practices.md`, `comparative-analysis.md`)
- Update the domain index if one exists

**Example output structure:**
```markdown
# Topic Best Practices

## 1. Principle Name
Cross-source insight with supporting evidence.
> "Quote from source" — [Source Name](url)

## 2. Next Principle
...

## Quick-Reference Checklist
| Component | Purpose | Example |

## Sources
- [Title](url) — Author
```

### 6. Notion Pages
```bash
browser_navigate("https://www.notion.so/Page-Name-1234567890abcdef")
browser_snapshot()  # Get structured text content
```
- Notion pages are single-page apps — you MUST use the browser tools, not HTTP requests
- Works for public Notion pages. Authenticated pages need a login-first workflow

### 4. Synthesize Output
- **Tables** for comparisons (vendors, competitors, pricing)
- **Bullet points** for findings
- **Clear verdicts**: USE / DON'T USE / NEEDS MORE INFO
- Never dump raw search results

### 5. Store the Knowledge
- **Key facts** → `hindsight_retain` (conversational recall)
- **Detailed research** → wiki page in correct domain:
  - `wiki/consultancy/research/` for competitor/technical research
  - `wiki/femme-events/vendors/` for vendor research
- **Source docs** → `raw/` subfolder if valuable to preserve
- **Daily log** → what was researched and key findings

## Pitfalls
- **Rate limits:** Brave API has limits -- batch queries efficiently
- **Site blocks:** Some vendor sites block automated browsing -- try alternative sources
- **Stale data:** Always note research date on wiki pages
- **Over-research:** Don't go down rabbit holes -- stop when you have actionable info
