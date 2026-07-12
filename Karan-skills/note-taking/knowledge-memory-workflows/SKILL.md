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

## Workflow
1. Classify the information: user preference, environment fact, reusable procedure, reference note, or temporary task state.
2. Search existing knowledge before adding duplicates.
3. Write in the correct layer: memory for compact durable facts, skills for procedures, Obsidian/wiki for rich notes.
4. For NotebookLM-style grounded research workflows, treat NotebookLM as a source-grounded research workspace, not the only durable memory layer; promote final conclusions into Hermes Brain/Hindsight/skills as appropriate. See `references/notebooklm-research-brain.md`.
5. When Karan asks to query a specific NotebookLM notebook and decide workflow/product implications, use the NotebookLM → Obsidian promotion pattern: ask for actionable synthesis, cross-check existing wiki/project state, create/update a concise wiki page, update index/log, and verify readback/search. See `references/notebooklm-to-obsidian-research-promotion.md`.
6. When Karan asks to capture a proposed plan/restructure/workflow in the wiki but says not to implement it yet, make the wiki note the deliverable and preserve the non-action boundary. If the root index is near budget, compact existing labels/headings to preserve the new catalog link rather than dropping discoverability. See `references/plan-capture-without-implementation.md`.
7. When Karan asks for AIOS/filesystem cleanup planning, treat it as a reversible manifest-driven migration/control loop, not casual file moving. Query the relevant NotebookLM notebooks when requested, inspect local state read-only, preserve Hermes Brain/Karan OS/repo boundaries, and include an implementation `/goal` with approval gates. See `references/aios-filesystem-cleanup-planning.md`.
8. Verify created/updated notes by reading them back.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/`.

## Verification Checklist
- [ ] No stale task progress is saved as memory.
- [ ] Duplicate notes/memories checked first.
- [ ] New notes or wiki pages read back after writing.
- [ ] Promotion decisions are conservative and reversible.
