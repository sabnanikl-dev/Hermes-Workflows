# No-JS progressive-enhancement smoke pattern

Use this when reviewing static/progressive-enhancement changes where the degraded path matters (SEO/crawler-visible HTML, no-JS fallbacks, generated static projections, etc.).

## Why

Normal browser navigation executes scripts, so it proves the enhanced path but can hide no-JS regressions. For static HTML served over local HTTP, a sandboxed iframe can inspect no-JS DOM/CSS without launching a separate browser profile.

## Browser console probe

Run from the already-loaded local preview page:

```js
(async () => {
  const html = await fetch('/').then(r => r.text())
  const iframe = document.createElement('iframe')
  // no allow-scripts: scripts do not run. allow-same-origin lets us inspect DOM/CSS.
  iframe.setAttribute('sandbox', 'allow-same-origin')
  iframe.style.cssText = 'position:absolute;left:-9999px;width:390px;height:1200px;'
  document.body.appendChild(iframe)
  await new Promise(resolve => {
    iframe.onload = resolve
    iframe.srcdoc = html.replace('<head>', '<head><base href="http://127.0.0.1:PORT/">')
  })
  await new Promise(r => setTimeout(r, 1000))

  const doc = iframe.contentDocument
  const win = iframe.contentWindow
  const result = {
    scriptsRan: doc.querySelector('#target-section')?.classList.contains('has-js-state'),
    staticImgCount: doc.querySelectorAll('.static-fallback img').length,
    staticDisplay: win.getComputedStyle(doc.querySelector('.static-fallback')).display,
    fallbackDisplay: win.getComputedStyle(doc.querySelector('.fallback-copy')).display,
    scrollWidth: doc.documentElement.scrollWidth,
    clientWidth: doc.documentElement.clientWidth
  }
  iframe.remove()
  return result
})()
```

Adapt selectors to the feature under review.

## What to verify

- Scripts did **not** run (`scriptsRan` false or equivalent).
- The no-JS/static content is present and visible.
- Fallback copy is not contradictory when static content is present.
- Enhanced-only UI is absent or hidden.
- No horizontal overflow (`scrollWidth === clientWidth`) unless intentionally expected.
- If images are key to the degraded path, validate actual URLs with HEAD requests and inspect rendered dimensions/aspect ratio.

## Pitfall

Do not hide a graceful fallback merely because generated markup exists. CSS cannot tell whether an image URL actually rendered. Prefer copy that is safe alongside static content, or hide only the contradictory subpart while preserving useful fallback/CTA text.