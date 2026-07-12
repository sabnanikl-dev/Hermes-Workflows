# Instagram Reel Recipe Extraction

Use this when the user gives Instagram Reels/TikToks/short-form videos and wants recipes, ingredients, transcripts, or a shopping list.

## Reliable extraction sequence

1. **Try page extraction, but expect Instagram to fail.** If `web_extract` reports unsupported/empty content, escalate rather than stopping.
2. **Open the reel in browser with `?hl=en`.** Browser snapshots often include the creator, caption, ingredients, methods, comments, linked recipe URL, and visible metadata without login.
3. **Search by shortcode if browser is thin.** Query the reel shortcode plus `Instagram recipe` to recover title/creator and sometimes indexed caption snippets.
4. **Use `yt-dlp --dump-json` for metadata.** It can often return `description`, uploader, duration, and media IDs for Instagram reels:
   ```bash
   yt-dlp --dump-json 'https://www.instagram.com/reel/<shortcode>/?hl=en'
   ```
   Prefer captions/descriptions from this JSON or browser snapshots over guessed recipe details.
5. **Follow canonical recipe links.** If the caption points to a blog/page, extract that page and use it as the authoritative recipe source.
6. **For requested transcripts, download/extract audio and run ASR.** A practical local path is:
   ```bash
   yt-dlp -x --audio-format wav -o '%(id)s.%(ext)s' '<reel-url>'
   mlx_whisper <audio-file> --model mlx-community/whisper-tiny --output-format txt
   ```
   If local ffmpeg is broken, a self-contained ffmpeg from `imageio-ffmpeg` can be placed earlier in PATH. Capture this as a setup fix, not as a claim that ffmpeg/ASR is broken.
7. **Reconcile ASR with caption text.** Whisper frequently mangles recipe names and food terms (e.g. arayes/gyudon/adobo/cobbler). Use captions/on-screen ingredient lists as ground truth for ingredients and method; use transcript mainly for narration/gist.
8. **Consolidate quantities for shopping.** Convert grams/ounces/cups only when helpful, group by grocery section, and separate pantry-check items from likely-buy items.

## Reporting pattern

- For each post: title/creator, transcript gist or quoted transcript excerpts, ingredients, method notes, servings/macros when present.
- Then provide one consolidated shopping list grouped by store section.
- State any uncertainty plainly: e.g. “transcript is machine-generated; recipe quantities came from caption/blog.”

## Pitfalls

- Do not invent missing ingredient quantities from transcript alone.
- Do not treat generic scraper failure as task failure; Instagram often needs browser/yt-dlp fallback.
- Do not preserve one-off reel URLs in memory; they are task artifacts, not durable knowledge.
