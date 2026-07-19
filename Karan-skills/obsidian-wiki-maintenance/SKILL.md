---
name: obsidian-wiki-maintenance
description: Maintain and update the Obsidian knowledge wiki at ~/obsidian-vault/hermes-brain/
---

# Obsidian Wiki Maintenance

## Location
- **Vault:** ~/obsidian-vault/hermes-brain/
- **OBSIDIAN_VAULT_PATH env var** must be set in ~/.hermes/.env

## Wiki Structure
```
SCHEMA.md                    # conventions, formats, workflows
index.md                     # master catalog (under 3000 chars, one line per page)
log.md                       # activity log table
raw/                         # immutable source docs
raw/femme-events/            # Femme Events source material
raw/consultancy/             # Papi/consulting source material
raw/shared/                  # cross-domain sources, transcripts, references
wiki/femme-events/           # vendors, venues, inventory, clients, processes, reference
wiki/consultancy/            # clients, research, pitches
wiki/shared/                 # users/, business/, tools/, infrastructure/, processes/, lessons/, project summaries
logs/                        # daily logs: YYYY/MM/YYYY-MM-DD.md (max 3000 chars each)
```

### Scope Boundary (Karan-approved)
- **Hermes Brain** is agent/business memory: durable summaries, references, lessons, business/client context, and source-derived wiki pages.
- **Karan OS** is the separate personal vault. Do not duplicate personal identity/operating-system docs into Hermes Brain; only reference the boundary when useful.
- **Project trackers do not live in Hermes Brain.** Linear/GitHub/project repos are execution truth. Hermes Brain may summarize project state, decisions, archived outcomes, and links, but should not maintain parallel task trackers.
- Root should stay boring: `SCHEMA.md`, `index.md`, `log.md`, `raw/`, `wiki/`, `logs/`, and explicitly approved Obsidian support files only. Root-level markdown stubs are usually accidental and should be moved/deleted after confirmation.

## Page Creation Rules
1. Use YAML frontmatter: title, domain, type, status, created, updated
2. Use `[[wikilinks]]` for internal vault notes; use Markdown links only for external URLs
3. Use Obsidian callouts for important warnings/decisions: `> [!warning] Title`
4. Information-dense, no filler prose
5. Read target page first before updating
6. Update index.md after adding/removing pages
7. Keep index.md under 3000 characters

## Obsidian-Native File Types

These are useful, but should stay support layers rather than replacing source-of-truth systems.

### Markdown notes (`.md`)
- Default durable knowledge format for Hermes Brain.
- Use frontmatter aligned with SCHEMA.md.
- Prefer path-explicit wikilinks for ambiguous or frequently broken references: `[[wiki/consultancy/business-plan|Papi AI Business Plan]]`.
- Use embeds only when they improve human review in Obsidian; do not embed huge raw/transcript pages into core wiki pages.

### JSON Canvas (`.canvas`)
- Use for visual maps: system architecture, workflow maps, project relationship diagrams, vendor/client flow maps.
- Keep canvases small and linked from a normal Markdown page that explains what the canvas is for.
- Validate JSON before writing: unique 16-character hex IDs, node required fields, and edge referential integrity.

### Bases (`.base`)
- Use for Obsidian-native dashboard/database views over existing notes, not as a replacement for Linear/GitHub/repo trackers.
- Good candidates: research index, vendor/client reference views, lessons by domain/type/status, project summary snapshots.
- Validate YAML and quote formulas/special characters carefully before saving.
- If a Base starts accumulating live task state, move that state back to Linear/GitHub and keep only durable summaries in Hermes Brain.

## Ingestion Workflow
1. Save source to appropriate raw/ subfolder (immutable)
2. Read and analyze for key entities/facts
3. Discuss with Karan if major ingest
4. Create/update wiki pages in wiki/
5. Update index.md
6. Log the action in log.md
7. Retain key points to Hindsight if useful for conversational recall

