# Additive Export Refactor Parity Verification

Use when a refactor is required to preserve all existing exported data while adding one narrow table/field/artifact.

## Verification pattern

1. Build the export from an untouched base checkout/worktree.
2. Build the export from the exact PR head in a separate checkout/worktree.
3. Enumerate every pre-existing table or artifact surface explicitly; do not infer preservation from aggregate row counts.
4. For each legacy SQLite table:
   - compare `PRAGMA table_info(table)`;
   - select every column in a deterministic order;
   - compare normalized complete row sets;
   - report base/head row counts as supporting evidence, not the primary assertion.
5. Assert the additive surface separately (expected schema, keys, rows, statuses).
6. Run the normal test suite too. The parity probe supplements tests; it does not replace them.
7. Verify generated databases stay ignored/uncommitted and the PR worktree is clean.

## Why counts are insufficient

Equal counts can hide changed values, dropped columns, null/default drift, reordered identifiers, or rows replaced one-for-one. Full schema + normalized row equality proves behavior preservation much more directly.

## Scope guidance

- Compare only surfaces promised to remain unchanged.
- Do not require byte-for-byte database equality: SQLite file layout, metadata, and insertion order can differ while logical contents are identical.
- If timestamps or generated IDs are intentionally nondeterministic, normalize only those documented fields and state the exception explicitly.
- Run from exact base and PR heads; stale local artifacts are not evidence.
