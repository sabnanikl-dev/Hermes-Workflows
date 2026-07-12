# Frontend Image/Layout PR Review

Use this reference when a PR adds/replaces local public images or changes a responsive visual layout.

## What to verify

1. PR scope
   - Confirm the PR links a GitHub issue (`Closes #N`).
   - Compare changed files against the issue and PR summary.
   - Flag unrelated typography/layout tweaks in a photo-only PR unless the issue explicitly asked for them.

2. Asset validity
   - Confirm each referenced image exists in the PR/worktree.
   - Run `file public/path/image.ext` and, when Pillow is available, read dimensions with:
     ```bash
     python3 - <<'PY'
     from PIL import Image
     for p in ['public/photos/example.jpg']:
         im = Image.open(p)
         print(p, im.size, im.mode, im.format)
     PY
     ```
   - Note dimensions and file size in the review when helpful.

3. Code references
   - Grep for old/new image references to ensure the intended component/page changed and no accidental stale reference remains:
     ```bash
     grep -R "/photos/NewImage.jpg\|/photos/OldImage.jpg" -n src public --exclude-dir=node_modules || true
     ```
   - Confirm `alt` text exists and accurately describes the visible image.

4. Automated checks
   - Run dependency install if needed, then the project validation commands, usually:
     ```bash
     npm ci
     npm run lint
     npm run build
     ```
   - Treat dependency audit warnings as non-blocking when the PR did not change dependencies; mention them separately.

5. Browser smoke test
   - Preview the built app locally and open the changed route/section.
   - Verify every new image reports `complete: true`, has non-zero `naturalWidth/naturalHeight`, and uses the expected URL.
   - Check desktop and mobile widths.
   - On mobile, explicitly compare `document.documentElement.scrollWidth` to `clientWidth` to catch horizontal overflow.
   - Read console output; unrelated existing third-party 404s can be non-blocking if the PR did not touch them.

Example browser probe:
```js
(() => {
  function r(el) {
    if (!el) return null;
    const b = el.getBoundingClientRect();
    return { x: b.x, y: b.y, w: b.width, h: b.height, top: b.top, bottom: b.bottom };
  }
  return {
    viewport: [innerWidth, innerHeight],
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    imgs: [...document.querySelectorAll('main img')].map(img => ({
      alt: img.alt,
      src: img.getAttribute('src'),
      currentSrc: img.currentSrc,
      complete: img.complete,
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
      rect: r(img),
    })),
  };
})()
```

## Review language

For photo/layout PRs, be concrete and visual but avoid subjective design overreach. Approve when the implementation meets the issue, images load, responsive layout is technically sound, and any aesthetic questions are not blockers. Request changes when scope leaks, assets are missing/broken, alt text is wrong/missing, layout overflows/clips, or PR claims do not match the diff.
