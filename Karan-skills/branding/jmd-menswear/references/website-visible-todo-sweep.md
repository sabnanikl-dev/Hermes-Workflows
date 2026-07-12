# JMD Website Visible TODO Sweep

Session-derived pattern for Karan requests like: “go through the JMD website and identify areas still labeled TODO; for each, open a GitHub issue.”

## Scope
This is for the website repo `sabnanikl-dev/jmd-6-holding-page-harness` and should be paired with the general `web-application-qa` reference `references/visible-todo-sweep-to-github.md`.

## JMD-specific handling

- Treat visible TODOs as client-facing polish bugs unless the user says otherwise.
- Search existing open and all-state issues before creating anything. JMD has many historical verification-gate issues, so all-state search prevents duplicate resurrection.
- Distinguish rendered TODO chips from repo-internal TODO language:
  - Create issues for visible `.todo` chips or user-facing `TODO`/`TBD` copy.
  - Do not create issues from `docs/spec.md`, handoff documents, AGENTS guidance, CSS variable names, comments, fixtures, or test-only placeholder language unless it renders to users.
- If checking `jmd-non-prod.vercel.app` and the sitemap contains apex `https://jmdmenswear.com/...` locs, remap only the paths onto the non-prod host for QA. The live WordPress/apex site may not represent the current static harness.
- Preserve JMD hard boundaries in each issue: no DNS/hosting/deploy, no CMS/Sanity/n8n/account mutation, no new inventory/ecommerce/price/stock/availability claims unless separately approved.

## Issue body checklist

- Exact visible TODO text.
- Live route and section (`#find`, About carousel, etc.).
- Source file/section when known.
- Goal: replace TODO with verified data or an intentionally final-looking non-specific UI.
- Acceptance criteria requiring no visible TODO remains and existing call/directions/store UX still works.
- Verification: `npm test`, text/DOM scan, desktop and mobile manual check.

## Example root cause from 2026-07
The homepage `#find` map card still rendered `TODO: verify before deploy — coordinates / pin (geo deferred)`. The correct issue shape was one bug for the map-pin/location treatment, not multiple issues for every source/doc mention of “coordinates,” “geo,” or “placeholder.”
