---
name: local-web-preview
description: Preview local HTML/CSS/JS sites with images and SVGs rendering correctly. Covers the file:// protocol limitation, local server setup, and SVG sizing in navigation bars.
version: 1.0.0
---

# Local Website Preview

When building local HTML sites, assets (images, SVGs, fonts) will NOT load via the `file://` protocol in most browsers due to security restrictions.

## Core Rules

1. **Never use `file://` URLs for preview** — always spin up a local HTTP server
2. **SVGs in navigation** — large logos with transparent space need nav padding stripped to zero
3. **Copy assets** into the website directory using clean filenames (avoid spaces)

## Setup (Every Project)

```bash
# 1. Create website directory with assets
mkdir -p ~/projects/client-website/

# 2. Copy all assets (images, SVGs, fonts) into the website dir
cp /source/logo.svg ~/projects/client-website/

# 3. Start HTTP server in the website directory
cd ~/projects/client-website/
python3 -m http.server 8000  # or any free port
```

## SVG Logo in Navigation

When embedding an SVG logo in a nav bar, the SVG often has lots of transparent padding around the actual graphic. Set height large enough and strip nav padding:

```html
<nav style="padding: 0; margin: 0; min-height: unset;">
  <div style="padding: 0; height: auto;">
    <a href="#">
      <img src="logo-nav.svg" style="height: 250px; width: auto;">
    </a>
  </div>
</nav>
```

Key CSS overrides:
- `nav { padding: 0; margin: 0; min-height: unset; }`
- `.nav-container { padding: 0 [sides]; height: auto; }`
- Let the SVG's own transparent space dictate the visual padding

## Common Pitfalls

| Problem | Fix |
|---------|-----|
| Images/SVGs show as broken icons | Must use HTTP server, not `file://` |
| Nav bar too tall for SVG logo | Strip nav padding to 0, let SVG transparent space handle spacing |
| SVG filename with spaces causes 404 | Rename to `logo-nav.svg` (hyphens, no spaces) |
| Footer SVG too large to inline | Use `<img src="file.svg">` with HTTP server, not data URI |
| Logo still too small on refresh | Browser may cache old CSS — hard refresh (Cmd+Shift+R) |

## Preview from a GitHub Repo Main Branch

When the user asks to "spin up localhost from main" or similar:

1. Sync the repo first; do not preview a stale branch:

```bash
cd /path/to/repo
git fetch origin main --prune
git checkout main
git pull --ff-only origin main
git status --short --branch
git log -1 --oneline
```

If the user says a merged PR is not visible on localhost, use the stale Vite preview checklist in `references/vite-stale-localhost-after-merge.md`: verify GitHub/`origin/main`, inspect the running port's process cwd, and restart the server from a clean `origin/main` preview worktree instead of resetting a potentially active checkout.

2. Pick a free port instead of assuming 8000 is available:

```bash
python3 - <<'PY'
import socket
for port in range(8000, 8021):
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1', port)) != 0:
            print(port)
            break
PY
```

3. Start the server from the actual site/public directory as a background process:

```bash
python3 -m http.server 8000 --directory /path/to/repo/site
```

4. Verify the page and critical assets before reporting the URL. Save fetched HTML to a temp file before parsing; do **not** pipe `curl` directly into an interpreter because local security guards may flag `curl | python` as unsafe even when the intent is just validation:

```bash
curl -I --max-time 5 http://127.0.0.1:8000/
curl -fsS --max-time 5 http://127.0.0.1:8000/ -o /tmp/preview-index.html
python3 - <<'PY'
from pathlib import Path
text = Path('/tmp/preview-index.html').read_text()
print('html bytes', len(text))
print('images', text.count('<img '))
PY
for path in /styles.css /assets/logo.png /assets/favicon.png; do
  curl -s -o /dev/null -w "$path %{http_code}\n" "http://127.0.0.1:8000$path"
done
```

5. Report the localhost URL plus enough stop info for the running process (PID/session id when available). Keep it concise; the user wants to view the site, not a deployment summary.

## Screenshot Capture + Chat Delivery

For a reusable exact-PR-head, multi-viewport static-site capture recipe—including `npx playwright screenshot --channel chrome`, stable evidence storage, pixel/vision verification, contact-sheet construction, and delayed server-notification cleanup—see `references/exact-head-static-screenshot-bundle.md`.

For frontend issue-to-PR work where the human still owns taste/visual approval, do not stop at the sentence “visual QA passed.” Attach fresh rendered-surface proof (`MEDIA:` files) in the merge-ready handoff by default, ideally a responsive contact sheet plus full-resolution captures. PR/check-status screenshots are not a substitute.

When the user asks for preview screenshots or a visual pause before merge:

