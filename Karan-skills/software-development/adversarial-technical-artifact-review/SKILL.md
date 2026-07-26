---
name: adversarial-technical-artifact-review
description: "Use when independently stress-testing technical feasibility reports, architecture documents, runbooks, migration plans, specifications, or other decision-critical artifacts with multiple reviewer agents and exact-hash closure."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [adversarial-review, architecture, feasibility, multi-agent, verification]
    related_skills: [code-review, autonomous-coding-agents, research-workflow]
---

# Adversarial Technical Artifact Review

## Purpose

Use this skill for decision-critical technical documents whose correctness depends on architecture, vendor/API behavior, operational constraints, security boundaries, or feasibility—not only source-code quality.

The goal is a material-readiness verdict bound to exact artifact bytes. It is not consensus theater and not an endless search for cosmetic improvements.

## Trigger Conditions

Use this workflow when the user asks to:

- poke holes in a feasibility or architecture report;
- have Claude Code, Codex, or other independent agents adversarially review a document;
- validate a migration plan, runbook, technical proposal, or system design before execution;
- fix review blockers and loop until reviewers say the artifact is ready;
- verify vendor/API/licensing claims that materially affect the recommendation.

## Core Invariants

1. **A pass is hash-bound.** Compute SHA-256 before dispatch. Every reviewer receives the exact path and expected hash. Any later edit invalidates the pass.
2. **Reviewers are read-only.** They identify failures; Hermes reconciles evidence and owns edits.
3. **Independent means independent.** Use different reviewer systems or isolated fresh contexts with the same contract. Never substitute a different runtime and mislabel it as the requested reviewer.
4. **Reviewer claims are leads, not authority.** Verify contested current facts against primary documentation before modifying the artifact.
5. **Material readiness is explicit.** P0/P1 block. P2 is non-blocking unless evidence shows it changes feasibility, safety, or the proposal decision.
6. **Process success is not verdict success.** A zero exit code does not equal PASS. Read and validate the review artifact and final marker.
7. **Live contract closure outranks green tests.** For issue-tracker controllers, independently read the bootstrap contract and live relation graph. Detect circular closeout gates, unauthorized approval markers, duplicate claims, missing required marker fields, and pagination that can hide active work or blockers.
8. **Concurrent edits invalidate code-review evidence too.** Hash implementation and tests before review and again before verdict. If they drift, reread the changed files and rerun the full suite plus adversarial probes against the final stable hashes.
9. **Contract review means the whole contract.** When the authority source is a Linear/GitHub work order, give a separate fresh reviewer the complete live issue body, approval/claim markers, relation state, implementation, tests, and run evidence. Require a criterion-by-criterion matrix; a code-diff review alone cannot certify lifecycle compliance.
10. **Exercise producer-consumer invariants with real generated artifacts.** Synthetic fixtures can accidentally create safer files than production code. For residue, grant, manifest, lock, or checkpoint formats, dogfood the real producer and have the real diagnostic/recovery consumer read its output, including owner, mode, link count, path type, digest binding, and cleanup behavior.
11. **Broad validator claims require class-wide mutations.** A correct current artifact plus a green positive suite does not prove a new fail-closed checker. Match the guarantee to the parser/grammar actually implemented, probe malformed/nested/alternate inputs across the claimed class, and narrow overbroad prose when a finite policy is the honest contract.
12. **Environment policy is not an OS authority boundary.** For autonomous-agent launchers, separately prove environment composition, filesystem/process isolation, lane-authenticated IPC, broker-handler shutdown, exact reviewed bytes, and committed changed-path containment. A synthetic HOME, process group, owner-only socket, clean `git status`, or claimed blocker IDs cannot stand in for those proofs. At the cycle cap, separate code-local fixes from missing platform primitives and require an explicit Continue/Narrow/Stop decision rather than silently redefining acceptance.
13. **A local sandbox-policy model does not certify the real client.** When code generates Claude Code sandbox settings, run the generated policy through the exact supported Claude version and OS sandbox. Prove required writes as well as denials, observe sandboxed `$TMPDIR` from inside Bash, and simulate sandbox startup failure. Do not assume `allowWrite` reopens a broad `denyWrite` because read rules use narrower-path precedence; keep exact immutable write denials and use `CLAUDE_CODE_TMPDIR` for lane-scoped temp. Validate tool side effects/markers, not model prose or the top-level Claude exit code. See `references/claude-sandbox-live-policy-qualification.md`.

## Workflow

### 1. Freeze and inspect the artifact

- Read the whole artifact and identify its decision claim.
- Compute SHA-256 and line count.
- Record path, hash, review round, reviewer identity, and read-only constraints.
- Define the pass criterion before dispatch: normally `P0=0` and `P1=0`.

### 2. Dispatch independent Round 1 reviewers

Give every reviewer the same broad attack surface:

- central product/feasibility claim;
- architecture authority and system-of-record boundaries;
- account, authentication, API, quota, and platform prerequisites;
- vendor licensing and client/provider ownership;
- hidden manual labor and staffing/coverage assumptions;
- approval binding, revision invalidation, and evidence semantics;
- retry ambiguity, duplication, cancellation, drift, and recovery;
- security, privacy, prompt injection, credentials, and public-media exposure;
- prototype scope versus the load-bearing production claim;
- monitoring, unknown states, incident handling, and go/no-go thresholds.

