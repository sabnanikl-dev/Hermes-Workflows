# Large Catalog + Product Dialog QA Test Design

Use this playbook for progressively enhanced catalogs with hundreds of records, bounded initial rendering, deferred image galleries, modal details, URL state, and fail-closed external actions.

## 1. Split contract and browser coverage

Use offline/unit validators for data integrity and negative fixtures; use browser automation for observable DOM, accessibility, history, layout, and request behavior.

### Offline assertions

- Exact record/category/image totals and unique stable IDs.
- Deterministic ordering and byte-stable generated output; generate twice and compare bytes/hash.
- `--check` rejects missing or stale generated artifacts.
- Reject missing IDs/text/images, duplicate IDs, invalid hosts/protocols/destinations, malformed rows, and forbidden fields such as price/inventory.
- Recursively scan the public projection for forbidden keys and source-only values.
- Inject markup-looking metadata and prove rendering uses text nodes/`textContent`, not `innerHTML`.
- Test action resolution as a pure fail-closed function with frozen time: enabled exact tuple passes; disabled, missing, stale, future-dated, failed, mismatched, or partial tuples produce no actions.

### Browser assertions

- Card count, image-node count, filters/search/reset, empty state, pagination/load-more reachability.
- Dialog semantics, focus entry/trap/restore, every close path, scroll-lock cleanup, image navigation, responsive geometry, and reduced motion.
- Query-state deep links and Back/Forward behavior.
- Real image-request bounds captured from before navigation.
- No-JS, delayed-data, malformed-data, initialization-error, broken-image, and hung-image paths.

## 2. Network assertions with a progressive fallback

A static no-JS fallback may legitimately request images before JavaScript hides it. Do not use an arbitrary request cap that ignores those requests.

Capture requests before navigation and derive:

- `initialCardPrimaryUrls`: primary URL from each enhanced card in the bounded first batch.
- `fallbackUrls`: URLs in the initial static fallback.
- `alternateUrls`: every non-primary catalog URL.
- `requestedImageUrls`: browser-observed image requests.

Exact initial assertions:

```text
initial enhanced cards <= configured batch maximum
one image node per enhanced browse card
requestedImageUrls subset-of (initialCardPrimaryUrls union fallbackUrls)
requestedImageUrls intersect alternateUrls == empty
```

Intercept remote images and fulfill them with tiny local image bytes. This records request intent without depending on external hosts or downloading high-resolution assets.

Do not use `networkidle` for hung-image tests. Hold one image route unresolved, wait for a catalog-ready DOM signal, and assert the rest of the catalog is usable while it remains pending.

For a failed thumbnail, assert failure stays card-local: title/model/detail trigger remain usable, unrelated cards remain, and the section does not disappear.

## 3. Representative fixtures

Derive fixtures programmatically from source:

- Minimum, maximum, and common image counts.
- Longest title and longest body/specification line.
- Duplicate-title records with distinct IDs.
- Enabled exact action tuple and neighboring disabled row.

Record exact IDs and expected counts. Search fixtures should include case-insensitive title, exact and partial model ID, filter+search intersection, no match, and a long/unbroken title.

If requirements do not prescribe ordering, require the builder to declare and pin one. Browser order should equal the generated artifact's sequence across reload/reset.

## 4. Accessible dialog

Test through semantic roles where possible:

- Pointer, Enter, and Space open the selected model.
- `getByRole("dialog", { name: ... })` resolves one visible modal.
- Focus moves inside; Tab and Shift+Tab wrap.
- Background controls cannot receive focus and are excluded from the active accessibility path through native modality or `inert`/`aria-hidden`.
- Visible close, Escape, intentional backdrop, and browser Back each work independently.
- Every close restores the exact trigger and original scroll/overflow state.

Repeat open/close cycles and assert one dialog node, no duplicate images, one Escape causes one close, history does not accumulate, and stale close timers cannot hide a quick reopen.

## 5. Deferred gallery

Before open, assert no alternate image URL for the model exists in an image node or request log. After open, dialog image order must equal source order.

Pointer controls, keyboard arrows, thumbnails, and swipe must keep active image, selected thumbnail/`aria-current`, and position status synchronized. One-image records omit or honestly disable irrelevant controls. Drag beyond tap slop must not synthesize an unwanted dialog open.

## 6. URL/history

Cover catalog-origin and direct-deep-link cases:

- Opening adds one selection state; Back closes; Forward reopens.
- UI close removes only selection and preserves filters/search.
- Closing a directly loaded deep link does not navigate away.
- Unknown, empty, duplicate, encoded-markup, and malformed IDs leave the catalog usable without uncaught errors.
- Canonical and sitemap remain queryless unless explicitly required otherwise.

## 7. Enabled/disabled action fixtures

Never mutate production allowlists or visit live payment/order destinations merely to test rendering.

Use route fulfillment or dependency injection:

- Production/current fixture proves disabled rows render neither action.
- Synthetic enabled fixture uses one exact approved ID/URL tuple, fresh passing evidence, and a frozen clock.
- Assert exact labels/hrefs, HTTPS, `target="_blank"`, `rel` containing `noopener`, and external-site disclosure.
- Do not click outbound links; attributes are sufficient for frontend rendering QA.
- Assert a disabled model does not affect an enabled neighbor or collection CTA.

Mismatched or partial tuples render neither action—no disabled placeholder and no generic fallback.

## 8. Responsive geometry

At every required viewport, assert page and dialog `scrollWidth <= clientWidth`.

Desktop: gallery and information panels have side-by-side, non-overlapping rectangles.

Mobile: computed vertical order matches requirements; dialog is nearly full-screen and internally scrollable; persistent close stays inside the viewport before and after scrolling to the bottom.

Use the longest title/spec fixture for wrapping and overflow. Check target dimensions and visible focus, not screenshots alone.

## 9. Progressive enhancement timing

Delay catalog data and prove fallback remains visible until usable enhanced content mounts. Only then may it become visually and accessibility-hidden.

Run JavaScript-disabled, missing artifact, HTTP/data failure, malformed JSON, and initialization-exception cases. In each, real fallback content and safe collection CTAs remain usable, model actions cannot bypass the gate, and no indefinite spinner replaces content.
