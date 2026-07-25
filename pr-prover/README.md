# pr-prover

The repository-owned executable loop that proves an **existing** pull request
merge-ready, blocked, or in need of Karan. Standard library only; no install
step and no runtime dependencies.

```text
inspect live PR → bind exact headRefOid → verify remote head
  → baseline gates (+ visual QA when required)
  → exact-head Reviewer A/B → machine-readable verdicts
  → classify: blocking / non-blocking / false-positive / needs-karan
  → at most two isolated fix attempts (one corrective rerun each)
  → verify push + read the signed fix comment back from GitHub
  → invalidate every prior verdict, inspect again
  → merge-ready | blocked | needs-karan, tied to the final exact head
```

This slice is **PAPI-88** of the [control-surface contract](https://github.com/sabnanikl-dev/Hermes-Workflows/issues/1).
The hardened launcher and credential scoping (PAPI-90), the slim SKILL.md router
(PAPI-92), and the final qualification suite (PAPI-93) are still pending.

## Run it

```bash
pr-prover/bin/pr-prover check-config --config /path/to/run.json
pr-prover/bin/pr-prover run          --config /path/to/run.json          # human report
pr-prover/bin/pr-prover run          --config /path/to/run.json --json    # machine report
pr-prover/bin/pr-prover reset        --config /path/to/run.json [--force]
```

Exit codes are the outcome: `0` merge-ready, `1` blocked, `2` needs-Karan
(including every fail-closed stop), `64` usage or configuration error.

Start from [`examples/run.example.json`](examples/run.example.json).

## Configuration

Every child command is an **argv array**. Templates substitute only these
tokens, and an unknown token fails the run rather than rendering literally:

| Token | Available to | Value |
|---|---|---|
| `{repo}` `{owner}` `{name}` `{pr}` | all lanes | from config |
| `{branch}` `{base}` `{head}` | all lanes | from the **live** PR, never from config alone |
| `{worktree}` | all lanes | the fresh worktree this lane runs in |
| `{reviewer}` | reviewer lanes | the lane name |
| `{attempt}` `{mode}` `{blockers_file}` | the builder lane | attempt number, `initial`/`corrective`, and the frozen blocker set as JSON |

The gate, reviewer, and builder commands themselves are supplied by the
operator — the example's `./scripts/*-lane.sh` names are placeholders. PAPI-90
replaces them with the hardened, credential-scoped launcher; until then the only
seam this slice needs is that every lane is an argv array and every lane's
verdict is machine-readable.

Gates take `"kind": "baseline"` (default) or `"kind": "visual"`. Visual gates
run only when `visual_qa_required` is `true`; setting that flag without a visual
gate is a configuration error, so browser/visual QA is never silently skipped.

## Lane contracts

A reviewer lane's last non-empty line must be exactly:

```text
DONE: STATUS=pass|fail BLOCKING=<count> HEAD=<40-hex sha>
```

with one line per finding above it:

```text
FINDING: SEVERITY=blocking|non-blocking|needs-karan ID=<slug> -- <summary>
```

The builder lane's last non-empty line must be exactly:

```text
DONE: PR=<number> BRANCH=<branch> STATUS=success|failure HEAD=<40-hex sha>
```

with one line per blocker it fixed:

```text
ADDRESSED: ID=<slug>
```

Parsing is unforgiving on purpose. Exactly one `DONE:` line may appear, it must
be the final non-empty line, the SHA must equal the bound head byte for byte,
and `BLOCKING=<count>` must reconcile with the findings above it. Lane output is
untrusted, so a body that quotes or forges a marker fails the run closed instead
of being read as a verdict.

## State and locking

One JSON state file holds a single attempt integer plus the head, the corrective
reruns already spent, and the terminal outcome. One `O_EXCL` lockfile marks that
a run exists. There is no PID inspection and no takeover path: if the lock is
held, the run stops and asks. After confirming no run is active, remove it with
`pr-prover reset --force`.

## What stops the run and asks Karan

`invalid-config` · `invalid-command` · `lock-contention` · `unexpected-state` ·
`malformed-verdict` · `stale-head` · `ambiguous-push` · `readback-mismatch` ·
`scope-contamination` · `builder-refusal` · `github-error` · `worktree-error`

Each carries evidence, and the worktree plus scratch directory are retained so
the failure can be inspected. Everything captured from a child is scrubbed of
credential-shaped text first.

## Isolation guarantees

- The source clone is reachable only through `git fetch`, `git rev-parse`, and
  `git worktree`. Checkout, commit, reset, clean, and push are unreachable by
  construction, so the operational clone is never modified.
- Every attempt gets a fresh worktree, detached at one verified SHA. An existing
  path is refused rather than reused, and worktrees this run did not create
  cannot be removed.
- The frozen blocker set is written under the OS temp directory, never inside a
  repository, so a builder's inputs cannot contaminate the diff.
- The loop never pushes, comments, approves, or merges. The builder pushes and
  comments under its own identity; this loop only verifies what landed.

## Verify

```bash
python3 -m unittest discover -s pr-prover/tests -v
python3 -m compileall -q pr-prover/src pr-prover/tests
git diff --check origin/main...HEAD
```

The suite runs entirely against deterministic doubles: no network, no `gh`, and
no real `git`.