## Access Rules
- NEVER read entire wiki into context
- Start with index.md to locate relevant pages
- Read only specific pages needed for current task
- Keep pages organized by domain/type in folders

## Health Check Workflow (weekly or on request)

Use the most efficient available backend:

1. **If Obsidian CLI is installed and Obsidian is running**, prefer it for Obsidian-native graph/metadata queries through the Hermes wrapper:
   ```bash
   GOB="~/.hermes/skills/note-taking/knowledge-memory-workflows/references/absorbed/obsidian/scripts/obsidian_hermes.sh"
   $GOB unresolved format=json
   $GOB unresolved total
   $GOB orphans
   $GOB deadends
   $GOB tags counts format=json
   $GOB properties format=json
   $GOB backlinks path="wiki/shared/projects/Project Status.md" format=json
   ```
   Then use `read_file`, `search_files`, and `patch` for precise fixes.
2. **If Obsidian CLI is unavailable**, run the Python analysis via `execute_code` as below.

Run Python via `execute_code` for efficient fallback analysis — all analysis in one script, then batch fixes.

### Step 1: Map the vault
Walk all .md files, collect relative paths and content. Flag empty pages (0 bytes). Count total pages.

### Step 2: Extract wikilinks and build link graph
For each page, extract `[[wikilinks]]` (handle `[[target|display]]` syntax). Build outgoing links per page and backlinks (reverse index). Exclude links inside backticks (code examples). Use: `re.findall(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', content)`

### Step 3: Identify issues (all checks in one pass)

**3a. Empty pages** — 0 bytes or whitespace-only. Delete if redundant or fill with content.

**3b. Broken wikilinks** — links to non-existent pages. Match targets against page basenames (case-insensitive). Separate wiki links (fixable) from daily log links (often skill names, acceptable). Common cause: Project Status dashboard using skill names as wikilinks.

**3c. Orphaned pages** — zero inbound wikilinks. Exclude structural files (SCHEMA, index, log, raw/, logs/). Fix meaningful orphans with Related sections or index entries; do not over-link daily logs/raw files just to satisfy graph metrics.

**3d. Stale content** — facts superseded by newer info. Use `hindsight_recall` to check for corrections (email addresses, project statuses, contact changes). CRITICAL: Email routing changes are highest-priority — misdirected emails cause real harm.

**3e. Stale dates** — `updated:` frontmatter showing old dates. Batch-update all touched pages.

**3g. Large-page triage** — flag pages over ~200 lines as candidates for review, but do not split living strategy documents solely because they are large. Karan explicitly wants `wiki/consultancy/business-plan.md` to remain a large living Papi AI strategy document. Apply size triage mainly to stale research dumps, transcripts, or pages that are hard to navigate.

**3f. Index sync** — verify all wiki/ pages in index.md. Daily logs use markdown link format, not wikilinks.

### Step 4: Execute fixes (in order)

1. **Stale content first** — fix incorrect facts before anything else
2. **Delete empty stubs** — remove dead weight
3. **Update durable summaries** — sync canonical business/client/project summary pages from Linear/GitHub/repo truth; do not recreate parallel task trackers in Hermes Brain
4. **Fix broken wikilinks** — redirect or remove dead links
5. **Add cross-links** — connect orphans via Related sections
6. **Rebuild index.md** — add missing wiki pages while keeping the index compact; use folder pointers for daily logs or dense source-note collections when listing every file would make the index noisy
7. **Update dates** — batch-update frontmatter on touched pages
8. **Log the action** — add entry to log.md

### Step 5: Verify
Re-run analysis: empty=0, broken links minimal (forward-references OK), orphans acceptable (standalone reference docs).

### Root Hygiene / Tracker Cleanup Workflow
Use this when Karan asks to reduce vault clutter, clean orphan files, or remove duplicate tracker structures:

