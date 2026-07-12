# Typography and special-symbol PR review probes

Use this when a PR changes decorative/display-font fallback behavior, text-wrapping helpers such as `SafeText`, CSS font utilities, or claims to fix ampersands, quotes, apostrophes, dashes, bullets, copyright symbols, plus signs, @ signs, underscores, or other glyph artifacts.

## Review goals

- Preserve brand display typography for normal punctuation that already renders well.
- Force only genuinely problematic glyphs into a stable fallback font.
- Avoid broad regexes that wrap quotes, apostrophes, parentheses, or dashes unless the issue explicitly proves those glyphs are broken.
- Keep data-driven and CMS-rendered text paths covered, not only hardcoded JSX.

## Deterministic probes

After building or running the app locally, inspect DOM behavior instead of relying only on eyeballing:

```js
Array.from(document.querySelectorAll('.font-symbol')).map(el => ({
  text: el.textContent,
  font: getComputedStyle(el).fontFamily,
  style: getComputedStyle(el).fontStyle,
  size: getComputedStyle(el).fontSize,
  weight: getComputedStyle(el).fontWeight,
}));
```

Targeted heading checks:

```js
(() => {
  const about = Array.from(document.querySelectorAll('h1,h2,h3')).find(h => h.textContent.includes('I Do'));
  return { text: about?.textContent, wrapped: about ? Array.from(about.querySelectorAll('.font-symbol')).map(e => e.textContent) : [] };
})();

(() => {
  const inquiry = Array.from(document.querySelectorAll('h1,h2,h3')).find(h => h.textContent.includes('Dates'));
  return { text: inquiry?.textContent, wrapped: inquiry ? Array.from(inquiry.querySelectorAll('.font-symbol')).map(e => e.textContent) : [] };
})();
```

Expected pattern for the Femme Events special-symbol fix:
- Quotes around `"I Do"` are not wrapped in `.font-symbol`.
- `Dates & Dreams` still wraps only `&`.
- Vendor/testimonial/category ampersands use the fallback and do not show demo/artifact glyphs.

## Visual smoke checks

Use a local static build preview when practical. Inspect at least:
- Hero/subheading ampersand.
- About heading/body quotes and apostrophes.
- Inquiry heading ampersand.
- Testimonials and vendor/category names with ampersands.
- Blog/CMS title paths if the helper is used there.

Report visual QA as evidence, but treat deterministic DOM probes and build/typecheck as the merge gate when screenshots are subjective.

## Common blockers

- Regression from a narrow glyph fix back to a broad punctuation wrapper.
- CSS fallback uses a known bad/decorative font that produced the artifact in the first place.
- PR claims normal punctuation remains in brand font, but DOM shows quotes/dashes/parentheses wrapped in `.font-symbol`.
- PR changes typography helper behavior without validating mapped data/CMS-rendered content paths.
