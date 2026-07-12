---
name: femme-events-design
description: "Femme Events brand design guidelines — Amanda's approved color palette, visual style, brand assets. Load when creating anything for Femme Events (website, graphics, social, print)."
---

# Femme Events Brand Design Guide

**Brand:** Femme Events (wedding coordination by Karan & Amanda)
**Website:** femmeevents.com
**Instagram:** @_femmeevents

## Color Palette — Amanda Approved (Updated April 17, 2026)

Full Tailwind-style 11-step scales across 5 core colors. Master JSON and CSS files in:
`/Users/creator/projects/femme-events/brand-assets/color-palette.json`
`/Users/creator/projects/femme-events/brand-assets/tailwind-colors.css`

### Core Colors (50-500 = light-to-vibrant, 600-950 = dark-to-rich)

| Color Name | -50 | -300 | -500 | -700 | -900 | -950 |
|------------|-----|------|------|------|------|------|
| soft-blossom | #f7edf0 | #d293a6 | #b44b6b | #6c2d40 | #240f15 | #190b0f |
| fuchsia-plum | #f8edf2 | #d392b3 | #b64980 | #6d2c4d | #240f1a | #1a0a12 |
| wisteria | #f6edf8 | #c891d4 | #a347b8 | #622b6e | #210e25 | #170a1a |
| dark-raspberry | #fbe9f3 | #e97cba | #da258c | #831654 | #2c071c | #1f0514 |
| pink-orchid | #f9ebf5 | #dd88c5 | #c7389e | #77225f | #280b20 | #1c0816 |

### Usage Guidelines
- **Backgrounds**: 50-100 (soft washes)
- **Subtle accents**: 200-300
- **Primary buttons/links**: 400-500
- **Headings/dark elements**: 600-700
- **Near-black text**: 900-950
- One color family dominates (60-70%), 1-2 supporting tones, one sharp accent

### Legacy Colors (DEPRECATED — existing codebase only)
The old 13-color palette (`#ddadbc`, `#efd5e1`, `#fdf8ea`, `#3f0d2a`, `#bd708c`, `#7f165b`, etc.) was replaced April 17, 2026. Existing component files still reference these hex codes — they should be migrated to the new tailwind scale when touched.

## Design Rules
- Use Amanda's new 5-color tailwind scale for all new design work
- Dark/light contrast for readability
- Logo and brand assets: `~/projects/femme-events/brand-assets/`
- Site: `~/projects/femme-events/website/Femme Events Website Build/Femme-Events-Website/`

## Fonts Used Across Designs

When debugging visual glyph/font artifacts, especially weird ampersands or punctuation in decorative/display fonts, use `references/font-glyph-artifact-audit.md`. Treat these as site-wide typography QA issues: scan hardcoded JSX, fallback data, metadata, and Sanity/CMS content paths; prefer a reusable symbol fallback/component over one-off replacements.

| Font Role | Font Name | Usage |
|-----------|-----------|-------|
| Primary / Website Hero Display | Frunchy Sage | Current live/site hero `h1` typeface for “Femme Events”; font file lives at `public/fonts/frunchy-sage.ttf` and is mapped to `--font-display` / `h1, h2` in `src/index.css`. |
| Secondary / Website Subheading | Balgin | Current site subheading font; font file lives at `public/fonts/balgin-display-regular.otf`. |
| Website Body / Serif Sans-feel | The Seasons | Current site body-ish brand font; font file lives at `public/fonts/the-seasons-regular.ttf`. Use `.font-system` for emails, phone numbers, heavy punctuation, and machine-readable contact text. |
| Legacy Primary / Display | Oranienbaum | Older wordmark guidance only; verify against live repo before recreating assets. |
| Legacy Secondary / Subheading | Cormorant Garamond (Italic) | Older “Coordination & Design” tagline guidance only. |
| Legacy Accent / Name | Tenor Sans | Older “Karan Sabnani”, “Amanda Brewton” guidance only. |
| Display / Event Title | Miracle | Decorative serif (Canva-exclusive; alternative: Playfair Display). |

## Contact Info on Brand Materials
- **Phone:** (678) 468-2842
- **Email:** Karan@FemmeEvents.com
- **Website:** femmeevents.com

