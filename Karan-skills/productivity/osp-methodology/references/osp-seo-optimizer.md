<!-- Archived source skill consolidated into `osp-methodology` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: osp-seo-optimizer
description: "Optimize web content for search engines using OSP's on-page SEO methodology. Generate meta titles, descriptions, slugs, and apply structured data. Use for Femme Events website pages, consulting client sites, and blog content."
version: 1.0.0
source: "Open Strategy Partners — osp_marketing_tools"
---

# OSP SEO Optimizer

Based on [Open Strategy Partners](https://openstrategypartners.com) on-page SEO methodology.

## When to load this skill

- Optimizing Femme Events website pages for search
- Creating SEO metadata for consulting client sites
- Writing blog posts or service pages that need to rank
- Auditing existing pages for SEO improvements
- When Karan says "optimize for SEO" or "write meta info for..."

## Meta information generation

### Required outputs for any page

1. **Article Title (H1)**
   - Longer than meta title
   - Contains primary keyword
   - Clear content type indicator
   - Action-oriented language

2. **Meta Title**
   - 50-60 characters max (avoid truncation)
   - Different wording than H1
   - Primary keyword front-loaded
   - Include brand if relevant (e.g., "| Femme Events")

3. **Meta Description**
   - 155-160 characters max
   - Matches search intent
   - Clear value proposition
   - Natural keyword inclusion
   - Compelling call-to-action

4. **URL Slug**
   - Hyphen-separated, lowercase
   - Keyword-focused
   - No unnecessary words (articles, prepositions)
   - Clean and readable

### Output format

```
📑 Article Title: [Title] ([N] chars)
🏷️ Meta Title: [Title] ([N] chars)
📝 Meta Description: [Description] ([N] chars)
🔗 URL Slug: [slug]

Analysis:
- Search Intent: [Informational/Commercial/Transactional/Navigational/Local]
- Primary Keyword: [how incorporated]
- Mobile Display: [considerations]
- CTR Optimization: [why this drives clicks]
```

## Search intent classification

| Intent | Signals | Content type |
|--------|---------|-------------|
| Informational | "how to", "what is", "guide" | Guides, FAQs, tutorials |
| Navigational | Brand/product names | Landing pages |
| Transactional | "buy", "book", "hire" | Service pages, booking pages |
| Commercial | "best", "compare", "review" | Comparisons, reviews |
| Local | "near me", "[service] in [city]" | Local landing pages |

### Femme Events intent mapping
- "wedding coordinator Atlanta" → Local + Transactional
- "wedding planning checklist" → Informational
- "Femme Events" → Navigational
- "best wedding planner Atlanta" → Commercial investigation
- "wedding coordination packages" → Transactional

### Papi AI Consulting intent mapping
- "AI consulting for small business" → Commercial + Local
- "automate business processes" → Informational
- "Papi AI Consulting" → Navigational
- "hire AI consultant" → Transactional

## On-page SEO checklist

### Content depth
- [ ] Cover subtopics supporting the main theme
- [ ] Include data, statistics, or case studies
- [ ] Add FAQ section (targets featured snippets)
- [ ] Optimize for multiple content formats (text, visuals)
- [ ] Strengthen internal and external links
- [ ] Address the full buyer's journey

### Keyword integration
- [ ] Primary keyword in title tag
- [ ] Primary keyword in meta description
- [ ] Keywords in H1, H2, H3 headings
- [ ] Keyword in first 100 words
- [ ] Keyword in conclusion
- [ ] LSI/semantic keywords throughout
- [ ] Keywords in image alt tags
- [ ] Keyword-rich internal link anchor text

### Internal linking
- [ ] Link to relevant high-value pages
- [ ] Use descriptive, keyword-rich anchor text
- [ ] Prioritize pillar/cornerstone content
- [ ] Link early in content (crawlers prioritize higher links)
- [ ] 3-5 internal links per 1,000 words
- [ ] Links open in same tab
- [ ] No broken or outdated links

### Structured data (Schema.org)
For Femme Events pages, implement:
- **Event schema** for weddings/events
- **LocalBusiness schema** for the business
- **FAQ schema** for frequently asked questions
- **Review schema** for testimonials
- **Service schema** for packages

For consulting clients, implement:
- **Organization schema**
- **Service schema** for offerings
- **Article schema** for blog posts
- **FAQ schema** where applicable

### Technical basics
- [ ] Single H1 per page
- [ ] Logical heading hierarchy (H1 → H2 → H3)
- [ ] Alt text on all images
- [ ] Mobile-responsive layout
- [ ] Fast page load (compress images, lazy load)
- [ ] HTTPS
- [ ] Clean URL structure

## Common pitfalls

- **Keyword stuffing** — prioritize readability over keyword density
- **Misinterpreting intent** — wrong content format for the search intent
- **Ignoring SERP features** — missed snippet/FAQ opportunities
- **Static approach** — search intent shifts; re-audit quarterly
- **Duplicate meta descriptions** — every page needs unique metadata
- **Missing local SEO** — for Atlanta-based businesses, always include geo-modifiers

## Pro tips

- **Combine intent layers** — informational content with transactional CTAs
- **Leverage "People Also Ask"** — mine Google PAA for FAQ content
- **Localize aggressively** — Femme Events should target "Atlanta", "Georgia", "metro Atlanta" in content
- **Google Business Profile** — keep updated, respond to reviews, post regularly
- **Schema markup** — implement JSON-LD in `<script>` tags, validate with Google Rich Results Test

## After optimization

1. Present all generated metadata in the standard format
2. Show a before/after diff if editing existing content
3. Suggest running the content editor skill for broader copy improvements
4. For new pages, recommend the value map skill to establish positioning first

## Attribution

Based on [Open Strategy Partners](https://openstrategypartners.com) on-page SEO and meta information methodology.
