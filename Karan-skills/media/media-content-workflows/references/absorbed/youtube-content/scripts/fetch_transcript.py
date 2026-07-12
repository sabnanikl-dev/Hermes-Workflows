#!/usr/bin/env python3
"""
Fetch a YouTube video's metadata (title, channel, thumbnail) + transcript
and output it as Obsidian-ready markdown or structured JSON.

Usage:
    python fetch_transcript.py <url_or_video_id> [options]

Options:
    --language, -l    Comma-separated language codes (e.g. en,tr)
    --obsidian        Output as Obsidian markdown note
    --timestamps      Include timestamped transcript in output
    --text-only       Output plain text only (no JSON/metadata)
    --output, -o      Save output to file (implies --obsidian)
    --tags            Comma-separated tags (e.g. youtube,research)
    --category        Category for frontmatter (default: video-notes)
    --no-transcript   Only fetch metadata, skip transcript
    --full-transcript Include full transcript text in JSON output
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime


def extract_video_id(url_or_id):
    """Extract the 11-character video ID from various YouTube URL formats."""
    url_or_id = url_or_id.strip()
    patterns = [
        r'(?:v=|youtu\.be/|shorts/|embed/|live/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id


def fetch_metadata(video_id):
    """Fetch video metadata via YouTube oEmbed API (free, no auth needed)."""
    url = "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={}&format=json".format(video_id)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode('utf-8'))
        return {
            'title': data.get('title', 'Unknown Title'),
            'author': data.get('author_name', 'Unknown Channel'),
            'author_url': data.get('author_url', ''),
            'thumbnail': data.get('thumbnail_url', ''),
            'video_url': 'https://www.youtube.com/watch?v={}'.format(video_id),
        }
    except Exception as e:
        return {
            'title': 'Unknown Title',
            'author': 'Unknown Channel',
            'author_url': '',
            'thumbnail': '',
            'video_url': 'https://www.youtube.com/watch?v={}'.format(video_id),
            'error': 'Metadata fetch failed: {}'.format(e),
        }


def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS or MM:SS format."""
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return "{}:{:02d}:{:02d}".format(h, m, s)
    return "{:02d}:{:02d}".format(m, s)


def fetch_transcript(video_id, languages=None):
    """Fetch transcript segments from YouTube via youtube-transcript-api."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("Error: youtube-transcript-api not installed. Run: pip install youtube-transcript-api",
              file=sys.stderr)
        sys.exit(1)

    api = YouTubeTranscriptApi()
    if languages:
        result = api.fetch(video_id, languages=languages)
    else:
        result = api.fetch(video_id)

    return [
        {"text": seg.text, "start": seg.start, "duration": seg.duration}
        for seg in result
    ]


def build_obsidian_note(metadata, transcript_text, timestamped_text=None,
                        summary=None, tags=None, category=None):
    """Build a complete Obsidian markdown note."""
    title = metadata['title']

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    tags_str = ' '.join(['#{}'.format(t) for t in (tags or [])])

    frontmatter_lines = [
        '---',
        'title: "{}"'.format(title),
        'video_url: {}'.format(metadata['video_url']),
        'channel: {}'.format(metadata['author']),
        'channel_url: {}'.format(metadata['author_url']),
        'thumbnail: {}'.format(metadata['thumbnail']),
        'scraped: {}'.format(now),
        'category: {}'.format(category or 'video-notes'),
        'tags: [{}]'.format(tags_str),
        '---',
        '',
    ]
    frontmatter = '\n'.join(frontmatter_lines)

    body = []
    body.append('# {}\n'.format(title))
    body.append('> 📺 **Channel:** ' + metadata['author'])
    if metadata.get('author_url'):
        body.append('> 🔗 **Link:** [{}]({})'.format(metadata['video_url'], metadata['video_url']))
    else:
        body.append('> 🔗 **Link:** {}'.format(metadata['video_url']))
    body.append('> 📅 **Scraped:** {}\n'.format(now))

    if metadata.get('thumbnail'):
        body.append('![Thumbnail]({})\n'.format(metadata['thumbnail']))

    if summary:
        body.append('## Summary\n')
        body.append('{}\n'.format(summary))
        body.append('---\n')

    body.append('## Transcript\n')
    if timestamped_text:
        body.append('```\n{}\n```\n'.format(timestamped_text))
    else:
        body.append('{}\n'.format(transcript_text))

    return frontmatter + '\n'.join(body)


def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube video metadata + transcript")
    parser.add_argument("url", help="YouTube URL or video ID")
    parser.add_argument("--language", "-l", default=None,
                        help="Comma-separated language codes (e.g. en,tr)")
    parser.add_argument("--obsidian", action="store_true",
                        help="Output as Obsidian markdown note")
    parser.add_argument("--timestamps", action="store_true",
                        help="Include timestamped transcript")
    parser.add_argument("--text-only", action="store_true",
                        help="Output plain text only (no JSON/metadata)")
    parser.add_argument("--output", "-o", default=None,
                        help="Save output to file (implies --obsidian)")
    parser.add_argument("--tags", default=None,
                        help="Comma-separated tags (e.g. youtube,research)")
    parser.add_argument("--category", default="video-notes",
                        help="Category for frontmatter (default: video-notes)")
    parser.add_argument("--no-transcript", action="store_true",
                        help="Only fetch metadata, skip transcript")
    parser.add_argument("--full-transcript", action="store_true",
                        help="Include full transcript text in JSON output")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    languages = [l.strip() for l in args.language.split(",")] if args.language else None

    metadata = fetch_metadata(video_id)

    if args.no_transcript:
        if args.text_only:
            print("Title: {}\nChannel: {}\nURL: {}".format(
                metadata['title'], metadata['author'], metadata['video_url']))
        else:
            print(json.dumps(metadata, indent=2))
        return

    try:
        segments = fetch_transcript(video_id, languages)
        full_text = " ".join(seg["text"] for seg in segments)
        timestamped = "\n".join(
            "{} {}".format(format_timestamp(seg['start']), seg['text'])
            for seg in segments
        )

        transcript_data = {
            "video_id": video_id,
            "title": metadata['title'],
            "channel": metadata['author'],
            "video_url": metadata['video_url'],
            "thumbnail": metadata['thumbnail'],
            "segment_count": len(segments),
            "word_count": len(full_text.split()),
            "duration": format_timestamp(segments[-1]["start"] + segments[-1]["duration"]) if segments else "0:00",
            "language": languages[0] if languages else "auto",
        }

        if args.full_transcript:
            transcript_data["full_text"] = full_text
        if args.timestamps:
            transcript_data["timestamped_text"] = timestamped

        if args.text_only:
            print(timestamped if args.timestamps else full_text)
            return

        if args.obsidian or args.output:
            tags_list = [t.strip() for t in args.tags.split(",")] if args.tags else None
            note = build_obsidian_note(
                metadata=metadata,
                transcript_text=full_text,
                timestamped_text=timestamped,
                summary=None,
                tags=tags_list,
                category=args.category,
            )
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(note)
                print("Saved to {}".format(args.output))
            else:
                print(note)
        else:
            print(json.dumps(transcript_data, indent=2, ensure_ascii=False))

    except Exception as e:
        error_out = {
            "video_id": video_id,
            "title": metadata['title'],
            "channel": metadata['author'],
            "video_url": metadata['video_url'],
            "error": str(e),
        }
        print(json.dumps(error_out, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
