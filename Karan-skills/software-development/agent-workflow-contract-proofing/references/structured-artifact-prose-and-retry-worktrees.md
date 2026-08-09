# Structured artifact parsing and retained-worktree retries

Use when a reviewer artifact appears to report a finding from narrative text, or when `reset` followed by a retry collides with retained evidence.

## Artifact boundary

- Headers and complete machine records are authoritative. A finding record is a complete line: `FINDING: SEVERITY=<severity> ID=<id> -- <summary>`.
- Headings, narrative, command output, and identifier-like words are not findings. A prose heading such as `FINDING: stale-pr-evidence` must not create a finding or a relay-parity failure.
- Do not solve this by weakening proof: malformed structured records, `STATUS`/`BLOCKING` contradictions, marker-count disagreement, exact-head mismatch, publication failure, and readback failure remain fail-closed.

## Canonical verdict → relay normalization

Use this when a reviewer’s final verdict has valid `FINDING:` records but its
prepared artifact is missing them. This is a generic transport defect, not a
project-validator rule.

1. Treat the parsed final verdict as canonical. Do not ask the model to recreate
   the same structured records in a second file.
2. Validate the prepared artifact’s role/head/status/blocking/signature and its
   prose as before. It may contain zero structured finding records.
3. If it includes any complete or malformed machine-shaped `FINDING:` line, run
   the existing canonical parser and fail closed unless its records exactly match
   the final verdict. Do not silently reconcile conflicts.
4. Build the publication copy by removing any validated duplicate artifact
   records and appending a deterministic render of the final verdict’s records.
   Then apply normal redaction, size/grammar validation, transport, and GitHub
   readback against those canonical records.
5. Preserve clean pass/no-finding artifacts byte-for-byte except for ordinary
   redaction; do not append an empty finding block.

Minimum regression matrix:
- final verdict has a blocker; prepared artifact has no records → relayed copy
  has exactly the final canonical record and ordinary A → B → Auditor flow runs;
- prepared artifact has matching records → publication contains one canonical
  copy, not two;
- missing/extra/conflicting/duplicated/malformed artifact records → fail closed;
- final verdict has no findings and prepared artifact has none → clean artifact;
- relay-side deletion or rewrite of canonical records → existing readback fails.

## Retry after terminal failure

1. Preserve a retained reviewer worktree as diagnostic evidence; do not delete it merely to start a retry.
2. A normal reset must refuse a held lock. Do not force reset or delete a lock until the run is proven inactive.
3. The retry must create a separate exact-head worktree with a fresh per-run opaque suffix. It must not reuse or collide with retained evidence.
4. Verify both that the retained worktree still exists and that normal exact-head/cleanliness checks ran in the new checkout.

## Regression proof

Test all of:
- a pass artifact with `STATUS=pass`, `BLOCKING=0`, and prose-only `stale-pr-evidence` / `redirect-wiring-substring` tokens, relaying with zero findings;
- valid explicit blocking records plus malformed or contradictory structured artifacts that still stop fail-closed;
- terminal relay failure retaining a clean exact-head reviewer worktree, then reset and successful fresh retry setup;
- reset preservation of unowned or ambiguous paths and refusal while a lock is held.
