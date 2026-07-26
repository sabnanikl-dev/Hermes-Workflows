---
name: cross-system-mission-control
description: Design and operate bounded, resumable missions that coordinate work across trackers, code repositories, specialist agents, durable knowledge, and human approval gates.
tags: [orchestration, mission-control, linear, github, resumability, approvals]
---

# Cross-System Mission Control

Use when a user gives a broad outcome such as “finish this project,” “take this workstream to the finish line,” or “work through the related tracker and repository issues one by one.”

This skill governs the control plane around existing tracker-, coding-, review-, and knowledge-specific skills. It does not replace them.

## Core Principle

A broad mission is safe only when it can be reconstructed from authoritative systems without relying on chat history. The controller must resume active work, select deterministically, route least-privilege workers, verify all mutations, and pause at explicit human gates.

## Source-of-Truth Boundaries

Define ownership before execution:

- Work tracker: non-coding contracts, decisions, dependencies, approvals, claims, and closeout evidence.
- Code tracker/repository: coding issues, branches, commits, PRs, reviews, checks, and engineering evidence.
- Durable knowledge system: reusable business/project knowledge and lessons, never live task state.
- Local ledger: optional execution cache only; never the sole authority.
- Human conversation: steering and approval surface, not durable execution evidence by itself.

Do not mirror every issue into every system. Use explicit cross-system links and mappings.

## Mission Contract

Before autonomous execution, require one version-bound mission root or manifest containing:

1. Intended outcome and definition of complete.
2. Ordered work and hard dependencies.
3. Explicitly parallel-safe groups.
4. Cross-system issue mappings and gate ownership.
5. Readiness requirements.
6. Standing authority for routine actions.
7. Human-only gates.
8. Interruption, conflict, and stop conditions.
9. Durable-knowledge closeout requirements.
10. Monitoring or delayed-completion requirements.

Bind approval to the exact contract revision or digest. Material edits invalidate prior approval.

Draft the contract from a read-only recon of the live trackers and repositories — real issue IDs, current PR review states, active claims — never from memory or prose alone. The recon doubles as the gap list for step 2 of the implementation sequence: it surfaces missing hard-dependency relations, parent/child status ambiguity, and open repair loops the mission must resume before selecting new work. Resolve "definition of complete" scope questions (e.g. whether production cutover and post-cutover monitoring are in scope) as explicit recorded decisions inside the contract before freezing.

## Authority Envelope

Separate routine execution from sensitive authority.

Routine authority may include read-only discovery, issue-contract grooming without changing approved intent, claims, non-final tracker transitions, branches/worktrees, implementation, tests, commits, pushes, PR creation, independent review, technical documentation, and source-backed durable-knowledge promotion.

Keep explicit human gates for merge, production deploy, DNS/domain changes, account/user/permission changes, publication, client-facing sends, purchases, credential entry, CAPTCHA/password prompts, legal/privacy/policy decisions, and materially conflicting business or architecture choices.

A broad mission phrase never silently expands these gates.

## Deterministic Inspection

Inspection and selection should be read-only. Model outcomes explicitly:

- `RESUME_ACTIVE`
- `SELECT_TRACKER_WORK`
- `SELECT_CODE_WORK`
- `WAITING_FOR_REVIEW`
- `WAITING_FOR_MERGE`
- `WAITING_FOR_HUMAN_DECISION`
- `WAITING_FOR_LIVE_APPROVAL`
- `MONITORING`
- `COMPLETE`
- `CONFLICT`

Fail closed on truncated pagination, duplicate active claims, stale approval digests, unresolved dependencies, contradictory mappings, stale PR heads/reviews, ambiguous local WIP, or multiple active issues without explicit parallel authority.

Resume or repair active work before selecting new work.

## Cross-System Mapping

Use machine-readable links for relationships such as:

