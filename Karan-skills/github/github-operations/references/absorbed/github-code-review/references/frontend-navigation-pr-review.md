# Frontend navigation PR review probes

Use this when a PR claims to change anchor links, fixed-header offsets, hash routing, query-param prefill behavior, CTA scroll behavior, or link click handling.

## Hash + query-param routing pitfalls

React Router effects that scroll on hash changes often depend on only `location.pathname` and `location.hash`. If a CTA uses a URL like `/?service=package#inquiry`, then clicking a different package while already at `#inquiry` may change only `location.search`. If the click handler also calls `event.preventDefault()`, the browser's native anchor scroll is suppressed and the app may update form state without scrolling.

Review checklist:
- If a link changes query params and targets a hash, confirm the scroll effect depends on `location.search` too, or that the click handler explicitly scrolls after navigation when the hash is unchanged.
- Test repeated same-page CTA clicks: start at `/?service=old#target`, scroll away, click another CTA to `/?service=new#target`, and confirm it scrolls back to the target.
- If the code calls `preventDefault()` on an `<a>`, verify it preserves modified-click behavior (`Meta`, `Ctrl`, `Shift`, middle-click) or avoid claiming open-in-new-tab behavior is preserved.
- Keep real `href` values on links where possible for accessibility, status bar preview, context menus, and no-JS fallback.

## Fixed-header anchor offsets

For fixed navbars, prefer one global `html { scroll-padding-top: ... }` rule over per-section `scroll-mt-*` classes when many anchors are affected. If moving from local offsets to global offset, verify old per-section offsets are removed to avoid double spacing.

## Evidence to collect

- PR diff for changed links, router effects, and CSS offset rules.
- Browser or deterministic local reproduction for repeated-click behavior when practical.
- Build/typecheck result if the repo has a frontend build.
