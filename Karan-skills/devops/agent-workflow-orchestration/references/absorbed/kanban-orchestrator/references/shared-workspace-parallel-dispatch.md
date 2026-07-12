# Shared Workspace Parallel Dispatch Pitfall

## Session signal
During the PAPI-28 through PAPI-32 Kanban pilot, multiple `builder` tasks were created as independent ready tasks against the same persistent Git repo workspace:

`dir:/Users/creator/projects/papi-ops-execution-harness-template`

The dispatcher spawned them concurrently. They completed, but local commits overlapped: one task's commit included sibling task changes, a reviewer flagged a stale AC-status row, and a follow-up builder task was required.

## Rule
Do not fan out repo-mutating tasks to the same `dir:<repo>` workspace unless writes are explicitly coordinated.

## Safer task graph patterns

1. **Dependency chain**
   - `preflight template update` → `evidence template update` → `metrics template update` → `post-run review update` → `review`.
   - Best when all tasks modify one repo/branch.

2. **Worktree fan-out**
   - Give each mutating task a separate Git worktree/branch.
   - Use one integration/review task to merge or cherry-pick.

3. **Scratch fan-out + integrator**
   - Researchers/builders produce patches, file drafts, or recommendations in `scratch`.
   - One integrator applies accepted changes in the real repo.

4. **Read-only parallelism**
   - Parallel tasks can share a `dir:` workspace if they only inspect files and write outputs to separate non-overlapping paths.

## Pre-dispatch check
Before creating parallel tasks, compare:

- `workspace_kind`
- `workspace_path`
- whether each task mutates files/commits
- branch/PR expectations

If two ready tasks share the same persistent repo path and both mutate, add dependencies or change workspace strategy.
