# Retroactive Qualification Escalation — Worked Pattern

## Scenario shape

A staged implementation mission required three pre-existing launchers to be identified and smoke-tested before creating any GitHub issue, branch, worktree, or mutation. Live inspection later found:

- the launchers themselves existed before the GitHub mutation;
- the implementation issue and clean baseline worktree had already been created;
- no implementation commit, remote feature branch, or pull request existed;
- the required canonical identity/smoke qualification record did not exist before those mutations.

The correct result was terminal `ESCALATE`, not `PASS` and not an inferred baseline exception.

## Why launcher age was insufficient

The normative clause required the operator to **record** each launcher’s `lstat`, symlink chain, realpath, ownership/mode/size, SHA-256, version, and non-mutating pinned-runtime smoke before mutation. Filesystem birth dates proved only that the executables were older. They did not prove that the required inspection, credential isolation, model pins, or smokes happened in time.

Fresh smokes were still useful. They established that:

- the underlying trust root was healthy;
- model/provider/reasoning/sandbox pins worked;
- credential-free launch paths worked;
- override-denial policies worked;
- hashes remained stable.

Those findings reduced the uncertainty of a future human-approved amendment, but they did not change the chronology result.

## Evidence bundle pattern

The terminal evidence used:

- a frozen source-contract SHA-256;
- authoritative GitHub issue creation time;
- worktree birthtime and branch reflog;
- launcher absolute paths, symlink hops, realpaths, ownership/modes/sizes, hashes, and versions;
- credential-free smoke stdout/stderr and output hashes;
- explicit `qualification_record_predates_mutation: false`;
- a short decision explaining that post-mutation smokes cannot be grandfathered;
- an acyclic manifest whose SHA-256 named the evidence directory;
- `0700` directories and `0600` files;
- bounded secret scanning;
- final rehash of launchers and evidence.

## Reviewer retry pattern

The first read-only reviewer read/dumped the full large mission contract and exited before returning the required verdict. That output did not count.

The successful retry:

1. kept the same live-issue, source, and manifest hashes;
2. supplied the full live issue contract;
3. restricted the source read to the exact bootstrap clause;
4. required a short verdict with an exact completion marker;
5. defined PASS as “the evidence correctly supports ESCALATE,” not “the mission may continue.”

This produced a bounded zero-blocker exact-manifest verdict.

## Tracker closeout pattern

Because the child contract explicitly allowed terminal `PASS | ESCALATE`, the child was completed with `ESCALATE` evidence while:

- the parent stayed In Progress pending human decision;
- the next child stayed Backlog/blocked;
- the dependency relation remained intact;
- child and parent comments were read back directly by ID;
- repository state was rechecked as clean, with no remote feature branch or PR;
- a GitHub comment was intentionally omitted because the gate prohibited GitHub mutation.

The user-facing phrase should be explicit: **“The gate is done by escalation; the pipeline is not authorized to continue.”**

## Human recovery options

A future contract amendment may choose to grandfather an untouched baseline mutation or abandon/restart with a newly defined trust boundary, but the agent must not choose or execute either path under the original no-retroactive-certification contract. Bind any amendment to the exact baseline and evidence-manifest digest, then independently review the revised authority before selecting the successor.
