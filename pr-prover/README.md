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
reviewer artifact lifecycle, and GitHub readback below are **PAPI-90**;
complete feedback surfaces, run-owned publication evidence, native
review/thread resolution, and the acknowledgement contract are **PAPI-97**; and
the cross-slice integration proof — the ordered lifecycle composed end to end,
the anti-Goodhart bad-faith-pass case, and this metadata reconciliation — is
**PAPI-93**. See the proof map in [`MISSION.md`](MISSION.md) for exactly which
invariants are shipped and which are owed.

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
the ordered upgrade steps printed as a structured `invalid-config` record —
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
| `{artifact_file}` | reviewer lanes and their relay | where this lane prepares its artifact, under the OS temp directory — the relay is given the redacted copy of that file, not the lane's own bytes |
| `{evidence_packet}` | reviewer lanes | the frozen read-only PR evidence this lane judges from, under the OS temp directory |
| `{attempt}` `{mode}` `{blockers_file}` | the builder lane | attempt number, `initial`/`corrective`, and the frozen blocker set as JSON |

`builder.comment_author` is **required** and must be the exact GitHub login the
builder comments under. See [Fix-comment readback](#fix-comment-readback). Each
reviewer's `artifact_author` is required for the same reason — see
[The reviewer artifact lifecycle](#the-reviewer-artifact-lifecycle).

`governing_issues` is **required** and must name at least one issue number. It is
the task contract: the reviewers are handed those issue bodies in their frozen
packet, because a lane judging shrunken scope or acceptance criteria needs the
document those are written in. It lives here, and not in anything parsed out of
the pull request, because a PR body is untrusted prose — a PR that says
`Refs #1` closes nothing, and one that says `Closes #999` names whatever its
author typed. Which contract a change is measured against is not a question the
change gets to answer.

`operator_acknowledgements` is **optional**, and absent means the strictest thing
this tool can mean. It lists exact immutable GitHub post ids an operator
authorized before launch, each paired with a digest of the body that post held
when they read it, and its only effect is to let those exact posts — still
saying what they said — acknowledge earlier feedback even though a configured
publishing login wrote them. See [Operator-pinned
acknowledgements](#operator-pinned-acknowledgements). It is never a login, a
pattern, or a standing permission, it is bounded at sixteen pins, and
`check-config` prints back every id it was handed.

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
What a visual gate then owes is [a semantic
answer](#a-visual-gate-answers-about-what-was-rendered), not a file.

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
  `{evidence_packet}` is missing, empty, bound to another repo, PR, base, or
  head, or carrying none of the task contract its prompt sends the reviewer to
  read — each of those is the lifecycle being misconfigured, and running anyway
  would hide it. Its prompt points at the packet rather than at live `gh`, and
  is deliberately **adversarial**: the reviewer's
  job on a fixed head is to try to *kill* the change — bad-faith passes,
  weakened or deleted coverage, gamed thresholds, shrunken scope, stale
  evidence, unproven invariants — not to check that it looks correct. A reviewer
  that sets out to confirm shares the builder's framing and its blind spot.

  **Its verdict travels by Codex's final-message channel, not by its output.**
  `codex exec` narrates while it works, and that narration includes the prompt it
  was handed — which is where the marker grammar is necessarily written down, so
  an entirely honest run prints text that reads exactly like a verdict. The
  adapter therefore runs `codex exec --output-last-message <file>` and puts only
  that file on its stdout. The narration is kept, because a lane that fell over
  is diagnosed from it, but it is re-emitted on stderr with every line prefixed
  `codex| ` so no line of it can begin with a marker keyword. A final message
  that is missing, unreadable, or empty is a loud failure and not a lane that
  quietly found nothing, and Codex's own exit status is passed through unchanged
  so the [marker-versus-exit-status](#the-marker-is-not-the-whole-verdict) check
  still has both halves to compare.

  **The rest of the run is pinned, not inherited.** The artifact this lane
  publishes declares which runtime reviewed the head, so the launch states the
  properties that declaration is about rather than accepting whatever default is
  in effect: `--ephemeral`, so nothing is persisted and the next cycle starts
  from the live PR rather than from a session that remembers the last one; the
  reviewer `--model` and its reasoning effort, so `RUNTIME=` is a property of
  the launch; `--sandbox workspace-write`, because a read-only lane cannot write
  the one artifact it is being asked for; and `--add-dir` naming only the
  artifact directory, so the file the lane is meant to leave behind is one it is
  actually permitted to create and no other location is added. That directory is
  checked to exist and to be **outside the worktree** before write access to it
  is granted, because a lane's own scratch output landing in the reviewed tree
  is indistinguishable from the contamination the post-lane check exists to
  catch. None of this is a security boundary: ambient user configuration is
  still loaded, this is a trusted inherited session, and what proves the
  checkout was left alone is the contamination check rather than the write
  scope.
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
never fires. The reviewer's stub is deliberately *Codex-shaped* rather than
cooperative: it echoes the prompt back the way the real CLI does, so its
narration genuinely contains marker-shaped lines, and it reads the artifact path
out of the prompt and creates that file before it returns, the way the CLI does.
A stub that printed one clean marker would agree with the adapter that was wrong,
and a proof whose artifacts were written by the test process afterwards would
show that the validator works while saying nothing about whether a reviewer lane
leaves one behind.

The ordered three-role lifecycle is proved the same way, through the real thing:
`OrderedRelayLifecycleTests` configures the three shipped reviewer lanes exactly
as [`examples/run.example.json`](examples/run.example.json) does and runs
`loop.run()`, so the adapter is really executed, the artifact it writes is the
one the *loop's* configured relay publishes, and the order, the attribution
snapshot, and the GitHub readback are the loop's own. A local loop over three
adapter calls with the validator invoked directly proves the adapter three
times; it cannot prove that the loop runs the three required roles in order or
relays what each of them actually wrote.

Gates remain the operator's own commands.

## A visual gate answers about what was rendered

A visual gate that checks its screenshots exist, are PNGs, and are the right
size has proved that files were written. It has not proved that anything in them
can be read, and those are different claims — a rendering can satisfy every one
of the first while omitting the print detail a page exists to show. So the
obligation on a configured visual gate is **semantic**: it must report a
per-assertion outcome for the properties the run requires, bound to the exact
head, and it must fail when one of them is absent even though every expected
PNG and PDF is present and well-formed.

`pr-prover` does not learn those properties. Which detail bodies a print page
owes, which table columns must stay labelled once a header row is hidden, and
which text is small enough to need a contrast floor are facts about one site;
a tool that knew them would be a browser and accessibility framework wearing a
merge-readiness tool's name, which
[`MISSION.md`](MISSION.md#explicit-non-goals) rules out. They belong to the
**operator-owned configured gate**, which `pr-prover` selects, hands the bound
head and a checkout of its own, and blocks the head on when it exits nonzero.

What *is* repository-owned is the shape of the obligation and the proof that it
bites, in
[`tests/test_visual_semantics.py`](tests/test_visual_semantics.py):

| The gate must prove | How the proof avoids taking its word for it |
|---|---|
| required collapsed detail bodies reach the print output | the strings are pulled out of the PDF's own page content streams |
| mobile failure-table values keep an accessible field label | every required column must be measured *and* carry a non-empty label; an unmentioned column fails |
| required small operational text is legible | the WCAG contrast ratio is recomputed from the colours the gate recorded, or an explicitly approved design token is named |

Screenshots and PDFs stay as human evidence and are still required — they are
what a person looks at when the verdict is contested — but on their own they are
never sufficient, and there is a case asserting exactly that: a rendering with
all nine images and three PDFs intact, and all three defects present, does not
pass. The one honest exception is written as one: no amount of decoding a PNG
recovers a cell's accessible name, so the label check enforces that the
measurement was taken for every required column rather than believing a summary.

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
  → redacted copy of it, revalidated and written beside it
  → trusted relay command publishing under the reviewer identity
  → GitHub readback of what actually landed
```

### The frozen evidence packet

A lane with no way to reach GitHub cannot inspect the PR, so the parent reads it
and freezes what it read to `{evidence_packet}` — a JSON file outside every
repository, written before the lane launches and cleared with the rest of the
scratch directory afterwards. It carries exactly these surfaces:

| Surface | What it is |
|---|---|
| `pull_request_body` | the live PR description — the change's own stated contract |
| `governing_issues` | the body of each issue `governing_issues` names: the task contract |
| `conversation_comments` | the PR conversation |
| `reviews` | submitted reviews, with their `commit_id`s |
| `inline_comments` | what was said inline on the diff |
| `check_runs` | the checks GitHub recorded for this exact commit |
| `linked_issues` | the issues the PR itself *claims* to close |

The `base..head` diff and the commit history are *not* in it: the lane has a real
checkout and reads those with `git`.

The first two are why the rest are worth having. The reviewer prompt tells a lane
to check the PR body for stale claims and to judge scope against the issue's
acceptance criteria; a lane handed neither can complete both kill switches
without ever seeing their source. They are also the two the PR cannot supply for
itself: `linked_issues` is what the PR *says* about which issues it closes, which
is evidence about the PR rather than authority over it, and a PR using `Refs #1`
closes nothing at all.

Each surface says how it was read and whether that read reached the end. An
incomplete surface is not an error — a PR can honestly have no inline comments,
and a boundary that could not prove a read complete has to be able to say so —
but it is stated, so a reviewer cannot mistake a first page for a whole PR. The two
contract surfaces are the exception: they are not reads that may honestly come
back empty, so an empty or clipped one stops the lane rather than being handed
over as evidence.

The packet binds itself with one canonical line:

```text
REPO=<owner/name> PR=<number> BASE=<ref> HEAD=<40-hex sha> SEQUENCE=<n>
```

`SEQUENCE` is per-run and strictly increasing, so a packet belongs to one lane
and no lane can be handed another's — the number and the lane's own name and
role are both written into the file and both checked. The loop writes the packet
and then reads it back and holds it to all of that, for the same reason it reads
its artifacts back from GitHub: what a lane is handed is the file on disk, not
the payload the process assembled. The adapter checks the binding line and the
two contract surfaces again from its own arguments. A packet that did not land,
landed empty, or was left at that path by an earlier cycle stops the lane
**before** it is launched, rather than producing a confident review of the wrong
head.

Binding is necessary and not sufficient, so the shape is validated too. Every
required surface must be present, with a boolean `complete`, a non-empty
`read_as`, a non-negative integer `count`, a list of `items`, and a count that
equals how many there are; `schema_version` and `SEQUENCE` must be actual
integers, because Python reads `true` as `1` and a JSON boolean would otherwise
satisfy both. A file that keeps the binding and loses the evidence is the one
failure a reviewer cannot detect from the inside: every one of those surfaces
would simply read as *nothing to see here*.

The envelope is not the evidence either, so the two contract surfaces are held to
their records as well. `pull_request_body` must be exactly one record, for this
PR's number, with a `body` that is text — an empty description is a fact about
the PR and stays valid, but a missing or `null` one is a lane checking for stale
claims against nothing. `governing_issues` must carry exactly the issues the run
configured, in that order, each with a body that is text: the packet writes those
numbers down as `governing_issue_numbers`, and the loop passes the same
configured tuple it handed GitHub into the readback, so a contract record for
`#999` on a run measured against `#1` stops the lane instead of quietly becoming
the acceptance criteria it is judged by.

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

Only a complete `FINDING: SEVERITY=… ID=… -- …` line is a finding record.
Headings, narrative, command output, and token-like words such as
`stale-pr-evidence` are prose even when they resemble an identifier; they cannot
create a lane finding or cause relay parity to fail.

The final message is the reviewer’s single structured source of truth. The
control plane parses those records once and renders the canonical block into the
relay artifact. A prepared artifact may contain no `FINDING:` records at all;
its narrative still travels. If it does include structured records, they are a
second machine claim and must exactly match the final verdict or the run fails
closed before publication.

### What the relay actually publishes

Not the reviewer's own bytes. An artifact is child output, and the artifact is
the one surface this tool **publishes**, under a name that is not the lane's — a
reviewer that quotes an `Authorization` header back as evidence, pastes a
command transcript, or dumps its environment to show what it ran with has
written a credential into that document. Nothing downstream catches it: parsing
scrubs the *records* it extracts, in memory, and hands on the body it read them
out of exactly as it found it, so readback re-parses, re-scrubs, and agrees.

So the parent renders the canonical final-verdict records, then scrubs the whole
body once by the same `redaction.scrub` every other surface goes through. The
result is written to its own path beside the original. That copy is what
`{artifact_file}` resolves to for the relay, and it is revalidated first —
signature, declarations, verdict, and canonical finding parity — on its own
bytes, because a check applied to bytes nobody publishes proves nothing about
the bytes that are.

Only the credential-shaped runs change; every other character survives, which is
why this uses `scrub` and not the clipping `sanitize`/`evidence` the report and
the packet use. A review clipped to fit an evidence budget would lose the
argument it exists to make.

Redaction is a text substitution, so it can also change what a document says: it
can consume a signature that looked like a credential, grow a body past the size
bound, or lengthen a `FINDING:` line that was already at the grammar's limit
past what the readback parser accepts. Each of those stops the run **before**
anything is published, on the same rule as everything else here — never publish
what readback would reject. The reviewer's original file stays on disk as local
input for the rest of the run, and is never a publication path.

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

And none of it is permission. Every report carries a constant `merge_authority`
line, in the JSON and in the Markdown, saying that Karan alone decides and that
what is above it is evidence about one exact head. It is a module constant
rather than a computed field, because a value something could set is a value
something could be made to set to the wrong thing.

## What this run owns, and what it does not

Every artifact the loop watches appear and verifies is retained in the run state
file **by GitHub's own id, paired with a digest of what readback verified it
holding**. The id is the whole definition of "this run published it", because
everything visible in a body becomes copyable the moment a real artifact exists
— the signature, the role line, the head declaration — while a configured login
proves nothing either, since the account is shared with a human. The digest is
the other half: published artifacts stay editable, so an id alone would let
somebody rewrite a verified lane comment into "do not merge" and keep it
invisible. An artifact nobody touched stays owned; an edited one re-enters human
classification.

## Human feedback, reconciled rather than guessed

Gates and reviewer lanes are not the whole PR. Before a fix attempt opens and
before `merge-ready` is reported, the loop reads three surfaces — conversation
comments, submitted reviews, and inline review threads — to their last page,
reads them again until two consecutive passes agree, and reconciles them in
[`feedback.py`](src/pr_prover/feedback.py). Anything it cannot prove somebody
resolved stops the run and asks Karan.

"Read to their last page" is checked rather than assumed, and so is every field
the reconciler needs. A thread whose reply list did not arrive, a comment or
review whose body did not arrive, and a review with no state are each an
incomplete read — not a thread with no replies, a post with nothing in it, or a
review nobody has to clear. Each stops the read where it happened.

A field can also arrive and still be unusable, which is the same false success
one step later. A review state must be one GitHub actually defines: `""`,
whitespace, and an unknown word are all strings, and every one of them reaches
the reconciler as a review that neither blocks nor clears, so a live
`CHANGES_REQUESTED` would resolve itself by being unreadable. A live thread must
carry at least one reply, because a review thread exists only from the comment
that opened it; a complete-looking empty reply list has no readable human author,
is dropped as agent-only, and clears the PR. Both are malformed evidence and stop
the read.

A post a human really did leave empty is still data and still parses; the
difference between "empty" and "absent" only exists at the boundary, so that is
where it is decided.

Nothing here interprets prose. Two surfaces carry their own resolution state and
one does not:

- a formal `CHANGES_REQUESTED` clears only when the **same author** submits a
  later `APPROVED` or `DISMISSED` review;
- an inline thread clears only when GitHub records it resolved or outdated;
- prose on the surfaces GitHub gives no resolution state — a conversation
  comment, and the body of a review carrying no decisive state, such as a plain
  `COMMENTED` one — clears only through a later line reading, after the
  surrounding whitespace of that line is trimmed:

  ```text
  PR-PROVER: ACKNOWLEDGED <one immutable GitHub artifact id>
  ```

  Neither of the first two is acknowledgeable. A `CHANGES_REQUESTED` review and
  an inline thread each have a native GitHub action that resolves them, so an
  acknowledgement naming one of those is a line that clears nothing — it stays
  in the body as the prose it is.

  The grammar is the whole line and it is exact: the literal prefix, **exactly
  one ordinary space**, and one id containing no whitespace. A double space, a
  tab, a case variant, an extra token, or the same words inside a sentence are
  all ineffective, on purpose — a form loose enough to forgive a typo is a
  second, unwritten way to clear somebody's stop.

That line is *spent* only when all six of these hold: its post is allowed to
acknowledge at all — see [operator-pinned
acknowledgements](#operator-pinned-acknowledgements); it names exactly one
eligible unresolved prose item on a surface with no native resolution; GitHub's
own UTC-aware timestamps put that target strictly earlier; the target is not the
post itself; the target is not already cleared, globally or by an earlier line
of the same post; and so the line performs exactly one unresolved-to-cleared
transition.

One canonical order — UTC-aware timestamp, then surface, then immutable id —
governs everywhere an order exists: which posts are considered as candidates,
which of an author's still-standing change requests a finding names, and the
sequence of findings a stop reports. The same conversation therefore reconciles
to the same answer, in the same order, however its pages were grouped or its
tuples arrived. That last one is not presentation: a stop describes only the
first few items it found, so the order decides which ones Karan is shown at all.

Only spent lines are removed from the body. A blank remainder is pure
bookkeeping and creates no finding — otherwise acknowledging anything would
leave one more thing to acknowledge. **Any** non-blank remainder is unresolved
human prose, and that deliberately includes every acknowledgement-*looking* line
that did nothing: a post reading `PR-PROVER: ACKNOWLEDGED <real id>` above
`PR-PROVER: ACKNOWLEDGED missing-target DO NOT MERGE` clears the first id,
clears nothing with the second, and the stop written on that second line must
not vanish with it.

The check guards two moments and only two: opening a fix attempt, and reporting
`merge-ready`. A `blocked` head is still reported blocked — the blockers are
real whatever the conversation says, and refusing to answer is not the same as
answering carefully.

### Operator-pinned acknowledgements

A post written under one of this run's own publishing logins acknowledges
nothing. That is the rule a lane must not be able to talk its way out of — it
would be marking its own homework — and it is the default here whatever else is
configured.

It has one failure mode, and it is not hypothetical. Where the builder publishes
as one account, the reviewers as another, and those two are also the only
identities the operator has, *nobody* can acknowledge anything: a conversation
the operator has already reconciled by hand still stops every run, with
`acknowledged: []` and no identity left that could change that. A run nobody can
answer is not a safer run than one that can be answered carefully.

So the run config may name exact immutable post ids, and for each one the body
that was read:

```json
"operator_acknowledgements": [
  {
    "id": "5107483039",
    "body_evidence": "9f2c…64 lower-case hex characters…"
  }
]
```

A publisher-authored post may spend acknowledgement lines when, and only when,
its own id is listed there *and* it still says what the pinned digest was taken
over. What that authorizes is one post the operator read before launch, saying
what it said then — never a login, never a shape, never a pattern, and never an
id on its own. An id survives every later edit, so an authorization stored as an
id alone is an authorization of whatever that post is changed to say afterwards,
and on the repository this seam exists for the account that can make that edit is
the publishing login itself. Concretely:

- **absent or `[]` is the strict default**, unchanged in every respect;
- the same account's *next* post is refused. What is pinned is one post, and
  nothing about the account carries over to anything else it writes;
- **the same post, edited after it was pinned, is refused.** Not only when the
  edit breaks the grammar: a rewrite into different, perfectly valid
  acknowledgement lines is refused too, because those lines are not the ones
  anybody read. The stop names such a pin under
  `operator_pinned_acknowledgements_changed`, so a lapsed authorization does not
  read like a mistyped id. Re-read the post, re-derive its evidence, and pin it
  again — that is the operator saying they have read what it says now;
- a pinned post is exempt from nothing else. The exact line grammar,
  immutable-id matching, chronology, the single unresolved-to-cleared
  transition, residual prose, and native review/thread resolution all still
  decide, so a mixed post spends its valid lines and its own remaining prose
  stays unresolved until a *separately* pinned later post clears that id;
- a pinned post is still feedback in its own right — pinning grants
  acknowledgement authority, not an exemption from being read;
- **nothing this run published can be reached by a pin, whatever it says now.**
  A lane artifact is refused because of the immutable id it carries, not because
  of the body it currently holds: an artifact that did not exist until a lane
  posted it cannot be one an operator read beforehand, and rewriting it does not
  turn it into one. Editing a verified artifact does cost it its *ownership* —
  that is how a rewritten artifact goes back to being read as feedback — and the
  two answers are kept separate precisely so that lapse cannot hand it the
  authority the denial exists to withhold;
- an id that names nothing on the PR does nothing, silently and safely.

`body_evidence` is the same digest the tool keeps for its own published
artifacts — `sha256` over the post's body and review state — so there is one
notion of "still the post we mean" rather than two. Derive it from the post
GitHub is serving:

```bash
# a conversation comment: its own id, and no review state
gh api repos/OWNER/NAME/issues/comments/5107483039 | python3 -c '
import hashlib, json, sys
post = json.load(sys.stdin)
payload = json.dumps([post["body"], ""], ensure_ascii=False)
print(hashlib.sha256(payload.encode("utf-8")).hexdigest())'

# a review: pin it as "review:<id>", and its state is part of the evidence
gh api repos/OWNER/NAME/pulls/16/reviews/4801303218 | python3 -c '
import hashlib, json, sys
post = json.load(sys.stdin)
payload = json.dumps([post["body"], post["state"].strip().upper()], ensure_ascii=False)
print(hashlib.sha256(payload.encode("utf-8")).hexdigest())'
```

Those are the only two surfaces a pin applies to; an inline thread comment is
resolved by its thread and never acknowledges anything. Read the post before you
run this: the digest records *that* you read it, and only you can supply the part
where you did.

There is no login allowlist, no approval service, no token or signature
protocol, and no third identity: the whole seam is a bounded list of pins
(sixteen at most) whose ids `check-config` prints back before a run starts, and
which every `needs-Karan` stop repeats as
`operator_pinned_acknowledgements` so the authorization in force is visible
beside the feedback it did not clear.

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

`SEVERITY=` is one of exactly those three lowercase words; `ID=` is 1–64
characters, the first a lowercase letter or digit and the rest lowercase
letters, digits, `.`, `_`, or `-`, unique within the lane's output; the
separator is exactly two hyphens with one space on each side; and `<summary>`
is 1–300 characters on that line alone — exactly 1–300, and a summary inside
that bound comes back out character for character. A parser that took one more
character than the prompt asked for would then have to shorten it to store it,
and two summaries that differ only inside the discarded part become one stored
value, which is the difference the one-to-one comparison below is trying to see.
An actual credential in a summary is redacted, and that is the only thing that
may differ from what the lane wrote.

That grammar is stated verbatim in the prompt the reviewer adapter generates and
round-tripped through the parser that will judge the **final message**. The
control plane then renders those parsed records into the relay artifact. A
reviewer no longer has to reproduce the same machine-readable data in both its
final message and a prose artifact, which removes the transport failure where a
real blocker existed but had no relayable record.

Parsing is unforgiving on purpose. Exactly one `DONE:` line may appear, it must
be the final non-empty line, the SHA must equal the bound head byte for byte, and
`BLOCKING=<count>` must reconcile with the findings above it. The prepared
artifact's `STATUS` and `BLOCKING` declarations must match that verdict. Lane
output is untrusted, so a body that quotes or forges a marker, repeats a finding
id, or echoes the grammar back as an example fails the run closed instead of
being read as a verdict.

A count is not a record, so the **published** artifact is held to the canonical
final-message records as well as to the count. Before relay, the parent renders
those records deterministically into its publication copy; a prepared artifact
with no structured records is therefore relayable without losing the reviewer's
narrative. If the prepared artifact does include `FINDING:` records, the same
[`verdicts.finding_records`](src/pr_prover/verdicts.py) parser reads them and
requires exact parity with the final verdict. Missing prepared records are
normalized; extra, conflicting, duplicated, malformed, renamed, or rewritten
records still stop the run before publication.

That check runs twice, on the two surfaces it has to be true of. Validating the
prepared file proves what the relay was *handed*; it says nothing about what
landed. A truncation or substitution between the file and the pull request keeps
the whole declaration block intact — the configured author and signature, the
role, the runtime, the exact head, `STATUS=fail`, `BLOCKING=1` — and loses the
records, so the readback that decides whether this run may call its transport
complete parses the published body with the same grammar and reconciles it
against the same findings. A published artifact that declares a blocker and
states none of them is a readback failure, not transport.

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

The one key a head change deliberately does *not* drop is the map of artifact
ids this run owns to the publication evidence readback verified for each. A
finding is evidence about one commit, but an artifact this run published for an
earlier head is still not human feedback — and cycle two has to recognise what
cycle one posted, which is impossible to rediscover from a body anybody could
copy.

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
Reset never guesses at worktree ownership or deletes worktrees. Every run gives
each gate, reviewer, and builder attempt a fresh opaque run suffix, so a retained
clean exact-head checkout remains inspectable while reset plus a retry creates a
new path instead of colliding with it.

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
- Every attempt gets a fresh worktree, detached at one verified SHA. Each path
  carries a new opaque per-run suffix, so an existing retained path is refused
  rather than reused and cannot block a reset plus retry; worktrees this run did
  not create cannot be removed.
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

One more file is worth naming, because it asks a different kind of question.
Every other module proves a seam; [`tests/test_integration_matrix.py`](tests/test_integration_matrix.py)
proves that the seams still hold *composed*, across a sequence of heads — the
ordered pass from inspection through to the rendered report, several
repository-native gates at once, visual QA selected deliberately and evidenced
on the exact head, a quiet builder distinguished from a stalled one, and the
artifact defects that must stop a run rather than reach the pull request.

"Evidenced" there is meant literally, and "decode" is meant literally too. The
scripted visual lane writes real image files and a head-bound manifest outside
the checkout it rendered from, and the case reads them back: the files exist,
are the size the manifest declares, are recorded against the head the lane was
handed, and decode — the complete chunk stream walked with exact bounds and
checksums, no bytes after `IEND`, every chunk type a legal four-letter code with
PNG's reserved third byte uppercase, the chunk order the format requires (one
13-byte `IHDR` first, one or more consecutive `IDAT`, one empty `IEND` last, and
no unknown critical chunk), the generated header format required, and the image
data concatenated, decompressed to completion, and checked to be exactly the
scanlines those dimensions need. Its negative cases are what give that meaning —
a lane that only prints a sentence naming the head, a declared file that is not
an image, one whose header is impeccable and whose image data is corrupt,
truncated, absent, mis-checksummed, or over-declared, one whose chunks are
well-formed in an order no PNG may have or under a type code no PNG may spell,
an image that is not its declared size, and well-formed evidence recorded
against a different head are each refused —
while an ordinary image whose compressed stream is split across consecutive
`IDAT` chunks, or which carries unrecognised ancillary chunks around that run, is
still accepted. Producing and reading those files is test support inside
that module; `pr_prover` itself stores and validates no images, and what a
browser lane's screenshots *mean* remains that gate's judgement rather than this
tool's.

Its load-bearing case is the one a passing loop cannot check for itself. A
builder can satisfy a gate by deleting the test that failed it, and every
mechanical measure this tool owns — the gate, the five-way push agreement, the
comment readback, the artifact lifecycle — is then green. What answers is the
adversarial review triad, and the fixture pins the consequence rather than the
intention: on a head whose only qualification is a metric the builder rewrote,
no `merge-ready` is reachable. The same fixture run with reviewers that share
the builder's framing reports `merge-ready`, which is why the adversarial
stance in [`MISSION.md`](MISSION.md) is load-bearing rather than stylistic.