Require P0/P1 findings to include artifact lines, consequence, minimum correction, and supporting evidence where applicable.

For tracker-governed execution, the immutable review packet must also include:

- the complete current issue/work-order body and exact digest;
- live approval, claim, state, relation, blocker, and pagination readbacks;
- implementation and test hashes;
- interruption/retry/recovery transcripts with named checkpoints;
- before/after boundary reads for adjacent issues that must remain untouched;
- a required matrix of `PASS`, `FAIL`, `NOT YET`, or `NOT APPLICABLE` for every contract clause and acceptance criterion.

A requested reviewer runtime is part of the contract. If the user asks for Claude Code, run an actual fresh Claude Code lane; do not substitute a same-model subagent or a self-review.

### 3. Validate review output

For each lane:

- confirm the process completed;
- read the result file;
- verify the requested headings and final marker;
- reject malformed or partial reviews;
- do not infer PASS from silence or exit code.

Required final marker:

`DONE: STATUS=pass|fail P0=<n> P1=<n> P2=<n>`

### 4. Reconcile and research

- Merge overlapping findings by root cause, not wording.
- Separate factual claims from reviewer judgment.
- Use current first-party documentation for material platform/API/licensing claims.
- When a live account or commercial term cannot be proven, replace certainty with an explicit validation gate rather than guessing.
- Fix the architecture and operating contract, not merely prose around the weakness.

### 5. Revise the artifact

Typical corrections include:

- conditional feasibility instead of an unconditional promise;
- one authoritative approval/system-of-record plane;
- immutable approval bound to exact content, rules, destination, mode, and schedule;
- distinct scheduled, delivered, published, failed, missed, and unknown states;
- transactional outbox, reconciliation-before-retry, and no blind retries after ambiguous creates;
- explicit client-owned account/credential/licensing boundaries;
- measured human workload and named primary/backup coverage;
- a live authorized gate that actually tests the central product claim;
- numeric client-agreed acceptance thresholds before the gate starts.

### 6. Run fresh whole-artifact review

- Compute a new hash.
- Use fresh reviewer contexts.
- Ask reviewers to verify prior closure **and** search the whole revision for regressions or new blockers.
- Continue while either reviewer reports P0/P1.
- If useful P2 changes are incorporated after a pass, hash again and run a final regression review.

### 7. Close with exact evidence

Before reporting completion:

- re-hash the final artifact;
- read both final result files;
- confirm both markers say PASS with P0=0/P1=0;
- verify critical clauses exist in the final artifact;
- report final path, hash, review rounds, blocking findings fixed, final verdicts, and any residual P2 notes.

Do not modify the exact reviewed artifact after the final hash-bound pass unless you rerun the gate.

## Severity Contract

- **P0:** unsafe, destructive, legally/commercially prohibitive, or the artifact recommends an impossible architecture.
- **P1:** materially misleading feasibility, missing prerequisite, broken authority/evidence model, untested load-bearing claim, or operational gap likely to invalidate delivery.
- **P2:** useful precision, readability, optional hardening, or implementation detail that does not change the decision.

## Pitfalls

- Asking only whether prior findings were fixed; reviewers must re-read the whole revision.
- Letting two reviewers share one evolving context or edit the artifact themselves.
- Treating vendor marketing, search snippets, or reviewer assertions as primary evidence.
- Promising exactly-once external side effects where the provider does not expose idempotency/reconciliation guarantees.
- Treating scheduler acceptance, notification delivery, or a provider “Sent” status as proof of live publication.
- Using a free UI/content prototype to claim live account/API feasibility.
- Patching cosmetic P2 findings forever after both lanes already meet the declared material gate.
- Editing after PASS and still citing the old review hash.

## Reference

See `references/dual-review-exact-hash-loop.md` for reusable Round 1, re-review, and final-regression prompt contracts plus a closure checklist.
See `references/live-work-order-controller-review.md` for independent live-contract checks, circular closeout detection, fail-open authority/concurrency/pagination probes, proposed-status transition simulation, review-versus-Done verdict scoping, auxiliary-command conformance checks, and concurrent-hash-drift handling.
See `references/tracker-crash-recovery-contract-review.md` for real producer/consumer dogfood, forced wrapper interruption, fresh-session reconstruction, exact-bound recovery, replay resistance, and contract-wide reviewer packet requirements.
See `references/deterministic-validator-claim-closure.md` for mutation-based review of fail-closed validators, bounded HTML/routing grammars, finite forbidden-language policies, and anti-whack-a-mole closure.
See `references/agent-launcher-os-capability-boundaries.md` for autonomous-agent launcher review: environment versus OS isolation, same-UID socket/auth pitfalls, Claude Code strict-sandbox limits, `setsid` escape, broker-handler draining, reviewer byte integrity, changed-path containment, and Continue/Narrow/Stop adjudication.
See `references/claude-sandbox-live-policy-qualification.md` for exact-client/OS qualification of generated Claude Code sandbox policies, write-rule asymmetry, lane-scoped temp verification, and a macOS fail-if-unavailable probe.
