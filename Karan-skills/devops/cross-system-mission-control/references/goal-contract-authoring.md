# Authoring a `/goal` for a Long Mission

How to express a large mission contract through Hermes `/goal` without the
enforcement silently evaporating.

## The truncation constraint (verify before trusting)

`/goal` runs a judge model each turn to decide done / continue / wait. The judge
input is **hard-truncated** in `~/.hermes/hermes-agent/hermes_cli/goals.py`:

```python
goal=_truncate(goal, 2000),
contract_block=_truncate(contract_block, 2500),
response=_truncate(last_response, _JUDGE_RESPONSE_SNIPPET_CHARS),  # 4000
```

Consequences:

- **Goal text over ~2000 chars is invisible to the judge past the cutoff.**
  A 38,707-char `/goal` (a real case, 2026-07-25) lost **94.8%** of its content.
  The cut landed mid-sentence inside the coordinates preamble; every PASS
  criterion, ESCALATE trigger, and authority rule sat past it and was never
  evaluated. The operator believed 438 lines of gates were enforced. None were.
- The contract block (all five fields joined) is capped at 2500 total.
- Verify these constants rather than assuming — they may change:
  `grep -n "_truncate(goal\|contract_block, \|_JUDGE_RESPONSE_SNIPPET" \
   ~/.hermes/hermes-agent/hermes_cli/goals.py`

Measure before shipping any long goal:

```bash
python3 -c "
raw=open('GOAL.md').read()
print(len(raw), 'chars ->', round(100*(1-2000/len(raw)),1), 'pct invisible')"
```

The same truncation applies to the continuation prompt the agent receives each
turn, so an over-long goal degrades both adjudication *and* steering.

## Consequent structure: pointer + gate

Split the two jobs the oversized document was conflating.

**The contract is a file.** State machines, envelope schemas, canonical JSON
rules, full PASS matrices — reference material. On disk, hash-pinned, re-readable.
It must not live in a prompt that re-renders every turn.

**`/goal` is a pointer plus a gate.** Name the outcome, point at the contract
file, name the one command that proves done. Target ≤2000 chars.

Include in the goal text:

- the contract file's absolute path + pinned SHA-256, and "it governs on every
  conflict with your own judgement";
- **"re-read it after any context compression"** — a long mission will compress
  the contract out of context and the agent silently loses its spec;
- the single highest-consequence invariant, promoted out of the file (an
  invariant buried at line 77 of an unread document is not enforced);
- the phase sequence as ordered names, each requiring an evidence handoff —
  *what* must be true, not *how*;
- **autonomy stated once, positively**: name the safe local action classes
  ("read, write, test, commit, push, open the PR, run reviewers — you do not
  need to ask permission for any of that"). Repeating stop-and-ask semantics
  across many sections is what causes a persistent model to halt on safe reads.

## The `verification` field carries the load

Of the five contract fields, `verification` is where enforcement actually lives.
The judge decides DONE strictly against it and demands concrete evidence.

Prose verification ("independently proven", "materially satisfied") is
unenforceable *and* usually truncated away. Replace with one executable:

> Run `python3 /abs/path/verify-<mission>.py` and paste its full stdout. It
> exits 0 only when every gate in §PASS passes: <enumerate>. A green unit
> suite alone is NOT this verification.

A judge cannot misjudge `exit 0`. This converts enforcement from *hoping the
model read paragraph 340* into a deterministic check.

**This shifts trust onto the verifier.** A weak oracle that exits 0 is more
dangerous than vague prose because it looks authoritative. See the oracle
provenance rules in `deterministic-validator-review` — the verifier must be
written in a *prior* invocation, adversarially reviewed, and hash-frozen for
the run it judges.

## Field-mapping cheatsheet

| Field | Carries | Anti-pattern |
|---|---|---|
| `outcome` | end state, incl. what must remain *un*changed | restating the task title |
| `verification` | one runnable command + exit-0 semantics | "independently proven" |
| `constraints` | what must not break/mutate; attempt ceilings | repeating authorized actions |
| `boundaries` | write paths / read-only paths / executables | vague "the repo" |
| `stop_when` | ESCALATE triggers by name + terminal stop | "if something goes wrong" |

Aliases are accepted on input (`done when`→outcome, `evidence`/`proof`→
verification, `scope`/`files`→boundaries, `blocked`→stop_when).

## Pre-flight checklist

1. Contract file written, hashed, path absolute.
2. Goal text measured ≤2000 chars.
3. Contract block measured ≤2500 chars total across all five fields.
4. `verification` names a runnable command, not prose.
5. Verifier hash-pinned and frozen (constraints field forbids editing it).
6. Autonomy granted once; stop conditions named as discrete triggers.
7. Compression re-read instruction present.
