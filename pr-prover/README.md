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

`builder.allowed_paths` is **required** too, and it is the contract a fix
attempt's *commits* are held to. See
[Committed changes stay in the packet](#committed-changes-stay-in-the-packet).
The vocabulary is small on purpose:

| Entry | Means |
|---|---|
| `src/thing.py` | exactly that path |
| `src/` | that directory and everything under it (the trailing slash is what makes it a directory rule) |
| `**` | the whole repository — only valid on its own, and only because the packet said so |

There is no other wildcard, no negation, and no regular expression. A missing or
unparsable `allowed_paths` fails the run: "the packet did not say" must never
come to mean "anything goes".

Gates take `"kind": "baseline"` (default) or `"kind": "visual"`. Visual gates
run only when `visual_qa_required` is `true`; setting that flag without a visual
gate is a configuration error, so browser/visual QA is never silently skipped.

A reviewer or builder lane is **either** a repository-owned script (`argv`) or a
launcher-composed agent (`agent`). Declaring both is a configuration error:
two answers to "what command runs here" is exactly the ambiguity that fails
closed.

**Every builder and reviewer lane must name one `identity`** — script lanes
included. A lane with no identity gets no capability channel, so it can neither
push nor post, and there would be no GitHub artifact to read its claims back
against. A configuration that omits one is refused with a migration error rather
than run in a weaker mode.

A script lane reaches GitHub exactly the way an agent lane does: through
`pr-prover-cap`, which the launcher puts first on the lane's `PATH`. A lane
script that calls `gh` or `git push` directly finds no credential and fails.

## Launchers, identities, and credential scope

One broker launches every child. It builds the child's environment from nothing,
opens the one narrow capability channel that lane is entitled to, and — for an
agent lane — composes the whole argv array itself.

| Lane | Identity | May ask the launcher to do | Tool maximum |
|---|---|---|---|
| gate | none | nothing; it has no channel | whatever the gate's argv is |
| reviewer A/B | `comment-pr`, `review-pr` | comment on, and file a COMMENT review against, the bound PR | `Bash Glob Grep Read TodoWrite` |
| builder | `push-branch`, `comment-pr` | push the bound branch, comment on the bound PR | `Bash Edit Glob Grep Read TodoWrite Write` |

### No child holds a credential

A capability is not a claim about a token; it is the list of operations the
launcher will perform on a lane's behalf. A child is given the path of a
launcher-owned unix socket (`PR_PROVER_CAPABILITY_SOCKET`) and one shim on its
`PATH`:

```text
pr-prover-cap push                       push this worktree's HEAD to the bound branch
pr-prover-cap comment --body-file FILE   post one comment on the bound PR
pr-prover-cap review  --body-file FILE   submit one COMMENT review on the bound PR
```

The shim carries no authority either. It serialises one request; the launcher,
on the other side, holds the scoped credential and composes each operation's
whole `git`/`gh` argv array from the bound repository, PR, branch, and head. A
request names an operation and, for the two that post text, a body — it cannot
name a repository, a pull request, a ref, a branch, a commit, or a force flag,
because those are not fields of the request.

**A socket path is not an authenticator.** Every lane on a machine runs as the
same user, so the mode bits on the socket keep no *sibling lane* out: a lane that
walked the launcher's scratch could find the builder's channel and spend the
builder's capabilities. So each channel is bound to one cryptographically random
per-lane secret, issued to exactly one lane in its narrow child environment
(`PR_PROVER_CAPABILITY_SECRET`) and presented as the first line of every request.
The comparison is constant time and happens *before* the request is parsed, so a
wrong or missing secret means no JSON is decoded, no operation is authorised, and
no `git` or `gh` subprocess starts at all. The refusal is worded identically
whatever was wrong, so the reply is not an oracle for which lane a socket belongs
to. The strict sandbox allows a lane exactly one unix socket — its own — so the
two defences are independent.

The secret travels in the environment rather than on argv, where every process on
the machine could read it, or in a file the request itself names.

**Closing a channel is deterministic.** `close()` stops accepting, stops the
serving thread, closes the listening socket, tells the broker to refuse, drains
the handlers it already accepted, and — if any is still running — terminates
their `git`/`gh` process groups (`SIGTERM`, bounded wait, `SIGKILL`) and joins
again, *before* removing the socket. When it returns, no accepted request can
still take effect and no subprocess that broker started is alive. A handler that
could not be accounted for is a fail-closed stop, not a reported outcome.

So a child cannot merge, cannot push another ref or another repository, and
cannot approve a review — not because it was told not to, but because none of
those is an operation it can express. The push target is always
`https://github.com/<bound repo>.git` with refspec
`<worktree HEAD>:refs/heads/<bound branch>` and no `--force`; a review is always
submitted with `event=COMMENT` against the bound head. The number of operations
one lane may perform is capped, so a lane that loops cannot post without bound.

The capability vocabulary — `push-branch`, `comment-pr`, `review-pr` — is closed
and has no merge, approval, deploy, or admin form, so an identity that could
merge cannot be *expressed*, let alone granted.

**Credentials are never in the config.** An identity names either a parent
environment variable (`token_env`) or an owner-only file (`token_file`) to read
one from at launch time. A source that is missing, empty, world-readable, or
holds more than one line fails closed.

**Every credential is verified before it is used.** The broker asks GitHub which
account the credential resolves to and what it may do on the bound repository,
using the launcher-side environment it will act with. The login must match
exactly; `admin` or `maintain` — the permissions that merge and change branch
protection — are refused outright; a builder credential must be able to push and
a reviewer credential must not. This is defence in depth *behind* the capability
broker, not the thing standing between a child and a merge.

### The child environment is built from nothing

Names are allowlisted, and anything credential-shaped is denied by name —
`GH_TOKEN`, `GITHUB_TOKEN`, `SSH_AUTH_SOCK`, anything containing
`TOKEN`/`SECRET`/`PASSWORD`/`API_KEY`, and whole vendor prefixes (`JMD_`, `AWS_`,
`VERCEL_`, `SANITY_`, `N8N_`, `KARAN_`, …) — so an unfamiliar `ACME_DEPLOY_TOKEN`
is refused without anyone enumerating it. `launch.env_allow` can widen the
allowlist only to names that are *not* denied and do not shadow launcher-owned
material.

**Injection is a closed set.** A launcher does not get to name what it writes
into a child: `HOME`, `PATH`, the configuration-discovery guards, and the one
capability channel, and nothing else. There is no `inject_as` any more, because
there is no credential to inject.

**Model access is a channel, not a variable name.** `launch.model_auth` names one
of the launcher's code-owned channels:

| `launch.model_auth` | Variable passed through |
|---|---|
| `anthropic-api-key` | `ANTHROPIC_API_KEY` |
| `claude-code-oauth-token` | `CLAUDE_CODE_OAUTH_TOKEN` |

A configuration cannot name the variable, so `GH_TOKEN`, `JMD_DEPLOY_KEY`,
`VERCEL_TOKEN`, `AWS_SECRET_ACCESS_KEY`, and `KARAN_APPROVAL_TOKEN` are not
expressible there rather than merely rejected there.

### A synthetic HOME

No child inherits the operator's home directory. `HOME` is denied like a
credential, because it *is* one: `gh` reads `~/.config/gh/hosts.yml`, `git` reads
`~/.gitconfig` and the OS keychain, `ssh` reads `~/.ssh`, and the model client
keeps its own stored credentials under its config directory.

The launcher builds a home per lane, inside that one launch's own directory
under the launcher's scratch root, and points every configuration-discovery
variable it knows about inside it:
`CLAUDE_CONFIG_DIR`, `GH_CONFIG_DIR`, `GIT_CONFIG_GLOBAL`,
`GIT_CONFIG_SYSTEM=/dev/null`, `GNUPGHOME`, and `XDG_{CONFIG,CACHE,DATA,STATE}_HOME`.
A child that is missing any one of them is refused before it launches. Only
material named in the code-owned `REVIEWED_HOME_MATERIAL` list is copied in, and
that list is empty — widening it is a code change that shows up in review, not a
configuration key.

Two temporary-directory variables are written by the launcher too, both pointing
inside the lane's own writable scratch, so a child's temporary files never land
in a directory the launcher or another lane shares. The operator's `TMPDIR` is
not inherited. `TMPDIR` is what an ordinary script lane's shell and toolchain
read; a Claude agent lane's sandboxed Bash ignores it — a live probe reported
`TMPDIR=/tmp/claude-501` whatever the launcher set, because the client supplies
its own session temporary directory — and reads `CLAUDE_CODE_TMPDIR`, so the
launcher sets that as well. Both are launcher-owned names: a run configuration
that tries to claim either is refused when the policy is built.

Credential helpers are cleared in the launcher-written gitconfig and none is put
back, for any lane. A direct `git push` from a child fails for want of a
credential; the only push that can succeed is the one the launcher performs.

### A lane is a process group

Every child is started in its own session, and the **group** — not just the
process the runner started — is terminated on every exit path: normal
completion, timeout, cancellation, and any other exception. `SIGTERM` first, a
bounded wait, then `SIGKILL`, and the call does not return until the group is
gone. Output is drained in threads and the runner waits on the process rather
than on end-of-output, so a backgrounded descendant holding the lane's stdout
cannot stall the teardown that is meant to kill it.

That is what lets the launcher remove a lane's scratch, synthetic home, and
capability socket knowing nothing is still holding them.

A descendant that calls `setsid` for **itself** leaves the group and is outside
this guarantee. Nothing in this package should be read as evidence that such a
process is destroyed; proving that is OS process-domain work and is owned by
**PAPI-93/PAPI-95**. See
[What this package cannot enforce on its own](#what-this-package-cannot-enforce-on-its-own).

### Launch discipline, in code

- **Empty MCP.** Every agent lane runs with `--strict-mcp-config` and an
  `--mcp-config` file the launcher wrote containing no servers.
- **A launcher-owned strict sandbox.** See
  [The strict sandbox](#the-strict-sandbox) below.
- **Bounded tools.** `--tools` and `--allowedTools` come from the code-owned
  maximum for the role; configuration may only narrow them. That maximum is now
  `Bash` and `TodoWrite` for both roles, because `Bash` is the only tool that
  runs *inside* the OS sandbox. Permission modes that dissolve the tool boundary
  are not configurable.
- **A fresh runtime and a trusted `PATH`.** Every launch gets its own runtime
  directory with its own copy of the capability shim. Its write bits are
  stripped, but that is defence in depth rather than the boundary: a lane's
  descendants run as the same user that owns those files and can restore a mode
  bit. What actually keeps a lane out of its own runtime, and out of every other
  lane's, is that the runtime is not in the lane's writable set in the sandbox
  document. The child's `PATH` is that directory plus a short list of trusted
  system directories — never the operator's, and never another lane's. Every
  configured program is resolved to an absolute path, checked (regular file,
  owner-executable, not group- or world-writable, not reached through a
  directory another user can write to, not anywhere inside the launcher's
  scratch), fingerprinted, and re-checked immediately before the spawn.
- **Lane-scoped material.** Every launch owns one directory under the launcher's
  scratch root, holding its synthetic home, its writable scratch (which is also
  the lane's `TMPDIR`), its read-only runtime, its read-only input directory, and
  its own settings file. The launcher's scratch *root* — which holds every lane's
  material, the empty MCP config, and the capability broker's own request
  payloads — is denied to every lane.
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
  `--add-dir`, or `--system-prompt` in from configuration fails closed instead
  of shipping. `--settings` and `--setting-sources` are on the same list, with
  exactly one exception each: the entries the launcher itself composed, checked
  against the exact path it just wrote and required to appear exactly once.

### The strict sandbox

Every Claude agent lane is launched with a settings file this package generated
for that one launch, passed as `--settings`, alongside a launcher-owned
`--setting-sources` entry that names no source at all — so neither the
operator's settings nor a `.claude` directory committed by the pull request
*under review* is read. A run configuration cannot supply either flag, replace
the file, or add a second occurrence a later parse might prefer.

The document is generated, written owner-only, then **re-read from disk and
proved again immediately before the spawn**, so an edit between composing a
launch and performing it fails closed. Every key it pins is checked by the name
Claude Code 2.1.219 actually reads, and a key outside the documented set is
refused outright — a setting the client ignores describes a policy nobody
enforces, which is worse than none. What it pins:

- `sandbox.enabled: true`, `sandbox.failIfUnavailable: true` — a missing or
  unsupported sandbox is fatal, never a silent downgrade;
- `sandbox.allowUnsandboxedCommands: false`, `sandbox.filesystem.disabled:
  false`, `sandbox.excludedCommands: []`, `sandbox.allowAppleEvents: false`, no
  extra directories, no MCP or policy override;
- `sandbox.network.allowedDomains: []` **and** `sandbox.network.deniedDomains:
  ["*"]` — an empty allow list is not a denial on its own — plus
  `sandbox.network.allowLocalBinding: false`;
- filesystem reads limited to the lane's worktree, this lane's own scratch,
  synthetic home, runtime and input, its settings file, the empty MCP config, and
  a short list of trusted runtime/library prefixes — never `/`;
- filesystem writes limited to *this lane's* scratch and synthetic home, plus the
  worktree for a builder; a reviewer's worktree is denied by exact path, as is
  the worktree's Git metadata for both, and the lane's own runtime, frozen input,
  settings file, and the empty MCP config;
- the launcher's scratch root and the operator's home denied for **reading**,
  with this lane's own paths — and, inside the home, the one resolved worktree
  this lane was authorised for, because a real checkout lives under
  `~/projects/worktrees/…` — named back inside them. Any other root inside the
  home, and any worktree that is itself a credential directory, is refused;
- the operator's credential directories (`.ssh`, `.gnupg`, `.aws`, `.config/gh`,
  `.claude`, `.netrc`, keychains, …) denied by exact path, for reads and writes
  alike;
- exactly one unix socket — this lane's own capability channel;
- every built-in tool that reaches the filesystem or the network *outside* the
  Bash sandbox (`Read`, `Edit`, `Write`, `Glob`, `Grep`, `WebFetch`,
  `WebSearch`, …) denied, so a lane reads, edits, and tests through sandboxed
  Bash and nothing else;
- `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` in the child environment, so a lane's own
  shells do not re-export the lane's environment — its capability secret in
  particular — into processes further down.

#### Reads nest; writes do not

Worth stating on its own, because a symmetric reading of the two produced a
policy that looked strict and refused every launch.

A broad `denyRead` closes a region and a more specific `allowRead` reopens a path
inside it. Claude Code documents this, and a live probe of 2.1.219 confirms it,
which is why the launcher's whole scratch root and the operator's whole home are
denied for reading and this lane's paths are named back.

A `denyWrite` region is absolute: a nested `allowWrite` does **not** reopen it. A
live probe proved that — with the operator's home and the launcher's scratch root
broadly denied for writing, the builder's own worktree, the lane's own scratch,
and the lane's own synthetic home were all refused with `Operation not
permitted`, though every one was named in `allowWrite`. So the write policy is
built the other way round. It leans on Claude's own default write boundary — the
working directory and the session temporary directory, and nothing else — plus
this lane's exact writable roots, and `denyWrite` carries only exact immutable
paths that shadow nothing the lane needs. What keeps a sibling lane, the broker's
material, and the rest of the operator's home out of a lane's *writes* is not a
denial at all: none of them is the working directory and none is an `allowWrite`
root.

`sandbox.decides()` models both rules separately, and the document is refused —
where it is built and again where it is proved — if any `denyWrite` entry covers
an `allowWrite` root.

What this confines is the authority a lane is *launched with* and the
filesystem, network, and GitHub reach of the processes it starts. It is not a
proof that a process which deliberately detaches itself from the lane's process
group is destroyed when the lane ends; that is
[PAPI-93/PAPI-95](#what-this-package-cannot-enforce-on-its-own).

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

## Reviewer isolation

Each reviewer runs in a worktree of its own, created fresh at the exact head. The
tree is sealed read-only at the filesystem, the launcher's strict sandbox denies
that lane writes to the worktree *and* to its Git metadata, and the loop proves
the tree exact **before and after** every reviewer lane — any difference is
`scope-contamination`, and the worktree is retained as evidence.

`git status` is not accepted as that proof. Status is computed from the index,
and the index is exactly what a `skip-worktree` or `assume-unchanged` bit tells
git to stop consulting, so a reviewer could edit a file and leave a clean status
behind. Five things are checked instead:

1. `HEAD` is the bound commit, and the tree that commit names is the bound tree.
2. No index entry carries `skip-worktree` or `assume-unchanged`.
3. Every tracked path matches the bound commit, compared through a **scratch
   index built with `read-tree`**. A fresh index carries no stat information for
   git to trust, so every path is compared by content — which is what catches a
   modification whose size and timestamp were carefully restored.
4. Nothing untracked was left behind.
5. No worktree-local git configuration was added that could redirect a read or
   conceal a change — a hooks path, a content filter, an external diff, a
   `status.showUntrackedFiles` that suppresses check 4, a credential helper.

One reviewer has nothing of another's to touch: reviewer A's worktree is removed
before reviewer B's is created. The filesystem seal on its own is a guard rather
than a jail — on POSIX the owner of a file may restore its write bit — which is
why the sandbox denial and the five checks above are what the guarantee rests on.

## Committed changes stay in the packet

A clean attempt worktree and a valid readback say only that the builder committed
and pushed *something*. They say nothing about which files the commit touched,
and "fix the blocker, and also commit this unrelated file" leaves the worktree
clean, the marker valid, the push bound to one new head, and the fix comment
readable.

So after a new head is reported and read back, the committed old-head-to-new-head
path set is compared against the frozen repair packet's `allowed_paths` contract,
**in the loop, before that head's gates or reviewers run**. A path outside the
contract stops the run as `scope-contamination` with the committed set, the
offending paths, and the contract preserved as evidence. The whole-repository
allowance (`"**"`) is honoured only when the packet carries it; a missing or
unparsable contract fails closed.

## Reviewer artifact readback

Every reviewer lane is held to the builder's standard, unconditionally. Its
printed verdict counts only once GitHub shows an artifact that is:

1. **New** — a review or comment id that was not there before the lane started;
2. **Under its own login** — the identity the launcher gave that lane, exactly;
3. **Tagged on its exact first line** — the whole first line, byte for byte:

   ```text
   PR-PROVER-REVIEW: repo=<owner/name> pr=<number> role=<A|B> head=<40-hex sha>
   ```

   Not "contains the tag": a quoted comment, an inlined diff, or a reviewer
   echoing text it read would all satisfy "contains".
4. **`COMMENTED`, for a submitted review** — and matching the commit GitHub
   recorded it against. `APPROVED` is a merge signal and Karan is the only merge
   gate; `CHANGES_REQUESTED` is a blocking gate on the PR itself; `PENDING` was
   never submitted and can still be edited; `DISMISSED` has been retracted. An
   unknown state is not this loop's artifact either. The launcher submits reviews
   with `event=COMMENT` for the same reason, so a child cannot produce any of the
   refused states in the first place.

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
`github-error` · `worktree-error` · `identity-error` · `launch-policy` ·
`capability-refused`

`identity-error` covers ambiguous auth, the wrong account, and a credential that
holds more authority than its capabilities declare. `launch-policy` covers a
child environment that still carries something it should not, a lane launched
outside the run's worktree root, a budget outside the window, and any attempt to
broaden authority at launch time. `capability-refused` covers a child asking the
launcher for an operation outside its bound capability — an unknown verb, a field
it does not get to name, or a push from a lane that cannot push.

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
  repository, so a builder's inputs cannot contaminate the diff. The run's own
  scratch holds every attempt's packet, so the builder is not pointed at it: the
  launcher copies the one file that lane is entitled to into the lane's read-only
  input directory and points the prompt and the environment at the copy.
- Each reviewer gets a worktree of its own, sealed read-only, denied write access
  by the lane's sandbox, and proved byte-for-byte identical to the bound commit
  before and after the lane — index hiding flags, worktree-local git config, and
  content-restoring edits included. One reviewer cannot contaminate another.
- A fix attempt's *commits* are held to the frozen packet's allowed-path
  contract, so an unrelated committed file stops the run even when everything
  else about the attempt is valid.
- One lane cannot spend another lane's capabilities: each channel is bound to a
  per-lane secret checked in constant time before a request is parsed, and each
  lane's sandbox allows exactly one unix socket — its own.
- Every launch owns one directory and writes nothing outside it: its own scratch
  (which is also its `TMPDIR` and `CLAUDE_CODE_TMPDIR`) and its own synthetic
  home, plus the worktree for a builder. Its runtime, its settings file, its
  frozen input, the empty MCP config, the broker's material, and every other
  lane's directory are outside its writable set — by exact denial where the path
  must stay immutable, and simply by not being an allowed write anywhere else.
  The write bits are stripped from the runtime as well, but that is the second
  lock: a same-uid descendant can restore a mode bit, and the sandbox is what the
  claim rests on.
- Every launch gets a fresh runtime directory and a `PATH` that is not the
  operator's, so no lane can modify an executable another lane later runs, and no
  configured program may resolve anywhere inside the launcher's scratch.
- The loop never pushes, comments, approves, or merges. The launcher performs
  each lane's push and comment on its behalf, bound to the exact repo, PR,
  branch, and head; this loop only verifies what landed.
- Every child is launched in a worktree this run created, inside the configured
  worktree root; a lane pointed anywhere else is refused.
- **No child holds a GitHub credential at all**, so merge, Karan-approval, JMD,
  deploy, client, and live-system authority are not in a child environment to
  begin with — and neither is the operator's own `gh` login, OS keychain, or
  model-client credential store, because `HOME` is synthetic and every
  configuration-discovery variable points inside it.
- A lane's whole process group is terminated and reaped, and its capability
  channel drained and cancelled, before its scratch, synthetic home, and socket
  are removed. A handler that cannot be accounted for stops the run.

### What this package cannot enforce on its own

Stated precisely, because a limit that is left vague reads as a claim:

- **Filesystem confinement is delegated, not implemented here.** A Claude agent
  lane is confined by the OS sandbox the launcher configures and proves
  ([The strict sandbox](#the-strict-sandbox)); the *enforcement* of that document
  is Claude Code's and the operating system's, and this package's guarantee is
  that the document says what it must and that a lane is never launched without
  it. A **script** lane has no such sandbox: its `Bash` runs as the operator's
  own uid and can read an absolute path such as `~/.ssh/id_rsa` even though
  nothing points there. What is enforced for both is that no *discovery* path
  leads to the operator's credentials and that no credential is in the
  environment.
- **Read-only worktrees against a determined process.** The filesystem seal is
  undoable by the file's owner. For an agent lane the sandbox denies the write;
  for any lane, the before-and-after exact-tree proof in
  [Reviewer isolation](#reviewer-isolation) is what fails the run.
- **A descendant that calls `setsid` for itself** leaves the lane's process group
  and outlives the teardown. Nothing in this package proves such a process is
  destroyed, and nothing above should be read as evidence that it is — the
  sandbox confines what a lane's processes may *reach*, not which of them
  survive. Proving destruction of a deliberately self-detached descendant is OS
  process-domain work, owned by **PAPI-93/PAPI-95**.

## Verify

```bash
python3 -m unittest discover -s pr-prover/tests -v
python3 -m compileall -q pr-prover/src pr-prover/tests
pr-prover/bin/pr-prover check-config --config pr-prover/examples/run.example.json
pr-prover/bin/pr-prover check-config --config pr-prover/examples/run.script-lanes.example.json
git diff --check origin/main...HEAD
```

Most of the suite runs against deterministic doubles: no network, no `gh`, and no
launched agent. Five files touch the real machine on purpose, because the
properties they assert are not properties of a double —
`test_commands.ProcessGroupTests` starts real processes that background real
descendants and asserts the whole group is gone; `test_drain.py` runs real
`git`/`gh` stand-ins and proves that a cancelled capability handler leaves no
side effect and no live process group behind; `test_capabilities.ShimTests` runs
the real capability shim over a real unix socket; `test_worktrees.SealTests`
asserts the filesystem actually refuses a write; and `test_integration_git.py`
drives real `git` against a throwaway bare repo and clone in a temp directory.

A hardened sandbox that forbids `bind()` on a unix socket will fail
`test_capabilities.ChannelTests` and `test_capabilities.ShimTests` for that
reason alone. The same wire protocol — authentication before parse, refusal
without a subprocess — is also covered by
`test_capabilities.ChannelHandlerTests`, which drives the real handler over a
socket *pair* and needs no bind.
