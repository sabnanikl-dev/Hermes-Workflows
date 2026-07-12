# Plan Capture Without Implementation

Use when Karan asks to preserve a proposed plan, restructure, harness, or workflow in Obsidian/wiki but explicitly says not to change the project/repo yet.

## Pattern

1. Treat the requested wiki note as the deliverable; do **not** mutate the target repo/project unless the user separately approves implementation.
2. Place the note in the domain folder the user named, following Hermes Brain page conventions:
   - frontmatter with `title`, `domain`, `type`, `status`, `created`, `updated`
   - `status: draft` when it is a proposal not yet accepted/executed
   - clear Overview, Current Context, Proposed Structure/Steps, What Not To Do, Migration Plan, Acceptance Criteria, Recommendation, Related sections
3. Preserve the distinction between:
   - current/source state observed from the repo or wiki
   - proposed future changes
   - explicit non-actions / “not implementing yet” guardrails
4. Update navigation only where useful and lightweight:
   - add catalog-worthy notes to `index.md`, keeping the index under its character budget
   - update `log.md` and the daily log when wiki state changes
5. Verify by reading/searching the new note and checking basic hygiene:
   - file exists and has final newline
   - no trailing whitespace
   - index/log references are present
   - root index remains within budget if edited
   - if the root index is near its character budget, compact nearby headings/labels before skipping the new catalog link; preserve discoverability while staying under budget
6. In the final response, say what was captured, where, what navigation/log files changed, what was verified, and explicitly confirm that no project/repo implementation changes were made.

## Pitfalls

- Do not turn a captured proposal into an implementation pass.
- Do not create a parallel task tracker in Hermes Brain; link/source Linear/GitHub/project repos for execution state.
- Do not save temporary task state as memory; the wiki note is the durable artifact.
- If the plan is class-level/reusable, store principles and template-worthy details, not chat transcript narrative.
