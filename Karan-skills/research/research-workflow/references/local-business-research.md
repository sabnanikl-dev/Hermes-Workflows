<!-- Archived source skill consolidated into `research-workflow` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: local-business-research
description: Research and verify local businesses/vendors when search engines block browser automation. Uses DDG HTML as a search fallback, then systematically verifies each candidate.
category: research
---

# Local Business Research

## When to Use
- User asks to find local vendors, businesses, or services in a specific area
- Previous vendor lists need verification or cleanup
- Researching local options for events, services, or procurement

## The Core Problem
Browser-based search engines (Google, Bing, Yahoo) aggressively block automated access with CAPTCHAs and rate limiting. Business directories (Yelp, The Knot, WeddingWire, Yellow Pages) use Cloudflare anti-bot protection. The approach below reliably bypasses these blocks.

## Step-by-Step Approach

### Phase 1: Search
Do NOT use `browser_navigate()` on Google/Bing for search — you'll hit CAPTCHA pages.

**Primary: Serper (Google Search API)** — Best results, Google-quality data:
```bash
curl -s "https://google.serper.dev/search" \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "event tent rental Lawrenceville Georgia", "num": 10}'
```
Returns title, link, snippet, sitelinks, and `knowledgeGraph` for direct answers.

**Alternative: Brave Search API** — Rich descriptions, good backup:
```bash
curl -s "https://api.search.brave.com/res/v1/web/search?q=event+tent+rental+lawrenceville+georgia&count=10" \
  -H "Accept: application/json" \
  -H "X-Subscription-Token: $BRAVE_API_KEY"
```

**Fallback: DuckDuckGo HTML** (when no API keys available) — Uses `html.duckduckgo.com` plain HTML via Python `urllib`. Fragile but requires zero setup.

### Phase 2: Quick Domain Verification
Before browsing any site, check if the domain resolves and returns a 200:
```python
import requests
for url in candidate_urls:
    try:
        r = requests.head(url, timeout=10, allow_redirects=True)
        print(f'{url} -> {r.status_code} -> {r.url}')
    except Exception as e:
        print(f'{url} -> ERROR: {e}')
```

Discard candidates that:
- Return 404/403/5xx
- Timeout or fail DNS
- Redirect to unrelated businesses (e.g., CA company instead of GA)

### Phase 3: In-Depth Verification
For domains that pass Phase 2, use `browser_navigate()` to:
1. Confirm it's the right business (location, services match)
2. Extract phone numbers, email addresses, pricing
3. Check whether the business actually serves the user's area

## What to Look For
- **Redirects = red flag.** If `a1partyrental.com` redirects to `100house.com` in California, it's not the GA business you're looking for.
- **403 Forbidden = possibly real but unreliable.** The domain exists and the business may still operate. Worth noting but flagging as "website not accessible."
- **DNS resolution failure = treat as unverified.** The business may have closed or changed domains.
- **Follow-up:** If a company's site is broken but a phone number exists from a directory listing, recommend calling.

## Reporting Format
Present results as concise bullet points (NO markup tables — user preference). For each company:
- Name, location, phone/email, website status
- One line about what's verified
- Flag any concerns (broken site, out-of-state redirect, etc.)

## Client-Facing Local Audit / GBP Report Pattern
When the output is a client-facing local business audit or Google Business Profile presentation, do not write it like a generic SEO report. Frame it for the business owners:
1. Start with what is already working, using proof from the profile or public evidence.
2. Separate exact fixes from strategic/future opportunities.
3. Name the owners/decision-makers when known and assign approvals based on their role: brand voice/photos/customer feel vs. operational accuracy/inventory/service claims.
4. Be specific about what needs fixing: missing description, stale posts/products, missing logo, unreplied reviews, hours conflicts, category/service gaps, FAQ/Ask Maps readiness, etc.
5. Explain the practical business outcome: more calls, directions, store visits, and trust — not abstract “SEO hygiene.”
6. Preserve approval gates for all public profile edits, review replies, posts, photos, FAQ/schema, service claims, and private dashboard metrics.
7. For 2026 GBP Q&A: do not treat seeded GBP Q&A as the main quick-fix surface. Google’s My Business Q&A API was discontinued Nov. 3, 2025, and the user-facing experience is shifting toward AI/Ask Maps. Recommend stronger answer sources instead: complete GBP fields, website FAQs/FAQ schema, specific reviews, current posts, and monitoring of generated answers.

Reference example: `references/client-facing-gbp-report-pattern.md`.

## Search API Selection

**Serper (Google Search)** — Primary. Best result quality, includes knowledge graphs and sitelinks.
```bash
curl -s "https://google.serper.dev/search" \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "YOUR QUERY", "num": 10}'
```

**Brave Search** — Good backup when Serper quota is exhausted.
```bash
curl -s "https://api.search.brave.com/res/v1/web/search?q=YOUR+QUERY&count=10" \
  -H "Accept: application/json" \
  -H "X-Subscription-Token: $BRAVE_API_KEY"
```

**DuckDuckGo HTML** — Last resort fallback. Fragile but needs zero setup.

## Competitive Landscape Research (vs. single vendor lookup)
When analyzing a market rather than finding one vendor, combine multiple approaches:
1. **Serper/Brave bulk search** — Cast a wide net with 3-5 related queries (e.g., "wedding coordinator Atlanta", "wedding design services Atlanta", "day-of coordinator Atlanta")
2. **Google Places API** — Verify businesses exist, get ratings/phone/address in batch
3. **Browser visits** — Navigate to 3-5 top competitor sites directly to verify positioning, services, and pricing
4. **Cross-reference** — Compare pricing tiers, service offerings, aesthetic positioning, and target customer profiles

Present competitor analysis as tiers (e.g., luxury/mid-range/budget) with strengths and weaknesses. This reveals market gaps and positioning opportunities.

## Pitfalls
- **Notion pages cannot be scraped via curl/urllib/requests** — Notion is a pure SPA with dynamic JS rendering. Always use `browser_navigate()` + `browser_snapshot()` to extract Notion content. HTTP fetches return empty HTML shell.
- **Never use `browser_navigate()` on Google/Bing** — CAPTCHA walls. Use Serper or Brave for search.
- Yelp, YellowPages, The Knot, WeddingWire all block automated access at the CDN level.
- Don't trust cached directory listings — always verify the actual domain resolves to the expected business.
- A company's name may have changed (e.g., "A-1 Party Rental" became "Hundred House" in a different state). Cross-reference the redirect destination.
- **API keys in `~/.hermes/.env` are not available in sandboxed Python** — use terminal curl or `execute_code` (runs on host where env vars are set).
- **Serper** returns 403 if quota is exhausted — fall back to Brave, then DDG HTML.

## Previous Findings (Metro Atlanta)
See agent memory for vendor research notes. Key lessons:
- Always verify business location matches the search area (phone redirects, domain redirects are common when businesses sell)
- Local event rental websites are often poorly maintained; 403s and DNS failures don't always mean the business is gone