1. **Propose batches before edits.** Separate safe root hygiene from deeper schema/index/frontmatter cleanup. Wait for approval per batch.
2. **Root cleanup:** delete only confirmed-empty root stubs; move real root markdown into the correct `wiki/` folder; inspect Obsidian support files (e.g. `.base`) before changing them.
3. **Duplicate `shared/` cleanup:** if a root `shared/` tree exists, move durable lessons into `wiki/shared/lessons/`, move durable archived summaries into `wiki/shared/projects/`, and fold stable business facts into canonical pages.
4. **Do not preserve active task trackers.** Delete root project tracker files after durable facts are folded into canonical wiki pages and current execution truth remains in Linear/GitHub.
5. **Update references immediately:** fix `Project Status.md`, `index.md`, and any non-log references to moved/deleted paths. Historical daily-log references can remain as history.
6. **Verify:** root entries should be only approved structural files/folders; moved destinations exist; deleted tracker paths are absent; no non-log markdown references deleted paths.
7. **Log:** update both `log.md` and the daily log.

### Health Check Pitfalls
- **Obsidian CLI optional backend:** If available, use `~/.hermes/skills/note-taking/knowledge-memory-workflows/references/absorbed/obsidian/scripts/obsidian_hermes.sh` for `unresolved`, `orphans`, `deadends`, `backlinks`, `links`, `properties`, `tags`, `tasks`, templates, and link-safe `move`/`rename`. It requires Obsidian 1.12.7+, CLI enabled in Settings → General, and the Obsidian app running. Keep direct file tools as the default for deterministic headless reads/writes/patches.
- **Tilde env var pitfall:** `OBSIDIAN_VAULT_PATH=~/obsidian-vault/hermes-brain/` is fine for the wrapper because it expands leading `~`, but raw shell checks like `test -d "$OBSIDIAN_VAULT_PATH"` may fail if `~` is stored literally. Prefer the wrapper or expand with `${HOME}`.
- **Obsidian CLI unresolved-link behavior:** Do not rely on YAML `aliases:` to satisfy `$GOB unresolved`; in testing, title-style wikilinks still appeared unresolved even after aliases were added. Fix real broken wiki links by converting them to explicit vault-path wikilinks, e.g. `[[wiki/consultancy/business-plan|Papi AI Consulting Business Plan]]`.
- **External markdown links can show as unresolved:** Absolute markdown links to local files like `[Plan](/Users/.../plan.md)` may appear in Obsidian CLI unresolved output. For working-file references outside the vault, prefer plain code paths such as `` `/Users/creator/projects/file.md` `` unless a true Obsidian link is needed.
- **Project Status dashboard** is the biggest broken link source — skill names used as wikilinks. Use dash or link to actual wiki page.
- **Root-level stubs are usually accidental.** Real content lives in `wiki/` subfolders. Approved root items should stay boring: `SCHEMA.md`, `index.md`, `log.md`, `raw/`, `wiki/`, `logs/`, and explicitly intentional Obsidian support files (for example `.base` files after inspection).
- **Duplicate project trackers are a smell:** root `shared/projects/` and detailed task tracker pages should be consolidated or removed. Linear/GitHub/project repos own active task state; Hermes Brain should keep only durable summaries, decisions, lessons, and source-system links.
- **Project-status sync should log its own wiki edits:** When an unattended project-status cron makes durable dashboard/archive changes, also update `log.md` and create/update the active daily log for that day, then verify the daily log is under 3,000 chars. If no dashboard/archive changes were made, do not create a daily log solely for the check.
- **Project-status verification should check durable facts, not exact planned prose:** After dashboard/archive edits, verify touched files exist, required sections remain, root `shared/` is absent, and key durable facts are present. If a verification needle fails because the file uses different but correct wording, rerun verification with a semantic/key-fact needle instead of editing the dashboard just to satisfy your own phrasing.
- **Stale cron prompts can recreate retired tracker paths:** if `ARCHIVED.md`, root `shared/`, or `shared/projects/*.md` reappears after cleanup, inspect/update the Weekday Obsidian Project Status Sync cron prompt/model/skills so it uses `wiki/shared/projects/Project Status.md` and `wiki/shared/projects/Archived Project Summaries.md` only.
- **Wikilinks inside backticks** are examples, not real links. Strip code blocks before analyzing.
- **Daily log broken links are acceptable** — skill name references for context.
- **Email/contact changes** are the most dangerous stale data. Always query Hindsight during health checks.
- **Index edits require exact context matching.** Do not assume markdown-link format for index entries; the vault mixes wikilinks (`[[Project Status]]`) and markdown links (`[label](relative/path)`). Read the relevant lines first with `search_files` or `read_file`, then patch using the exact surrounding block.
- **Use two-step insertion when adding index entries.** If an edit misses, inspect the nearby headings/entries and reattempt with an exact unique context chunk rather than guessing.
- **Edit local wiki entries with exact context, not assumed line content.** When updating project trackers like `shared/projects/papi-ai-consulting.md`, read the current block first, then patch the exact headings/list item text.

