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
  → agree marker + PR head + remote head + commit list + worktree HEAD
  → read the signed fix comment back from GitHub
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

`builder.comment_author` is **required** and must be the exact GitHub login the
builder comments under. See [Fix-comment readback](#fix-comment-readback).

`state_file` and `lock_file` must resolve **outside** `source_repo`, and a path
equal to or nested inside the clone is a configuration error. The run writes both
while it is also asserting that the operational clone is never modified and that
an attempt worktree is clean, so a control file living in that clone would
contaminate the very tree being judged. Siblings and any other outside path are
unaffected; `worktree_root` is held to the same rule where worktrees are created.

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

### The marker is not the whole verdict

A lane's exit status and its printed marker must agree, so parsing a marker is
never on its own enough to accept a result:

| Process result | Verdict | Outcome |
|---|---|---|
| timed out | anything | **`lane-failure`** — the marker is not read at all |
| exit ≠ 0 | reviewer `STATUS=pass` / builder `STATUS=success` | **`lane-failure`** |
| exit 0 | reviewer `STATUS=pass` / builder `STATUS=success` | accepted |
| exit ≠ 0 | reviewer `STATUS=fail` / builder `STATUS=failure` | **accepted and preserved** |
| exit 0 | reviewer `STATUS=fail` / builder `STATUS=failure` | accepted |

The last-but-one row is deliberate. A timed-out lane produced a truncated
stream, and a truncated stream can end on a marker the lane never meant as
final — so a timeout always fails closed, whatever it claimed. But a lane that
exits nonzero *while printing a valid failing verdict* is doing the normal
thing: reviewers and builders conventionally exit nonzero to mean "I found
blockers" or "I could not finish". Treating that as an infrastructure error
would discard exactly the findings the frozen blocker set is built from, so
that lane is preserved and keeps reporting.

Baseline and visual gates are unchanged: a gate that fails *or* times out
becomes a blocking finding rather than stopping the run.

## Freshness

Gates and reviewer lanes take minutes to hours, and nothing stops a push, a
close, or a retarget while they run. One reusable assertion re-reads the live
PR and the verified remote branch **immediately before every terminal outcome
and immediately before a fix attempt opens**, and requires all of the PR number,
`OPEN` state, head branch, base branch, and full 40-hex head SHA to still match
the snapshot the work was measured against. Any difference is `stale-head`: the
run reports nothing and spends no attempt on a head that has already moved.

## Push agreement

A builder's push is accepted only when five independent views of it agree:

| View | Where it comes from | What it alone cannot prove |
|---|---|---|
| the `DONE:` marker | the builder lane's own output | anything — it is a claim |
| the live PR head | `gh pr view` after the lane exits | that *this* attempt caused it |
| the remote branch head | `git fetch` + `rev-parse` in the source clone | that *this* attempt caused it |
| the PR commit list | `gh pr view --json commits` | that *this* attempt caused it |
| the attempt worktree's local `HEAD` | `git rev-parse HEAD` in that exact worktree | that the push reached GitHub |

The last row is the one an outside actor cannot move. An unrelated push to the
branch shifts the PR head, the remote head, and the commit list together, so
those three agreeing says only that *someone* pushed. A clean `git status`
does not close the gap either: a worktree that committed nothing is clean too.
So the attempt worktree's own `HEAD` is read explicitly and must equal the head
that landed — a builder that pushed from somewhere else, or a worktree left
sitting on the pre-attempt commit, is `stale-head` and the run stops rather than
crediting the attempt with work it cannot account for.

## Fix-comment readback

After a push is bound to exactly one new head, the builder's fix comment is read
back from GitHub. Three conditions are required together, and a comment
satisfying only some of them is a `readback-mismatch`:

1. **New.** The loop snapshots GitHub's own comment ids before it invokes the
   builder, and accepts only an id that was not already there.
2. **From the expected login.** `builder.comment_author` is compared exactly.
3. **About this head.** The body must carry both the configured signature and
   the new 40-hex SHA.

The signature and the SHA both become public the moment the real comment is
posted, so neither proves anything on its own — anybody who can comment on the
PR can copy them verbatim. The login is the part an arbitrary commenter cannot
supply, and the comment id is the part they cannot reuse. That is why the author
is mandatory configuration rather than an optional tightening.

## State and locking

One JSON state file holds a single attempt integer plus the head, the corrective
reruns already spent, the terminal outcome, and the phase of the run. One
`O_EXCL` lockfile marks that a run exists. There is no PID inspection and no
takeover path: if the lock is held, the run stops and asks.

### An interrupted attempt cannot be resumed into a clean result

A fix attempt is not over when the builder exits — the push still has to be
bound to one new head and the signed fix comment still has to be read back. The
state file records `phase: "attempt-in-flight"` together with the pre-attempt
head **before** the builder is invoked, and clears it only once that verification
passes.

So a run killed anywhere in that window restarts holding explicit proof that it
owes work. It stops as `unexpected-state` before its first GitHub read, and the
recorded head is left exactly as the interrupted attempt wrote it — the loop
never re-inspects, rebinds itself to whatever head is live by then, and reports
`merge-ready` for a push nothing verified. Confirm on the PR what that attempt
actually did, then `pr-prover reset` before running again.

### Reset refuses before it deletes

`pr-prover reset` removes the state file; `--force` also removes the lockfile.
An unforced reset that finds a lock decides the refusal **first** and removes
nothing at all: a held lock may mean a run is still in flight, and its state file
is the only record of which attempt it is on and what verification it owes.
After confirming no run is active, `pr-prover reset --force` discards both.

### Persistence fails closed

Every filesystem step behind the state file — creating the parent, writing the
temporary file, replacing the real one — is translated into `unexpected-state`
with the stage that broke, and lockfile creation and release into
`lock-contention`. An unusable control path (`/dev/null/state.json` and its
relatives) is therefore a `needs-karan` report with evidence, never a traceback
out of `ProverLoop.run()`. When the run is already stopping for another reason
and *recording* that stop is what fails, the original reason is what gets
reported; the save failure is noted in the run log rather than replacing it.

## What stops the run and asks Karan

`invalid-config` · `invalid-command` · `lock-contention` · `unexpected-state` ·
`malformed-verdict` · `lane-failure` · `stale-head` · `ambiguous-push` ·
`readback-mismatch` · `scope-contamination` · `builder-refusal` ·
`github-error` · `worktree-error`

Each carries evidence, and the worktree plus scratch directory are retained so
the failure can be inspected.

Redaction happens twice. Output captured from a child is scrubbed of
credential-shaped text where it is captured, and then the assembled report —
JSON and Markdown alike — passes through one recursive sanitizer at
serialization. That final boundary walks nested dicts, lists, and tuples and
scrubs every string in them, keys included, so a value that reached the report
without being scrubbed at its call site still cannot leak. Structure and scalar
types survive the walk, so the report stays readable and machine-usable rather
than being flattened into one stringified blob; depth and self-reference are
bounded with explicit markers.

## Isolation guarantees

- The source clone is reachable only through `git fetch`, `git rev-parse`, and
  `git worktree`. Checkout, commit, reset, clean, and push are unreachable by
  construction, so the operational clone is never modified.
- Every attempt gets a fresh worktree, detached at one verified SHA. An existing
  path is refused rather than reused, and worktrees this run did not create
  cannot be removed.
- The frozen blocker set is written under the OS temp directory, never inside a
  repository, so a builder's inputs cannot contaminate the diff.
- The state file and the lockfile must live outside the operational clone, so
  this run's own bookkeeping can never show up as a change to the tree it is
  judging.
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