- tracker decision/readiness issue → repository implementation issue;
- repository implementation issue → tracker approvals required for activation;
- cutover issue → implementation and operational prerequisites;
- post-cutover monitoring → verified cutover completion.

Prefer native dependency relations for hard dependencies, explicit links in both issue bodies, and a structured mapping section in the mission manifest. Prose mentions alone are not enough for deterministic selection.

## Execution Loop

1. Reconstruct complete live state.
2. Resume active work or repair a conflict.
3. Otherwise select exactly one eligible issue or one approved parallel-safe group.
4. Create a revision-bound claim and execution packet.
5. Route to the narrowest role-native worker.
6. Verify output and external mutations independently.
7. Run the appropriate independent review.
8. Perform durable-knowledge closeout.
9. Advance the authoritative tracker with direct readback.
10. Repeat until waiting, conflict, human gate, monitoring, or complete.

Workers must not self-approve, create human approval markers, or perform final tracker transitions unless the contract explicitly grants that narrow action.

## Durable Supervision

Use a persistent supervisor only after the read-only inspector and fixture suite pass.

The supervisor must:

- bind to one exact mission root and revision;
- acquire a mission lock;
- permit one active executable issue unless parallelism is explicit;
- remain quiet during normal progress;
- report meaningful state changes;
- pause at human gates;
- resume after verified approvals or merges;
- survive fresh sessions and restarts by reconstructing authority from source systems;
- self-disable at mission completion.

Do not create a generic recurring job that searches for arbitrary work.

## Human-Gate Reporting

Make pauses decision-ready:

- state what is verified complete;
- state the exact decision or approval needed;
- list options and consequences when useful;
- state what live actions have not occurred;
- record the decision in the authoritative system and verify readback before resuming.

Batch related human decisions rather than interrupting for routine mechanics.

## Implementation Sequence

1. Freeze the mission contract and authority envelope.
2. Normalize tracker state and cross-system mappings.
3. Build and fixture-test a read-only inspector.
4. Add bounded claims, routing, verification, and closeout.
5. Add durable supervision and recovery.
6. Dogfood one low-risk, non-production issue.
7. Obtain independent acceptance before activating the full mission.

See `references/goal-contract-authoring.md` before expressing a mission as a Hermes `/goal` — the judge hard-truncates goal text at 2000 chars and the contract block at 2500, so a long prose goal silently loses most of its enforcement. That reference covers the measured limits, the pointer-plus-gate split, and why the `verification` field must name a runnable command.

See `references/mission-plan-checklist.md` when capturing the architecture as a plan before implementation. See `references/mission-activation-wiring.md` for the tracker-mutation recipe when activating an approved contract (mission-root creation, re-parenting/orphan detection, blocks verification via inverseRelations, two-way repo⇄tracker links, Linear state-by-type trap).

See `references/narrowing-live-mission-hierarchies.md` before replacing an overbuilt live parent contract with a smaller one. It covers dispositioning active versus historical/superseded children, preserving original evidence and a pre-edit snapshot, rebuilding the dependency DAG without parent/pilot cycles, keeping one GitHub implementation issue/PR, and verifying every tracker mutation by direct readback.

See `references/github-visible-claim-and-progressive-acceptance-sync.md` when a tracker acceptance slice drives one GitHub issue/PR. It covers remote branch visibility at claim time, exact-head Codex review/frozen repair ledgers, and progressively checking tracker criteria from verified evidence with direct readback.

## Verification

Fixture at minimum:

- one eligible tracker issue;
- one active worker;
- one open PR;
- merged PR with stale tracker state;
- multiple active issues conflict;
- stale approval after body edit;
- truncated connections;
- unmet dependency;
- missing cross-system mapping;
- human merge gate;
- live/production gate;
- delayed monitoring state;
- missing durable-knowledge closeout;
- interrupted run resumes safely;
- duplicate claim rejected;
- completion disables the supervisor.

Runtime smoke tests should cover worker grants, builder auth, remote push verification, independent review launch, knowledge write/readback, tracker mutation/readback, stale notification rejection, merge detection, and no continuation past a human gate.

