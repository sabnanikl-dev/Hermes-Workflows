---
name: knowledge-memory-workflows
description: "Use for durable knowledge workflows: Obsidian vault operations, Hermes brain/wiki maintenance, and conservative memory closeout/dreaming promotion."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [memory, obsidian, wiki, closeout, knowledge-management]
    related_skills: [hermes-brain-wiki]
---

# Knowledge and Memory Workflows

## Overview
Use this umbrella when the task is to manage durable knowledge rather than immediate task state: Obsidian notes, wiki maintenance, closeout/dreaming reports, or deciding whether a pattern should become memory, a skill, or a reference.

## When to Use
- Read/search/create notes in the Obsidian vault.
- Maintain the Hermes brain/wiki.
- Run or design conservative closeout/dreaming workflows.
- Decide promotion targets for learned patterns.

## Proactive Runtime Lifecycle
For substantive project, business, research, planning, or personal/portfolio work, Obsidian is part of the task lifecycle rather than an optional closeout step:
1. **Preflight:** use the default-profile `vault-context-router` context when present. It has already read bounded canonical entry-page excerpts for the matched owner task. Read only exact additional pages needed; never bulk-read either vault.
2. **Execute against owners:** vault pages supply durable context and constraints, while Linear, GitHub, repositories, client systems, and live endpoints supply current execution truth.
3. **Closeout:** classify whether reusable knowledge changed. Maintain an established Hermes Brain page when sourced agent/business knowledge changed; propose Karan OS placement unless the current user turn explicitly requested capture or maintenance; promote repeatable procedures through the skill-evolution standard; create nothing when no reusable knowledge emerged.
4. **Verify:** read back any vault edit, preserve index/log contracts, and disclose the exact durable path when placement materially changed.

Automatic Karan OS preflight is limited to `00 Vault Charter.md`, `02 Vault Map.md`, and `03 Working Preferences.md` on relevant owner tasks. Do not pass private Karan OS context to child/specialist agents. The runtime contract is `wiki/shared/infrastructure/Vault Use Runtime Contract.md` in Hermes Brain.

## Workflow
1. Apply the mandatory pre-write routing gate before every durable create or substantial update:
   - active execution state → Linear, GitHub, or the repository-owned tracker;
   - actual deliverable, working asset, code, or evidence → project directory or repository;
   - content primarily helping Karan think, decide, reflect, or manage personal life → Karan OS;
   - durable business/operating context an agent needs to perform → Hermes Brain;
   - repeatable executable procedure → the owning skill;
   - genuine ambiguity → recommend one canonical destination, explain alternatives and discoverability effects, and ask rather than filing silently.
2. Classify by primary consumer and canonical responsibility, not topic alone. Karan OS is Karan-owned and Hermes-assisted; Hermes writes there only after an explicit capture, drafting, or maintenance request. Hermes Brain is Hermes-maintained inside established structure and Karan-governed for new boundaries, private imports, sensitive claims, and strategy/authority changes.
3. Search existing knowledge, project repositories, and approved client systems before adding duplicates.
4. Write in the correct layer: memory for compact durable facts, skills for procedures, Obsidian/wiki for rich curated notes, repositories for repository-owned knowledge, Linear/GitHub for tracker truth, and client systems for their operational truth. When both Karan OS and Hermes Brain need part of the same concept, preserve one canonical source and create only a bounded projection with consumer/purpose, minimum approved statement, exclusions, and freshness trigger; do not mirror or bidirectionally synchronize by default.
5. For Linear-sourced work, classify every potential knowledge output before creation. If an established mapping or the approved issue names the canonical destination, use it and disclose the choice. If creating a new durable file/folder/index would establish or alter an information-architecture boundary, recommend an exact location and ask Karan to confirm where it should live before writing. The question must include intended user, reuse case, recommended path/system, rationale, meaningful alternatives, and discoverability/index implications.
6. Do not promote ticket state, raw transcripts, transient metrics, or temporary evidence as durable knowledge. If no reusable knowledge emerged, record `Durable knowledge: none` rather than creating filler.
7. For material behavior-changing skill promotion, follow `wiki/shared/infrastructure/Skill Evolution Operating Standard.md` in Hermes Brain: preserve evidence, compile the lesson in the wiki, search for the owning skill, propose one atomic patch, record it in `Skill Evolution Ledger.md`, validate proportionally, and retain or roll back based on evidence. Preserve rejected outcomes so future agents do not repeat them blindly. Minor typo/metadata/vendor-command refreshes are exempt unless they alter behavior or authority.
8. Keep runtime and maintenance context separate: execution agents normally receive the approved skill and task context; broad wiki access belongs to knowledge-maintenance or skill-proposal work unless the task itself requires wiki retrieval.
9. For NotebookLM-style grounded research workflows, treat NotebookLM as a source-grounded research workspace, not the only durable memory layer; promote final conclusions into Hermes Brain/Hindsight/skills as appropriate. See `references/notebooklm-research-brain.md`.
10. When Karan asks to query a specific NotebookLM notebook and decide workflow/product implications, use the NotebookLM → Obsidian promotion pattern: ask for actionable synthesis, cross-check existing wiki/project state, create/update a concise wiki page, update index/log, and verify readback/search. See `references/notebooklm-to-obsidian-research-promotion.md`.
11. When Karan asks to capture a proposed plan/restructure/workflow in the wiki but says not to implement it yet, make the wiki note the deliverable and preserve the non-action boundary. If the root index is near budget, compact existing labels/headings to preserve the new catalog link rather than dropping discoverability. See `references/plan-capture-without-implementation.md`.
12. When Karan asks for AIOS/filesystem cleanup planning, treat it as a reversible manifest-driven migration/control loop, not casual file moving. Query the relevant NotebookLM notebooks when requested, inspect local state read-only, preserve Hermes Brain/Karan OS/repo boundaries, and include an implementation `/goal` with approval gates. See `references/aios-filesystem-cleanup-planning.md`.
13. Verify created/updated notes by reading them back.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/`.

## Verification Checklist
- [ ] No stale task progress is saved as memory.
- [ ] Duplicate notes/memories checked first.
- [ ] New notes or wiki pages read back after writing.
- [ ] Promotion decisions are conservative and reversible.
- [ ] Material skill changes link evidence and a ledger entry.
- [ ] Proposed skill behavior was validated or explicitly marked inconclusive/rejected.
- [ ] Runtime agents were not granted broad wiki context or additional authority merely to support skill evolution.
