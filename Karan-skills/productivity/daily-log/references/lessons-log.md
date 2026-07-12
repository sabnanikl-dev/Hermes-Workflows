<!-- Archived source skill consolidated into `daily-log` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: lessons-log
description: How to document mistakes as standalone lesson pages in the hermes-brain wiki.
category: productivity
---

# Lessons Log

## When to Create a Lesson

Only for genuine mistakes that represent a **recurring pitfall** or **meaningful misunderstanding**. Threshold: "Would I (or Karan) need to know this to avoid wasting time again?"

**Examples that qualify:**
- Launch agent plist overrides .env (specific gotcha with a fix)
- Config loader doesn't map platform settings to env vars (structural bug)

**Examples that DON'T qualify:**
- Trivial typos
- Things easily caught by error messages
- One-off misunderstandings with no recurrence risk

## Lesson Location

`~/obsidian-vault/hermes-brain/wiki/shared/lessons/[Lesson Name].md`

## Lesson Format

```markdown
---
title: "Lesson Name"
domain: "shared"
type: "lesson"
status: "resolved"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---

# Lesson: Lesson Name

## What Happened
Brief description of the mistake and its symptom.

## Root Cause
What actually went wrong. Be specific.

## Fix
What was done to resolve it.

## How to Prevent
Actionable rule or verification step.

## Impact
- What broke
- How long it took to fix
- Any side effects
```

## Rules

1. **One lesson per page** — don't combine unrelated mistakes
2. **Update index.md** — add the lesson under `## shared/lessons`
3. **Wikilink from related pages** — e.g., Hermes Agent Setup.md links to its lessons
4. **Also log in daily log** — reference the lesson page
5. **No filler** — information-dense, no narrative prose

## Hindsight Integration

After creating a lesson page, also `hindsight_retain` a one-line summary so auto-recall surfaces it contextually:

```
hindsight_retain("Lesson: [brief description] → see [[Lesson Name]] in wiki/shared/lessons/")
```
