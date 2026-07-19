---
name: web-application-qa
description: Systematic web application QA, dogfooding, responsive audits, browser evidence capture, bug reports, and GitHub issue handoff.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [qa, testing, browser, web, dogfood, responsive, accessibility, bug-reports]
---

# Web Application QA

Use this skill when the user asks to dogfood, QA, test, audit, or review a web app or production website. This is the class-level umbrella for exploratory browser testing, responsive/layout audits, console/network evidence collection, bug reports, and optional GitHub issue creation.

## When to use

- The user gives a URL and asks for bugs, QA, dogfooding, or an audit.
- A live production site needs read-only verification with screenshots and reproduction steps.
- A web app flow needs browser interaction testing: forms, auth, navigation, checkout, search, dashboards, mobile menus, carousels, or sticky anchors.
- The deliverable is a report, evidence folder, issue list, or GitHub issues.

## Inputs

Collect or infer:

1. Target URL or local preview URL.
2. Scope: full site, specific routes, feature flow, or responsive pass.
3. Output directory, defaulting to `./dogfood-output` or a repo-local evidence folder.
4. Whether external mutation is allowed: GitHub issue creation is allowed only if requested or clearly approved.

## Core workflow

### 1. Plan the pass

Create an output shape like:

```text
<output_dir>/
  screenshots/
  notes.md
  report.md
```

Build a route/flow checklist before clicking randomly: home, navigation, footer, important CTAs, forms, edge states, mobile menu, long pages, and the highest-risk user journeys.

### 2. Explore with evidence

For each route or flow:

1. Navigate to the page.
2. Capture an accessibility snapshot to understand the DOM and links.
3. Check console messages after every navigation and after significant interactions.
4. Capture screenshots for visual state and reproducibility.
5. Exercise interactions: click buttons/links, fill valid and invalid forms, test keyboard navigation, scroll long pages, and verify empty/error states.
6. Record viewport, URL, title, CTA labels and targets, console errors, failed requests, and screenshot paths.

For responsive audits, test desktop and mobile viewports. Use `document.documentElement.scrollWidth` versus `clientWidth` to distinguish true horizontal overflow from intentional carousels.

### 3. Reproduce before reporting

Do not report a bug from a single surprising observation. Re-run the minimal path, capture the exact URL, and write steps that another human can follow.

For every issue, capture:

- Title.
- Severity: Critical, High, Medium, Low.
- Category: Functional, Visual, Accessibility, Console, UX, Content, Performance.
- URL and viewport.
- Steps to reproduce.
- Expected behavior.
- Actual behavior.
- Screenshot and console/network evidence.
- Likely owner/file only if you inspected the repo or source evidence supports it.

### 4. Categorize and de-duplicate

Merge duplicates that share the same root cause. Sort by severity first, then user impact. Keep the report concise enough to be actionable.

### 5. Report or create issues

Use `templates/dogfood-report-template.md` for a complete report. If the user requested GitHub issues, search existing issues first, create only reproduced bugs, and read back created issues to verify title, body, labels, URL, and state.

## Specialized playbooks

- `references/issue-taxonomy.md` — severity/category definitions.
- `references/live-production-qa-to-github.md` — read-only production sitemap/viewport pass with GitHub issue handoff.
- `references/mobile-carousel-card-qa.md` — mobile carousel/card clipping and CTA-visibility checklist.
- `references/mobile-carousel-load-gate.md` — diagnose carousels that appear stuck on static/no-JS fallback because loaders wait for a full image feed before mounting.
- `references/mobile-carousel-smooth-scroll-controls.md` — reproduction and evidence pattern for mobile carousel prev/next buttons swallowing rapid taps during smooth scroll.
- `references/no-js-progressive-enhancement-smoke.md` — sandboxed iframe pattern for no-JS/degraded-path QA on static/progressive-enhancement changes.
- `references/large-catalog-dialog-test-design.md` — exact offline/browser assertion design for bounded catalogs, deferred image requests, accessible dialogs, URL history, responsive geometry, progressive fallback, and fail-closed action fixtures.
- `references/async-canvas-readiness-and-identity.md` — diagnose false negatives in slow canvas/WebGL apps using bounded readiness predicates, visible-state gates, exact deep-link identity binding, and fatal-vs-noisy network triage.
- `references/responsive-paired-action-layout-qa.md` — enforce a human-required two-action row across mobile/desktop with shrink-safe CSS, real geometry assertions, overflow/tap-target checks, mutation testing, and exact-head screenshots.
- `references/stale-deployment-alias-vs-ui-regression.md` — distinguish absent/clipped UI from a stale public alias by comparing live assets, fetched default-branch artifacts, deployment state, and final mobile geometry.
- `templates/dogfood-report-template.md` — final QA report template.

## Pitfalls

- For asynchronous canvas/WebGL applications, do not classify from a short fixed sleep or treat the presence of WebGL as a failure. Wait for a bounded visible readiness/terminal-state predicate and bind identity through the approved URL/token tuple plus rendered state; see `references/async-canvas-readiness-and-identity.md`.
- When the human contract requires a paired action row to remain side by side, do not trust wrapping flex CSS or one desktop screenshot. Use shrink-safe two-column layout plus real 375/768/1440 geometry assertions for aligned rows, non-overlap, tap targets, container bounds, and zero page overflow; see `references/responsive-paired-action-layout-qa.md`.
- When merged UI is missing from a stable preview/non-production URL, compare the fetched default-branch artifact, deployment status, and public-alias asset before editing code. Missing DOM controls plus fallback copy often means stale deployment state, not clipping; fetch remote refs first and finish verification on the public alias. See `references/stale-deployment-alias-vs-ui-regression.md`.
- Do not mutate production app data, CMS content, deployment settings, or code during a read-only audit.
- Do not call a route healthy just because it returns HTTP 200; verify title, canonical/OG metadata, visible state, CTAs, and console health.
- Do not rely on screenshots alone; pair each issue with steps and actual/expected behavior.
- Do not create GitHub issues for speculative or unreproduced findings.
- If screenshot paths are shown in a CLI conversation, use plain paths. Use `MEDIA:<path>` only when the delivery platform expects media tags.
- When the user asks for screenshot proof but the real target screen is behind an approval-gated mutation (deploy, dev-host registration, CMS/project config, content write, OAuth/CORS change), do **not** click through or mutate live config just to get a prettier screenshot. Capture/disclose the gate if useful, then provide honest repo-side screenshot proof from committed code/evidence, clearly labeled as not-hosted/not-deployed proof, and state what approval-gated step remains.