## Reference Notes
- `references/hermes-brain-cleanup-boundaries-2026-05-05.md` captures Karan's confirmed Hermes Brain vs Karan OS boundary, project-tracker rule, Batch 1 cleanup outcome, and business-plan large-page exception.

## Hindsight vs Wiki Decision
- **Hindsight:** preferences, corrections, session continuity, quick facts, conversational context
- **Wiki:** reference data, structured info, reusable content, has natural page name
- **Rule:** If you'd want to find it via page name or cross-link, it's wiki. If agent should "just know" contextually, it's Hindsight.

## Daily Log Rules
- Path: logs/YYYY/MM/YYYY-MM-DD.md
- One file per active day only (no empty files for idle days)
- Max 3000 characters
- Structure: What We Did, Wiki Changes, Mistakes & Lessons, Next Steps

## Lessons Documentation
- Create standalone pages in wiki/shared/lessons/ for mistakes and operational learnings
- Format: title, domain=shared, type=lesson, status=resolved
- Sections: What Happened, Root Cause, Fix, How to Prevent, Impact, Related
- Cross-reference from the relevant infrastructure/tool page via wikilink

## macOS Launch Agent Warning
- launchctl plist env vars override .env file completely
- Always check ~/Library/LaunchAgents/*.plist for EnvironmentVariables when modifying service config
- Use `plutil -extract EnvironmentVariables xml1 -o - <plist>` to verify
- Lesson: Updated .env but Hindsight still used old model/key because plist had hardcoded values (2026-04-09)

## Project Status and Tracker Boundary
- Hermes Brain is agent/business memory, not the source of truth for execution tracking.
- Linear/GitHub/project repos own active issues, backlog, acceptance criteria, PR state, and task history.
- `wiki/shared/projects/Project Status.md` may exist as a high-level snapshot, but do not maintain parallel task trackers in the vault.
- When project state changes, summarize only durable facts/decisions/links in Hermes Brain; keep granular task lists in Linear/GitHub.
- Before marking project work completed in `Project Status.md`, verify the owning source system: use `gh` for GitHub PR/issue state and the Linear helper/API for Linear issue state. For Linear, confirm the issue's workflow state/type directly (for example `Done` / `completed`) instead of relying only on session notes. For web/endpoint acceptance criteria, verify the live endpoint or deployed URL separately from the merged PR and distinguish “repo code merged” from “live behavior verified”; if an issue remains open after a merged PR, keep the dashboard row active or mark the completion as pending closeout rather than completed.
- Karan OS is the separate personal vault; do not store personal-vault implementation content inside Hermes Brain except as a boundary/reference note.

## Raw vs Projects Distinction
- ~/projects/ = working files actively edited (pitch decks, code, contracts in progress)
- raw/ = immutable source documents for wiki ingestion (completed docs, vendor emails, client questionnaires)
- wiki/ = structured knowledge base derived from raw sources
- Acceptable raw file types: PDFs, RTFs, text, CSVs, images (vision-capable), any document with extractable info