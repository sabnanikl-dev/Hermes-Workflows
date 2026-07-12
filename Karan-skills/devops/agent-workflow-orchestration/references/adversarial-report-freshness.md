# Adversarial report freshness for scheduled scouts

Use when a scheduled repo-local scout has a required read-only reviewer/adversarial report, especially if the report is generated outside the repo and may lag behind current `HEAD`.

## Pattern

1. Read the report as reviewer input, not source of truth.
2. Extract only safe metadata into the scout/context packet:
   - report present/readable;
   - generated timestamp;
   - reviewer decision (for example `BLOCK_PUBLIC_LAUNCH`);
   - report commit/HEAD when available;
   - current repo `HEAD`;
   - stale-vs-current boolean;
   - P0/P1 finding counts;
   - short guidance such as “stale relative to current HEAD; re-check live repo state before acting.”
3. Do **not** copy raw reviewer prose into buyer-facing docs, NotebookLM prompts, issues, or repo context packets.
4. If stale, treat findings as hypotheses to verify against current files. Do not keep fixing already-resolved findings.
5. If fresh and P0/P1 findings exist, prioritize unresolved repo-local, buyer-useful, in-authority fixes before ordinary polish.

## Verification fixture

Use an ad-hoc temp script that imports the changed context/audit module and monkeypatches the report path to three fixtures:

- **fresh green:** report HEAD matches current `git rev-parse HEAD`; metadata shows `stale_vs_current_head=false`, correct P0/P1 counts, and raw sentinel prose is absent from JSON output.
- **stale red:** report HEAD differs from current HEAD; metadata shows `stale_vs_current_head=true` and guidance names staleness.
- **missing safe path:** missing report returns `present=false` with safe fallback guidance.

When a post-commit verifier asks for fresh evidence, generate a new `tempfile.mkstemp(prefix="hermes-verify-", suffix=".py", dir=<requested-dir>)`, print a unique `RUN_ID`, run the fixture, delete the temp script, and print `TEMP_SCRIPT_EXISTS_AFTER_CLEANUP=False`.

## Pitfall

Do not assert optional metadata keys by indexing them in missing/error cases. Use absence checks such as `'stale_vs_current_head' not in result` or `result.get('stale_vs_current_head') is None`; otherwise the verifier can fail with `KeyError` even when the production behavior is correct.
