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
Cross-reference each claim against its canonical source:
- Email addresses and durable preference corrections: memory/Hindsight plus authoritative account or source data when available
- URLs: verify the referenced site or exact local path
- Active task, issue, PR, deployment, and project status: Linear, GitHub, repositories, and live endpoints—not Hermes Brain or Karan OS
- Durable business/client summaries: compare against authoritative source material before updating Hermes Brain
- Contact information and dates: verify against the latest authoritative record

### Step 7: Concept gap scan
Look for terms referenced across multiple pages but with no dedicated page (e.g., "client pipeline", "Hindsight setup details"). Do not create a page merely to satisfy graph metrics; require a real reuse case and canonical owner.

### Step 8: Boundary drift scan
Flag personal identity/life-planning content in Hermes Brain, active tracker state in either vault, cross-vault copies with no canonical source, retired paths, stale bounded projections, and Karan OS notes that have become approved reusable agent/business knowledge. Report advisory findings first; require Karan approval before cross-vault moves, deletion, splits, or broad rewrites.

## Report Format
Categorized output:
- 🚨 **Critical**: Stale/broken data that could cause real issues (wrong email, incorrect status)
- 🟡 **Structural**: Orphans, missing cross-links, empty pages
- 📋 **Concepts needing pages**: Mentioned but absent
- **Proposed fixes**: Ordered by impact

## Fix Workflow (After Detection)

Order matters. Fix in this sequence to avoid cascading broken links:

1. **Stale data first** — wrong emails, outdated statuses, incorrect facts. Use memory/Hindsight for durable corrections, but verify active task/deployment/account state from the owning live system before changing a claim.
2. **Delete empty stubs** — remove 0-byte pages before fixing links, after confirming they are not intentional placeholders and obtaining approval when deletion is not already in scope.
3. **Update durable summaries** — sync only reusable business/client/project facts from Linear, GitHub, repositories, live endpoints, or source documents. Do not recreate active trackers in Hermes Brain.
4. **Fix the Project Status snapshot if retained** — keep it high-level and explicitly noncanonical for execution. Link to owning systems; do not copy backlogs, acceptance criteria, or PR-by-PR history.
5. **Add cross-links** — fix meaningful orphans through Related sections. Do not over-link daily logs/raw files or invent pages solely to improve graph metrics.
6. **Update index.md** — add catalog-worthy wiki pages while keeping the index compact and under budget. Use folder pointers for daily logs and dense collections rather than listing every file.
7. **Update frontmatter dates** — update `updated:` fields on touched pages only.
8. **Log the action** — add a concise row to `log.md` and update/create the active daily log when durable wiki state changed.

### Pitfalls During Fixes
- **Dashboard wikilinks to skill names**: The Project Status dashboard frequently links `[[skill-name]]` instead of `[[Wiki Page Name]]`. Skills are NOT wiki pages. Replace with actual wiki page links or `—`.
- **`[[Femme Events]]` vs `[[Femme Events Overview]]`**: The actual page is "Femme Events Overview.md". Use display text: `[[Femme Events Overview|Femme Events]]` to keep readability.
- **Batch date updates**: Use `execute_code` with a loop calling `patch()` — doing them one by one burns 11+ tool calls.
- **Don't fix daily log broken links**: Daily logs intentionally reference skill names for context. Those aren't bugs.
- **SCHEMA.md has example wikilinks**: Wrap them in backticks so they don't register as broken links in future scans.
- **Always re-run the full scan after fixes** to verify the numbers actually improved.

## Key Lessons
- Linear, GitHub, repositories, client systems, and live endpoints own active state; Hermes Brain may keep only durable summaries and a high-level noncanonical snapshot
- Karan OS is Karan-owned personal context; cross-vault audits are advisory until Karan approves a migration manifest
- User pages (Amanda, Karan) go stale fastest — email routing, contact information, role descriptions, and runtime metadata need authoritative verification
- Skills get wikilinked by mistake when authors do not distinguish wiki pages from tool names
- Hindsight is useful for durable corrections and conversational context, but it is not the source of truth for current tracker, deployment, account, or endpoint state
- Empty root-level stubs accumulate when pages are created speculatively; verify purpose and approval scope before deleting