## Print/Cricut Asset Notes
- Before recreating a Femme website text asset, inspect the live repo/CSS rather than relying on older brand-doc font names; the current hero display is Frunchy Sage from `public/fonts/frunchy-sage.ttf`.
- For sticker/Cricut exports, render transparent `RGBA` PNGs at 300 DPI, keep generous transparent padding around glyphs, and verify alpha/corner transparency plus no clipping before sending.
- If sending generated PNGs through Hermes chat, copy them into Hermes' actual safe media roots (`~/.hermes/cache/images/...` for PNG/JPG/WebP, `~/.hermes/cache/documents/...` for ZIP/PDF/etc.) before using `MEDIA:` tags.

## Development & Deployment

### Repo
- GitHub: `sabnanikl-dev/Femme-Events-Website`
- Local path: `~/projects/femme-events/website/Femme Events Website Build/Femme-Events-Website/`
- **WARNING**: Path has spaces — always `cd` with quotes or use `pushd`/full quoting in shell commands
- If local branch diverges from main after a merge, use `git fetch origin main && git reset --hard origin/main` (Karan approves these)

### Vercel Website Deploys
- Production project: `femme-events-website` under Vercel scope `sabnanikl-devs-projects`
- GitHub integration: `sabnanikl-dev/Femme-Events-Website`, production branch `main`
- Build settings: framework `vite`, install `npm install`, build `npm run build`, output `dist`, Node `24.x`
- Required Vercel env vars for production/preview/development: `VITE_FORMSPREE_ENDPOINT`, `VITE_SANITY_PROJECT_ID`, `VITE_SANITY_DATASET`, `VITE_SANITY_API_VERSION`
- Vite + React Router needs `vercel.json` SPA fallback:
  ```json
  { "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
  ```
  Without it, direct loads for `/about`, `/journal`, and `/what-happens-next` return Vercel 404 even though homepage works.
- Custom domains are added in Vercel: `femmeevents.com` and `www.femmeevents.com`; DNS remains at domain.com unless Karan explicitly chooses nameserver migration.
- Preserve Google Workspace DNS when updating domain.com: do not remove MX `smtp.google.com`, SPF, DKIM, or Google verification TXT records.
- After any production deploy, verify both Vercel URL route status and browser console for at least one direct route before reporting success.
- For the full domain.com → Vercel cutover procedure, DNS/email preservation checks, forced-resolution probes, and silent propagation watchdog pattern, see `references/vercel-domain-cutover.md`.

### Sanity Studio Deploys
- Studio lives at `studio/` subdirectory in the repo
- After ANY PR that adds/changes a Sanity schema, redeploy the studio:
  ```
  cd studio && npx sanity deploy
  ```
- Deploys to: https://femmeevents.sanity.studio/
- After deploy, leave a comment on the related GitHub issue confirming the studio is updated
- Hermes owns studio deploys (not Karan, not Amanda)

### CMS Pattern (established in posts + testimonials)
- `src/data/<type>.ts` — static fallback (interface + hardcoded data)
- `src/lib/<type>.ts` — Sanity fetch layer (mirrors posts pattern: sanityClient guard, fallback, empty-result fallback)
- `src/components/<Component>.tsx` — useState with getInitial() for sync render, useEffect for async Sanity fetch
- Three layers of safety: no Sanity client → fallback, fetch error → fallback, empty CMS result → fallback
- **Sparse CMS rule:** for incremental CMS migrations, do not let "CMS returned one item/category" overwrite the full static fallback. Merge CMS records into fallback data and de-dupe by stable human keys (category/vendor name or slug). CMS should win on matching records, but fallback content must remain visible until Amanda has fully populated Sanity.
- See `references/cms-fallback-merge.md` for the Issue 62 vendor regression pattern and merge checklist.

