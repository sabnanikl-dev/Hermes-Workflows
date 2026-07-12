---
name: wiki-health-check
description: Systematic health check process for the Obsidian wiki — detects stale data, broken links, orphans, and sync issues
---

# Wiki Health Check Process

## Trigger
Run weekly or on Karan's request. Always use a Python script — manual inspection misses issues across 40+ pages.

## Execution Pattern

### Step 1: Walk the vault
- Collect all .md files with paths and sizes in `~/obsidian-vault/hermes-brain/`
- Skip `.obsidian` and dot-prefix directories

### Step 2: Detect empty pages
- `len(content.strip()) == 0` → instant flag (dead weight, clutters search)

### Step 3: Extract and index wikilinks
- `re.findall(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', content)` from every page
- Build backlink index: for each wikilink target, track all source pages

### Step 4: Find broken links
- Compare each wikilink target (case-insensitive) against existing page basenames
- **CRITICAL: Many "broken" links are actually skill names** wikilinked instead of plain text (e.g., `[[multi-agent-dev-workflow]]`, `[[github-auth]]`). Check both wiki pages AND available skills before flagging as broken.

### Step 5: Find orphan pages
- Pages with zero inbound wikilinks AND zero outbound wikilinks
- Exception: index.md, daily logs, and raw/ files legitimately have few links

### Step 6: Stale claim detection
Cross-reference key facts against memory/Hindsight:
- Email addresses (routing changes, new/retired addresses)
- URLs (are referenced sites still reachable?)
- Project statuses (compare `shared/projects/*.md` frontmatter vs `wiki/shared/projects/Project Status.md` dashboard)
- Contact info and dates

### Step 7: Concept gap scan
Look for terms referenced across multiple pages but with no dedicated page (e.g., "client pipeline", "Hindsight setup details")

## Report Format
Categorized output:
- 🚨 **Critical**: Stale/broken data that could cause real issues (wrong email, incorrect status)
- 🟡 **Structural**: Orphans, missing cross-links, empty pages
- 📋 **Concepts needing pages**: Mentioned but absent
- **Proposed fixes**: Ordered by impact

## Fix Workflow (After Detection)

Order matters. Fix in this sequence to avoid cascading broken links:

1. **Stale data first** — wrong emails, outdated statuses, incorrect facts. These cause real harm if someone acts on them. Always cross-check Hindsight (`hindsight_recall`) before changing, since Hindsight captures the *latest* state from conversations.
2. **Delete empty stubs** — remove 0-byte pages before fixing links (so you don't accidentally "fix" a link to point at an empty page).
3. **Update project pages** — sync statuses, mark completed tasks, add meeting dates. Compare `shared/projects/*.md` against the Project Status dashboard AND Hindsight for ground truth.
4. **Fix the Project Status dashboard** — this is the central nervous system. Fix broken wikilinks here by pointing to actual wiki pages (not skill names or deleted stubs). Use `—` for items with no wiki page rather than leaving broken links.
5. **Add cross-links** — fix orphaned pages by adding Related sections. Priority: user pages, business pages, lesson pages. Each should link to 3-5 related pages.
6. **Update index.md** — add any pages missing from the catalog. Include daily log links.
7. **Update frontmatter dates** — batch-update `updated:` fields on all touched pages. Use `execute_code` with a loop for efficiency.
8. **Log the action** — add a row to `log.md`.

### Pitfalls During Fixes
- **Dashboard wikilinks to skill names**: The Project Status dashboard frequently links `[[skill-name]]` instead of `[[Wiki Page Name]]`. Skills are NOT wiki pages. Replace with actual wiki page links or `—`.
- **`[[Femme Events]]` vs `[[Femme Events Overview]]`**: The actual page is "Femme Events Overview.md". Use display text: `[[Femme Events Overview|Femme Events]]` to keep readability.
- **Batch date updates**: Use `execute_code` with a loop calling `patch()` — doing them one by one burns 11+ tool calls.
- **Don't fix daily log broken links**: Daily logs intentionally reference skill names for context. Those aren't bugs.
- **SCHEMA.md has example wikilinks**: Wrap them in backticks so they don't register as broken links in future scans.
- **Always re-run the full scan after fixes** to verify the numbers actually improved.

## Key Lessons
- The Project Status dashboard and individual project pages often drift out of sync — always compare them
- User pages (Amanda, Karan) go stale fastest — email routing, contact info, role descriptions change in conversation but wiki doesn't auto-update
- Skills get wikilinked by mistake when authors don't distinguish wiki pages from tool names
- Hindsight is the source of truth for "what actually happened" — wiki pages only know what was written at creation time
- Empty root-level stubs accumulate when pages are created speculatively but never filled — delete aggressively