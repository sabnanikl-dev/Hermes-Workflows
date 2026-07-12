# Static-site current-head PR prover notes

Use this reference when proving an existing static-site / SEO PR merge-ready after review blockers.

## Patterns that worked

- Treat public copy blockers as a **class**, not a single line. After Claude fixes the cited files, run a targeted sweep across PR-changed customer-visible pages for the same phrases before re-review. Example patterns: `approved public`, `approved rental`, `approved starting`, `inside the approved scope`, `public rental copy`, `approved details`, plus a broader `approv` sweep to separate visible customer copy from docs/developer comments.
- If the sweep finds a residual same-class leak, send it back to the Claude fix lane as part of the same fix cycle. Keep the prompt pointer-first when possible, but include the precise residual finding when Hermes discovered it after the original live review.
- For static SEO pages, combine normal repo gates with small deterministic probes:
  - each new route returns HTTP 200 from a local static server;
  - exactly one `<h1>`;
  - unique title and meta description;
  - self-canonical equals expected public URL;
  - BreadcrumbList JSON-LD parses;
  - sitemap contains exactly one `<loc>` for each canonical URL;
  - no visible customer-copy matches for internal approval phrases.
- For UI/static smoke, one browser pass on a representative affected route at mobile width is often enough after automated route probes: check console warnings/errors, horizontal overflow, h1 count, and whether the blocker phrase appears in `document.body.innerText`.

## Current-head review closeout

- A fix commit makes prior approvals stale. Re-run Reviewer A and B on the new head and verify their signed reviews by `commit_id`, not only `reviewDecision` or `latestReviews`.
- If the same reviewer GitHub account posts both A and B reviews, `latestReviews` may collapse or hide role separation. Read the full reviews API and filter by both current `commit_id` and role signature lines.
- A prior `CHANGES_REQUESTED` on an old head can remain in review history; do not treat it as current if both reviewer roles have signed `APPROVED` reviews on the current head and review threads are resolved/absent.
- Non-blocking follow-ups called out by reviewers do not block merge-ready status, but include them in the final report so Karan understands what remains optional.

## Example public-copy sweep

```bash
node - <<'NODE'
const fs = require('fs');
const pages = [
  'site/index.html',
  'site/prom-formalwear-conyers-ga/index.html',
  'site/wedding-tuxedo-rentals-conyers-ga/index.html',
  'site/quinceanera-formalwear-conyers-ga/index.html'
];
const patterns = [
  /approved\s+(?:public\s+)?rental/i,
  /approved starting/i,
  /inside the approved scope/i,
  /language stays approved/i,
  /public rental copy/i,
  /approved details/i,
  /approved rental ensemble/i,
];
let bad = [];
for (const page of pages) {
  const html = fs.readFileSync(page, 'utf8');
  for (const pat of patterns) if (pat.test(html)) bad.push(`${page}: ${pat}`);
}
if (bad.length) { console.error(bad.join('\n')); process.exit(1); }
console.log('public-copy-sweep: OK');
NODE
```
