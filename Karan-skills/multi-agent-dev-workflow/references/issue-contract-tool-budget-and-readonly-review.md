# Issue-contract integrity, tool-budget checkpoints, and read-only review probes

Use this reference during long issue-to-PR review/fix loops.

## 1. Preserve source-of-truth precedence

The live GitHub issue acceptance criteria outrank the PR body, builder summary, and implementation docs for deciding whether the issue is complete.

A builder must not resolve a reviewer blocker by merely changing a PR checkbox or rewriting docs to describe weaker behavior. Example class: the issue requires projection-directed loading, but the code performs a full-corpus load and filters only the returned rows. Changing the PR to say “result isolation, not loading isolation” makes the description accurate but does not satisfy the issue.

Required handling:

1. Re-read the live issue before every fix cycle.
2. Keep fix prompts pointer-first, but explicitly forbid weakening or laundering issue acceptance criteria through PR/docs edits.
3. If implementation and AC differ, implement the AC or ask the human to amend the issue on the authoritative issue surface.
4. Reviewers must evaluate against the unchanged issue, not the builder's revised acceptance checklist.

## 2. Validate safety DSLs relationally, not field-by-field

For registry/query/guard DSLs, validating recognized operation names and operand shapes is not enough. Validate compatibility across fields:

- status guards require `status` in the selected output;
- ID-prefix guards require the applicable ID output for row queries;
- field-equality guards must name a selected output field;
- filter values must have permitted scalar/list shapes, not arbitrary mappings;
- expected row keys must exactly match selected output keys;
- malformed roots and parser errors should become the documented structured usage error.

Add negative probes for each false-pass class. A malformed safety assertion that becomes an empty result or `dict.get(...) == None` is a blocker even when the normal corpus passes.

## 3. Read-only reviewer probe fallback

Hardened Codex read-only sandboxes may prohibit creating temp files. Do not weaken the lane or give it workspace-write solely for convenience.

Use deterministic in-memory substitutes where possible:

- SQLite `:memory:` plus connection backup for mutation scenarios;
- direct imports of pure validation/evaluation functions;
- in-memory registry documents for malformed-input probes;
- AST parsing instead of bytecode generation;
- the immutable packet's exact-head baseline/CI evidence for temp-backed suites the lane cannot rerun.

Classify the temp restriction as an environment limitation, not a product failure. The Integration Auditor launcher may independently run temp-backed commands when its policy permits.

## 4. Tool-budget-aware orchestration

Repeated one-minute `process.wait` / `poll` calls can consume the parent session's tool-iteration budget long before a legitimate 10–20 minute builder/reviewer run finishes.

Before launching each builder or review cycle, reserve enough calls for the complete remainder:

- observe completion marker;
- verify local/remote/PR head;
- rerun exact-head tests;
- prepare a fresh packet/worktree;
- launch and collect every required reviewer;
- relay and read back artifacts;
- perform final GitHub-state synthesis.

Operating pattern:

1. Launch bounded workers with `background=true, notify_on_complete=true`.
2. Do not poll every minute merely because `process.wait` is clamped. Inspect only at meaningful milestones or a several-minute cadence, batching process state, worktree state, and PR state in one parallel call.
3. Near the session/tool ceiling, stop at a verified checkpoint before launching another cycle. Never launch a final fix cycle if its completion and mandatory re-review cannot still be observed.
4. If a hard cap arrives mid-cycle, report the last verified head and mark the worker outcome unknown. Do not claim the fix landed.
5. For work likely to outlive the interactive budget, use the durable workflow/watchdog pattern before starting rather than relying on chat polling.

## 5. Final-cycle rule

At the normal two-cycle cap, a current-head blocker requires escalation unless the human explicitly authorizes a narrowly scoped exceptional cycle. A builder commit is not completion; only fresh current-head A, B, and Integration Auditor outcomes close the cycle.

Do not let one passing lane erase blockers from another lane. Merge-readiness is the union of material current-head findings across A, B, and Integration. At the cap, relay all final-head artifacts first, verify the formal review/comment state, then present the deduplicated blocker classes and ask for an explicit scope-bound exception only if further work is warranted.

## 6. Instrument the real boundary, not the advertised result

Isolation regressions must observe every actual read/parse operation, including discovery and resolver work performed before the final path set is returned. Checking only the files passed to the exporter can produce a false pass while a resolver scans excluded modules to locate explicit entity/rule references.

For projection/client-directed loading:

1. Wrap or inject the shared `parse_yaml` function at every relevant import site.
2. Record reads during manifest lookup, projection lookup, explicit-reference resolution, and export.
3. Assert that no foreign-client or excluded-module file was parsed—not merely that it was absent from the returned export paths.
4. Include a probe whose projection explicitly references an entity/rule from a module so the resolver path is exercised.
5. Stop scanning once references are resolved, or use manifest-owned indexes; do not scan all remaining modules and call the result isolated.

## 7. Validate the complete registry envelope

Relational query/guard checks are necessary but not sufficient. Validate identity, metadata, gating fields, and the top-level key set before using entries as dictionary keys, paths, booleans, or safety assertions:

- `id`, `client_id`, and `projection` must be non-empty strings;
- `question` and `rationale` (or whatever human-readable metadata the issue/registry contract promises) must be present, non-empty strings—not merely optional documentation;
- `required`, when present, must be a real boolean (reject `0`, `1`, strings, mappings, and lists rather than relying on truthiness);
- reject unknown question-level keys, while permitting only explicitly documented extension keys such as `x_*`;
- validate the exact `guards` key at the envelope boundary: a misspelling such as `gaurds` must be an error, never a silently ignored safety policy;
- malformed envelope values must become the same structured usage error/exit-2 path as malformed query bodies.

Negative probes should cover mapping-valued IDs/client IDs/projections, missing/non-string `question` and `rationale`, non-boolean `required`, and misspelled/unknown top-level keys. Explicitly prove both that malformed requiredness cannot turn a failed required question into a successful process exit and that a misspelled safety field cannot remove guards while leaving the question PASSing.

## 8. Enforce library contracts at the library boundary

A safe current caller does not satisfy a public helper's documented security contract. If `export(root, output, paths=...)` says paths stay under `root`, the export function itself must resolve and reject out-of-root paths before parsing, even when the competency runner currently supplies paths through a safe join helper.

Also verify resource cleanup on validation/parse failure: validate path containment before opening the database where practical, or guarantee connection closure and partial-output cleanup on exceptions. Add direct library probes with an outside-root file and traversal/symlink cases appropriate to the platform.

## 9. Synchronize live PR metadata after every implementation pivot

A signed fix comment does not repair a stale PR body. After every follow-up commit, compare the live PR description against the exact current head for:

- loading/execution architecture;
- regression and fixture counts;
- commands and outcomes;
- acceptance checkboxes;
- generated-artifact claims;
- issue-closing linkage.

Never copy a builder-reported test/probe count into the PR contract without deriving it from executable output. Read the JSON/human result and compute the real case count (for example `len(registry_probes.cases)`), including the valid-vs-malformed split; compare that number to every PR-body and fix-comment claim. Prefer generated summaries or assertions over manually maintained counts so adding four probes cannot accidentally turn “19” into “20.”

If code moved from full-corpus to projection-directed loading, or probe counts changed, update the PR body before final review and include the live body in the immutable packet. A metadata-only correction on an unchanged head can use the narrow metadata path defined in the umbrella skill; code-contract defects still require a builder cycle or explicit exception.
