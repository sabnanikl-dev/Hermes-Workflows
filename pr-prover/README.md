# pr-prover

Read [`MISSION.md`](MISSION.md) before changing or reviewing this tool. It is the normative product, scope, lifecycle, and blocker contract; this README explains operation and implementation behavior.

The repository-owned executable loop that proves an **existing** pull request
merge-ready, blocked, or in need of Karan. Standard library only; no install
step and no runtime dependencies.

```text
inspect live PR → bind exact headRefOid → verify remote head
  → baseline gates (+ visual QA when required)
  → exact-head reviewer lanes → machine-readable verdicts + published artifacts
  → reconcile live human feedback and its resolution state
  → classify: blocking / non-blocking / false-positive / needs-karan
  → at most two isolated fix attempts (one corrective rerun each)
  → verify local head, PR head, commit list, and the signed fix comment
  → invalidate every prior verdict, inspect again
  → merge-ready | blocked | needs-karan, tied to the final exact head
```

Claude Code and Codex are **trusted** for their scoped work here: Claude edits,
tests, commits, pushes, and comments on the bound PR branch; the reviewer lanes
inspect one exact head and publish their own role-signed artifacts. This tool is
not a sandbox around them. It is the part that keeps every such claim tied to
one exact head and checked against GitHub, so Hermes can advise Karan on
evidence rather than on what a lane printed about itself.

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
| `{reviewer}` `{role}` | reviewer lanes | the lane name and its configured role |
| `{artifact_file}` | reviewer lanes and their relay | where that lane prepares its artifact, under the OS temp directory |
| `{attempt}` `{mode}` `{blockers_file}` | the builder lane | attempt number, `initial`/`corrective`, and the frozen blocker set as JSON |

