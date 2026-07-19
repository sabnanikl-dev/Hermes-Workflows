---
name: hermes-brain-wiki
description: Three-layer memory architecture (Standard -> Hindsight -> Obsidian Wiki) with vault structure, SCHEMA conventions, and maintenance workflows for persistent knowledge management.
---

# Hermes Brain Wiki

Three-layer memory architecture for Karan's businesses (Femme Events + Papi AI Consulting).

## Architecture Layers

### Layer 0: Standard Memory (~500 bytes max)
- **What:** Core identity, critical per-turn facts
- **Where:** `~/.hermes/memories/MEMORY.md` / `USER.md`
- **When loaded:** Every single turn
- **Content:** Name, contact, core preferences, security rules
- **Rule:** Keep under 40% capacity. Everything else goes to Hindsight or Wiki.

### Layer 1: Hindsight (Conversational Memory)
- **What:** Auto-recalled facts, session context, preferences, corrections
- **Where:** Local service on port 9100 (model: openai/gpt-4o-mini)
- **When loaded:** Semantic recall via `pre_llm_call` hook
- **Content:** Vendor research results, Amanda's communication style, past decisions
- **Rule:** If the agent should "just know" it contextually, it's Hindsight.

### Layer 2: Obsidian Wiki (Structured Knowledge Base)
- **What:** Curated, cross-referenced wiki pages
- **Where:** `~/obsidian-vault/hermes-brain/`
- **When loaded:** On-demand via index.md -> specific page reads
- **Content:** Vendor databases, client histories, playbooks, research, brand guides
- **Rule:** If it needs a page name, cross-links, or structured reference, it's Wiki.

## Vault Structure

```
~/obsidian-vault/hermes-brain/
├── SCHEMA.md              # Conventions, page formats, workflows
├── index.md               # Master catalog (keep under 3000 chars)
├── log.md                 # Chronological activity record
├── raw/                   # Immutable source documents (never modify)
│   ├── femme-events/
│   ├── consultancy/
│   └── shared/              # cross-domain sources, transcripts, references
├── logs/                  # Daily logs: YYYY/MM/YYYY-MM-DD.md (max 3000 chars)
└── wiki/                  # Agent-written and maintained pages
    ├── femme-events/
    │   ├── vendors/       # Vendor profiles (pricing, contacts, notes)
    │   ├── venues/        # Venue pages (specs, capacity, quirks)
    │   ├── inventory/     # Rental inventory catalog
    │   ├── clients/       # Client pages with accumulating context
    │   └── processes/     # Checklists, timelines, templates
    ├── consultancy/
    │   ├── clients/       # Client project pages
    │   ├── research/      # Tools, platforms, frameworks evaluated
    │   ├── playbooks/     # SEO, POS integration, CRM patterns
    │   ├── pitches/       # Pitch strategies and what landed
    │   └── builds/        # Custom tools built, specs, lessons
    └── shared/            # Cross-domain pages (business ops, scheduling)
```

## Vault Boundaries

- **Hermes Brain** is agent/business memory: durable summaries, references, lessons, business/client context, source-derived wiki pages, and concise project snapshots.
- **Karan OS** is the separate personal vault at `/Users/creator/Documents/Obsidian Vault/Karan OS`. Do not duplicate personal identity/operating-system docs into Hermes Brain.
- **Linear/GitHub/project repos** are source of truth for active task execution, backlog, acceptance criteria, PR state, and detailed tracker history. Hermes Brain should summarize durable facts and link out; do not maintain parallel project trackers.
- **Obsidian-native support files are allowed when they improve human review:** `.canvas` for visual maps/flowcharts and `.base` for lightweight views over existing wiki notes. They must support, not replace, the Markdown wiki and external source-of-truth trackers.
- **Root hygiene:** root should stay boring: `SCHEMA.md`, `index.md`, `log.md`, `raw/`, `wiki/`, `logs/`, and explicitly approved Obsidian support files only.

