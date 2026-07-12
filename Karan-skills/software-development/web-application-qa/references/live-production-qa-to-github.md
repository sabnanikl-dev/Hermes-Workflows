# Live Production QA → GitHub Issue Handoff

Use this reference when a QA audit is explicitly read-only but the user wants confirmed findings turned into GitHub issues.

## Workflow pattern

1. Build the live sitemap first.
   - Collect visible nav links and direct public routes.
   - Test direct route loads and in-site navigation separately.
   - Include anchor/hash routes when conversion CTAs depend on them.

2. Test desktop and mobile as separate passes.
   - Capture route screenshots for each viewport.
   - Check console/network after each page load and after major interactions.
   - For mobile, distinguish true document-level overflow from intentional horizontal carousels:
     - compare `document.documentElement.scrollWidth` with `clientWidth`;
     - inspect offscreen elements, but do not file carousel slide offscreen positions as overflow bugs by themselves.

3. Reproduce suspected issues before filing.
   - Confirm with a second navigation or direct interaction.
   - For anchor bugs, capture numeric evidence: `location.href`, `scrollY`, target `getBoundingClientRect().top`, sticky header bottom, and top visible text.
   - For console/network bugs, capture exact error text and route/viewport.

4. Inspect repo read-only only enough to identify likely source files/components.
   - Do not edit files, commit, push, deploy, or mutate production/CMS settings during read-only QA.
   - Use source inspection to improve the GitHub issue: likely root cause, suggested files, recommended fix.

5. Search existing GitHub issues before creating new ones.
   - Search all states, not only open issues.
   - If an issue is already intentionally tracking the behavior, mention it in the report and do not create a duplicate.

6. Create issues only for confirmed bugs/problems.
   - Write body files first for long issue descriptions.
   - Include severity, affected route, viewport, steps, expected/actual, evidence, likely root cause, recommended fix, suggested files/components, and classification.
   - Verify created issues by reading them back and checking title, state, URL, labels, and key body substrings.

## Evidence handling

- In CLI sessions, report screenshot paths as plain local paths. Do not use `MEDIA:/path` tags; those are only for messaging gateways.
- If screenshots are local and not uploaded to GitHub, say so explicitly in the issue/final report.
- Keep a local report with sitemap, issues created, non-duplicates, clean areas, evidence paths, and limitations.

## Common findings to classify carefully

- CMS/browser CORS failures: likely CMS/project configuration if the frontend client calls the CMS CDN directly and the production origin is missing from the allowlist.
- Anchor/CTA landing problems: often codebase issues around target element placement, sticky header scroll padding, layout shifts, or broad section anchors instead of form-specific anchors.
- Decorative asset 404s: usually low severity unless they visibly break the page; recommend local assets or removing the third-party dependency.
- Content that looks odd but was explicitly requested or already tracked: do not file a duplicate. Reference the existing issue instead.
