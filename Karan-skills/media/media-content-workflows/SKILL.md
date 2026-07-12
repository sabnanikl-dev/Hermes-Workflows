---
name: media-content-workflows
description: "Use for media content workflows: YouTube transcripts, GIF search/downloads, Spotify control, music/song generation prompts, and audio feature/spectrogram analysis."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [media, youtube, gifs, spotify, audio, music]
    related_skills: [songwriting-and-ai-music]
---

# Media Content Workflows

## Overview
Use this umbrella for tasks involving online media, music/audio workflows, transcripts, GIFs, and playback/control surfaces.

## When to Use
- Fetch and transform YouTube transcripts.
- Search or download GIFs.
- Control Spotify playback, search, queue, playlists, or devices.
- Generate music/sound prompts or use HeartMuLa-style song generation.
- Analyze audio features, spectrograms, chroma, MFCC, or similar representations.

## Subworkflows

### YouTube
Extract transcripts first, then transform into chapters, summaries, blog posts, or threads. Preserve video URL/title and note transcript gaps.

For durable knowledge-ingest requests (for example, “watch this video and add it to the wiki”), capture both raw source artifacts and a curated synthesis: metadata JSON, captions/transcript, source URL, title/channel/length, a concise takeaways note, and links from the relevant index/log. If generic web extraction fails, use the YouTube page/player metadata and `yt-dlp` fallback pattern in `references/youtube-transcript-ingest.md` rather than giving up or summarizing from the title alone.

### Instagram Reels / short-form recipe videos
For Instagram recipe reels, do not rely on generic web extraction alone: Instagram pages often expose useful caption text through browser snapshots or `yt-dlp --dump-json` even when scrapers fail. Capture (1) the post caption/description, (2) any linked canonical recipe page, and (3) audio transcript when requested. Treat ASR output as noisy: correct obvious food-term errors using the caption/on-screen ingredient list, and explicitly label machine transcript limitations. See `references/instagram-reel-recipe-extraction.md` for the proven workflow.

### GIFs
Use search terms that capture emotion/action + style. Download/return the final asset path or URL.

### Spotify
Resolve device and track/playlist identity before playback changes. Report the action taken and target device.

### Music and audio
Separate songwriting craft, generation prompt design, and signal analysis. Verify generated/downloaded files exist before finalizing.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/`.

## Verification Checklist
- [ ] Media URLs, file paths, or IDs are included for outputs.
- [ ] Downloads/generations are verified on disk or via API response.
- [ ] Playback changes identify the device/context.
- [ ] Transforms preserve source attribution.
