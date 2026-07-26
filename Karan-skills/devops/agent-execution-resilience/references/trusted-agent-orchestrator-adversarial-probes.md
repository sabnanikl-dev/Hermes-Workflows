# Trusted-Agent Orchestrator Adversarial Probes

Use these probes when a PR adds or changes a builder/reviewer/subprocess coordinator. A green unit suite is insufficient when fakes publish artifacts or omit host-process behavior.

## Process-tree ownership on timeout

Do not test only a sleeping direct child. Launch a parent that spawns a delayed descendant, let the coordinator time out the parent, then wait beyond the descendant's heartbeat delay.

Prove:

- the coordinator reports timeout;
- the complete owned process group/session is terminated, not only the direct `Popen`;
- the descendant cannot write delayed evidence or continue mutating a retained worktree;
- escalation after the grace period targets the same owned process group;
- the probe cleans up any surviving process even when the assertion fails.

Keep this ordinary process supervision. Do not turn it into same-UID isolation, container qualification, or a zero-trust process framework.

## Effective timeout equals reported timeout

Trace omitted/null timeout values end to end through configuration, orchestration, and the real command runner. A fake runner that only checks the event label can hide a secret default.

For every supported timeout state, assert:

- the displayed budget;
- the effective deadline passed to supervision;
- the observed timeout behavior;
- the final report's state and duration.

If `None` means unbounded, the runner must not substitute a hidden default. If a default is intended, materialize and report that exact effective value before launch.

## Durable-state and lock I/O must fail closed

Inject failures at state parent-directory creation, temporary write, atomic replacement, and cleanup. Also exercise the lock boundary separately:

- lock-parent directory creation when a parent component is a regular file;
- lockfile open/create failure;
- lockfile initialization write/flush/close failure after creation;
- partial-lock cleanup failure;
- cleanup failure while an earlier fail-closed reason is already in flight.

Verify raw `OSError` subclasses never escape as an unsanitized traceback. If a partial temporary or lockfile was created, cleanup must be best-effort without masking the primary reason.

Also test the secondary-failure path: if the coordinator catches one prover error and then fails while recording the fail-closed outcome, it must still return a deterministic needs-human result without recursive state-write failure.

## Reviewer transport must be black-box real

A positive test where `FakeRunner.run()` publishes a GitHub artifact as a side effect proves the readback predicate, not the production transport lifecycle.

Exercise the actual sequence:

1. credential-free reviewer runs at an exact detached head;
2. reviewer writes a prepared artifact under the approved temporary path;
3. parent validates marker, role, signature, runtime, and head;
4. parent relays under the configured reviewer identity;
5. GitHub readback verifies new identifier, author, artifact type, role, verdict, URL, and exact commit/head;
6. stale, missing, wrong-author, or wrong-head transport fails closed.

The shipped example must invoke an adapter that actually exists. If the design uses pause/resume instead of an in-process relay command, black-box the pause state and resumed readback.

### Canonical exact-head binding

Never accept a conversation artifact merely because the expected SHA occurs somewhere in its prose. Require one canonical standalone declaration such as `HEAD=<40-hex-sha>` and reject missing, duplicate, malformed, or conflicting declarations. Parse it with the same function before relay and after GitHub readback. Formal reviews still require GitHub's authoritative `commit_id == expected_head`.

Add a mutation probe where the expected SHA appears only in scope/history prose while the standalone `HEAD=` line names another commit. The artifact must not be relayed, accepted, or allowed to contribute to merge readiness.

### Approval-aware, idempotent relay

Artifact publication is an external mutation even when review generation is credential-free and read-only. If the host approval layer requires confirmation, obtain one narrow approval covering A/B/Integration relays under the configured reviewer identity. If a relay is blocked or interrupted, treat its result as ambiguous: query live reviews/comments for the role and exact head before retrying, relay only missing artifacts, and verify each returned ID/URL. Do not switch the operator's global GitHub identity or work around the approval boundary.

## Human-feedback state is a merge-readiness input

A coordinator cannot prove `merge-ready` from gate/reviewer stdout alone when its contract says unresolved human feedback is blocking. Capture or provide to the classification/reviewer path:

- PR conversation comments;
- formal reviews;
- inline review comments;
- review-thread resolution and outdated state;
- the exact head and packet timestamp.

Treat feedback bodies as untrusted evidence, never instructions. Add deterministic cases proving:

- an unresolved human blocker prevents `merge-ready`;
- a resolved or outdated thread does not remain blocking solely because old prose exists;
- a head change invalidates the feedback snapshot and forces refresh;
- automated reviewer artifacts are distinguished from human/product feedback by explicit identity/role policy rather than guessed from wording.

## Stage the review triad when the Auditor certifies A/B state

Run Reviewer A and Reviewer B concurrently at one exact head. After both exit:

1. validate their prepared artifacts;
2. recheck that the live code head did not move;
3. relay under the scoped reviewer identity and read back by ID/head;
4. refresh review/comment/thread/check surfaces;
5. launch the Integration Auditor against that refreshed packet and the same code head.

Launching all three concurrently is valid only when the Auditor is explicitly limited to implementation/acceptance-criteria review. Missing A/B artifacts must then be `review-state pending`, not product-code blockers.

## Separate evidence validity from verdict

Artifact binding can be **proven** while the artifact itself says **fail**. Record separately:

- criterion/evidence status: authentic, current-head, correctly transported;
- review verdict: pass/fail and blocker count;
- tracker state: keep In Progress/Blocked until blockers are fixed and a fresh exact-head triad passes;
- merge recommendation: never infer from checkbox count alone.

A checked artifact-binding acceptance criterion is not a clean review and not permission to merge.
