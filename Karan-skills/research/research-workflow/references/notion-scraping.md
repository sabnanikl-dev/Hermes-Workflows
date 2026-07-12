<!-- Archived source skill consolidated into `research-workflow` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: notion-scraping
description: "How to scrape Notion pages — curl fails, use browser_navigate instead"
category: research
---

# Scraping Notion Pages

Notion pages block curl/scraping with HTML-only rendering. Use browser navigation to access content.

## When to Use
You have a public Notion page URL and need to extract its content.

## The Core Problem
- `curl` on Notion URLs returns only a bare HTML shell with no content
- The Notion API requires authentication even for public pages
- Business directories (Yelp, The Knot, WeddingWire) use Cloudflare anti-bot protection

## What Works: Browser Navigation
Use `browser_navigate()` — it renders JavaScript and loads the full page content:

```
browser_navigate("https://www.notion.so/Page-Title-pageid")
```

The page will render with all content, headings, text, code blocks, and interactive elements visible in the accessibility tree snapshot.

## What Doesn't Work
- `curl https://notion.so/...` — returns empty shell HTML
- Notion API v3 without auth token — blocked
- DDG HTML search — Notion pages often index poorly in search engines

## Tips
- Long Notion pages will have `browser_snapshot()` truncated — scroll down and take additional snapshots
- The `.pvs=21` suffix in Notion URLs is a viewing parameter — safe to keep or remove
- Code blocks in Notion appear as `figure: "> Loading Plain Text code…"` in browser snapshots — you may not get the actual code content
- For Notion pages with lots of nested content, navigate to sub-pages directly rather than relying on a single snapshot

## Pitfalls
- Notion uses lazy loading for code blocks — you may see "> Loading Plain Text code…" instead of actual code
- Private Notion pages or pages with "Sign in required" will only show the login prompt
- Notion's `__NEXT_DATA__` JSON extraction works sometimes but is unreliable across page types
