# Browser Vision Screenshot Proof Pattern

Use this when local/browser screenshot proof is needed for PR visual QA and CLI headless screenshots are unreliable or produce blank/white images.

## Pattern

1. Verify the checkout is the exact PR head before capture:

```bash
gh pr view <PR> --json headRefOid --jq .headRefOid
git rev-parse HEAD
```

2. Start a local HTTP server from the PR worktree's site/public directory.

3. Navigate with browser tools to the target URL. If an anchor like `#faq-heading` does not land with the changed section clearly visible, adjust in-page scroll before screenshot:

```js
document.getElementById('faq-heading')?.scrollIntoView();
window.scrollBy(0, -220);
({ scrollY: window.scrollY, headingTop: document.getElementById('faq-heading')?.getBoundingClientRect().top })
```

4. Use `browser_vision` to capture the proof image. It saves a real screenshot under `~/.hermes/cache/screenshots/browser_screenshot_*.png` even if the tool response only says the image was loaded into context.

5. Copy the newest relevant screenshot from the cache into a stable evidence directory outside the throwaway worktree, with a descriptive filename:

```bash
OUT=~/projects/pr-work/<repo>-evidence/<issue>-visual-qa
mkdir -p "$OUT"
LATEST=$(python3 - <<'PY'
from pathlib import Path
files=list(Path.home().joinpath('.hermes/cache/screenshots').glob('browser_screenshot_*.png'))
files.sort(key=lambda p:p.stat().st_mtime, reverse=True)
print(files[0])
PY
)
cp "$LATEST" "$OUT/<pr>-<page>-proof.png"
stat -f '%z %N' "$OUT/<pr>-<page>-proof.png"
```

6. If multiple pages/viewports are captured, create a contact sheet with PIL and deliver both the contact sheet and individual files via `MEDIA:/absolute/path.png`.

7. Kill the local preview server after proof capture.

## Pitfalls

- Do not trust blank/white PNGs produced by ad-hoc headless Chrome commands. Open/analyze the image before delivering; a nonzero file size alone is not visual proof.
- Hash anchors can still leave the changed component partly hidden behind sticky navigation or outside the screenshot crop. Use `scrollIntoView()` plus an offset and then capture.
- Always copy proof out of temp/worktree paths before cleanup so Telegram/media links remain valid.
- For accordion/dropdown visual QA, capture both the collapsed question list and at least one expanded answer. Use DOM tools to set/open a native `<details>` item if needed, then capture the section after applying a sticky-nav offset.
