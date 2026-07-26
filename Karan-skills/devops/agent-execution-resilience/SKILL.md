---
name: agent-execution-resilience
description: Operate security-sensitive autonomous coding/review runs through live sandbox proof, reviewer timeouts, model quota/auth interruptions, durable handoffs, and verified resume without losing or overclaiming work.
version: 1.3.0
author: Hermes Agent
metadata:
  hermes:
    tags: [agents, resilience, sandbox, verification, handoff, recovery]
    related_skills: [autonomous-pr-prover, scoped-child-agent-execution, scheduled-monitoring-workflows, linear-worker-execution]
---

# Agent Execution Resilience

## Purpose

Use this skill when a long-running builder, reviewer, or integration-audit lane is security-sensitive and may be interrupted by provider quota, authentication/session boundaries, timeout, sandbox startup failure, or context loss.

The goal is not merely to restart the command. The goal is to preserve authority boundaries, distinguish valid proof from partial evidence, resume without destroying WIP, and leave a durable handoff another session can execute safely.

## Triggers

Load this skill when:

- an autonomous builder/reviewer exits after creating partial WIP;
- a pinned model hits quota or session limits;
- a reviewer times out after writing an artifact;
- generated sandbox settings pass deterministic tests but real enforcement is uncertain;
- a live sandbox probe reveals behavior that the local policy model missed;
- a task must pause and be resumed by a cron/fresh session;
- Linear/GitHub needs an auditable handoff rather than a vague progress note.

## Core invariants

1. **Never destroy unknown WIP.** No reset, clean, stash, checkout-over, rebase, or history rewrite during recovery.
2. **Pinned runtime remains pinned.** Quota/auth failure is not permission to switch models or profiles silently.
3. **Live enforcement outranks generated policy.** JSON shape and local decision helpers are necessary but not sufficient proof of an OS sandbox.
4. **Timeout invalidates the lane result.** A timed-out reviewer artifact is not an official pass/fail, though independently reproducible findings may still be real.
5. **Proof is head-bound.** Separate tests for the last committed head from tests for current uncommitted WIP.
6. **Resume prompts are self-contained.** A fresh session must not need the original chat to understand paths, blockers, authority, or verification.
7. **External state is read back directly.** Capture comment/review/commit IDs and verify them by ID or exact head; do not infer success from command exit alone.
8. **No authority creep during recovery.** A resume job inherits only the already-approved task scope; no merge, deploy, credential access, account changes, or new external mutations.
9. **Calibrate hardening to the mission trust model.** If Claude/Codex are trusted for scoped repository work and Karan retains merge authority, preserve exact-head/readback/worktree controls without inventing hostile same-UID containment. Reliability hardening and zero-trust tenancy are different products.
10. **Treat continuation approval as bounded but durable.** When Karan says “continue until mergeable” (or equivalent), do not stop after each builder/reviewer completion to request the same authorization again. Continue through every remaining normal fix cycle, verification gate, credential-free review launch, transport-only relay, and evidence/PR-metadata correction needed for a technical merge-ready verdict. The phrase never authorizes the merge itself, a deploy, authority expansion, or a cycle-cap exception.

## Procedure

### 1. Freeze and inventory

Immediately inspect and record:

- repository/worktree/branch;
- last committed local SHA, remote branch SHA, and PR head when applicable;
- `git status --short --branch`;
- diff statistics and `git diff --check`;
- modified/untracked paths;
- known probe artifacts or strays that must not be committed;
- process ID, exit code, and bounded reason;
- which verification results cover the committed head versus current WIP.

Do not clean anything while another process may still be writing. Confirm process state and recent file activity first.

### 2. Classify the interruption

- **Provider quota/session reset:** preserve WIP; schedule a resume after the reported reset if it is near-term.
- **Authentication/session mismatch:** verify the exact CLI's auth status and run a no-tool smoke. Preserve host OAuth/keychain state; remove explicit remote credentials and scrub descendants instead of blanking the entire environment.
- **Reviewer timeout:** invalidate the lane result. Inspect artifacts/transcript only as leads, independently reproduce findings, and require a fresh reviewer after fixes.
- **Sandbox unavailable:** if the approved mission requires a sandbox, fail closed and never continue unsandboxed merely because the task is in flight. If the mission explicitly trusts the scoped agent and does not require hostile-tenant isolation, do not manufacture a sandbox gate; use the trusted launch/readback path instead.
- **Unknown/partial side effect:** inspect the target system before retrying to prevent duplicate comments, pushes, or updates.

### 3. Prove live sandbox behavior

Run deterministic policy-model tests first, then real disposable agent probes against exact generated settings. Preserve individual assertions for:

- authorized worktree and lane-owned paths;
- immutable runtime/input/settings/MCP paths;
- sibling/foreign lanes and broker material;
- operator-home credentials and unrelated-home paths;
- unrelated secrets outside HOME;
- configured credential files outside HOME and nested inside reopened roots;
- external network, local TCP binding, and unauthorized Unix sockets;
- fail-closed behavior when the OS sandbox launcher is unavailable.

See `references/live-sandbox-enforcement-probes.md`.

### 4. Prove subprocess ownership and orchestration behavior

For trusted-agent coordinators, do not let fake runners or direct-child-only timeout tests stand in for host behavior. Add disposable former-red probes for:

- **Process-tree cleanup:** a timed-out parent spawns a delayed descendant; prove the complete owned process group/session is terminated and the descendant cannot write after timeout. Clean up survivors even when the probe fails. This is ordinary process supervision, not same-UID isolation or container qualification.
- **Effective timeout truth:** pass omitted/null timeout values through configuration, orchestration, and the real runner; prove the displayed budget equals the enforced budget. A label such as “unbounded” must never hide a runner default.
- **Durable-state and lock failures:** inject state and lock parent-directory, temporary/initialization-write, atomic-replace, and cleanup failures; raw `OSError` subclasses must become sanitized deterministic needs-human results, including failure while recording an earlier fail-closed outcome. Partial lock cleanup must not mask the primary reason.
- **Real reviewer transport:** a fake runner that publishes a review as a side effect proves only the readback predicate. Black-box the credential-free reviewer → prepared artifact → parent relay/pause-resume → GitHub readback lifecycle and verify the shipped adapter actually exists.
- **Canonical artifact head binding:** conversation artifacts require exactly one standalone full-SHA `HEAD=` declaration that equals the bound head before relay and after readback; reject cases where the expected SHA appears only in prose. Formal reviews still require authoritative GitHub `commit_id` equality.
- **Human-feedback reconciliation and pagination completeness:** capture conversation comments through a fully paginated REST surface, paginate formal reviews and top-level review threads, and either paginate every nested thread-comment connection or fail closed when nested `pageInfo.hasNextPage` reports truncation. Never treat a convenience first-page response as complete. Prove later-page human blockers prevent `merge-ready`; malformed or incomplete pagination metadata fails closed; resolved/outdated feedback does not remain blocking by stale prose alone; head drift invalidates the collection; and all bodies remain untrusted evidence.
- **Real installed-adapter smoke before the formal triad:** when a change touches the repository-owned reviewer adapter, prepared artifact, relay, or feedback-read lifecycle, run one real credential-free installed-CLI smoke in a disposable exact-head worktree before A/B/Integration. A stub proves plumbing only. Require the machine marker, one canonical `HEAD=<sha>`, a clean worktree, scoped-identity relay, and ID/head readback. If this pre-triad smoke finds a partial omission inside an already-frozen blocker class, publish the artifact and use the one permitted corrective builder rerun inside that same cycle; a new blocker class or second omission still requires the normal stop/exception rule.
- **Metadata readback before packet freeze:** independently derive diff counts, test totals, commit presence, and PR-body claims from executable output such as `git diff --numstat`, the test runner, and live PR commit data. If a builder comment is materially stale, add a signed correction or refresh the PR body before reviewers; preserve the historical artifact rather than editing away evidence.
- **Approval-aware relay:** if external-post approval blocks or interrupts a relay, treat state as ambiguous, inspect live artifacts before retrying, relay only missing roles, and verify author/type/head/verdict/URL without switching the operator's global GitHub identity. Apply the same rule when a relay command prints a concrete URL or ID but later exits nonzero because post-processing, cleanup, or a shell trap failed: the side effect may already be live, so read it back by ID/role/head before deciding whether anything is missing.

Keep evidence validity separate from verdict: exact-head identity/role/readback may be proven even when the authenticated artifact says `fail`. A checked artifact-binding criterion is not merge readiness, tracker completion, or merge authority.

Detailed probe and staged-triad recipe: `references/trusted-agent-orchestrator-adversarial-probes.md`.

### 5. Build the resume packet

A continuable resume prompt/job must include:

- exact worktree, repo, PR/issue, branch, and full committed SHA;
- preserved WIP and explicit no-reset rule;
- frozen blocker classes and non-goals;
- prompt/settings/empty-MCP/artifact paths;
- known exited processes and temporary strays;
- pinned model and auth-safe launch shape;
- ordered independent verification matrix;
- authorized commit/push/comment/review operations;
- explicit no-merge/deploy/account/credential boundary;
- final readback requirements.

For a provider reset, prefer a one-shot continuable scheduler job to busy-polling. Cron-run sessions must not recursively schedule more jobs.