1. Capture screenshots from the local/preview HTTP URL, not `file://`. For anchored sections, prefer a tall full-page screenshot from `/` if `/#anchor` screenshots render blank or misleading.
2. For PR proof before merge, re-check the live PR head first and capture **fresh screenshots from that exact local checkout/head**; do not reuse committed evidence screenshots unless explicitly labeled as repo evidence rather than fresh proof.
3. If the public/live state is intentionally blocked by an approval gate (for example approved real photos/data are not yet available), capture both:
   - the real public blocked/safe state; and
   - a clearly labeled injected/mock-data state that exercises the future UI behavior without committing or publishing the mock data.
   Pair the screenshots with a small deterministic geometry/DOM assertion where relevant (for example `overflowX === 0` and visible carousel cards inside the viewport).
4. Before reporting, verify the files exist and have non-zero size **and are not blank/mis-cropped**. If a CLI/headless screenshot produces a blank white image or misses the changed section, do not deliver it; recapture with browser tools. Non-zero PNG size is not enough proof: Chrome/Chromium headless can emit small all-white screenshots for local static `/#anchor` captures on macOS. Inspect the screenshot visually (or with `vision_analyze`) before citing it as evidence; if blank, use browser automation plus DOM assertions for the target section instead of trying to pass off the file.
   - **Long-page lazy-image pitfall:** a full-page screenshot expands the capture but does not necessarily perform real scrolling, so below-fold `loading="lazy"` images can remain as placeholder blocks even when the site works. Before capturing a long catalog, scroll each rendered row/batch into the viewport, wait for decoding, and assert every intended image has `complete === true && naturalWidth > 0`; then recapture. Do not report placeholder-filled full-page screenshots as rendering proof.
5. For browser-tool screenshots, especially component/section proof, use the browser to scroll the target element into view and offset for sticky nav (for example `document.getElementById('faq-heading')?.scrollIntoView(); window.scrollBy(0, -220);`) before calling `browser_vision`. Pair visual inspection with a compact DOM assertion for the changed section (e.g. banned-copy regex is false, required address/CTA text exists, CTA hrefs are correct, locator/component bounding box has non-zero dimensions, `scrollWidth <= innerWidth`) so a screenshot-capture quirk does not leave QA ambiguous. Browser screenshots are cached under `~/.hermes/cache/screenshots/browser_screenshot_*.png`; copy the newest relevant file to stable evidence storage before delivery. See `references/browser-vision-screenshot-proof.md`.
   - For FAQ/dropdown proof, set a deterministic accordion state before capture: open one representative native `<details>` item, leave the rest collapsed, and assert answer text is still present in the static DOM plus any FAQPage JSON-LD parity. See `references/accordion-faq-visual-qa.md`.
6. If screenshots are captured inside a temporary PR worktree that may be removed after merge/branch cleanup, copy the final proof files to a stable evidence directory outside that worktree before deleting it (for example `~/projects/pr-work/<repo>-evidence/<issue>-visual-qa/`). Otherwise Telegram/media links and later follow-up proof can break after cleanup.
7. In Telegram/chat delivery, put each deliverable on its own `MEDIA:/absolute/path/to/file.png` line with a short label. Do not assume a previous Markdown image/path mention delivered the image.
8. If there are several viewport/screenshots, make a contact sheet when useful so Karan can visually scan proof quickly, then optionally keep individual files available.
9. If the user says they cannot see the screenshot, first re-check the existing file path and re-send the same media files before regenerating them.

## Vite PR Branch Preview

Use this when Karan asks to view an open PR locally before merge, especially for React/Vite frontend changes.

1. Use an isolated worktree so the main checkout and any unrelated untracked files stay untouched:

```bash
REPO=/path/to/repo
PR_BRANCH=fe/example-branch
WT=/tmp/<repo>-pr-preview
cd "$REPO"
git fetch origin main "$PR_BRANCH" --prune
rm -rf "$WT"
git worktree add "$WT" "origin/$PR_BRANCH"
```

2. Install deps in the worktree if needed and choose a free Vite port:

```bash
cd "$WT"
[ -d node_modules ] || npm ci
PORT=$(python3 - <<'PY'
import socket
for port in range(5173, 5195):
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1', port)) != 0:
            print(port); break
PY
)
```

3. Start Vite as a tracked background process, not a shell-disowned server:

```bash
npm run dev -- --host 127.0.0.1 --port "$PORT"
```

4. Verify before giving the URL:

```bash
curl -fsS --max-time 2 "http://127.0.0.1:$PORT/" >/tmp/preview-index.html
```

5. Report the URL, branch/worktree path, and process session id. If the user later says to merge or stop previewing, kill the tracked process and remove the temporary worktree.

See `references/vite-pr-branch-preview.md` for the exact operational checklist.

## Quick Server Commands

```bash
# Python 3
python3 -m http.server 8000 --directory /path/to/site

# Vite dev preview from a checked-out app
npm run dev -- --host 127.0.0.1 --port 5173

# Kill old server on port
lsof -ti:8000 | xargs kill -9 2>/dev/null
```