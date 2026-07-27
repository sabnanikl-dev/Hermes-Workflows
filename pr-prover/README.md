# pr-prover

Read [`MISSION.md`](MISSION.md) before changing or reviewing this tool. It is the
normative product, scope, lifecycle, and blocker contract; this README explains
operation and implementation behavior. Repository-wide rules live in
[`AGENTS.md`](../AGENTS.md).

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

The executable is **PAPI-88** of the [control-surface contract](https://github.com/sabnanikl-dev/Hermes-Workflows/issues/1);
the repo-native contract and the slim
[`autonomous-pr-prover`](../Karan-skills/software-development/autonomous-pr-prover/SKILL.md)
router that sends Hermes here are **PAPI-92**; finding provenance and the
structured failure records are **PAPI-99**; the trusted execution adapters,
reviewer artifact lifecycle, and GitHub readback below are **PAPI-90**.
Deterministic human-feedback reconciliation (PAPI-97) and the final integration
proof (PAPI-93) are still pending; see the proof map in
[`MISSION.md`](MISSION.md) for exactly which invariants are shipped and which
are owed.

## Run it

```bash
pr-prover/bin/pr-prover check-config --config /path/to/run.json
pr-prover/bin/pr-prover run          --config /path/to/run.json          # human report
pr-prover/bin/pr-prover run          --config /path/to/run.json --json    # machine report
pr-prover/bin/pr-prover reset        --config /path/to/run.json [--force]
```

Exit codes are the outcome: `0` merge-ready, `1` blocked, `2` needs-Karan
(including every fail-closed stop), `64` usage or configuration error.

Start from [`examples/run.example.json`](examples/run.example.json). It shows
the acceptance lifecycle the tool enforces — `reviewer-a`, `reviewer-b`,
`integration-auditor`, in that order — wired to the two adapters this repository
ships.

## Configuration

`schema_version` is **`2`**. Version 1 described a different, incompatible file:
its `reviewers` were a free list of lanes, with no required `role`,
`artifact_author`, or `artifact_signature` and no fixed three-role lifecycle. One
version number cannot truthfully denote both shapes, so the discriminator was
bumped rather than left in place over new semantics. A v1 file is refused with
the four ordered upgrade steps printed as a structured `invalid-config` record —
there is no migration layer, because the edit is mechanical and a migration would
be more machinery than the break is worth. The state journal keeps its own schema
version, which is independent of this one.

Every path field — `source_repo`, `worktree_root`, `state_file`, `lock_file` —
is validated before it is resolved. A string that is valid JSON but not a usable
path (an embedded NUL is the reachable case) is an `invalid-config` record and
exit 64, not a `ValueError` traceback, and the record names the field rather than
echoing the value back.

Every child command is an **argv array**. Templates substitute only these
tokens, and an unknown token fails the run rather than rendering literally:

| Token | Available to | Value |
|---|---|---|
| `{repo}` `{owner}` `{name}` `{pr}` | all lanes | from config |
| `{branch}` `{base}` `{head}` | all lanes | from the **live** PR, never from config alone |
| `{worktree}` | all lanes | this lane's own fresh worktree, at the exact head |
| `{reviewer}` `{role}` | reviewer lanes | the lane name, and the mission role it runs as |
| `{artifact_file}` | reviewer lanes and their relay | where this lane prepares its artifact, under the OS temp directory |
| `{evidence_packet}` | reviewer lanes | the frozen read-only PR evidence this lane judges from, under the OS temp directory |
| `{attempt}` `{mode}` `{blockers_file}` | the builder lane | attempt number, `initial`/`corrective`, and the frozen blocker set as JSON |

`builder.comment_author` is **required** and must be the exact GitHub login the
builder comments under. See [Fix-comment readback](#fix-comment-readback). Each
reviewer's `artifact_author` is required for the same reason — see
[The reviewer artifact lifecycle](#the-reviewer-artifact-lifecycle).

`env` and `env_unset` are a small **named overlay** on the environment a lane
inherits, never a replacement for it. The trusted agents run as the operator's
own user and authenticate through the normal OAuth/keychain session, so there is
no `env -i`, no synthetic `HOME`, and no generated sandbox policy anywhere in
this tool: `HOME`, `USER`, `LOGNAME`, and `SHELL` cannot be set or cleared by a
lane, and a value that looks like a credential is refused outright. Tokens
belong in the keychain and in `gh`'s own auth, not in a config file that ends up
in evidence.

A **relayed reviewer lane** gets one further adjustment, and it is deliberately
narrow. Removing `GH_TOKEN` and friends by name is necessary and is not
sufficient: an operator who is logged in normally has a stored `gh` session, and
`gh` resolves it through `GH_CONFIG_DIR`, then `$XDG_CONFIG_HOME/gh`, then
`$HOME/.config/gh`. So the lane's `GH_CONFIG_DIR` is pointed at a fresh, empty
directory this run owns, one per lane. The search stops there, finds no host,
and consults no keyring — `gh` only reaches for stored credentials for hosts its
resolved configuration already knows. `HOME` is *not* retargeted, because that
is where the trusted agent's own OAuth session lives and synthesizing one is
both forbidden by the mission and a way to break Codex in the same stroke as
`gh`. The denial is scoped to `gh` and to the judging half only: the relay
inherits its own session untouched and publishes exactly as before.

`state_file` and `lock_file` must resolve **outside** `source_repo`, and a path
equal to or nested inside the clone is a configuration error. The run writes both
while it is also asserting that the operational clone is never modified and that
an attempt worktree is clean, so a control file living in that clone would
contaminate the very tree being judged. Siblings and any other outside path are
unaffected; `worktree_root` is held to the same rule where worktrees are created.

Gates take `"kind": "baseline"` (default) or `"kind": "visual"`. Visual gates
run only when `visual_qa_required` is `true`; setting that flag without a visual
gate is a configuration error, so browser/visual QA is never silently skipped.

`check-config` also prints **advisories**: a lane with no timeout, or a builder
budget too short for a real fix cycle. They are notes rather than errors, because
a repository with a two-minute suite may genuinely know better — but a trusted
agent cut off mid-verification looks exactly like a hang, and that is not a thing
to discover for the first time at minute forty of a live run.

## The acceptance lifecycle is configuration

`reviewers` is not a free list of lanes. It must be exactly

```text
reviewer-a  →  reviewer-b  →  integration-auditor
```

in that order. The loop runs the lanes as configured, and the auditor's whole
job is to reconcile two artifacts that must already exist when it starts — so a
missing auditor, a duplicated role, or an auditor-first order is a configuration
error rather than a run that quietly proves less than it claims. Two lanes
sharing a role are refused for a second reason: each could satisfy the other's
artifact readback, which is exactly the independence the lanes exist for.

## The shipped adapters

Two are repository-owned, and the example config wires both:

- [`scripts/codex-reviewer.sh`](scripts/codex-reviewer.sh) runs one Codex
  reviewer against one exact head in a disposable worktree, with **no GitHub
  credential and no reachable `gh` login**, and writes its finished artifact to
  `{artifact_file}`. It refuses to run if a token variable is set, if
  `GH_CONFIG_DIR` is unset or still holds a `gh` hosts file, or if the packet at
  `{evidence_packet}` is missing, empty, or bound to another repo, PR, base, or
  head — each of those is the lifecycle being misconfigured, and running anyway
  would hide it. Its prompt points at the packet rather than at live `gh`, and
  is deliberately **adversarial**: the reviewer's
  job on a fixed head is to try to *kill* the change — bad-faith passes,
  weakened or deleted coverage, gamed thresholds, shrunken scope, stale
  evidence, unproven invariants — not to check that it looks correct. A reviewer
  that sets out to confirm shares the builder's framing and its blind spot.
- [`scripts/claude-builder.sh`](scripts/claude-builder.sh) runs the trusted
  Claude builder in that cycle's own worktree. It is **pointer-first**: it names
  the blockers file, `AGENTS.md`, `MISSION.md`, and the live PR rather than
  copying them, so the prompt cannot drift away from the sources. Tools are
  task-scoped — enough to read, edit, verify, commit, push, and comment, and
  nothing that grants merge, deploy, release, or account authority — and an
  empty MCP config is passed with `--strict-mcp-config`, because optional MCP
  servers are the usual cause of a non-interactive launch hanging on unrelated
  tool startup.

Neither adapter is a security boundary. Both are ordinary hygiene for launching
a trusted agent reliably, and both are covered by
[`tests/test_adapters.py`](tests/test_adapters.py), which runs them for real
against stub binaries — a double cannot catch a mistyped flag or a guard that
never fires.

Gates remain the operator's own commands.

## Lanes are launched, watched, and ended

Every lane goes through one path, and it holds four properties a lane's own
output cannot establish:

- **The session is inherited, never rebuilt.** `env=None` means the child gets
  the real environment, so the normal OAuth/keychain session keeps working.
- **The reported budget is the enforced budget.** A lane configured with no
  timeout gets no deadline and the run log says `unbounded`; there is no hidden
  default underneath it. Only a lane's own budget ever ends it.
- **Silence is not a hang.** Elapsed time, bytes produced, and how long a lane
  has been quiet are recorded while it runs and reported when it ends. A builder
  can buffer its stdout for twenty minutes; that is written down, never acted on.
- **A lane is a process tree.** Each child starts in its own process group, and
  that group is ended on *every* path out of the runner — the ordinary exit-zero
  one as much as the timeout. A builder that backgrounds a test suite, prints a
  clean marker, and exits politely would otherwise keep mutating its worktree
  after the loop has recorded the lane as stopped, which is a false success
  rather than a slow one. Before `run` returns, the group is proved empty.

## The reviewer artifact lifecycle

A reviewer is trusted to judge one head. It is not handed a GitHub credential to
publish with, because the identity a reviewer publishes under is not the
identity its lane happens to run as. So the artifact takes one explicit route,
and each step is separately checkable:

```text
frozen evidence packet → credential-free audit
  → prepared artifact under the OS temp directory
  → trusted relay command publishing under the reviewer identity
  → GitHub readback of what actually landed
```

### The frozen evidence packet

A lane with no way to reach GitHub cannot inspect the PR, so the parent reads it
and freezes what it read to `{evidence_packet}` — a JSON file outside every
repository, written before the lane launches and cleared with the rest of the
scratch directory afterwards. It carries the pull request's own state, the
conversation comments, the submitted reviews with their `commit_id`s, the inline
review comments, the check runs for this exact commit, and the issues the PR
closes. The `base..head` diff and the commit history are *not* in it: the lane
has a real checkout and reads those with `git`.

Each surface says how it was read and whether that read reached the end. An
incomplete surface is not an error — the conversation-comment read carries no
pagination guarantee yet, and proving it does is PAPI-97's obligation (M5) — but
it is stated, so a reviewer cannot mistake a first page for a whole PR.

The packet binds itself with one canonical line:

```text
REPO=<owner/name> PR=<number> BASE=<ref> HEAD=<40-hex sha> SEQUENCE=<n>
```

`SEQUENCE` is per-run and strictly increasing, so a packet belongs to one lane
and no lane can be handed another's. The loop writes the packet and then reads
it back and holds it to that line, for the same reason it reads its artifacts
back from GitHub: what a lane is handed is the file on disk, not the payload the
process assembled. The adapter checks the same line again from its own
arguments. A packet that did not land, landed empty, or was left at that path by
an earlier cycle stops the lane **before** it is launched, rather than producing
a confident review of the wrong head.

Everything inside is untrusted evidence. The whole payload goes through the same
recursive redaction the report and the frozen blocker file do, with the clip set
to the largest artifact this tool will relay — the Integration Auditor's job is
to reconcile the artifacts Reviewer A and Reviewer B published, and it must not
be handed truncated copies of them.

Every artifact must carry, each on a line of its own:

```text
ROLE=<the lane's configured role>
RUNTIME=<the model or runtime it actually ran as>
HEAD=<the full 40-hex lowercase commit reviewed>
STATUS=pass|fail
BLOCKING=<number of blocking findings>
KILL-SWITCH: <what it tried in order to kill the change, and what that found>
```

plus the configured signature. Whole lines only, and each key exactly once.
Prose never counts: scope paragraphs and command transcripts legitimately quote
a SHA, so an artifact could satisfy a substring test while stating on its own
line that it reviewed something else. `STATUS` and `BLOCKING` must also match
the lane's own marker — the marker is what the loop classifies from and the
artifact is what Karan reads, and two stories about one head is not a formatting
slip. `KILL-SWITCH:` is the adversarial mandate made checkable: at least one
line saying what was attempted, so "I found no problem" is a different statement
from "I did not look".

The prepared file is held to all of that **before** the relay may publish it, so
an artifact that would fail readback never reaches the PR at all. Then the post
itself must be from the configured login and bound to this head — by GitHub's
own review `commit_id` where there is one, *and* by the canonical declaration in
every case.

### Which post counts as this run's transport

The remaining question is *which* matching post. "New since the lane launched"
is the wrong test, and the difference matters: a valid artifact posted by the
judging lane itself — right login, right head, every declaration correct — is
new since the lane launched too, and crediting it would let a relay that
published nothing produce complete transport. That is not hypothetical; it is
what a reachable stored `gh` session bought before the config-directory denial
above existed.

So the run snapshots the PR's artifact ids **twice**: once before the lane is
launched, and again after the lane exits and immediately before the relay is
launched. Attribution runs off the second one. Only an id that appeared inside
the relay's own window can be this run's transport, and a lane-side post — even
a genuine one — falls outside it and is never credited. If the relay then
publishes nothing, the run fails closed with `readback-mismatch`, and the
evidence names how many artifacts arrived while the credential-free lane was
running, so a missing relay post reads as what it is rather than as an
unexplained readback puzzle.

A lane without a `relay` publishes for itself. There is no relay window, so its
pre-launch snapshot is the newest one there can be and attribution uses that. It
is read back the same way; only the transport differs.

The report's `transport_complete` is a claim about that whole lifecycle, not
about whichever records happen to exist: three records, the required roles in the
required order, each read back on GitHub, and all of them bound to the one head
the ledger they support was produced against. An empty ledger — a gate that
blocked before any reviewer launched, a stop before transport began — is not
complete, and neither is a finished Reviewer A record with nothing after it. Per
record, the `transport` list says exactly how far that one got. None of this is a
verdict: three failing reviews whose artifacts all landed are complete transport
and a blocked head.

## What this run owns, and what it does not

Every artifact the loop watches appear and verifies is retained **by GitHub's
own id**, in the run state file. That is the whole definition of "this run
published it", and the reason is that everything visible in a body becomes
copyable the moment a real artifact exists — the signature, the role line, the
head declaration — while a configured login proves nothing either, because the
account is shared with a human.

Before a builder is launched, any comment or review the run cannot attribute to
itself stops the run and asks Karan. No prose is interpreted, no login is
trusted for being configured, and no resolution state is read. A builder fixing
against an unread human objection is the failure this prevents, and being wrong
in this direction costs an unnecessary question while being wrong in the other
costs a push over a "do not merge".

The bluntness is priced deliberately. An old approving review stops the fix lane
too. Making it precise — complete surfaces, positive ownership under a shared
login, native review and thread resolution, and a finite acknowledgement
contract — is PAPI-97's subject, and this check reads only the conversation
comments and submitted reviews until then.

The stop guards the **fix lane only**. A run still reports `merge-ready`,
`blocked`, or `needs-Karan` on the head it measured: refusing to answer is not
the same as answering carefully, and the report is what Karan reads before
deciding.

## Fix cycles start fresh

Each cycle launches the builder as a new process with a new prompt and a new
blocker file. There is no resume path and no conversation handed back: cycle two
is re-grounded on the live PR and on the ledger frozen for *that* cycle, because
a builder carrying a failed cycle's reasoning into the next one degrades exactly
when the last cycle matters most. Everything that has to survive between cycles
— the attempt number, the corrective rerun spent, the bound head, the artifacts
this run owns — travels through the run state file instead.

The blocker file carries the same
[structured failure records](#failures-are-the-builders-next-instruction) the
report renders, one per blocker: what failed, the evidence, the bounded
remediation, and the escalation condition. The builder remediates what those
records name as in-bounds and stops otherwise.

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

### Every finding carries its provenance

A finding is created with the evidence that explains it, never annotated with it
afterwards. Four things travel with every one:

| Field | What it is |
|---|---|
| `agent_id` + `role` | the exact lane and the mission role it ran as — `reviewer:A`, `gate:tests` |
| `head` | the full 40-hex commit it was produced against |
| `location` | a typed surface: `file-line`, `review`, `thread`, `comment`, `gate-command`, or `lane-output` |
| `evidence_excerpt` | the verbatim text the lane emitted, scrubbed |

There is no untyped location and no optional field. A finding whose provenance
is incomplete cannot be constructed at all — the run fails closed naming the
field that is missing — because the alternative is an escalation that looks
complete and cannot be acted on. `head` and `source` are read *off* the
provenance rather than stored beside it, so a rendered string can never disagree
with the record it came from, and a stored finding whose rendered `source`
contradicts its provenance is rejected rather than believed.

Classification adds the other half. Every decision appends a lineage entry —
who decided, about which finding, from which category to which, and when — so a
finding two lanes raised at different severities, or one an adjudicator moved,
records the decision instead of only its result. A lineage entry naming a
different finding than the one it sits under is refused, at construction and
again when a journal is read back: decision history that could belong to
another finding is not decision history.

Deduplication picks which claim *governs* a finding id; it does not decide that
the other lane's evidence stops existing. Every originating claim is kept whole
in `origins` — its own typed location, its own excerpt, its own head — and
`sources` is read off that list rather than stored beside it, exactly as a
finding's `head` and `source` are read off its provenance. One entry per lane:
a lane restating an id replaces its own earlier claim, never another lane's.

A `needs-Karan` report renders all of it inline under the finding — every
origin, not only the governing one — so the escalation is actionable without
reopening the raw lane output, and it names the exact head the ledger was
produced against. A fail-closed stop after classification is an escalation too,
so it carries the same ledger rather than leaving it in the state file.

### Failures are the builder's next instruction

Every failure is expressed as one record with four parts: **what failed**, the
**exact evidence** (expected versus actual, or the command that ran), the
**bounded remediation** the builder may attempt, and the **escalation
condition** for when the fix would fall outside those bounds. Gate failures,
readback mismatches, malformed markers, stale heads, and classification stops
all take that shape, alongside every other fail-closed reason code.

The human summary in the Markdown report and the JSON block beside it are two
renderings of that one record — the fenced block *is* what the builder consumes,
and the frozen blocker set carries the same block for each blocker it names. So
there is no second description of a failure to keep in step with the first.
Remediation is deliberately narrow: it either points at work inside the frozen
blocker set or says plainly that there is none and the run stops.

That includes the two classes that stop before a run report exists.
`invalid-config` and `invalid-command` are caught in the CLI, before a loop can
be built, and they are still rendered as the same record in the same two forms
rather than as one line of prose on stderr. The prose line stays, as the
operator's log summary of the record printed beside it.

A readback mismatch says which condition each fresh comment actually failed —
wrong login, missing signature, or a body about some other head — for a bounded
number of candidates, because those are three different fixes.

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
reruns already spent, the terminal outcome, the phase of the run, and the four
classification buckets for the head it is bound to. One `O_EXCL` lockfile marks
that a run exists. There is no PID inspection and no takeover path: if the lock
is held, the run stops and asks.

The buckets are journaled with the full provenance and lineage each finding was
created with — every origin of it, not only the governing claim — so an
escalation read after a crash still says who found what, where, and on which
head. They are held to the same strictness as the rest of the journal: an
incomplete provenance record, a finding sitting in a bucket its own category
contradicts, lineage or an origin attributed to a different finding, a rendered
`sources` list that disagrees with the origins it was rendered from, or *any*
origin produced against a different head than the run is bound to is unexpected
state, not something to repair. And because a finding is evidence about one
exact commit, binding the run to a new head drops the old head's findings rather
than carrying them forward.

The one key a head change deliberately does *not* drop is the list of artifact
ids this run owns. A finding is evidence about one commit, but an artifact this
run published for an earlier head is still not human feedback — and cycle two
has to recognise what cycle one posted, which is impossible to rediscover from a
body anybody could copy.

### The lock is released by identity, not by pathname

A lock path that is removed — by `reset --force`, say — and then acquired again
names a *different* file. An older run that unlinks the pathname on its way out
would delete the newer run's lock and leave two runs going at once, so each
acquisition remembers the identity of the file its own `O_EXCL` create produced,
read from the descriptor it still owns. Failed-acquisition cleanup and ordinary
release then share one deletion: remove the path only while it still resolves to
*that* file, and leave a replacement to the run that owns it.

Checking the identity and unlinking it are two steps, so both are held under a
short exclusive lock on the containing directory — the same one every
acquisition takes while it creates and identifies its lockfile. That is the
whole protocol, and it is what stops another run from acquiring the pathname in
between. Removing a lockfile by hand while a run is live is still unsupported.

What cleanup achieved is then reported rather than assumed. `removed`,
`already-absent`, `replacement-preserved`, and `cleanup-failed` are four
different outcomes; the last two mean a lockfile is still on disk, and
`cleanup-failed` says so and says to clear it by hand once no run is active. An
initialization failure keeps its own cause and reason — the disposition travels
beside it as evidence, never in place of it.

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

Reading nothing also means having no current head to report. The recorded head
is what the interrupted attempt was working on, not evidence that the PR is
still there, so the report says `unknown` for the head (`"head": null` in JSON)
and renders the recorded head only as the commit its ledger was produced
against — marked unverified in both renderings, with `classification_head_current`
false. A report never presents a head it did not observe as the live one.

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
`readback-mismatch` · `relay-failure` · `evidence-packet` · `human-feedback` ·
`scope-contamination` · `builder-refusal` · `github-error` · `worktree-error`

Each carries evidence, and the worktree plus scratch directory are retained so
the failure can be inspected. Each also reaches a failure record — what failed,
the evidence, the bounded remediation, the escalation condition — in both
renderings described [above](#failures-are-the-builders-next-instruction),
including the two classes the CLI reaches before a run report exists. A stop
that happens after classification also carries the ledger it froze, with the
head that ledger was produced against printed beside it — called the exact head
only while the live PR was observed on it, marked historical evidence once the
PR has moved, and marked unverified when the stop happened before any live read.

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
- **So does every gate and every reviewer lane, one each.** The acceptance
  lifecycle is sequential, so a shared checkout would put whatever Reviewer A
  left behind in front of Reviewer B and then the Integration Auditor — the two
  lanes whose verdicts decide `merge-ready` — while all three artifacts still
  declared the committed head. Each lane's own checkout is proved clean and
  sitting on exactly the bound SHA both before it is launched and after it
  returns; a lane that wrote into the tree it was judging stops the run as
  `scope-contamination` and keeps its worktree for inspection, and a successful
  lane's worktree is removed. A relay shares its reviewer's checkout rather than
  taking one of its own: it publishes a file that already lives outside every
  repository.
- The frozen blocker set, each reviewer's prepared artifact, each lane's frozen
  evidence packet, and each relayed lane's empty `gh` configuration directory are
  all written under the OS temp directory, never inside a repository, so a
  lane's inputs and outputs cannot contaminate the diff it is judging.
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

The suite needs no network and never calls `gh`, and it never runs a real Claude
or Codex. Almost all of it runs against deterministic doubles, including every
`git` call the loop makes. Three files deliberately do not:

- `tests/test_integration_git.py` runs real `git` against a throwaway bare
  repository and clone under the OS temp directory, because a double cannot
  catch a wrong refspec or a bad `rev-parse` argument;
- `tests/test_trusted_agents.py` drives the real `SubprocessRunner` against
  small shell children, because "silence is not a hang", "the reported budget is
  the enforced budget", and "the process tree ends with the lane" are claims
  about `subprocess` behaviour that a double would simply agree with;
- `tests/test_adapters.py` runs the two shipped adapter scripts against stub
  `codex`/`claude` binaries on a temporary `PATH`, because a double cannot catch
  a mistyped flag, a shell quoting bug, or a guard that never fires.

All three touch nothing outside their temp directories, and each skips itself
when what it needs (`git`, a POSIX shell) is absent.
