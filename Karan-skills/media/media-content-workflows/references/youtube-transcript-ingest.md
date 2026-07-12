# YouTube Transcript + Knowledge Ingest Fallback

Use this when the user asks to watch/ingest a YouTube video, especially when generic web extraction is unavailable or empty.

## Goal
Produce grounded output from actual video metadata/captions, not title-only inference:
- raw metadata JSON
- raw captions/transcript
- curated summary/synthesis with source attribution
- wiki/index/log updates if the user asked for durable ingest

## Proven fallback sequence

1. **Fetch metadata from YouTube page/player response**
   - Request the canonical watch URL with browser-like headers and `Accept-Language: en-US,en;q=0.9`.
   - Extract `ytInitialPlayerResponse` if present for title, channel, length, caption track hints.
   - Do not rely on a fragile single regex only; YouTube script wrapping can vary.

2. **Prefer `yt-dlp` for robust metadata/captions**
   - If `yt-dlp` is not installed globally but `uvx` is available, run it ephemerally:
     ```bash
     tmpdir=$(mktemp -d)
     cd "$tmpdir"
     uvx yt-dlp --skip-download --write-auto-subs --sub-langs en --sub-format json3/vtt 'https://youtu.be/VIDEO_ID'
     uvx yt-dlp --skip-download --dump-json 'https://youtu.be/VIDEO_ID' > metadata.json
     ```
   - Use the generated `.json3` captions when direct `api/timedtext` URLs return empty responses.
   - Warnings about missing JS runtimes/ffmpeg are not necessarily blockers for metadata/subtitle extraction; verify actual output files.

3. **Convert captions into readable transcript**
   - Parse JSON3 `events[].segs[].utf8`.
   - Keep timestamps (`MM:SS` or `HH:MM:SS`) and collapse whitespace.
   - Label auto-generated captions as such.

4. **For Obsidian/Hermes Brain ingest**
   - Save immutable raw artifacts under an appropriate `raw/` subfolder.
   - Create/update a curated wiki page with: source details, raw file links, takeaways, reusable prompt/process, open questions, and next actions.
   - Update `index.md` only with a compact pointer; keep index under its size budget.
   - Update `log.md` and the daily log if present.
   - Verify all files exist and the transcript has non-trivial line/character counts before reporting success.

## Pitfalls
- Do not summarize a video from title/description alone when transcript extraction is possible.
- Treat creator-stated traffic/revenue numbers as claims unless independently validated.
- If market validation requires live search and search tooling is unavailable, clearly separate “video-derived plan” from “validated market facts.”