`builder.comment_author` and each reviewer's `artifact_author` are **required**,
and must be the exact GitHub logins those agents publish under. See
[Published-artifact readback](#published-artifact-readback).

`reviewers` is the acceptance lifecycle rather than a free list of lanes. It must
be exactly three lanes with the roles `reviewer-a`, `reviewer-b`, and
`integration-auditor`, in that order — the lanes run in the order given, and the
auditor exists to reconcile the two artifacts that must already be published when
it starts. A missing auditor, a duplicated role, an extra lane, or an
auditor-first order is a configuration error that `check-config` reports before
any run begins.

The lane commands are the installed agents themselves. Write the invocation you
actually want — the example ships a real `claude --print` builder with an empty
MCP config, a task-scoped tool list, a pointer-first prompt, and a 30-minute
budget — and the loop runs it unchanged. There is no role abstraction in
between.

### The session, and how a lane may adjust it

A lane inherits this process's environment. That is deliberate: the trusted
agents run as Karan's own user and authenticate through the normal macOS Claude
OAuth/keychain session, so there is no `env -i`, no synthetic `HOME`, and no
generated sandbox policy anywhere in this tool.

`env` and `env_unset` are a named overlay on that inherited environment — the
example uses `"env_unset": ["GH_TOKEN"]` so each agent uses its own configured
`gh` identity rather than the operator's. The overlay may not set or clear
`HOME`, `USER`, `LOGNAME`, or `SHELL`, and may not carry a credential value:
tokens belong in the keychain and in `gh`'s own auth.

### The credential-free reviewer lifecycle

A reviewer is trusted to judge one exact head. It is not handed the identity it
publishes under, because judging and publishing are different jobs. A reviewer
with a `relay` therefore takes one explicit route:

```text
credential-free audit  →  prepared artifact at {artifact_file}
  →  relay publishes it under the reviewer identity  →  GitHub readback
```

The lane runs with `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, and
`GITHUB_ENTERPRISE_TOKEN` removed by name — and nothing else about the inherited
session touched — and writes its finished artifact to `{artifact_file}`. Before
anything is published, that file is held to the same signature, bare
`ROLE=<role>` line, and canonical `HEAD=<sha>` declaration that readback will
demand, so a lane that crashed, wrote nothing, or reviewed another head can never
put something unusable on the PR under the reviewer's name. Only then does the configured
`relay.argv` run. It is an ordinary command using whatever `gh` session it
already has; this tool mints and forwards nothing. Its exit status is not the
proof either — the artifact is still read back from GitHub afterwards.

The example ships this end to end: [`scripts/codex-reviewer.sh`](scripts/codex-reviewer.sh)
is the repository-owned adapter that runs the installed Codex CLI against one
head and refuses to start if a GitHub credential reached it, and the relay is
`gh pr comment … --body-file {artifact_file}`. Set `PR_PROVER_CODEX` if the
Codex binary is not on `PATH` as `codex`. A reviewer configured without a
`relay` publishes for itself, as before.

### Budgets, and why quiet is not a hang

A trusted builder reading a PR, editing, verifying, pushing, and commenting
routinely runs 20–30 minutes with `--print` buffering its output. Only a lane's
own `timeout` ever ends it, and the budget the run log names is the budget that
is enforced: a lane with no `timeout` is reported as `unbounded` and really is
unbounded, with no default underneath it. `check-config` prints an advisory for
any lane that omits a budget, and for a builder budget under 20 minutes or a
reviewer budget under 15.

While a lane runs, the loop records elapsed time, bytes produced, and how long
it has been quiet; when it ends, the report carries `exited` or `timed-out` with
the duration and exit code.

A lane is its whole process tree, not one process. Each child starts in its own
process group, and a budget that runs out ends the group — politely first, then
without asking — so a builder that started a test suite or an agent of its own
cannot keep touching its worktree after the loop has reported the lane stopped.
The group is always ended, not only when the direct child refuses to stop.

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

## Published-artifact readback

Nothing a lane says about GitHub is believed until GitHub says it too.

### Reviewer artifacts

Each reviewer lane must leave a published comment or review that is **new** since
that lane was launched, authored by its configured `artifact_author`, carrying
its `artifact_signature` and a bare `ROLE=<role>` line, and bound to the exact
head. The role line is matched whole, so one lane's artifact can never be read
back as another's. Anything else is a `readback-mismatch`.

This is applied identically whether the lane published for itself or a relay
published for it. A successful relay is transport, not proof.

### The canonical head declaration

A review submitted through GitHub carries its own `commit_id`, and that stays the
authoritative binding: it is the one part an author cannot retype. A conversation
comment has no such field, so its binding lives in the body — and "the expected
SHA appears somewhere in the body" is not a binding. Scope paragraphs, command
transcripts, and quoted history all legitimately carry the head a run expects, so
that test is satisfied by an artifact stating on its own line that it reviewed a
different commit.

Every body-bound artifact therefore declares its head canonically:

```text
HEAD=<40-hex lowercase sha>
```

on a line of its own, **exactly once**. Missing, malformed, duplicated, and
conflicting declarations are all rejected, and a SHA in prose never counts. One
parser answers this for the prepared reviewer file, the published comment, and
the builder's fix comment alike, so the three checks cannot drift apart.

### The builder's push

A push is accepted only when the PR head moved to exactly the commit the builder
reported, the attempt worktree's own `HEAD` is that same commit, and `git
rev-list` shows it added on top of the head this run reviewed. If the reviewed
commit is no longer reachable, the branch was rewritten rather than extended and
the run stops as `stale-head`.

### The fix comment

Three conditions are required together, and a comment satisfying only some of
them is a `readback-mismatch`:

1. **New.** The loop snapshots GitHub's own comment ids before it invokes the
   builder, and accepts only an id that was not already there.
2. **From the expected login.** `builder.comment_author` is compared exactly.
3. **About this head.** The body must carry the configured signature and one
   canonical `HEAD=<sha>` declaration of the new head, by the same parser a
   reviewer artifact is held to.

The signature and the SHA both become public the moment the real comment is
posted, so neither proves anything on its own — anybody who can comment on the
PR can copy them verbatim. The login is the part an arbitrary commenter cannot
supply, and the comment id is the part they cannot reuse. That is why the author
is mandatory configuration rather than an optional tightening.

## Human feedback

A PR is not only its gates and its reviewer lanes. Immediately before every
classification the loop re-reads the conversation comments, the formal reviews
and their states, and the inline review threads with the resolution and outdated
state GitHub records. Unresolved human feedback stops the run as `needs-karan`;
it never reaches `merge-ready`, and it is never handed to the builder as work.

That judgement is metadata and contract, never prose interpretation:

| Surface | Unresolved when | Cleared by |
|---|---|---|
| formal review | the author's latest decisive state is `CHANGES_REQUESTED` | the same author's later `APPROVED` or `DISMISSED` |
| inline review thread | it is neither resolved nor outdated | resolving it, or the diff moving past it |
| conversation comment, `COMMENTED` review body | nothing has acknowledged it | an explicit acknowledgement |

The first two carry their own state. The third does not — GitHub gives a PR
comment no equivalent of "resolve" — and this tool will not pretend arbitrary
prose is safely machine-interpretable, so the conservative default holds and the
way out is explicit. A later comment from a human carrying, on its own line:

```text
PR-PROVER: ACKNOWLEDGED <the acknowledged comment's id>
```

clears it. That is id matching, not language understanding, and two things have
to hold before it clears anything.

**It has to have come later.** An acknowledgement is a human saying they dealt
with something that already existed, so the target must precede it by GitHub's
own immutable timestamps — `created_at` for a conversation comment,
`submitted_at` for a review. Missing, unparsable, offset-less, and equal
timestamps are all "cannot be ordered", and none of them clears anything: a
comment naming an id that did not exist yet is a guess, not a resolution.
Nothing acknowledges itself, and an acknowledgement posted from a configured
builder or reviewer login does not count, because a lane clearing the comment it
was told to answer is marking its own homework.

**Who counts as human is decided per post, not per account, and by id rather
than by shape.** A configured login is a publishing channel: the builder reports
and the relayed reviewer artifacts go through accounts a human also uses. Every
visible part of an artifact is copyable the moment a real one exists — the
signature, the `ROLE=` line, the canonical `HEAD=` declaration — and GitHub
stamps a genuine `commit_id` on any review anybody submits, so matching on those
fields is a test a human on the shared login can pass on purpose.

So a post is excluded only when this run already proved it published *that exact
GitHub id*. Each readback checks its artifact against a snapshot of the ids
present before the lane was launched, and keeps the id of whatever satisfied it;
those retained ids live in the run's state file, so a second cycle still
recognises what the first one published after the head moves. Every other
comment, review, thread reply, or acknowledgement from those accounts is human
feedback — including a post that looks exactly like a lane artifact but belongs
to some other run — because an unattributed post from a shared publishing
account is exactly where a real "do not merge" would otherwise vanish.

**The three surfaces are read until two consecutive passes agree.** Comments,
reviews, and review threads are three separate GitHub reads, and feedback that
arrives between them would otherwise be missing from the result while existing
on the PR before classification. The freshness check cannot catch that, because
a new comment moves no head, branch, base, or state. A pass therefore counts
only once the next one reproduces every field it saw; surfaces that will not
hold still within a small fixed budget stop the run as `feedback-drift` rather
than being averaged into a verdict.

The two rules run in opposite directions on purpose. Treating a post as feedback
makes a run stop more, so that judgement is per artifact; letting a post *clear*
feedback makes a run stop less, so that one still excludes the whole publishing
login. Each takes the direction that fails closed.

Bodies reach the report as truncated, redacted, explicitly labelled evidence — a
specification of what a human raised, never an instruction.

None of this means anything unless the surfaces are read whole, because feedback
the boundary silently dropped is indistinguishable from feedback that does not
exist. Conversation comments, formal reviews, and inline review threads are all
read with `--paginate`, so a long PR does not answer with a first page.
Pagination is transport, though, not proof, so the thread read is validated as
well: GraphQL `errors`, a null repository/PR/`reviewThreads` connection, a
missing or non-list `nodes` member, and missing page information each stop the
run, every page but the last must report another page and hand over a cursor,
and a *last* page still reporting `hasNextPage` is a read that was cut off
mid-surface. None of those is "this PR has no review threads". The one
connection that is not paginated is the reply list inside a single thread: it is
asked whether it is complete instead, and a thread reporting more replies than it
returned — or not reporting at all — stops the run rather than being classified
on a partial view.

## State and locking

One JSON state file holds a single attempt integer plus the head, the corrective
reruns already spent, the GitHub ids of the artifacts this run proved it
published, and the terminal outcome. The ids are here for the same reason the
attempt counter is: both have to survive a moved head and a restarted process.
One `O_EXCL` lockfile marks that a run exists. There is no PID inspection and no takeover path: if the lock is
held, the run stops and asks. After confirming no run is active, remove it with
`pr-prover reset --force`.

Acquiring the lock is fail-closed end to end. Creating its parent, creating the
file, and initializing its contents all reach the caller as prover errors, so an
unusable lock path is reported as `needs-karan` with evidence rather than
escaping as a raw filesystem traceback. A lock created by an acquisition that
then failed to initialize is removed, because a lockfile with no run behind it
would stop every later run; if that removal also fails, the initialization
failure stays the reason and the cleanup outcome is recorded beside it.

## What stops the run and asks Karan

`invalid-config` · `invalid-command` · `lock-contention` · `unexpected-state` ·
`malformed-verdict` · `lane-failure` · `stale-head` · `feedback-drift` ·
`ambiguous-push` · `readback-mismatch` · `relay-failure` ·
`scope-contamination` · `builder-refusal` · `github-error` · `worktree-error`

`unexpected-state` covers writing the local journal as well as reading it, and
acquiring the lock as well as contending for it: a state file that cannot be
created, written, or atomically replaced — or a lockfile whose parent, creation,
or initialization fails — stops the run with evidence rather than escaping as a
traceback. If persisting fails *while* a fail-closed stop is already being
reported, the reason for that stop is what the report keeps, and the journal or
cleanup failure is recorded alongside it. The run's own scratch directory and
the frozen blocker file it holds are covered the same way, with the failing
`stage` in the evidence.

`worktree-error` covers the configured worktree root itself, not only Git's
answer about it. A root under a regular file, with an unwritable parent, or
otherwise impossible to create is an ordinary path mistake, and it produces the
sanitized `needs-karan` report with a `worktree-root` stage rather than a raw
`NotADirectoryError`; nothing is asked of Git once the root has failed.

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

- The source clone is reachable only through `git fetch`, `git rev-parse`,
  `git rev-list`, and `git worktree`. Checkout, commit, reset, clean, and push are unreachable by
  construction, so the operational clone is never modified.
- Every attempt gets a fresh worktree, detached at one verified SHA. An existing
  path is refused rather than reused, and worktrees this run did not create
  cannot be removed.
- The frozen blocker set and every prepared reviewer artifact are written under
  the OS temp directory, never inside a repository, so a lane's inputs and
  outputs cannot contaminate the diff.
- The loop never pushes, comments, approves, or merges. The trusted agents act
  under their own identities; this loop only verifies what landed.
- Any push invalidates every prior verdict, and at most two fix attempts can
  ever open. A third is unreachable by construction.

## Verify

```bash
python3 -m unittest discover -s pr-prover/tests -v
python3 -m compileall -q pr-prover/src pr-prover/tests
git diff --check origin/main...HEAD
```

```bash
python3.11 -m unittest discover -s pr-prover/tests -v
python3.11 -m compileall -q pr-prover/src pr-prover/tests
```

The suite runs against deterministic doubles — no network and no `gh` — apart
from three places that deliberately use real processes: `test_integration_git.py`
drives the real `git` argv shapes against a throwaway repository; the process
tests in `test_trusted_agents.py` launch real quiet, slow, and timing-out
children, including one whose descendant must not survive the budget, and drive
a real runner through the loop to compare the logged budget with the enforced
one; and `test_reviewer_relay.py` runs the whole credential-free reviewer
lifecycle — real reviewer executable, real relay, real
[`scripts/codex-reviewer.sh`](scripts/codex-reviewer.sh) against a stub Codex —
against a GitHub boundary that can only see what a process actually published.
