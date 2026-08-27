# Hash-Frozen Generated-Report Review

Use this reference when reviewing a generated report whose producer can rewrite canonical output, or when a conclusion depends on captured official documentation.

## Candidate containment

1. Generate and validate the report **before** review.
2. Record artifact path, SHA-256, byte count, and line count.
3. Record hashes of every supporting evidence file the report cites.
4. Make the candidate and its evidence read-only for the review window when practical.
5. Give reviewers an explicit command allowlist: file readers, searches, hashes, and proven read-only Git inspection only.
6. Forbid project entrypoints, imports with top-level behavior, package scripts, and `--help` probes in the canonical checkout. A CLI that appears informational may still execute generation.
7. Run producer discovery or reproduction only in a disposable copy/worktree. Compare resulting hashes rather than letting reviewers regenerate canonical bytes.
8. Re-hash the candidate after each reviewer finishes. Any drift supersedes that packet, regardless of the reviewer’s verdict.

Filesystem read-only mode is defense in depth, not the authority boundary: the file owner may be able to chmod it back. The reviewer contract and post-review re-hash remain mandatory.

## Delayed packet adjudication

When asynchronous reviews return out of order:

- Compare each packet’s expected/computed hash to the current candidate.
- Treat findings from stale bytes as leads: verify whether each finding survives in current bytes.
- Never use a stale PASS as acceptance.
- Do not dismiss a stale FAIL solely because it is late; repair surviving material findings and dispatch a fresh review.
- Record superseded hashes and why their verdicts are non-authoritative in the acceptance sidecar.

## Official-source negative claims

A current reference/enum page proves current definitions, not historical stability. For claims such as “no documented metric-definition change was found”:

1. Capture the dated official reference page and official changelog/release history.
2. Preserve the source URLs, capture date, byte sizes, and SHA-256 values in an in-repo provenance sidecar.
3. Keep a readable text extraction when the authoritative capture is large HTML/PDF.
4. Link every capture and hash from the report.
5. State what the captured changelog *does* document.
6. Phrase absence conservatively: “the captured official changelog records no X change; undocumented or differently documented changes are not ruled out.”
7. Never use temporary paths as final evidence locators.

## Acceptance and commit sequencing

1. Review exact candidate bytes first.
2. After PASS, create a separate acceptance sidecar; do not edit the accepted report to announce acceptance.
3. Bind the report hash, evidence hashes, reviewer markers, frozen blocker closure, authority boundaries, and superseded packets in the sidecar.
4. Re-hash the report after writing the sidecar.
5. Stage from an explicit path list; never use broad staging.
6. If a dry-run path list includes the not-yet-created sidecar, expect path resolution to fail. Dry-run existing candidate paths first, then create the sidecar after PASS and dry-run the complete list.
7. Exclude unrelated untracked files explicitly and verify the committed path set after commit.
8. Only then reconcile tracker criteria/comments/state with direct readback.

## Minimal reviewer prompt clause

> READ-ONLY: do not execute project producers or entrypoints, do not use `--help`, and do not import project modules in the canonical checkout. Use only byte-safe readers, hashes, searches, and proven read-only Git inspection. Independently bind the expected candidate/evidence hashes. Report `DONE: STATUS=pass|fail P0=n P1=n P2=n`. Files modified: none.
