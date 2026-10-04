# Website Copy Intake Review Docs

Use this reference when Amanda/Karan provide raw copy notes that are not ready to implement directly on the Femme Events website.

## Workflow

1. Read the source material first, not summaries.
2. Preserve Amanda’s raw essence and emotional point of view, then polish for public website clarity.
3. Create a standalone HTML review document before opening implementation issues.
4. Include:
   - source/context note
   - north-star brand direction
   - proposed website copy blocks
   - alternate heading/name options where decisions are still open
   - scope guardrails so the website does not overpromise
   - section-by-section GitHub issue plan for later implementation
5. Wait for copy approval before creating new implementation issues or changing the live site. When an implementation issue already exists and Karan authorizes its workflow with an Amanda copy gate, prepare the exact-copy checkpoint first; do not duplicate the issue or ask Karan to authorize the same bounded build twice. Keep merge/deploy authority separate.
6. For Discord approval, look up Amanda and the intended Femme channel, send one final review request with the exact revision and readable artifact, then read back the exact message, mention, and attachment metadata before reporting delivery. Delivery is not approval. Freeze the delivered copy revision; edits after delivery require a new revision and renewed approval.
7. Keep the recipient document focused on the actual page prose, search/social text, proposed link labels, and one simple approval instruction. Put branch names, commit hashes, source maps, internal guardrails, and unrelated optional business questions in a separate internal artifact. Do not make Amanda review engineering provenance.
8. Generate recipient HTML/PDF from one copy source and check actual mobile geometry before sending. Long URLs and table cells can overflow even when the HTML has a viewport tag; wrap them and verify rendered width rather than hiding horizontal overflow. Inspect the exported PDF and confirm it retains all proposed visitor-facing strings.

## Femme Voice Guardrails From Karan/Amanda Iteration

- No em dashes in visible copy. Use commas, periods, colons, or rewritten sentences instead.
- Avoid “weird” in public copy. Prefer “different,” “non-traditional,” “not-so-standard,” or “alternative” depending on tone.
- Avoid headings that feel pick-me, woe-is-me, or self-pitying.
- Avoid awkward phrases like “copy-paste” in polished heading options.
- Keep the voice girly, feminist, warm, clear, a little rebellious, and visually feminine.
- If a heading/name is uncertain, provide 3-5 options rather than one forced answer.
- “Amanda is your new best friend in your corner,” not “in the corner.”

## Current Service Copy Guardrails

These are working copy decisions from Karan/Amanda iteration. Reconfirm before final implementation if the conversation has moved on.

- Package 1: “In Your Corner”
  - Services begin six weeks before the wedding day.
  - Use “all-day wedding management,” not “all-day wedding coverage.”
  - Do not mention coordinator count.
  - Do not include post-wedding vendor tip management.

- Package 2: “Getting It Together”
  - Services begin 12 weeks before the wedding day.
  - Do not include Design Guidance here. Keep that primarily for The Full Femme.

- Package 3: “The Full Femme”
  - Services begin six months before the wedding day.
  - Lean into design: mood board refinement, visual story, palette, florals, linens, stationery guidance, decor notes, styling details.
  - Use “call and email” for support language, not “text and email.”

- Site-wide service scope:
  - Do not imply budget management.
  - Do not list pricing publicly unless explicitly approved. Use inquiry-based pricing language.
  - Do not mention coordinator count unless explicitly approved.

## Heading Option Pattern

For About / Brand Story sections, make options feel feminine and confident, not defensive. Examples from iteration:

- For the girls rewriting the rules in lipstick.
- Girlhood, glitter, logistics, and a wedding that feels like you.
- Tradition can come. She just does not get to run the show.
- A love letter to the bride who wants it her way.
- Pretty does not have to mean predictable.

For Services sections, avoid generic planner language and avoid “copy-paste.” Examples from iteration:

- Planning support with a little extra blush.
- Coordination for the pretty, personal, not-so-standard wedding.
- For the wedding you can picture, but do not want to manage alone.
- Soft energy. Sharp logistics.
- Wedding support that keeps the vision intact.

## Verification Before Reporting Back

Before telling Karan the review doc is updated, inspect the visible text for banned terms or punctuation:

- em dash / en dash / spaced dash used as prose punctuation
- “weird”
- “copy-paste”
- coordinator count language
- budget management implications
- post-wedding vendor tip management

If possible, render the HTML locally and visually verify that option lists are readable and not hidden by styling.