### 6. Leave a durable tracker handoff

Use a single comprehensive handoff comment, not a trail of ambiguous “still working” notes. Capture its returned ID and verify the exact comment directly.

See `references/interrupted-run-handoff.md`.

### 7. Resume and re-prove

After the pinned runtime smoke succeeds:

1. Tell the worker to inspect and complete existing WIP, not restart.
2. Keep the same frozen blocker class and authority boundary.
3. Independently inspect every changed file.
4. Remove only verified temporary strays.
5. Run full tests, compile/config/static gates, and real former-red probes.
6. If green and authorized, commit/push and verify remote/PR exact head.
7. Run fresh exact-head reviewers; never reuse timed-out/wrong-head artifacts.
8. Update durable tracker/PR evidence and read it back.

## Reviewer timeout rule

Keep these two questions separate:

- **Is this a valid reviewer result?** No, if the process timed out.
- **Did it surface a real defect?** Possibly; reproduce independently.

A complete-looking file written seconds before timeout does not become official. Use verified findings to reopen the corrective cycle, then rerun the entire required exact-head review set.

## macOS auth-preservation rule

For subscription-authenticated Claude Code on macOS, preserve the OAuth/keychain session environment. A fully blank environment may make a logged-in CLI appear unauthenticated. The durable recovery pattern is:

- preserve host session/auth state;
- remove explicit remote credentials such as `GH_TOKEN` only when the lane does not need to publish directly;
- use strict empty MCP and task-scoped tool permissions;
- start with `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` or the repository-owned child-environment scrubber when compatible with the lane;
- if that setting explicitly forces `--permission-mode dontAsk` back to default and blocks a trusted scoped builder, stop only the exact process, verify the tree, and relaunch once with `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=0` plus the explicit allowlist—never disable scrubbing globally;
- run a tiny no-tool smoke before resuming expensive work.

This records the fix pattern, not a claim that any tool is permanently broken.

## Verification checklist

Before reporting a recovered run as complete:

- [ ] No unknown process is still modifying the tree.
- [ ] WIP was preserved and scope-inspected.
- [ ] Temporary probe strays were verified and excluded.
- [ ] Both committed-head and WIP proof boundaries are stated accurately.
- [ ] Full deterministic tests/gates passed on final content.
- [ ] Live former-red sandbox/Git probes passed with individual evidence.
- [ ] Commit/push occurred only under explicit authorization.
- [ ] Remote and PR exact head were read back after push.
- [ ] Fresh reviewers completed without timeout on the final head.
- [ ] Tracker/PR artifacts were verified directly by ID/head.
- [ ] Merge/deploy/human gate was not bypassed.

## Pitfalls

- Do not call a timed-out reviewer artifact a valid failure merely because its prose is useful.
- Do not call generated sandbox JSON “live proof.”
- Do not treat `allowRead` as a global allowlist when the target sandbox uses deny-then-specific-reopen precedence.
- Do not keep polling through a known provider reset when a one-shot continuable resume is safer.
- Do not put prior-head test counts into a handoff as proof of uncommitted WIP.
- Do not omit known untracked probe files from the handoff.
- Do not retry uncertain external comments blindly; inspect by ID/content first.
- For reviewer-artifact relay, prefer a per-command scoped token for the configured reviewer identity and verify `gh api user` under that token. Do not mutate the globally active `gh` account as the normal path. If recovery temporarily switches it, use a guaranteed restoration path and verify the operator identity afterward before any further GitHub action.

## Related skills and overlap

This skill owns interruption recovery and proof continuity. `autonomous-pr-prover` owns the PR review/fix/re-review lifecycle; `scoped-child-agent-execution` owns bounded worker launch/supervision; `linear-worker-execution` owns Linear work-packet execution. Load them together when their scopes overlap.

## References

- `references/live-sandbox-enforcement-probes.md` — real-agent path/network/socket/fail-unavailable probe patterns.
- `references/interrupted-run-handoff.md` — self-contained resume packet and Linear handoff schema.
- `references/trusted-agent-launch-recovery.md` — trust-calibrated thin orchestration, Claude permission-mode recovery, direct artifact readback, and clean replacement recovery for overengineered drafts.
- `references/trusted-agent-orchestrator-adversarial-probes.md` — real process-tree, effective-timeout, state-I/O, reviewer-transport, staged-triad, and evidence-vs-verdict probes for trusted-agent coordinators.
- `references/feedback-pagination-and-installed-adapter-smoke.md` — complete GitHub feedback pagination, nested-connection fail-closed probes, real installed-adapter smoke, same-cycle corrective recovery, and metadata readback before packet freeze.
