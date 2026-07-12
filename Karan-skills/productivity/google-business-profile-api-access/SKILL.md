---
name: google-business-profile-api-access
description: Apply for Google Business Profile API access as an authorized consultant or agency managing client-owned locations. Covers honest positioning, website field handling, and approval-safe language.
tags: [google-business-profile, gbp, api-access, local-seo, consulting]
triggers:
  - "GBP API"
  - "Google Business Profile API"
  - "business profile api access"
  - "GBP access application"
  - "Google Business Profile application"
---

# Google Business Profile API Access Application

Use this when helping Karan apply for Google Business Profile API access for client work, especially when he has been granted manager access to a client's GBP from his own Google account.

## Core Positioning

Apply as Karan / independent consultant / agency operator assisting the client, not as if Karan works for the client.

Best framing:

> I am an independent consultant assisting small local businesses with authorized Google Business Profile management. I have been granted Manager access to client-owned profiles by the business owner, and API access will only be used for authorized client locations.

Do not claim to be an employee of the client unless that is factually true.

## Primary Reason for Seeking Access

Use a reason closest to:

- Agency or third-party location management
- Manage listings for business clients
- Local SEO / reputation / business profile management
- Reporting and insights for businesses

Recommended free-text answer:

> I help small local businesses manage and improve their digital presence. I am requesting Google Business Profile API access so I can securely manage business profile data, monitor profile status, retrieve location insights, support local visibility audits, and streamline profile maintenance for client-owned locations where I have explicit authorization.

If referencing a specific client:

> I am onboarding a local retailer and have been granted Manager access to their Google Business Profile by the business owner. API access will support profile verification tracking, profile data audits, business information accuracy checks, local visibility reporting, and ongoing profile maintenance. Access will only be used for client-authorized locations.

## What to Avoid

Avoid language that sounds like:

- Scraping Google data
- Lead generation from public listings
- Data resale
- Review automation or fake engagement
- Mass messaging
- Unauthorized edits
- Managing businesses without account access

Never overclaim an enterprise-scale listings platform if the current setup is a small consulting practice.

## If Asked Why API Instead of UI

Use:

> The API is needed to standardize audits, reporting, and ongoing maintenance across client-owned locations. The Google Business Profile web interface is useful for manual edits, but API access allows repeatable internal workflows, reduces manual errors, documents profile status, and supports client reporting from authorized profile data.

## Users / Customers Answer

Use:

> Users are internal operators managing Google Business Profiles on behalf of small business clients who have explicitly granted account access. Clients receive reporting and recommendations. API access is not exposed directly to the public.

## Data Storage Answer

Use:

> I only store the minimum operational data required for client reporting and audit history, such as business profile fields, profile status, performance metrics, timestamps, and notes. I do not sell or share Google Business Profile data with third parties.

## Hard Eligibility Requirements

Google requires ALL of these before they even review your application text:

