# Mobile carousel load-gate QA pattern

Use when a carousel/slider appears as a static grid, fallback, blank area, or delayed enhancement on mobile even though data exists.

## Symptom

- Mobile screenshot shows fallback/static projection instead of the intended carousel.
- Console is clean and scripts eventually load.
- Desktop may eventually show the carousel, but mobile/throttled network makes it look broken.

## Investigation steps

1. Inspect the live DOM state:
   - Does the enhanced carousel root have children?
   - Does the section have the class/data attribute that hides fallback markup?
   - Is the no-JS/static projection still displayed?
2. Check console and script/resource loading, but do not stop at “no errors.”
3. Inspect carousel loader code for blocking gates before mount:
   - `new Image()` probes for every feed item.
   - `Promise.all` over every image/resource before rendering.
   - “only mount after every image settles” logic.
   - No timeout or early-mount path.
4. Measure resource timing for carousel scripts and images.
5. Check image payload size and dimensions. Full-size CMS originals can make the fallback appear “stuck” even when the code is technically working.
6. Search existing issues before filing: terms like `carousel`, `static projection`, `fallback`, `mobile`, `photos`, `showroom`, `load`, `preload`.

## Root-cause language

Prefer: “The carousel is blocked by a full-feed preload/probe gate; the fallback remains visible until all images settle.”

Avoid: “The carousel did not load” unless scripts/data truly failed.

## Issue acceptance criteria to include

- The carousel mounts without waiting for every image in the feed.
- A slow, broken, or never-settling later image does not block mount.
- The no-JS/static fallback remains visible with JS disabled.
- With JS enabled and at least one safe/loadable image, the enhanced state hides the fallback.
- Browser-facing images are appropriately transformed/sized for the UI, not full-size originals by default.
- Existing controls still work: autoplay/pause, arrows, swipe, keyboard, dots, lightbox/modal if present.
- Regression test simulates first image loading while later image hangs/errors.

## Common fix directions

- Mount after the first safe/loadable image or first visible subset.
- Probe only the initial viewport/window instead of the entire feed.
- Add a bounded timeout if probing is still needed.
- Let browser lazy-loading handle non-visible images.
- Generate width-limited/auto-format CMS image URLs for carousel/static projections.
- Preserve safety filters for allowed hosts, alt text, and metadata stripping.