## Page Format (SCHEMA.md Conventions)

### Frontmatter
```yaml
---
title: "Page Name"
domain: "femme-events | consultancy | shared"
type: "vendor | venue | client | process | research | playbook | pitch | build | person | business | reference | project | project-dashboard | project-archive | lesson | infrastructure | workflow | checklist | business-plan"
status: "active | archived | draft"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

### Section Order
1. **Overview** - 1-2 sentences, what/why
2. **Details** - Data, specs, contacts, pricing
3. **Notes** - Observations, quirks, context
4. **Related** - Wikilinks to connected pages

### Naming
- Title Case: `Femme Events Brand Guide.md`
- Descriptive: `Vendor A-1 Party Rental.md`
- Use spaces (Obsidian handles this)

## Workflows

### Project State vs Project Tracking

Hermes Brain is **agent/business memory**, not the execution tracker. Karan OS is the separate personal vault.

Source-of-truth boundaries:
- **Linear/GitHub/project repos:** live issues, task execution, backlog, acceptance criteria, PR state, engineering tracker details.
- **Hermes Brain:** durable business context, project summaries, decisions, lessons, links to source systems, and status snapshots when useful.
- **Karan OS:** personal identity, working preferences, personal operating notes, and user-owned vault maps.

Workflow when project status comes up:
1. If the request is about active tasks/backlog/execution, use Linear/GitHub/repo context as the source of truth rather than creating or maintaining parallel tracker pages in Hermes Brain.
2. If a durable summary belongs in the wiki, update a concise business/project summary page with links back to Linear/GitHub; avoid copying task lists wholesale.
3. Keep `wiki/shared/projects/Project Status.md` as a high-level snapshot only if useful, not a full project tracker.
4. Never move Karan OS/personal vault content into Hermes Brain; reference its canonical external path only when the boundary itself matters.

### Ingestion (New Source Document)
1. Save source to `raw/` subfolder (immutable)
2. Read and analyze for key entities/facts
3. Discuss with Karan if major ingest; proceed directly for small updates
4. Create/update wiki pages in `wiki/` with cross-references
5. Update `index.md` with new entries; keep the index compact and under its size budget
6. Log action in `log.md` and update/create the relevant daily log when the session changes durable wiki state
7. Retain key points to Hindsight with `hindsight_retain` when available; if Hindsight storage is unavailable, do not block the wiki ingest
8. Verify all raw files, curated pages, and navigation/log edits exist before reporting success

For YouTube/video sources, save raw metadata + captions/transcript alongside the curated page and clearly distinguish transcript-derived takeaways from unverified market/revenue claims.

### Query (Answering Questions)
1. Start with `index.md` to locate relevant pages
2. Read ONLY specific pages needed (never bulk-read the vault)
3. Cross-reference related pages for complete context
4. Update wiki if conversation surfaces new facts
5. Retain conversational insights to Hindsight

### Weekly Health Check
Use the Obsidian CLI wrapper when available for graph/metadata queries, then use file tools for precise edits:

```bash
GOB="~/.hermes/skills/note-taking/knowledge-memory-workflows/references/absorbed/obsidian/scripts/obsidian_hermes.sh"
$GOB unresolved total
$GOB orphans total
$GOB deadends total
$GOB tags counts format=json
$GOB properties format=json
```

1. **Broken wikilinks** - Scan for `[[references]]` to non-existent pages (`$GOB unresolved` when available)
2. **Orphaned pages** - Find pages with no incoming links (`$GOB orphans` when available)
3. **Stale pages** - Flag pages not updated in 60+ days
4. **Index sync** - Verify all `wiki/` pages are in `index.md`

## Hindsight vs Wiki Decision Matrix

| Criteria | Hindsight | Wiki |
|----------|-----------|------|
| Conversational context | Yes | No |
| Session-specific details | Yes | No |
| Preferences, corrections | Yes | No |
| Reusable reference data | No | Yes |
| Structured with cross-links | No | Yes |
| Will be queried multiple times | No | Yes |
| Needs human curation | No | Yes |
| Has a natural page name | No | Yes |

## NotebookLM as Research Substrate

Karan's preferred architecture is: **NotebookLM is a leveraged research tool; Obsidian Hermes Brain remains the durable memory layer.** Do not create a generic "Hermes Research Brain" NotebookLM notebook by default. Instead:
1. Query specific existing NotebookLM notebooks relevant to the task.
2. Use NotebookLM for source-heavy reading, citation-backed synthesis, and artifact generation.
3. When the user asks for implications/opportunities, prompt NotebookLM for actionable synthesis: principles, workflow/product opportunities, and small next experiments rather than a generic summary.
4. Cross-check current project/repo/GitHub/Linear state separately before turning NotebookLM research into recommendations; NotebookLM is grounded in its sources, not live system state.
5. Promote only durable, distilled, page-worthy knowledge into Obsidian `wiki/` pages.
6. Preserve NotebookLM outputs as raw/reference material only when they are valuable sources; do not dump every query into the wiki.
7. Use Obsidian CLI when available for vault search/graph/navigation, then file tools for precise edits.
8. When a new curated wiki page is created from NotebookLM research, update `index.md` when catalog-worthy, update the daily log if wiki state changed, and verify by readback/search before reporting success.

Promotion rule: NotebookLM answers are intermediate research. Obsidian pages are curated memory. Hindsight/standard memory get only compact facts/preferences that should be recalled conversationally.

## Environment Configuration

Required env var in `~/.hermes/.env`:
```
OBSIDIAN_VAULT_PATH=~/obsidian-vault/hermes-brain/
```

Hindsight API service `io.vectorize.hindsight.api` on port 9100. Model: `openai/gpt-4o-mini` (changed from claude-sonnet-4 on 2026-04-09 for cost optimization). Uses a **separate OpenRouter API key** (`HINDSIGHT_API_LLM_API_KEY`) for rate limit isolation from the main agent.

## Project Directory Mapping

Existing project directories that map into the wiki:
- `~/projects/femme-events/` → wiki pages reference files here (brand assets, contracts, website, signatures)
- `~/projects/consultancy/` → wiki pages reference files here (client projects, pitch decks, briefs, contracts)
- The wiki indexes and cross-references these; it does NOT duplicate working files.

## Pitfalls

- **`.env` files are protected from `patch` tool writes** - you must use `terminal` to append/modify, or ask the user to edit manually. The `.env` credential file cannot be written to directly by the patch tool and is security-scanned.
- **NEVER** read the entire wiki into context. Always start with index.md.
- **NEVER** modify files in `raw/` - they are immutable sources.
- **Don't** put everything in Hindsight. If it's structured reference data, it belongs in the Wiki.
- **Don't** put everything in Wiki. If it's a quick preference or session artifact, use Hindsight.
- **Living document exception:** `wiki/consultancy/business-plan.md` may remain large by design. Karan wants it preserved as a living Papi AI strategy document that can grow as the business pivots; do not split it solely due to line count.
- **Standard memory stays minimal** (~500 bytes). If you're adding details there, you're doing it wrong.
- **Root-level stubs are usually accidental.** Real content belongs under `wiki/`; raw/source material belongs under `raw/`; daily chronology belongs under `logs/`. Move real root markdown into the correct folder, delete confirmed-empty stubs after verification, and inspect Obsidian support files (for example `.base`) before changing them.
- **Don't create parallel project trackers in Hermes Brain.** Use Linear/GitHub/project repos for active task state. Preserve only durable project summaries, decisions, lessons, archived outcomes, and links in the wiki.
- **Consultancy email rule:** CC sabnani.kl@gmail.com on consultancy emails only. No automatic CC for Femme Events emails (per-event basis).
