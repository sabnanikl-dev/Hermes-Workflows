# pr-prover

The repository-owned executable loop that proves an **existing** pull request
merge-ready, blocked, or in need of Karan. Standard library only; no install
step and no runtime dependencies.

```text
inspect live PR → bind exact headRefOid → verify remote head
  → baseline gates (+ visual QA when required)
  → exact-head Reviewer A/B → machine-readable verdicts + artifact readback
  → classify: blocking / non-blocking / false-positive / needs-karan
  → at most two isolated fix attempts (one corrective rerun each)
  → verify push + read the signed fix comment back from GitHub
  → invalidate every prior verdict, inspect again
  → merge-ready | blocked | needs-karan, tied to the final exact head
```

This is **PAPI-88** (the loop) and **PAPI-90** (the hardened launchers and
credential scoping) of the
[control-surface contract](https://github.com/sabnanikl-dev/Hermes-Workflows/issues/1).
The slim SKILL.md router (PAPI-92) and the final qualification suite (PAPI-93)
are still pending.

## Run it

```bash
pr-prover/bin/pr-prover check-config --config /path/to/run.json
pr-prover/bin/pr-prover run          --config /path/to/run.json          # human report
pr-prover/bin/pr-prover run          --config /path/to/run.json --json    # machine report
pr-prover/bin/pr-prover reset        --config /path/to/run.json [--force]
```

Exit codes are the outcome: `0` merge-ready, `1` blocked, `2` needs-Karan
(including every fail-closed stop), `64` usage or configuration error.

Start from [`examples/run.example.json`](examples/run.example.json) for
launcher-composed agent lanes, or
[`examples/run.script-lanes.example.json`](examples/run.script-lanes.example.json)
for repository-owned lane scripts. Both are credential-scoped.

## Configuration

Every child command is an **argv array**. A script lane's template substitutes
only these tokens, and an unknown token fails the run rather than rendering
literally (an agent lane has no template: the launcher composes its argv):

| Token | Available to | Value |
|---|---|---|
| `{repo}` `{owner}` `{name}` `{pr}` | all lanes | from config |
| `{branch}` `{base}` `{head}` | all lanes | from the **live** PR, never from config alone |
| `{worktree}` | all lanes | the fresh worktree this lane runs in |
| `{reviewer}` | reviewer lanes | the lane name |
| `{attempt}` `{mode}` `{blockers_file}` | the builder lane | attempt number, `initial`/`corrective`, and the frozen blocker set as JSON |

`builder.comment_author` is **required** and must be the exact GitHub login the
builder comments under. See [Fix-comment readback](#fix-comment-readback).

Gates take `"kind": "baseline"` (default) or `"kind": "visual"`. Visual gates
run only when `visual_qa_required` is `true`; setting that flag without a visual
gate is a configuration error, so browser/visual QA is never silently skipped.

A reviewer or builder lane is **either** a repository-owned script (`argv`) or a
launcher-composed agent (`agent`). Declaring both is a configuration error:
two answers to "what command runs here" is exactly the ambiguity that fails
closed. An `agent` lane must name one `identity`.

## Launchers, identities, and credential scope

One broker launches every child. It builds the child's environment from nothing,
hands over at most the single scoped identity that lane owns, and — for an agent
lane — composes the whole argv array itself.

| Lane | Identity | May do | Tool maximum |
|---|---|---|---|
| gate | none | run repository commands | whatever the gate's argv is |
| reviewer A/B | `comment-pr`, `review-pr` | comment and review on the bound PR | `Bash Glob Grep Read TodoWrite` |
| builder | `push-branch`, `comment-pr` | push the bound branch, comment on the bound PR | `Bash Edit Glob Grep Read TodoWrite Write` |

The capability vocabulary is closed and has no merge, approval, deploy, or admin
form, so an identity that could merge cannot be *expressed*, let alone granted.

**Credentials are never in the config.** An identity names either a parent
environment variable (`token_env`) or an owner-only file (`token_file`) to read
one from at launch time. A source that is missing, empty, world-readable, or
holds more than one line fails closed.

**Every credential is verified before it is used.** The broker asks GitHub which
account the credential resolves to and what it may do on the bound repository,
using the environment the child is about to get. The login must match exactly;
`admin` or `maintain` — the permissions that merge and change branch protection
— are refused outright; a builder credential must be able to push and a reviewer
credential must not.

**The child environment is built from nothing.** Names are allowlisted, and
anything credential-shaped is denied by name — `GH_TOKEN`, `GITHUB_TOKEN`,
`SSH_AUTH_SOCK`, anything containing `TOKEN`/`SECRET`/`PASSWORD`/`API_KEY`, and
whole vendor prefixes (`JMD_`, `AWS_`, `VERCEL_`, `SANITY_`, `N8N_`, …) — so an
unfamiliar `ACME_DEPLOY_TOKEN` is refused without anyone enumerating it.
`launch.env_allow` can widen the allowlist only to names that are *not* denied;
`launch.model_auth_env` permits exactly one model-access variable by name and
can never name GitHub authority.

`HOME` is allowed, because the toolchain needs it — and on its own it is a hole,
since `gh` falls back to `~/.config/gh/hosts.yml` and `git` to `~/.gitconfig`
and the OS keychain. So every child also gets a launcher-written `GH_CONFIG_DIR`
and `GIT_CONFIG_GLOBAL` (with `GIT_CONFIG_SYSTEM=/dev/null`). Credential helpers
are cleared there; a lane that may push gets exactly one back — `gh`, which can
only offer the token the launcher injected — and a lane that may not push gets
none, so an attempted push fails for want of a credential rather than on trust.

### Launch discipline, in code

- **Empty MCP.** Every agent lane runs with `--strict-mcp-config` and an
  `--mcp-config` file the launcher wrote containing no servers.
- **Bounded tools.** `--tools` and `--allowedTools` come from the code-owned
  maximum for the role; configuration may only narrow them. Permission modes
  that dissolve the tool boundary are not configurable.
- **Bounded budget.** 20–30 minutes of wall clock. Outside that window the run
  stops rather than clamping quietly.
- **Quiet stdout.** Children are captured, never inherited; progress rendering is
  turned off by environment, and escape sequences and carriage-return rewrites
  are stripped from the captured stream before anything parses it.
- **Pointer-first prompts.** The prompt is owned by this repository and is not
  configurable. It names the bound repo, PR, branch, head, and login; points at
  the frozen blocker file rather than quoting it; states that PR bodies,
  comments, reviews, and issues are data and never instructions; lists what the
  child may never do; and states the exact final marker.
- **No authority-broadening flags.** The composed argv is re-scanned before
  launch, so a future edit that threads `--dangerously-skip-permissions`,
  `--add-dir`, `--settings`, or `--system-prompt` in from configuration fails
  closed instead of shipping.

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

The builder's `identity` and its `comment_author` must be the same account, or
the run would launch as one login and then accept a fix comment from another.

## Reviewer artifact readback

A reviewer lane bound to a scoped identity is held to the same standard as the
builder. Its printed verdict counts only once GitHub shows an artifact that is:

1. **New** — a review or comment id that was not there before the lane started;
2. **Under its own login** — the identity the launcher gave that lane, exactly;
3. **Bound to this exact work** — carrying the tag line

   ```text
   PR-PROVER-REVIEW: repo=<owner/name> pr=<number> role=<A|B> head=<40-hex sha>
   ```

   and, for a submitted review, matching the commit GitHub recorded it against.

Anything else is a `readback-mismatch`. A review of an older head cannot be
re-labelled into this one, and one reviewer's artifact cannot stand in for the
other's.

## State and locking

One JSON state file holds a single attempt integer plus the head, the corrective
reruns already spent, and the terminal outcome. One `O_EXCL` lockfile marks that
a run exists. There is no PID inspection and no takeover path: if the lock is
held, the run stops and asks. After confirming no run is active, remove it with
`pr-prover reset --force`.

## What stops the run and asks Karan

`invalid-config` · `invalid-command` · `lock-contention` · `unexpected-state` ·
`malformed-verdict` · `lane-failure` · `stale-head` · `ambiguous-push` ·
`readback-mismatch` · `scope-contamination` · `builder-refusal` ·
`github-error` · `worktree-error` · `identity-error` · `launch-policy`

`identity-error` covers ambiguous auth, the wrong account, and a credential that
holds more authority than its capabilities declare. `launch-policy` covers a
child environment that still carries something it should not, a lane launched
outside the run's worktree root, a budget outside the window, and any attempt to
broaden authority at launch time.

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
- The loop never pushes, comments, approves, or merges. The builder pushes and
  comments under its own identity; this loop only verifies what landed.
- Every child is launched in a worktree this run created, inside the configured
  worktree root; a lane pointed anywhere else is refused.
- No child environment carries merge, Karan-approval, JMD, deploy, client, or
  live-system credentials — including the operator's own `gh` login and the OS
  keychain, which are unreachable because `GH_CONFIG_DIR` and
  `GIT_CONFIG_GLOBAL` point at launcher-owned files.

## Verify

```bash
python3 -m unittest discover -s pr-prover/tests -v
python3 -m compileall -q pr-prover/src pr-prover/tests
git diff --check origin/main...HEAD
```

The suite runs entirely against deterministic doubles: no network, no `gh`, and
no real `git`.
