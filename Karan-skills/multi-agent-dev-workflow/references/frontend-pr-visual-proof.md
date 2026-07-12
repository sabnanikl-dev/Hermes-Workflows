# Frontend PR visual proof: render the changed UI, not the PR status

Use this when Karan asks for “screenshot proof” after a frontend/UI PR or issue-to-PR run.

## Lesson

Do not assume “screenshot proof” means GitHub PR status, checks, or review state. In frontend work, Karan usually wants proof of the rendered product surface: the affected page/section/component with the approved content visible.

## Preferred proof sequence

1. Identify the exact PR `headRefOid` and create or refresh an isolated render worktree at that commit.
2. Serve the site/app locally from that worktree, or use the deployed preview only if it is reachable without SSO/protection and reflects the same head.
3. Navigate directly to the affected page/anchor and wait for the specific changed UI condition, not just page load.
   - Example for JMD About owner photos: wait for `[data-owner-photo-state="carousel"] .about-owner-carousel__img[src*="cdn.sanity.io/images/yjaks0cn/production"]`.
4. Capture the relevant section/component, not a generic full-page proof unless the full-page context matters.
5. If the component is interactive, capture at least one interaction state when useful (for example initial + next + next for a carousel).
6. Verify the DOM state that backs the screenshot: item count, CDN/source count, active state, alt text/source, no obvious console/layout failures.
7. Send the image artifact first, then a short note with the exact source commit/environment and what was verified.

## Pitfalls

- PR status screenshots are not visual QA. They only prove gates, not that the user-facing page looks right.
- If the deployed preview is behind Vercel SSO/protection, say that and use a local render from the exact PR head. Do not treat the Vercel login page as a preview of the app.
- Avoid over-explaining before sending the artifact. Karan asked for proof; lead with the screenshot.
- When using a local render, label it clearly as local render from exact PR head, not production/live preview.
- If using temporary fixture data, label it in the screenshot/caption and re-run canonical verification against the real PR worktree afterward.

## Minimal final response shape

```
MEDIA:/path/to/rendered-component-proof.png

Rendered from PR #<n> head `<sha>`.
Verified: <specific visible/DOM facts>. <Any limitation, e.g. preview behind SSO>.
```
