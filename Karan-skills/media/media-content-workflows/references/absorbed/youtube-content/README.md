---
name: youtube-content
description: >
  Fetch YouTube video transcripts and transform them into structured content
  (chapters, summaries, threads, blog posts). Use when the user shares a YouTube
  URL or video link, asks to summarize a video, requests a transcript, or wants
  to extract and reformat content from any YouTube video.
---

# YouTube Content Scraper

Extract metadata (title, channel, thumbnail), transcripts, and formatted content from YouTube videos. Designed to feed directly into the Obsidian wiki.

## Setup

```bash
/Users/creator/.hermes/hermes-agent/venv/bin/pip install youtube-transcript-api
```

## What It Does

1. **Fetches metadata** via YouTube's free oEmbed API (title, channel, thumbnail, URL) — no auth needed
2. **Fetches transcript** via `youtube-transcript-api` — works on any video with captions/subtitles
3. **Outputs to Obsidian** — full markdown with frontmatter, thumbnail, and timestamped transcript

## Usage

```bash
YOUTUBE="python3.11 ~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py"

# Quick metadata only (no transcript)
$YOUTUBE "https://youtube.com/watch?v=VIDEO_ID" --no-transcript --text-only

# Full JSON output with metadata + transcript summary
$YOUTUBE "https://youtube.com/watch?v=VIDEO_ID" --timestamps

# Plain transcript text (no metadata)
$YOUTUBE "URL" --text-only

# Timestamped plain transcript
$YOUTUBE "URL" --text-only --timestamps

# Full transcript text in JSON (warning: can be very long)
$YOUTUBE "URL" --full-transcript --timestamps

# Obsidian-ready markdown note
$YOUTUBE "URL" --obsidian --timestamps --tags youtube,research --category research-notes

# Save directly to Obsidian wiki
$YOUTUBE "URL" --obsidian --timestamps --tags youtube,research \
    --output ~/obsidian-vault/hermes-brain/wiki/shared/research/Video-Title.md
```

## Command Options

| Flag | What it does |
|------|-------------|
| `--obsidian` | Formats output as Obsidian markdown with frontmatter |
| `--timestamps` | Includes timestamps in transcript output |
| `--text-only` | Strips all JSON/metadata, returns plain text |
| `--output FILE` | Saves output to file (auto implies --obsidian) |
| `--tags tag1,tag2` | Adds tags to Obsidian frontmatter |
| `--category NAME` | Sets the category in frontmatter (default: video-notes) |
| `--no-transcript` | Metadata only, skip transcript fetch |
| `--full-transcript` | Includes full transcript text in JSON output |
| `--language en,tr` | Specify language codes (try English, then fallback) |

## Output Formats

After fetching the transcript, the script outputs:

### JSON (default)
Structured data: video_id, title, channel, video_url, thumbnail, segment_count, word_count, duration, language, and optionally full_text + timestamped_text.

### Obsidian Markdown (--obsidian)
Full markdown note with:
- YAML frontmatter (title, URL, channel, thumbnail, scraped date, tags, category)
- Header with video title
- Metadata blockquote (channel, link, scraped date)
- Thumbnail image
- Timestamped transcript in code block

### Plain Text (--text-only)
Raw transcript text, optionally with timestamps. Good for piping to summaries.

## Full Workflow: YouTube URL → Obsidian Wiki

When the user sends a YouTube URL:

1. **Fetch metadata + transcript**
```bash
$YOUTUBE "URL" --obsidian --timestamps --tags youtube,<topic>
```

2. **Save to Obsidian** — pick the right directory:
```bash
# General research
$YOUTUBE "URL" --obsidian --timestamps --tags youtube,ai \
    --output ~/obsidian-vault/hermes-brain/wiki/shared/research/<clean-title>.md

# femme-events related
$YOUTUBE "URL" --obsidian --timestamps --tags youtube,wedding \
    --output ~/obsidian-vault/hermes-brain/wiki/femme-events/research/<clean-title>.md

# consultancy related
$YOUTUBE "URL" --obsidian --timestamps --tags youtube,consulting \
    --output ~/obsidian-vault/hermes-brain/wiki/consultancy/research/<clean-title>.md
```

3. **Optional: Generate a summary** — use the transcript to create chapters, summaries, or key takeaways
4. **Log the scrape** — append to daily log

## Error Handling

- **Transcript disabled**: tell the user; suggest they check if subtitles are available on the video page.
- **Private/unavailable video**: relay the error and ask the user to verify the URL.
- **No matching language**: retry without `--language` to fetch any available transcript, then note the actual language to the user.
- **Metadata fetch fails**: oEmbed can fail for age-restricted or private videos. Still outputs what we can.
- **Dependency missing**: run `python3.11 -m pip install youtube-transcript-api` and retry.
- **macOS Python version**: Script requires Python 3.10+. Use `python3.11` from the Hermes venv: `/Users/creator/.hermes/hermes-agent/venv/bin/python3.11`