### Stakeholder Content Implementation
- When Amanda/Karan provides content via email/comment, normalize it into polished site copy without inventing claims or changing the meaning.
- For Femme website copy intake with Amanda, review the existing component/page copy first and include it in the draft message as the working baseline. Ask interview-style questions rather than asking Amanda to write polished copy from scratch. Default the sender/signoff to exactly “Hermes, Karan’s personal agent” when the email is from Hermes. For About copy, bias questions toward Amanda personally plus the Femme Events brand story unless Karan directs otherwise.
- For Femme Journal post prompts specifically, avoid generic wedding-blog framing. Karan wants the Journal to feel uniquely Amanda: her taste, eye, opinions, small details she notices, and lived coordinator/designer perspective. Give her gentle directions and optional angles, but invite personal stories, honest takes, and “what you would tell a bride directly” rather than steering her into SEO/canned article topics.
- Preserve the current homepage information architecture unless the user explicitly asks to replace it. If stakeholder content expands an existing homepage section into a different stage of the client journey, add a separate page/route and link to it rather than overwriting the homepage section.
- Do not add a homepage photo gallery just because first-party photos were supplied. If a gallery/photo section is explicitly requested, prefer the Sanity-managed asset workflow; only commit optimized local public assets when that workflow is explicitly chosen for the PR.
- Vendor lists should use high-confidence official names/links/socials only. Exclude ambiguous vendors rather than guessing publicly, and call out the exclusion in the PR.
- Never publish downloaded third-party vendor logos/photos/reference images unless rights/permission are confirmed; using names and researched official URLs is safer.
- If direct Sanity upload is unavailable or unnecessary for the current PR, update the static fallback data so the site still renders safely.
- For direct vendor image/logo population in Sanity, do not commit third-party media to the repo. Source from official vendor-controlled pages, stage/normalize assets in `/tmp`, visually QA a contact sheet, upload with `@sanity/client`, and verify every published vendor has a working Sanity CDN image. See `references/vendor-image-sanity-upload.md`.
- For Femme local SEO / Google visibility work, start with the local SEO visibility reference: technical foundation, GBP, service landing pages, reviews/citations, skills.sh candidates, and agent delegation. See `references/local-seo-visibility-plan.md`.
- For website copy intake that is not ready to implement, create a standalone, polished HTML review document first (with Amanda’s raw essence preserved, proposed copy blocks, scope guardrails, and a section-by-section GitHub issue plan), then wait for copy approval before opening implementation issues. See `references/website-copy-intake-review-doc.md`.
- Femme copy review docs must preserve Amanda’s voice while respecting Karan/Amanda iteration notes: no em dashes in visible copy, avoid “weird” in public copy (prefer “different,” “non-traditional,” or “not-so-standard”), avoid copy that sounds pick-me/woe-is-me, and avoid awkward phrases like “copy-paste” when proposing polished service headings. If user asks for copy options, provide 3-5 clearly labeled alternatives rather than one forced recommendation.
- Latest homepage/brand copy direction from Karan/Amanda: lean more into “stylish bride energy” while staying inclusive and not overly niche. Position Femme for brides who want a wedding that feels stylish, personal, trend-forward, non-traditional where appropriate, and a little unexpected, without making them manage every detail alone. Emphasize the blend of design, organization, and calm support so the vision feels polished, intentional, and genuinely like them.
- Femme service copy must not imply coordinator count or budget management unless explicitly approved. Current approved service-positioning guardrails: “In Your Corner” starts six weeks before the wedding day; “Getting It Together” starts 12 weeks before the wedding day; “The Full Femme” starts six months before the wedding day; use “all-day wedding management,” not “all-day wedding coverage”; keep design guidance primarily in The Full Femme; use support by call and email rather than text/email if describing unlimited support. Approved headings from the May 2026 copy iteration: About / Brand Story section heading = “For celebrations with feeling, personality, and a plan.” Services heading = “For the look, the feeling, and every moving piece in between.”
- See `references/stakeholder-content-implementation.md` for the distilled Issue 62 pattern and PR-comment correction.

### Sanity Schema Checklist (for new content types)
1. Create `studio/schemas/<type>.ts` with defineType/defineField
2. Register in `studio/schemas/index.ts`
3. Create `src/data/<type>.ts` (interface + fallback data)
4. Create `src/lib/<type>.ts` (fetch layer)
5. Wire into component with useState + useEffect pattern
6. After merge: redeploy studio, comment on issue

## Google OAuth
Uses personal assistant account (karanagent20@gmail.com), NOT Karan's business Gmail.
