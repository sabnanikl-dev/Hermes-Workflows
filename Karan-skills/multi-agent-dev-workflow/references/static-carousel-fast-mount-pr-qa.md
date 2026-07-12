# Static carousel fast-mount PR QA pattern

Session-derived pattern from a JMD static-site PR that fixed a carousel stuck on its no-JS/static image grid because the controller waited for every feed image probe before mounting.

## When this applies

Use for static/progressive-enhancement carousel PRs where:

- HTML ships a no-JS/static projection.
- JS should replace the static projection with an interactive carousel.
- Image feeds may be large, slow, broken, or partially hanging.
- Browser-facing URLs should be transformed/sized while the canonical data keeps raw source URLs + dimensions.

## Implementation checks

1. **Do not wait for the full feed.** Probe only a small initial window, mount from the first loadable image, and let the carousel/browser lazy-load later images.
2. **Bound hung probes.** A never-settling leading image needs a timeout/fallback path so it cannot strand the static grid forever.
3. **Keep a safety fallback.** If the whole initial window fails, do not mount broken cards; keep the no-JS/static projection visible.
4. **Size browser-facing CDN URLs at the presentation boundary.** Keep canonical feed data raw when that is the public contract, but transform URLs used by the browser/static projection (for Sanity, e.g. `?auto=format&fit=max&w=1200&q=75`).
5. **Make transforms idempotent/defensive.** Only append to approved CDN URLs without an existing query string, and keep public-safety validators pointed at the approved CDN prefix.
6. **Document the split.** Contract/spec docs should say which layer owns canonical raw data vs display-sized URLs.

## Deterministic regression test shape

Add an offline fake-browser validator that runs the real controller with a fake `Image` and fake timers:

- first image loads, later images hang/error -> carousel mounts, `.has-photos` is applied, and only the first image was probed;
- entire initial window errors -> no carousel mount, static fallback stays visible;
- entire initial window hangs -> timeouts fire and fallback remains;
- broken leading image -> skip to next loadable image;
- hung leading image -> timeout then skip to next loadable image;
- mounted `img.src` values are display transforms, not raw originals.

## Local visual QA notes

For a static site served with `python3 -m http.server`, Vercel/serverless API routes are unavailable. That is still useful for repo-side visual QA, but be explicit: the local browser is exercising the committed static artifact / endpoint-failure fallback path, not the live `/api/...` server path.

Pair screenshot/vision proof with DOM assertions:

```js
(() => {
  const section = document.getElementById('on-the-floor');
  const root = document.getElementById('on-the-floor-carousel');
  const staticGrid = document.querySelector('.on-the-floor__static');
  return {
    hasPhotos: section?.classList.contains('has-photos'),
    staticDisplay: staticGrid ? getComputedStyle(staticGrid).display : null,
    carouselChildren: root?.children.length,
    imageCount: document.querySelectorAll('#on-the-floor-carousel img').length,
    firstSrc: document.querySelector('#on-the-floor-carousel img')?.currentSrc,
    overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth
  };
})()
```

For mobile without a viewport-resize tool, inject a same-origin fixed-width iframe and assert `scrollWidth <= clientWidth`, `.has-photos`, hidden static grid, and transformed image URLs inside the iframe.

## Review closeout

- Verify PR head equals local HEAD and remote branch head before reporting.
- Run project validators plus the new focused fast-mount validator.
- Run A/B reviewers against the current PR head after visual/DOM evidence is collected.
- If reviewers submit `COMMENTED` reviews rather than approvals, verify role signatures and `commit_id` on the current head; do not rely only on `reviewDecision`.
