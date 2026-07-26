# Static-site current-head PR prover notes

Use this reference when proving an existing static-site / SEO PR merge-ready after review blockers.

## Patterns that worked

- Treat public copy blockers as a **class**, not a single line. After Claude fixes the cited files, run a targeted sweep across PR-changed customer-visible pages for the same phrases before re-review. Example patterns: `approved public`, `approved rental`, `approved starting`, `inside the approved scope`, `public rental copy`, `approved details`, plus a broader `approv` sweep to separate visible customer copy from docs/developer comments.
- If the sweep finds a residual same-class leak, it belongs to the open blocker set: name the precise residual finding, since it was discovered after the original live review and no reviewer artifact carries it yet.
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

- A fix commit makes every prior pass stale. The outcome is re-proved on the new exact head by `pr-prover`; a static-site PR gets no shortcut around that.
- When one reviewer account carries more than one lane, a collapsed account-level summary can hide role separation. Judge each artifact by its declared role, verdict, and exact head.
- A change-request artifact against an old head is audit history, not a current-head blocker.
- The copy sweep is the part that is easy to skip and expensive to miss: a same-class residual leak on an unchanged-looking page is still a current-head blocker.

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