## Contract Hardening Patterns

When drafting or hardening a mission contract against a Sovereign-Rig-style control plane (owner-controlled files, replaceable model executors), apply the checklist in `references/mission-contract-hardening.md`. Key moves that recur across missions:

- **Path indirection:** never hardcode a local clone path when multiple clones of the same remote exist. Record the operational clone as an explicit decision in the contract; treat changing it as a material edit.
- **Mutual exclusion:** if a separate effort (repo canonicalization, vault migration, control-plane buildout) could move or prune the mission's working paths, state the block explicitly in both documents.
- **Claims as tracker comments** carrying contract revision + digest + packet digest + executor + TTL — never local-only state — so crash recovery reconstructs from trackers alone.
- **Executor provenance** in claims, PR bodies, and closeouts, so work is auditable after a model/brain swap.
- **Digest freeze mechanics:** SHA-256 of the contract file's *pre-freeze bytes* (recording the digest inside the file mutates it, so a self-referential digest can never match current bytes). Hash the file exactly as approved, record that hash in frontmatter + approval block + tracker mission root, label it "pre-freeze bytes," and have the supervisor bind to the recorded string — not a live re-hash of the mutated file. Define which sections are material (bump revision) vs groomable.
- **Explicit inspection state machine** (RESUME_ACTIVE … CONFLICT … COMPLETE) as a table, not prose stop-conditions.
- **Monitoring states need a mechanism,** not just intent: revision-bound cron, watchdog cadence, end date derived from a verified event (e.g. cutover date), findings to the tracker only, self-disable.
- **Independence clause:** the mission must not depend on an unapproved control plane; later registration/adoption is additive.

## Pitfalls

- Do not treat a single-root work-order inspector as proof that a project-level mission is ready.
- Do not use chat history as execution authority.
- Do not let a local ledger become a hidden tracker.
- **Do not route mission state through a local board system (e.g. Hermes Kanban) in any role — not as tracker, lane mirror, or visibility layer. Karan rejected this explicitly (2026-07-24) after the kanban.db corruption history surfaced; mission authority stays in Linear/GitHub and must be reconstructible with all local board state deleted. Do not re-propose it.**
- Do not infer approval from priority, assignment, labels, or prose.
- Do not start new work while active work, an open PR, or a repair loop needs resolution.
- Do not treat a local branch/worktree as a GitHub-visible claim. When remote branch creation is authorized, create/link the remote claim at pickup or explicitly disclose that GitHub will remain blank until push/PR.
- Do not defer every acceptance checkbox to final closeout or check behavior optimistically at draft-PR creation. Update exact criteria progressively from independent evidence, read back each full-body mutation, and keep reviewer-blocked criteria unchecked.
- Do not let one worker plan, implement, review, approve, and close its own work.
- Do not turn durable knowledge into a parallel task tracker.
- Do not confuse writing a mission plan with authorizing implementation or live mutations.
- Do not leave "which local clone/workdir" implicit — a supervisor that resolves the repo by habit can build in a clone a later consolidation retires.
- **Do not assume a long `/goal` is enforced.** The goal judge truncates goal text at 2000 chars and the contract block at 2500. A 38,707-char `/goal` (2026-07-25) lost 94.8% of its content — every PASS criterion and ESCALATE trigger sat past the cut and was never evaluated, while the operator believed 438 lines of gates were live. Measure the char count and move the bulk into a hash-pinned contract file. See `references/goal-contract-authoring.md`.
- **Do not let the mission write its own completion oracle.** If the agent being judged can edit the verifier that judges it, the independence guarantee is void — an agent one assertion short of ESCALATE has both motive and write access. Produce the verifier in a prior invocation, adversarially review it, hash-pin it, and make editing it an ESCALATE trigger. Independence comes from temporal ordering + immutability + review, not from who typed it.
