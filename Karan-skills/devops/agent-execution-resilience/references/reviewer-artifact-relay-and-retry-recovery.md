# Reviewer artifact relay and retry recovery

Use this reference when a prover/reviewer loop produces a valid-looking reviewer artifact but its parent relay fails, or when a terminal run leaves scratch worktrees that block a same-head retry.

## Artifact truth boundary

Treat only the declared machine contract as verdict/finding input:

- required `ROLE`, canonical full-SHA `HEAD`, and verdict/header fields;
- declared `BLOCKING` count;
- explicit, line-anchored finding records such as `FINDING: <id>`.

Never tokenize or pattern-match prose to manufacture finding IDs. A reviewer may legitimately write narrative such as “a non-blocking stale-evidence concern remains.” It is not a finding unless the artifact's machine contract declares one.

### Required parity checks

1. Parse explicit finding records with anchored syntax.
2. Require declared `BLOCKING` count to equal the explicit-record count.
3. For `STATUS=pass` and `BLOCKING=0`, require zero explicit finding records and relay the pass—even if the body mentions terms that resemble finding IDs.
4. For an actual block/fail verdict, require every declared finding to appear in the prepared artifact and to survive publisher/readback verification.
5. Fail closed on malformed/missing headers, duplicate or conflicting markers, head mismatch, record-count mismatch, or incomplete transport—not on prose alone.

### Regression fixtures

Keep fixtures for all of these cases:

| Case | Expected result |
| --- | --- |
| Pass headers, `BLOCKING=0`, prose says `stale-pr-evidence`, no `FINDING:` line | pass; zero findings |
| Block headers, `BLOCKING=1`, one anchored `FINDING: stale-pr-evidence` | block; finding parity required |
| Pass headers plus an explicit `FINDING:` line | malformed/contradictory; fail closed |
| Block headers with a missing or altered relayed finding | relay failure; no merge-ready result |

## Retryable retained worktrees

Evidence retention must not make the command's documented recovery path unusable.

### Safe strategy

Prefer a unique controlled worktree path per reviewer attempt/run, for example one derived from PR number, full/head prefix, reviewer role, and monotonic attempt/run token. Retain a failed run's evidence path, but allocate a new path on retry.

If cleanup is used instead, it must be narrowly gated:

1. Confirm no active process or lock owns the path.
2. Confirm the path is inside the prover-controlled worktree root after canonical path resolution.
3. Confirm expected repository identity and exact head.
4. Confirm a clean worktree.
5. Delete only that verified directory; never broad-prune a temporary parent.
6. Preserve the failed artifact/transcript separately or retain a path reference in terminal state.

Dirty, foreign, unexpected-head, outside-root, or active paths remain fail-closed and require operator review.

### Reset contract

`reset` must do more than delete state: after a completed/abandoned same-head run, a subsequent `run` must be able to allocate fresh lane workspaces without manual filesystem cleanup. Reset must not remove active locks or unverified evidence.

## Verification sequence

1. Run parser unit tests for the four artifact fixtures above.
2. Simulate a terminal relay failure that retains a clean exact-head worktree.
3. Reset state.
4. Start a same-head retry and prove a fresh worktree is allocated (or that narrowly verified cleanup occurred).
5. Simulate unsafe cleanup candidates—dirty, foreign repo/head, outside root, active lock—and prove they fail closed.
6. Run an installed-CLI smoke that prepares and relays a real pass artifact before using the full A/B/Integration triad.
