# Typography symbol polish review probes

Use when a PR changes display-font fallback behavior, special-character wrapping, `SafeText`/`SymbolText` components, or CSS utilities like `.font-symbol`.

## Review goals

Typography artifact fixes are visual, but still need deterministic checks. Verify both sides of the tradeoff:

- Problematic symbols still get the fallback font (`&`, `+`, `@`, `_`, or whatever the PR claims).
- Normal punctuation that should remain in the brand font is not accidentally wrapped (`"`, `'`, curly quotes, apostrophes, dashes, parentheses, bullets, etc.).
- The fallback font does not use a demo/artifact glyph and does not overpower the surrounding display type.

## Deterministic probes

After building or running a local dev server, use browser DOM probes alongside visual inspection:

```js
Array.from(document.querySelectorAll('.font-symbol')).map(el => ({
  text: el.textContent,
  font: getComputedStyle(el).fontFamily,
  style: getComputedStyle(el).fontStyle,
  size: getComputedStyle(el).fontSize,
  weight: getComputedStyle(el).fontWeight,
}));
```

For a heading that should keep quotes in the brand font:

```js
(() => {
  const heading = Array.from(document.querySelectorAll('h1,h2,h3'))
    .find(h => h.textContent.includes('I Do'));
  return {
    text: heading?.textContent,
    symbolChildren: heading ? Array.from(heading.querySelectorAll('.font-symbol')).map(e => e.textContent) : null,
    html: heading?.innerHTML,
  };
})()
```

For a heading that should wrap only an ampersand:

```js
(() => {
  const heading = Array.from(document.querySelectorAll('h1,h2,h3'))
    .find(h => h.textContent.includes('Dates'));
  return {
    text: heading?.textContent,
    symbolChildren: heading ? Array.from(heading.querySelectorAll('.font-symbol')).map(e => e.textContent) : null,
    html: heading?.innerHTML,
  };
})()
```

## Visual smoke checks

Use a browser screenshot/vision pass for visible artifact blockers:

- hero subtitle ampersands
- About headings with quotes/apostrophes
- Inquiry headings with ampersands
- testimonial names like `Name & Name`
- vendor category names like `Florals & Design`
- CMS/blog titles if the PR touches data-driven rendering

A visual pass should look for replacement boxes, demo-font watermarks, obviously oversized system punctuation, or fallback glyphs that clash with the brand direction.

## Validation

For React/Vite projects, run at minimum:

```bash
git diff --check origin/main...HEAD
npm ci
npm run lint
npm run build
```

Existing npm audit findings are worth noting, but do not block a symbol-only PR unless the PR changes dependencies or introduces new dependency risk.
