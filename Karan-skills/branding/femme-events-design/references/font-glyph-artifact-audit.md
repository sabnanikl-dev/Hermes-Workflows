# Font/Glyph Artifact Audit — Femme Events

Use this when the site shows a weird symbol instead of an expected character, especially ampersands in display typography.

## Trigger
- User reports an ampersand (`&`) or other punctuation rendering as an unexpected glyph/artifact.
- Visual QA finds decorative/display fonts changing common symbols in a way that hurts readability.

## Issue / QA Checklist
1. Treat it as a site-wide visual polish bug, not a one-off text replacement.
2. Search the repo for visible special characters across JSX, data fallbacks, metadata, and schemas/content paths. Include at least:
   - `&`, `&amp;`, `&nbsp;`, `&copy;`
   - apostrophes/quotes
   - dashes
   - plus signs
   - bullets and other decorative symbols
3. Note known hardcoded and data-driven sources in the issue body so the implementer can audit all instances.
4. Include Sanity/CMS-rendered content paths where applicable; special characters may come from fallback data or CMS fields.
5. Recommend a reusable fix pattern instead of manually patching each instance:
   - a small `SafeAmpersand`/`SymbolText` component,
   - a CSS utility that forces symbols into a reliable fallback font,
   - or targeted typography rules for display fonts with bad glyphs.
6. Require desktop and mobile visual QA.
7. Require before/after screenshots or a concise visual QA note listing audited sections.
8. Add/ask for a short code comment explaining why symbol fallback exists, so future content additions do not regress.

## Suggested GitHub Issue Labels
- `bug`
- `frontend`
- `must-have` if it affects public/client polish
- assignment label for the intended builder, e.g. `assigned:claude-code`

## Acceptance Criteria Snippet
- [ ] Ampersands render correctly everywhere they are visible on the site.
- [ ] A site-wide scan/audit is completed for other visible font artifacts or broken special characters.
- [ ] The fix covers hardcoded content and data-driven/CMS-rendered content paths.
- [ ] Typography still matches Femme Events brand direction.
- [ ] Mobile and desktop views are checked.
- [ ] Build passes.
- [ ] PR includes before/after screenshots or a concise visual QA note listing audited sections.
