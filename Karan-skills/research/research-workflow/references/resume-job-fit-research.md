<!-- Archived source skill consolidated into `research-workflow` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: resume-job-fit-research
description: Research and shortlist job roles from a resume using Serper, Firecrawl/web extraction, and browser verification.
version: 1.0.0
---

# Resume-to-Role Fit Research

## When to Use
Use when the user provides a resume/CV and asks for specific job roles the candidate would be a strong fit for, especially when they request role, description, salary estimate, and fit rating.

## Workflow

### 1. Extract the resume first
- For local PDFs, use `pymupdf`/`fitz` if available; install `pymupdf` if missing.
- Capture:
  - current/target title
  - location and work preferences
  - recent employers and role progression
  - tools/software named
  - hard skills, soft skills, and domain keywords
  - seniority signals and likely compensation range

Example:
```bash
python3 -m pip install --quiet pymupdf
python3 - <<'PY'
import fitz
pdf='PATH_TO_RESUME.pdf'
doc=fitz.open(pdf)
print('\n'.join(page.get_text() for page in doc))
PY
```

### 2. Build candidate-search queries from the resume
Create 5–8 targeted Serper queries combining:
- location, e.g. `Atlanta GA`
- strongest job-family terms from resume, e.g. `catering sales manager`, `special events manager`, `venue sales manager`, `event operations manager`
- high-match venue/domain terms, e.g. `museum`, `wedding venue`, `hotel`, `hospitality`, `catering`, `corporate events`
- job board/application terms, e.g. `apply`, `careers`, `salary`

Use Serper for fast discovery:
```bash
curl -s "https://google.serper.dev/search" \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q":"Atlanta GA catering sales manager events jobs apply salary","num":10}'
```

### 3. Prioritize direct/employer pages over aggregators
Prefer verified employer career pages and ATS pages over Indeed/ZipRecruiter/LinkedIn snippets. Aggregators are useful for salary estimates and discovering leads, but often block browser access or contain stale postings.

Good sources:
- employer career pages
- Workday/ADP/Greenhouse/Lever/TeamWorkOnline pages
- company blog/careers posts

Use aggregator snippets only when:
- direct page is inaccessible
- salary is only visible in search snippets
- you need a cross-check that the role is real/current

### 4. Try Firecrawl/web extraction, then Browser fallback
- Use `web_extract`/Firecrawl for clean extraction if credits/API key are available.
- If Firecrawl/web_extract fails due to missing credits, missing key, or site blocking, switch to Browser immediately.
- Browser snapshots often work for ATS pages that scrape poorly.
- If Browser hits Cloudflare/blocked pages, fall back to Serper snippets and alternate direct employer pages.

Document limitations briefly in the final output when a source could not be fully scraped.

### 5. Verify role details in Browser
For each finalist, collect:
- official title
- company and location
- full-time/part-time/remote/on-site
- key responsibilities
- required/preferred experience
- posted salary if available
- application link/source URL

For dynamic ATS pages, use `browser_snapshot(full=true)` after navigation, and use page search/filter controls when available.

### 6. Salary estimate method
Use this hierarchy:
1. Official posting pay range
2. Same role/company salary snippet from Serper/aggregators
3. Same role/local-market estimates from Glassdoor/Indeed/ZipRecruiter/PayScale
4. Broader role/location estimate if no direct comp exists

Always label estimates as official, snippet-based, or market estimate. Avoid presenting estimated comp as guaranteed.

### 7. Fit rating rubric
Rate each role 1–10 based on:
- 35% direct experience overlap with resume responsibilities
- 25% domain/industry match
- 20% tools/process match, e.g. CRM, BEOs, proposals, F&B, vendor coordination
- 10% seniority match/stretch
- 10% practical constraints, e.g. location, schedule, full-time status, pay quality

Call out if a role is a strong fit but low-pay/part-time, or a good reach due to seniority.

### 8. Output format
Use a concise table with:
- Role/company/location
- Why it fits
- Brief job description
- Salary estimate
- Fit rating
- Source/apply link if useful

Then provide a short prioritized recommendation list: top 3 to apply to first, plus backup/reach notes.

## Pitfalls
- Job-board pages often block browser access; do not waste time fighting Cloudflare unless the direct employer page is unavailable.
- Firecrawl/web_extract may fail due to exhausted credits even when the skill says to use it; fall back to Browser and note the limitation.
- Search snippets can expose salary ranges hidden behind blockers; use them as estimates with attribution.
- Some application forms require Google sign-in or are private; still include the employer career page when the listing is verified.
- Do not overfit to exact titles. Search adjacent titles from the resume’s actual responsibilities.