1. **Verified GBP, active 60+ days** — must be a real, verified Business Profile (your own or a client's). Verification = postcard/phone/video completed.
2. **Website representing the business** — the GBP must have a legitimate, working website linked that clearly represents the business on the profile.
3. **Email must be owner/manager on the GBP** — the Google account you apply with must have owner or manager role on the Business Profile.
4. **GBP fully complete** — all fields filled (hours, description, categories, photos, services, etc.). Incomplete profiles get auto-rejected.

Source: https://developers.google.com/my-business/content/prereqs#request-access

## ⚠️ CRITICAL: Website Field Must Match the Business on the GBP

**Lesson learned (2026-04-30):** Google rejected our application because we linked Karan's personal landing page (`karan-sabnani-landing.vercel.app`) instead of the client's actual website (`jmdmenswear.com`). Google's reviewer sees a GBP for "JMD Menswear" linked to a personal consultant portfolio = instant quality check fail.

**Rule:** When applying for API access for a specific client's GBP, use THE CLIENT'S WEBSITE — not your consultant page. Google's requirement is:

> *"Have a website representing the business listed on the GBP."*

This means the website URL must match the business name on the GBP. A consultant landing page does not "represent" a menswear store.

**Correct approach:** Link `jmdmenswear.com` (or whatever the client's actual domain is) to the GBP listing AND use it in the application.

## Company Website Field

Decision rule (updated after rejection):

- **The GBP's website field** → always use the client's actual business website (e.g., `jmdmenswear.com`). This is what Google checks.
- "Your company website" (about you, the applicant) → use Karan's own consultant landing page.
- "Business website you manage" → use the client website.
- "Website where the API will be used" → use Karan's consulting/internal tool site unless API use is only embedded in the client site.

If no client site exists yet, ensure one is live and clean before applying. The client site must:
- Load without SSL errors or security warnings
- Not redirect to safebrowse.io or any malware/warning page
- Clearly represent the business listed on the GBP
- Have content consistent with GBP info (name, address, phone, hours)

If no consultant site exists yet, create a simple temporary consultant landing page first. It should be truthful, professional, and avoid claiming the client as Karan's company.

Minimum landing page content:

- Karan Sabnani as the public identity
- Independent digital presence or local business systems consulting
- Services: GBP audits, local visibility reporting, website/landing page setup, review workflow support, content and operations systems
- Client authorization statement: only manages profiles for businesses that grant access
- Contact email
- Optional client example only if truthful and approved

## Constraint-Safe Landing Page Build Pattern

When the user asks for a temporary approval-support site:

1. Read the relevant business plan / operating model source files.
2. Rewrite positioning into public-safe language.
3. Respect explicit forbidden terms exactly. For example, if user says do not mention a brand name or "AI", scan the final HTML for those strings.
4. Avoid em dashes if requested. Also scan for en dashes if the style constraint is strict.
5. Build mobile-first, since application reviewers may open it on any device.
6. Include a favicon to avoid noisy 404 console errors during preview.
7. Serve via local HTTP server and verify:
   - page title
   - responsive mobile viewport
   - no horizontal overflow
   - no forbidden strings
   - no console errors

Useful verification snippet:

```bash
python3 - <<'PY'
from pathlib import Path
p = Path('/path/to/index.html')
s = p.read_text()
for term in ['Papi', 'papi', 'AI', ' ai ', '—', '–']:
    print(repr(term), term in s if term != ' ai ' else term in s.lower())
print('bytes', p.stat().st_size)
PY
```

Browser verification:

```js
() => ({
  width: innerWidth,
  scrollWidth: document.documentElement.scrollWidth,
  overflowX: document.documentElement.scrollWidth > innerWidth,
  forbidden: ['Papi','papi','AI','—','–'].filter(x =>
    (document.documentElement.innerText + document.documentElement.outerHTML).includes(x)
  ),
  title: document.title
})
```

## Deploying the Temporary Consultant Site

If the user needs a URL for the application and has Vercel available, deploy the static landing page directly from its folder.

1. Confirm CLI availability and auth:

```bash
node --version
npm --version
npx --yes vercel --version
npx --yes vercel whoami
```

If `whoami` says no credentials, have the user run:

```bash
cd /path/to/site
npx --yes vercel login
```

2. Add a tiny `vercel.json` for static clean URLs:

```json
{
  "cleanUrls": true,
  "trailingSlash": false
}
```

3. Deploy production from the site directory:

```bash
cd /path/to/site
npx --yes vercel --prod --yes
```

For a single-file static site, Vercel should detect no framework and use `.` as the output directory. Capture both the production URL and the aliased project URL.

4. Verify deployment status:

```bash
npx --yes vercel inspect https://PROJECT_ALIAS.vercel.app
```

Expected status: `Ready` and target `production`.

5. Verify the live site in-browser, not only the local file:

```js
() => ({
  title: document.title,
  url: location.href,
  forbidden: ['Papi','papi','AI','—','–'].filter(x =>
    (document.documentElement.innerText + document.documentElement.outerHTML).includes(x)
  ),
  hasWebDevelopment: document.documentElement.innerText.includes('Web development'),
  hasLightweightToolBuilding: document.documentElement.innerText.includes('Lightweight tool building'),
  overflowX: document.documentElement.scrollWidth > innerWidth
})
```

Also check browser console errors after loading the production URL. Inline favicon is useful to avoid `/favicon.ico` 404 noise.

## Post-Approval Setup Notes from Google Docs

Once approval is granted, verify Cloud Console quota first: `0 QPM` means not approved/usable yet; `300 QPM` means approved. Google docs say the Google My Business API may not be visible until access is approved.

For dedicated OAuth setup and re-auth, follow `references/dedicated-gbp-oauth-token.md`. It includes the backup-before-reauth pattern, localhost consent URL handling, required identity/scope/refresh-token checks, and the read-only audit verification sequence.

For wiring GBP into a project workspace or cloud-agent environment, follow `references/cloud-agent-gbp-api-wiring.md`. It covers local symlinks into `~/.hermes`, mounted secret files, base64 env secret fallback, smoke tests, and secret hygiene checks.

Google's current Business Profile APIs are federated by feature area, with different base URLs. For implementation plans, include at least:

- Google My Business API v4.9 (`https://mybusiness.googleapis.com`) for Reviews, LocalPosts, and Media.
- Account Management (`https://mybusinessaccountmanagement.googleapis.com`) for account/location access discovery.
- Business Information (`https://mybusinessbusinessinformation.googleapis.com`) for location fields, categories, attributes, and Google updates.
- Business Profile Performance (`https://businessprofileperformance.googleapis.com`) for daily metrics and monthly search keyword impressions.
- Verifications, Notifications, Q&A, Place Actions as needed; Lodging is listed in Google's basic setup even if not relevant to non-lodging clients.

OAuth uses user consent, not service accounts. For GBP work, prefer a dedicated least-privilege token separate from general Gmail/Drive/Calendar OAuth; see `references/dedicated-gbp-oauth-token.md`. Smoke-test with scope `https://www.googleapis.com/auth/business.manage` and `GET https://mybusinessaccountmanagement.googleapis.com/v1/accounts` expecting `200 OK` after approval. There is no sandbox environment; use read-only calls first and `validateOnly=true` where write endpoints support it.

The 2026 reference overview highlights recurring posts through LocalPosts and review media/reply status through Reviews; include these as high-value post-approval capabilities when relevant.

### Post-Approval Local SEO Operating Pattern

After API acceptance, start with **read-only visibility operations** before any profile mutation:

1. Discover accounts/locations and verify the intended business profile.
2. Audit profile completeness: categories, website URL, phone, service areas, hours, description, services, attributes, photos/media, and verification/status fields.
3. Pull performance metrics and search keyword impressions on a weekly/monthly cadence.
4. Monitor review count, average rating, unanswered reviews, and recurring review themes.
5. Draft LocalPosts, media upload plans, and review replies, but keep them approval-gated.

Default safety rule: API access does not imply permission to publish. Treat LocalPosts, review replies, media uploads, profile field edits, directory submissions, and public social posts as external/public mutations requiring explicit approval. For agent workflows, a dedicated marketing/SEO profile may own research, audits, reporting, and drafts, while default Hermes handles approval and final execution.

### Local SEO Operating Pattern After Approval

For broader local SEO and Google visibility planning beyond GBP/API access, use the `local-seo-visibility-ops` skill. It covers technical SEO, Search Console, service pages, reviews, citations/directories, competitor patterns, automation vs human work, and Claude/Codex leverage.

For local SEO clients or owned brands such as Femme Events, treat the API as a visibility cockpit before using it as an automation layer:

1. **Read-only audit first:** discover accounts/locations, then compare profile fields against the website and approved brand facts: business name, category, service areas, website, phone, hours, description, services, photos/media, attributes, Q&A, and profile status.
2. **Performance monitoring:** pull Business Profile Performance metrics and monthly search keyword impressions on a recurring cadence; pair this with Search Console query data to decide which service pages or posts to tune.
3. **Review monitoring:** track rating, count, new reviews, unanswered reviews, and recurring language/themes. Draft replies in brand voice, but do not post review replies without explicit approval.
4. **LocalPosts workflow:** generate draft LocalPosts from journal content, service pages, seasonal planning tips, or event proof. Publishing is a live public mutation and requires explicit approval.
5. **Media workflow:** only upload approved first-party images or media with usage rights; verify the asset is live after upload.
6. **Profile updates:** for any write operation, show current value → proposed value → reason, then request approval before mutation. Use `validateOnly=true` where available.

Avoid using the API for scraping, lead generation from public listings, review automation, fake engagement, or unsolicited outreach.

## Rejection Diagnostics

If Google says "did not pass our internal quality checks," check these in order:

1. **Website/GBP mismatch** — does the website URL actually represent the business on the GBP? (Most common cause.)
2. **Website broken** — does the site load clean? Check for SSL errors, safebrowse redirects, malware warnings. Use incognito + cellular data to verify (browser cache can hide issues).
3. **GBP too new** — must be verified and active for 60+ days minimum.
4. **GBP incomplete** — missing hours, description, photos, categories, or services.
5. **Email not linked** — your Google account must be listed as owner/manager on the GBP.
6. **Case ID for reapplication** — original case ID `7-0941000040185` (Karan's first attempt, rejected 2026-04-30). Resubmitted case ID `2-4471000041032` (2026-04-30, using jmdmenswear.com as website).

To check approval status after reapplying: view quotas for Business Profile APIs in Google Cloud Console. 0 QPM = not approved. 300 QPM = approved.

## Approval-Safe Tone

Be specific, legitimate, and operationally grounded. The best approval strategy is truthful scope plus explicit guardrails:

- authorized locations only
- manager access granted by owner
- internal use only
- no scraping
- no data resale
- no unauthorized edits
- minimal necessary storage
