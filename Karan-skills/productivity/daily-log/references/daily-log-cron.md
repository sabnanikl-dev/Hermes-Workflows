<!-- Archived source skill consolidated into `daily-log` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: daily-log-cron
description: Automated end-of-day daily log synthesis for Obsidian vault. Runs as a cron job at 1 AM ET. Pulls from session transcripts, writes daily log, skips if already exists. Logs errors as lessons.
category: productivity
---

# Daily Log (Cron)

## Purpose
Automated end-of-day synthesis of session activity into a daily log markdown file in the Obsidian vault. Runs at 1:00 AM ET via cron.

## Location
`~/obsidian-vault/hermes-brain/logs/YYYY/MM/YYYY-MM-DD.md`

## Execution Workflow

### Step 1: Use "yesterday" as the target date
The cron runs at 1 AM ET, which means "today" is already the next calendar day. Always synthesize the **previous day's** sessions:

```python
from datetime import datetime, timedelta
yesterday = datetime.now() - timedelta(days=1)
log_path = f"~/obsidian-vault/hermes-brain/logs/{yesterday.strftime('%Y/%m')}/{yesterday.strftime('%Y-%m-%d')}.md"
log_path = os.path.expanduser(log_path)
if os.path.exists(log_path):
    print("Daily log already exists. Skipping.")
    exit()
```

### Step 2: Search previous day's sessions (multi-strategy)
**Do NOT rely solely on date-based `session_search`** — date queries like "April 10 2026" or "2026-04-10" frequently return zero results. Use this layered approach:

1. **Call `session_search` with no arguments** to get recent sessions. Pick sessions matching yesterday's date from the `started_at`/`last_active` timestamps and titles/previews.
2. **For each matched session**, call `session_search` with descriptive keywords from the title/preview to get full summaries.
3. **If still sparse**, read raw session JSON files directly:
   ```python
   import os, glob, json
   session_dir = os.path.expanduser("~/.hermes/sessions")
   # Find files with yesterday's date stamp in filename (e.g. 20260410)
   ydate = yesterday.strftime("%Y%m%d")
   files = glob.glob(os.path.join(session_dir, f"*{ydate}*.json"))
   # Read each JSON, extract user messages and assistant responses
   ```
4. Supplement with `hindsight_recall` using yesterday's date or recent keywords to fill gaps.

Look for:
- Work completed (3+ tool call tasks)
- Decisions made
- Discussions with notable outcomes
- Errors and fixes

### Step 4: Synthesize and write the daily log
Create the directory if needed:
```bash
mkdir -p ~/obsidian-vault/hermes-brain/logs/YYYY/MM/
```

Prefer `write_file` for the final markdown body, then verify with `python3.11` or `wc`/file metadata. Avoid shell heredocs for the full markdown when possible: daily-log headings such as `Mistakes & Lessons` can trigger terminal safety checks that mistake `&` for shell backgrounding. If a write exceeds 3,000 chars, immediately rewrite a shorter version and verify again before final response.

Write in this format (max 3,000 chars):
```markdown
---
title: "YYYY-MM-DD"
type: "daily-log"
date: "YYYY-MM-DD"
---

# YYYY-MM-DD

## What We Did
- Bulleted summary of work, discussions, and decisions

## Wiki Changes
- Pages created/updated/moved/deleted (use wikilinks)

## Mistakes & Lessons
- [[Lesson Page Name]] for genuine mistakes only

## Next Steps
- Pending items and follow-ups
```

### Step 5: Error handling
If the process fails at any point:
1. Determine what went wrong
2. Create a lesson page at `~/obsidian-vault/hermes-brain/shared/lessons/YYYY-MM-DD-daily-log-failure.md`
3. Include:
   - What happened
   - Root cause
   - How to fix or prevent

## Rules
1. Max 3,000 chars per daily log file
2. Skip silently if a log already exists for today
3. Skip silently if no sessions happened today (don't create empty logs)
4. Use wikilinks to lesson pages and project status
5. Include decisions, discussions, and high-level tasks -- not just fixes
6. Always use `python3.11` in the hermes-agent venv for any scripting
7. Log errors as standalone lesson pages
