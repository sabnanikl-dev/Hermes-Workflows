# Parallel Lineage Synthesis

Use this only when a target window contains several large, independent root lineages and serial transcript reading would flood the parent context.

## Partitioning

- Assign each worker a non-overlapping set of root lineages.
- Give exact session IDs, timezone, exclusive cutoff, output budget, redaction rules, and read-only scope.
- For a lineage crossing the boundary, require message-level timestamp filtering; do not rely on the continuation's filename or session start/end.
- Tell workers to exclude subagents and copied continuation history already represented by the human-facing lineage.

## Worker Output Contract

Each worker should return compact bullets covering:

1. work or decision;
2. verification category;
3. cutoff-time state;
4. unresolved next step;
5. files mutated by the worker itself (normally none for read-only synthesis).

Avoid PR numbers, commit hashes, raw tool output, secrets, and exhaustive test counts unless the final artifact requires them.

## Parent Responsibilities

Worker summaries are secondary synthesis, not proof. The parent must:

- reconcile overlapping or contradictory claims;
- independently verify any artifact writes and current GitHub/Linear/file state before reporting success;
- combine workstreams into one draft;
- preflight the complete character count, not each worker's fragment;
- read back and validate the final artifact.

Do not delegate a small day: delegation overhead can exceed the value. Prefer direct inspection when there are only one or two short lineages.