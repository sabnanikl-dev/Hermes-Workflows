---
name: writing-humanization-and-voice-editing
description: Humanize AI-sounding prose, strip chatbot artifacts, match a real voice sample, and rewrite drafts into natural user-facing writing.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [writing, editing, humanize, anti-ai-slop, voice, prose, text, rewriting]
---

# Writing Humanization and Voice Editing

Use this skill when the user asks to humanize, de-AI, de-slop, un-ChatGPT, rewrite, polish, or make text sound more like a real person. Also use it for your own user-facing prose when the output would otherwise read like generic assistant copy.

This umbrella replaces the narrow `humanizer` entry while preserving its class-level checklist and attribution.

## Inputs

The text usually arrives as:

1. Inline pasted text.
2. A local file path; read it first and patch/write only after showing the intended change.
3. A draft plus a voice sample to match.

If a voice sample is provided, read it before rewriting. Note sentence length, vocabulary level, paragraph starts, punctuation habits, transitions, opinions, and recurring phrases.

## Core workflow

1. Scan for AI tells and chatbot artifacts.
2. Rewrite the text while preserving meaning and factual claims.
3. Match the requested tone and any provided voice sample.
4. Add specificity, rhythm, and personality where appropriate.
5. Do a final anti-AI pass: ask what still makes the text sound generated, revise once more, then present the final.
6. For file edits, use targeted `patch` where possible and show what changed.

## High-signal AI tells to remove

### Content inflation

- Significance padding: "serves as a testament," "pivotal," "underscores," "broader landscape," "enduring legacy."
- Promotional filler: "vibrant," "rich," "renowned," "breathtaking," "must-visit," "groundbreaking."
- Vague authority: "experts argue," "industry observers," "several sources."
- Formulaic "Challenges and Future Outlook" sections.
- Fake depth from `-ing` clauses: "highlighting," "showcasing," "reflecting," "ensuring."

### Language patterns

- Overused AI vocabulary: delve, crucial, intricate, key, landscape, tapestry, testament, underscore, enhance, foster.
- Copula avoidance: replace "serves as" / "stands as" / "boasts" with simple "is," "has," or direct verbs.
- Negative parallelisms: "not just X, but Y."
- Forced rules of three.
- Synonym cycling instead of clear repetition.
- False ranges: "from X to Y" where no real scale exists.
- Passive or subjectless fragments when an active subject is clearer.

### Style artifacts

- Em dash overuse.
- Excessive bolding.
- Bold inline-header lists.
- Title Case Headings unless the style guide requires them.
- Emoji-decorated bullets/headings.
- Curly quotation marks in plain technical/business copy.
- Chatbot signposting: "Let's dive in," "Here's what you need to know," "I hope this helps," "Would you like me to..."

### Filler and weak endings

- "In order to" -> "To."
- "Due to the fact that" -> "Because."
- "At this point in time" -> "Now."
- Excessive hedging: "could potentially possibly."
- Generic upbeat conclusions: "The future looks bright," "exciting times ahead."

## Add actual voice

Clean prose can still sound dead. Improve it by:

- Varying sentence length.
- Letting the writer have a point of view when appropriate.
- Using first person when it fits.
- Replacing abstractions with concrete examples.
- Cutting the warm-up sentence under headings.
- Keeping some human rhythm instead of perfect symmetry.

Before:

> AI-assisted coding serves as a pivotal moment in the evolving software development landscape, unlocking productivity and fostering innovation.

After:

> AI coding assistants are useful for boilerplate and repetitive refactors. They are also very good at sounding right while being wrong, so the productivity gain depends on whether someone is still reviewing the work.

## Output shape

For short rewrites, return the final text directly. For larger or sensitive rewrites, use:

1. Draft rewrite.
2. Remaining AI tells you noticed.
3. Final rewrite.
4. Brief summary of changes, only if useful.

## Attribution and license

The original narrow `humanizer` skill was ported from Siqi Chen's MIT-licensed `blader/humanizer`, based on Wikipedia's "Signs of AI writing" guide. Keep that attribution when reusing the detailed checklist. The original license text is preserved in `references/humanizer-license.txt`.

## Pitfalls

- Do not change factual claims unless the user asked for fact-checking or the claim is clearly unsupported.
- Do not make professional text overly casual just to sound human.
- Do not preserve fake citations, fake people, or made-up metrics from an AI draft; flag them.
- Do not silently overwrite files. Show the rewrite or diff.
