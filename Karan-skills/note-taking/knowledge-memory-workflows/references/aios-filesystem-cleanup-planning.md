# AIOS Filesystem Cleanup Planning Pattern

Use this when Karan asks to reorganize his machine/filesystem for AI-OS or agentic workflow friendliness.

## Core lesson
Treat mass filesystem cleanup as a **manifest-driven migration/control loop**, not casual spring cleaning. The deliverable should be a reversible operating plan and, when requested, a polished artifact; implementation requires separate explicit approval.

## Recommended workflow
1. **Load relevant skills**
   - `knowledge-memory-workflows` / `hermes-brain-wiki` for memory/vault boundaries.
   - `notebooklm-to-obsidian-synthesis` when the user asks to query NotebookLM.
   - `creative-html-visual-artifacts` + `local-web-preview` when producing a polished HTML plan/report.

2. **Read-only local inventory first**
   - Inspect top-level home structure, major size centers, project roots, worktree/repo markers, Downloads/Desktop clutter, and protected state candidates.
   - Do not read secrets or mutate files.
   - Summarize metadata only: path, kind, size, mtime, extensions, markers, duplicate/clutter signals.

3. **Query the specific NotebookLM notebooks**
   - For AIOS/file organization principles, query the `AI OS` notebook.
   - For implementation-loop design, query `Strategic Engineering: Harnessing AI as a Force Multiplier`.
   - Feed a compact current-state digest into the notebook prompt; ask for operational principles, warnings, verification gates, and success metrics.

4. **Synthesize into a migration plan**
   - Prefer `file-over-AI`, maps/indexes/manuals, and ACE-like routing (`Atlas`, `Calendar`, `Efforts`) while respecting Karan’s existing canonical roots (`~/projects`, `~/obsidian-vault/hermes-brain`, Karan OS personal vault).
   - Avoid blindly renaming established roots just because notebook sources use a different naming scheme.
   - Preserve source-of-truth boundaries: Hermes Brain is agent/business memory; Karan OS is personal; repos/Linear/GitHub remain active execution truth.

5. **Implementation loop shape**
   - Inventory → classify → dry-run proposed moves → adversarial verification → user approval → small reversible batches → final report.
   - Use state files as the spine:
     - `Safety-Rubric.md`
     - `AIOS_MAP.md`
     - `MANIFEST.json`
     - `PROPOSED_MOVES.json`
     - `ROLLBACK_MANIFEST.json`
     - `STATE.md`
   - Include explicit stop conditions: approval needed, protected path, secret-risk flag, git/worktree ambiguity, verification mismatch, pass/batch cap, or user pause.

6. **Safety rules**
   - No deletion in the plan phase.
   - Do not move or mutate: `~/.ssh`, `~/.hermes`, `~/.codex`, `~/.claude`, `~/.notebooklm`, auth stores, `.env`/tokens/keys, Obsidian raw sources, Karan OS, or git repos/worktrees without explicit approval and registry checks.
   - For git/worktrees, require `git worktree list --porcelain` or equivalent before any relocation.
   - Put ambiguous items into `needs_human_review`, not a guessed destination.

7. **HTML artifact expectations**
   - Build a real standalone HTML report with executive summary, current-state audit, target taxonomy, residency rules, implementation `/goal`, loop architecture, risk matrix, and success metrics.
   - Verify file existence, required sections, browser rendering, and console errors.
   - Stop any temporary preview server after QA.

## Pitfalls
- Do not turn a cleanup plan into live cleanup without explicit approval.
- Do not collapse Hermes Brain and Karan OS boundaries.
- Do not let NotebookLM’s generic ACE examples override already-working local conventions.
- Do not delegate actual filesystem mutation to subagents; keep mutation with default Hermes after approval.
- Do not make cron/scheduled cleanup until the manual loop has proven reliable.