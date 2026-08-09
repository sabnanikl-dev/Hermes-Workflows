# Run-Scoped Prepared Artifact Hygiene

Prepared reviewer bodies are evidence slots. A reusable `/tmp/reviewer-a-body.md` can already contain a valid-looking artifact from another PR, head, role, or attempt. A child may append to it, partially rewrite it, or fail after leaving the stale body available to the parent.

## Preferred naming

Derive the path from immutable run identity:

```bash
ROLE=reviewer-a
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
ARTIFACT="/tmp/pr-prover-pr${PR}-${HEAD}-${ROLE}-${RUN_ID}.md"
test ! -e "$ARTIFACT"
```

Record the exact path in both the frozen packet and child prompt. Do not discover the artifact afterward by globbing for “the newest” file.

## Static-path fallback

When a wrapper requires a static path:

1. inspect whether the path exists;
2. preserve an old body only if it is needed as historical evidence, under a different immutable name;
3. remove the static path in the parent;
4. prove absence immediately before launch;
5. capture the child launch timestamp and expected PR/head/role.

The barrier is pre-launch absence. A child successfully rewriting an old file is not equivalent evidence.

## Post-exit validation

Before relay, verify:

- the path exists and is a regular file;
- it was created or changed during the current child process window;
- it names exactly the expected PR, full head SHA, role, model, reasoning level, verdict, and blocker count;
- no old PR number/SHA/role/signature remains;
- exactly one canonical standalone `ROLE=`, `HEAD=`, `STATUS=`, and `BLOCKING=` line exists;
- the body verdict matches the child's final `DONE:` marker;
- the detached reviewer worktree is still clean at the expected head.

Treat a mismatch as an incomplete reviewer lane. Do not “repair” substantive child output in the parent. Parent edits are limited to disclosed transport metadata that does not alter findings or verdict.

## Retention

Retain the validated body through relay and direct readback. After the immutable GitHub artifact ID and readback hash are recorded, remove or archive local artifacts according to the run's evidence policy. Never reuse the same path as an implicit handoff between heads.
