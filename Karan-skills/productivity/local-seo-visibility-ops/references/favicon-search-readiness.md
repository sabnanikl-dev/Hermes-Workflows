# Favicon search readiness: implementation versus Google processing

## Trigger and claim boundary
Use when a website's favicon works in a browser but Google shows a generic globe, or the user asks how we know the code is correct rather than merely assuming search-cache delay.

Maintain separate verdicts:
1. Production implementation passes the tested technical requirements.
2. Google's recorded crawl/index state predates or postdates deployment.
3. A specific live SERP observation shows the icon or a generic fallback.

Eligibility is not guaranteed display. A missing SERP icon does not by itself identify a code defect; passing tests do not by themselves establish eligibility.

## Read-only evidence sequence
1. Fetch current authoritative guidance: https://developers.google.com/search/docs/appearance/favicon-in-search . Preserve the retrieval date; do not promote stale third-party requirements into permanent rules.
2. Fetch original homepage HTML and parse only the head for supported icon links, canonical, and robots meta. Establish whether discovery requires JavaScript. Resolve relative URLs against the final homepage URL.
3. Fetch every declared supported icon and save structured observations: requested/final URL, redirect chain, status, MIME, X-Robots-Tag, decoded format, actual dimensions, and SHA-256. Decode image bytes rather than trusting extensions, declared sizes, or HTTP 200. ICOs may contain several square frames; inspect all available sizes.
4. Read robots.txt and evaluate homepage access for Googlebot and image access for Googlebot-Image. Inspect HTML/indexing headers separately from crawl permission.
5. Check HTTP/HTTPS and apex/www homepage redirects and canonical consistency. Google favicon identity is hostname-based; inspect the host actually appearing in the search result.
6. Optionally repeat homepage/icon requests with Googlebot/Googlebot-Image user-agent strings and compare hashes. Explicitly state this tests user-agent handling from our network, not verified Google IP access, WAF behavior for Google's network, or actual crawler retrieval.
7. Load the google-search-console skill. Refresh existing dedicated credentials without printing secrets; verify intended identity, scopes, and property access. Use read-only URL Inspection for canonical and alternate homepages:
   - POST https://searchconsole.googleapis.com/v1/urlInspection/index:inspect
   - JSON: inspectionUrl, siteUrl, languageCode.
   - Capture indexStatusResult.verdict, coverageState, robotsTxtState, indexingState, pageFetchState, lastCrawlTime, googleCanonical, userCanonical, and crawledAs.
8. Compare timestamps programmatically against verified production deployment evidence. If only merge time is available and the recorded crawl predates merge, that establishes it also predates the ensuing deployment; do not label merge time as deployment time. Render human-facing times in an explicit timezone.
9. Inspect the actual Google result visually and save a query/time-scoped screenshot. Do not infer a rendered favicon from a favicon-cache endpoint or search API text. A CAPTCHA screenshot is blocked evidence, not search absence. Before resuming from a blocked state, re-inspect; a single later navigation retry may succeed. Report the action that actually occurred, not a supposed CAPTCHA solution.
10. Save a compact project-local Markdown verdict plus sanitized JSON. Programmatically verify claimed counts, status codes, dimensions, and timestamp ordering. Keep transient deployment observations out of durable vault pages.

## Official requirements observed September 2026
The official page, last updated 2026-08-28 when consulted, said:
- Supported link relations include icon, apple-touch-icon, and apple-touch-icon-precomposed.
- Square image, at least 8x8; larger than 48x48 recommended. Do not invent a mandatory multiple-of-48 rule.
- Supported formats listed BMP, GIF, ICO, PNG, JPEG, PPM, and TIFF; check current docs rather than assuming every browser-supported format is supported in Search.
- Googlebot must be able to crawl the homepage and Googlebot-Image the icon.
- Stable favicon URL and brand-representative, appropriate imagery.
- Recrawl/processing can take several days to several weeks; homepage URL Inspection can be used to request indexing.

## Interpretation and next step
- Preferred wording: “No technical blocker found in these production checks; Google's last recorded homepage crawl predates deployment, which strongly supports processing delay.”
- Avoid: “The code is definitely correct; Google just hasn't refreshed.”
- URL Inspection API reflects the indexed record; it neither runs the UI's live URL test nor requests indexing. It exposes no favicon-specific acceptance/processing status. A post-deployment page crawl does not prove the icon has finished processing.
- With explicit approval, request homepage indexing through Search Console UI; preserve success/readback evidence. Do not use Google's restricted-purpose Indexing API as a general website recrawl substitute.
- Leave stable icon URLs alone. After a recorded post-deployment crawl and reasonable processing time, inspect again. If the issue persists for several weeks, review actual verified crawler/WAF logs and Google's favicon feedback path instead of assuming indefinite lag. Do not create a recurring watcher unless requested.

## Validated example, not current live state
Femme Events, September 15, 2026 EDT: production raw HTML declared ICO and PNG icons, five linked assets decoded correctly and returned 200, robots allowed access, and bot-user-agent probes matched ordinary bytes. The ICO contained 16/32/48/64/128 square frames and the Apple touch icon was 180 square. Search Console reported the canonical homepage indexed, allowed, successfully fetched, and last crawled September 12 at 15:32:05 EDT; the favicon change merged September 15 at 22:30:58 EDT and deployed afterward. The observed SERP still showed a generic globe. This supported lag without proving eventual display.

Evidence was kept in the project's issue-150-evidence directory: favicon-live-audit.json, favicon-gsc-inspect.json, favicon-google-readiness.md, and google-live-serp.png. Re-fetch live facts on future work; these filenames are provenance, not current status.
