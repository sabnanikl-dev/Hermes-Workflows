---
name: agent-execution-resilience
description: Operate security-sensitive autonomous coding/review runs through live sandbox proof, reviewer timeouts, model quota/auth interruptions, durable handoffs, and verified resume without losing or overclaiming work.
version: 1.8.0
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
- a prover completed but an outer shell wrapper or supervisor reported a conflicting failure;
- a `needs-karan` stop exposes contradictory governing text that may require an additive clarification;
- a hardened launcher exits at usage/path/preflight boundaries before the agent starts;
- live PR-preview acceptance evidence is blocked by Vercel deployment protection or a shell/environment boundary;
- a preview, deployment, browser, or API gate attaches a credential to requests against an operator-supplied origin;
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
11. **Report execution state literally.** “Prepared/configured/at the review stage” is not “running.” Say a goal or lane is active only after a process was actually launched and a live handle/process-state check supports it. Use explicit states—prepared, launched/active, exited, paused/blocked—and include the process handle when one exists. If interrupted before launch, say so directly rather than implying background continuation.
12. **Bind credentials before egress.** A secret-bearing network gate must refuse any request whose origin is not the exact trusted origin derived from the deployment-binding trust root. HTTPS and shared-platform suffixes are not trust boundaries; refusal must happen before the first request, not after functional checks fail.
13. **Give long lanes bounded human-visible progress.** In Buzz/Telegram-style human-facing work, publish the launched PID/handle and do not go dark through a long silent model run. Poll live process plus repository/PR state at meaningful transitions and, when no milestone appears for roughly fifteen minutes, publish one concise factual update: active/exited, current commit/WIP/PR state, and next gate. Do not manufacture activity or send bare acknowledgements. Preserve channel-specific exceptions such as Discord final-only reporting.
14. **A local commit is not a completed builder handoff.** If a turn cap lands after commit but before push/PR/readback, report the PR as absent and the builder as incomplete. Preserve the commit and clean tree. A narrow same-cycle continuation may finish tests, push, PR creation, linkage, and readback; if implementation reasoning or code repair is needed, start a fresh bounded builder context instead of smuggling a new work cycle through continuation.

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

### 2.5 Distinguish launcher failure from a spent work cycle

A non-interactive builder launch that exits before any repository or external mutation because its permission mode denied the authorized edit/test surface is a **launcher failure**, not a substantive fix attempt. Before retrying, prove all of the following: the worktree remains clean at the same reviewed SHA; no commit or push landed; no PR body/comment/review changed; and the frozen blocker ledger is unchanged. Record the failed launch, inspect the installed CLI's current permission choices, correct only the task-scoped launcher contract, and rerun inside the same cycle. Once the builder mutates, commits, pushes, or materially adjudicates the blocker, normal cycle accounting applies—launcher recovery is never an unlimited builder-retry loophole.

Do not place a mutating builder under a managed read-only/safe mode unless a disposable preflight proves its intended edit and shell families are permitted. Preserve the isolated worktree, strict empty MCP, inherited subscription/keychain auth, explicit remote-credential removal, and task-scoped tool/command allowlist. If a broader non-interactive permission mode is required, keep the available tool set and prompt authority bounded; do not broaden system-wide authority silently.

### 2.5b Recover a post-edit verification denial without discarding the candidate

A different case begins when the builder **did edit** the bounded files but stopped before commit because its policy denied the required verification commands. That is neither a clean launcher failure nor a verified repair. Preserve the uncommitted candidate and let default Hermes take over only when the original task already authorizes the bounded repair and push.

Recovery order is load-bearing:

1. read the complete process log and prove no commit, push, review/comment, deploy, or other external mutation occurred;
2. snapshot local/remote/PR head equality, then inspect the entire uncommitted diff, changed paths, status, and `git diff --check` without cleaning or normalizing anything;
3. run the issue-required deterministic suite and former-red/adversarial probes directly against the candidate;
4. derive documentation counts and claims only from real output, then reconcile the narrowly affected docs;
5. commit only the verified bounded paths, rerun the required suite at the exact committed SHA, and push once; and
6. freshly verify remote branch, PR `headRefOid`, final PR commit, PR commit-list presence, checks, and clean worktree.

If the push succeeds but a later command in the same compound shell fails, do **not** retry the push. Treat transport as potentially complete, split the remaining work into read-only queries, and verify the existing side effect. If the candidate itself fails, preserve the evidence and route a fresh bounded builder or stop at the cycle cap rather than patching opportunistically.

See `references/post-edit-verification-denial-takeover.md` for a concise takeover checklist and failure classification matrix.

When the inner tool's retained outcome conflicts with its wrapper/supervisor, a `needs-karan` stop is caused by contradictory governing text, or the adapter fails before useful work, use `references/control-plane-stop-and-launcher-recovery.md`. It defines artifact-first recovery, additive-only contract clarification, blocker deduplication, repair-cycle accounting, current-argv/MCP preflight, and detached-child watchdog proof.

The exact-head review triad is serialized evidence collection, not an early-exit test: **Reviewer A → relay/readback → packet refresh → Reviewer B → relay/readback → packet refresh → Integration Auditor → relay/readback**. A valid blocker from Reviewer A is evidence that B and the Auditor must independently reproduce, refute, scope, and deduplicate; it is not permission to skip the remaining lanes. Stop the chain early only for head drift, incomplete/stale transport, infrastructure failure that invalidates the lane, or an explicit workflow contract that requires stopping. This is especially load-bearing after the final fix cycle, when the completed triad—not A alone—supports the bounded escalation and no-cycle-3 decision.

### 2.5a Fail-closed dependency-boundary probes and bounded exceptions

Before any expensive review run whose baseline gate carries a protected-preview or API credential, audit credential egress independently of the requested feature repair. Trace the free-form URL through parsing, client construction, request headers, and every redirect/manual hop. Use an injected client plus a sentinel—never the real secret and never an external request—to prove arbitrary and unrelated shared-platform origins cannot receive it. A wrapper's deployment-to-commit binding does not make a lower-level arbitrary-URL CLI safe. Require exact-origin capability binding and refusal before the first request; see `references/credential-bearing-network-gate-origin-binding.md`.

For privacy, consent, payment, or identity code, do not let green happy-path tests be the only proof. Before the final triad, inject failures at every foreign dependency that participates in a local safety decision: browser storage writes, provider-owned queues/callbacks, script insertion, and network dispatch as applicable. The local deny/kill state must be recorded **before** any potentially throwing foreign call. Provider notification is best effort and must be caught narrowly after the local state is safe; failure to notify must never restore or retain collection.

When a fresh, independently reproduced safety blocker arrives after the normal cycle cap, freeze the complete ledger and ask Karan for a narrow exception—not a general invitation to keep patching. The authorization and builder brief must identify: the exact finding IDs, allowed files, required former-red probes, preserved activation/deploy boundaries, and whether the next triad is review-only. If Karan says “stop after this review,” treat that as a hard stop: report subsequent findings, do not repair them.

When enforcing that authority with an external builder wrapper, validate blocker IDs from the structured frozen `blockers` ledger; a reviewer-finding packet may legitimately have an empty `next_instructions` array. Test the empty-instruction shape and the attempt-2 refusal with a stub before launch. A prelaunch wrapper refusal preserves the substantive attempt only when the real builder never launched, no mutation/comment/push occurred, and the exact PR head is unchanged. Full contract, replay, feedback-pin, and closeout procedure: `references/bounded-human-approved-exception-wrappers.md`.

For a **review-only post-exception triad**, preserve the prover state that already records the exhausted attempt count. After the authorized builder pushes, verify local/remote/PR head equality, reconcile and pin any new builder or bot comments, then rerun the same validated config and state without `reset` or fresh-state creation. Head drift must invalidate stale evidence while the retained attempt count prevents another builder launch. Before running, inspect the state directly and prove `attempt == max_attempts`, the old outcome is bounded/blocked, and the new PR head differs from the stored head. If any of those are false, stop rather than accidentally restoring a repair budget. If the fresh triad finds blockers, report them; do not repair them under the expired exception. See `references/review-only-post-exception-triad.md`.

When browser evidence must describe a runtime that is then committed, separate code from evidence: commit the runtime repair first, run intercepted desktop/mobile QA against that immutable runtime, then make an evidence-only commit whose diff changes no runtime bytes. Bind the report to the runtime commit, tree hash, and relevant asset checksum. For a production-disabled loader, safely prove both states: committed bytes remain inert, while a temporary one-literal eligible copy exercises exactly one intercepted provider loader with no egress. Never call screenshots or branch/date prose exact-head evidence unless their runtime binding is explicit.

A normal push may update the Git branch ref before GitHub associates it with the pull request. Cross-check local `HEAD`, `git ls-remote origin refs/heads/<branch>`, and the GitHub branch-ref API; wait/retry until `gh pr view <N> --json headRefOid` also equals the same full SHA before freezing or launching an exact-head review. The branch ref alone is not PR-head proof.

Before starting an expensive exact-head Reviewer A → Reviewer B → Integration Auditor chain, write a continuation checkpoint containing the current verified full SHA, local/remote/PR/commit-tail equality, builder artifact readback, changed paths, exact gate counts, PR-body/closing-linkage readback, fresh packet/worktree paths, next required lane, and remaining cycle budget. If turn/tool budget is unlikely to cover all three lanes plus relay/readback, stop at that checkpoint rather than stranding a partially launched chain. On resume, inspect live head and process/session state first; never call an incomplete chain merge-ready.

### 2.6 Preflight retained feedback before costly gates on restored PRs

A restored-head successor run or re-pilot inherits the PR conversation even when it intentionally starts with fresh state, locks, evidence, and cycle budget. Inventory every conversation comment, formal review, inline comment, and review thread **before launch**, and evaluate it using the prover's actual resolver—not a prose assumption that “old head” means resolved. The strict barrier may run all baseline/visual gates and then stop before the first builder attempt, so skipping this preflight can consume expensive evidence work and still end at attempt `0/N`.

Use this resolution map:

- current-run artifacts count only when their ownership/signature/head/readback contract passes and they remain unedited;
- an inline thread counts resolved only when GitHub reports it resolved;
- an active `CHANGES_REQUESTED` review remains active until the requesting identity approves or dismisses it; an outdated commit alone is not dismissal;
- a remaining comment needs a later standalone `PR-PROVER: ACKNOWLEDGED <artifact id>` line when the configured policy uses acknowledgement records;
- bot linkbacks, deployment comments, and earlier automation artifacts may still appear in the strict unacknowledged set—do not silently exempt them unless the shipped policy does.

Acknowledgement is a reconciliation record, not permission to ignore content. Read each artifact, map its request to the frozen blocker ledger or record why a successor/restored-head contract supersedes it, and preserve that mapping in the tracker. Before posting ACK lines or changing review state, verify that the task-specific authorization covers those external mutations. If it does not, stop-and-ask **before** launch rather than after the gates. When authorized, dismiss a stale agent-owned review as *superseded by the successor run*; never submit a false approval for a head whose gates are failing.

Before posting any ACK, also derive `config.publisher_logins` and compare it with every authenticated identity actually available. The shipped reconciler deliberately excludes ACK candidates authored by configured builder/reviewer publishers. If every available identity is in `publisher_logins`, the ACK path is structurally unavailable: an exact-looking publisher-authored ACK will produce `acknowledged: []`, and adding more such comments only enlarges the unresolved surface. Do not fake an author, weaken the run config, swap builder/reviewer identities, or patch the candidate just to pass its own qualification. Preserve the failed ACK readback, report the publisher-identity deadlock as a control-plane blocker, and split a follow-up repair if authorized.

After an exact-post pin repair exists, do not assume the original reconciliation comment clears itself. A comment that combines ACK lines with explanation is a **mixed post**: its valid lines may clear earlier artifacts, but the residual prose becomes one new unresolved feedback item, commonly reported as `acknowledged-and-raised-more`. Recover with a later pure bookkeeping post containing only `PR-PROVER: ACKNOWLEDGED <mixed-post-id>`, read it back, derive its exact body evidence, and pin both posts in a fresh pre-launch run config with fresh state/lock/worktree/evidence paths. Preserve the stopped run as immutable evidence and require `check-config` to print every pin before relaunch. Use `references/operator-pinned-acknowledgement-recovery.md` for the full sequence and stop conditions.

Read the feedback surfaces back twice for stability, reset only the fresh successor state, and leave historical run state/evidence immutable.

Remember the lifecycle consequence: baseline/visual findings cause reviewer lanes to be skipped. If the feedback barrier then prevents a fix attempt, report exactly that—no reviewer artifacts, no builder mutation, and no cycle spent—rather than implying the ordered triad ran.

A hardened read-only reviewer that cannot write its requested `/tmp` artifact may still return a valid complete signed body in terminal output. Recover it by paging the full process log, selecting one complete `ROLE=...` through signature plus matching `DONE:` block, materializing it unchanged outside the lane, rechecking exact head/runtime/worktree cleanliness, relaying through the dedicated reviewer identity, and reading it back by ID. Treat this as transport-only degradation. If the body is partial, inconsistent, stale, or unsigned, rerun the reviewer rather than reconstructing prose from memory.

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
- **Marker-only artifact classification and retryable worktrees:** parse verdicts and findings from declared machine headers/records only—never infer a finding from reviewer prose. A `STATUS=pass`, `BLOCKING=0` artifact with no explicit finding records must relay as a pass even if it discusses a non-blocking concern. Retained terminal-run worktrees must not make `reset` + same-head retry impossible: use a fresh per-attempt path or narrowly verified cleanup, preserving active/dirty/foreign evidence fail-closed. See `references/reviewer-artifact-relay-and-retry-recovery.md`.
- **Canonical artifact head binding:** conversation artifacts require exactly one standalone full-SHA `HEAD=` declaration that equals the bound head before relay and after readback; reject cases where the expected SHA appears only in prose. Formal reviews still require authoritative GitHub `commit_id` equality.
- **Human-feedback reconciliation and pagination completeness:** capture conversation comments through a fully paginated REST surface, paginate formal reviews and top-level review threads, and either paginate every nested thread-comment connection or fail closed when nested `pageInfo.hasNextPage` reports truncation. Never treat a convenience first-page response as complete. Prove later-page human blockers prevent `merge-ready`; malformed or incomplete pagination metadata fails closed; resolved/outdated feedback does not remain blocking by stale prose alone; head drift invalidates the collection; and all bodies remain untrusted evidence.
- **Real installed-adapter smoke before the formal triad:** when a change touches the repository-owned reviewer adapter, prepared artifact, relay, or feedback-read lifecycle, run one real credential-free installed-CLI smoke in a disposable exact-head worktree before A/B/Integration. A stub proves plumbing only. Require the machine marker, one canonical `HEAD=<sha>`, a clean worktree, scoped-identity relay, and ID/head readback. Explicitly tell the spawned reviewer that this invocation is the required smoke and it must not invoke the adapter/reviewer recursively; watch the process tree for a second adapter chain. Include mixed acknowledgement-plus-new-feedback and post-verification artifact-edit probes when feedback ownership changed. If this pre-triad smoke finds a partial omission inside an already-frozen blocker class, publish the artifact and use the one permitted corrective builder rerun inside that same cycle; a new blocker class or second omission still requires the normal stop/exception rule. If the repair budget is already exhausted, relay the artifact and use the formal triad to reproduce/refute it without silently launching another builder. For adapter/relay changes, also prove the exact pinned CLI argv, actual external artifact creation, finding-record parity, and the normal relay/readback lifecycle; use `references/real-agent-adapter-proof-and-detached-reviewer-supervision.md` for the required negative probes and detached-process supervision pattern.
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

For subscription-authenticated Claude Code on macOS, preserve the OAuth/keychain session environment. A fully blank environment may make a logged-in CLI appear unauthenticated. During `claude auth login`, the browser callback may complete the PTY and persist credentials before an out-of-band authorization code can be submitted. If `process submit` reports that the process already exited, inspect the process log and run `claude auth status` plus a real pinned-model `claude --print` smoke before restarting login. `Login successful` plus the model smoke is success; an already-exited PTY alone is not failure. The durable recovery pattern is:

- preserve host session/auth state;
- remove explicit remote credentials such as `GH_TOKEN` only when the lane does not need to publish directly;
- use strict empty MCP and task-scoped tool permissions;
- start with `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` or the repository-owned child-environment scrubber when compatible with the lane;
- if that setting explicitly forces `--permission-mode dontAsk` back to default and blocks a trusted scoped builder, stop only the exact process, verify the tree, and relaunch once with `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=0` plus the explicit allowlist—never disable scrubbing globally;
- run a tiny no-tool smoke before resuming expensive work;
- do not guess a dated model identifier from a requested family name. Probe the stable CLI alias (for example `opus`) with `--output-format json`, inspect the returned `modelUsage` key, and require that canonical identifier to match the requested family before launching the expensive lane. A successful text response proves auth; the canonical usage record proves which model actually answered.

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
- `references/real-agent-adapter-proof-and-detached-reviewer-supervision.md` — exact shipped-CLI proof, external artifact/finding/relay parity, duplicate-output extraction, and native-process watchdog recovery.
- `references/continuation-safe-long-agent-runs.md` — builder-permission preflight, launcher-failure cycle accounting, post-push continuation checkpoints, execution-budget gates, and read-only reviewer artifact recovery.
- `references/semantic-visual-gates-for-generated-artifacts.md` — exact-head render-first/fail-late evidence, PDF-text semantics, collapsed-table labels, contrast recomputation, and known-bad negative proof.
- `references/publisher-acknowledgement-identity-deadlocks.md` — preflight publisher/identity deadlocks, immutable post-ID repair invariants, negative proof matrix, and qualification/tracker sequencing.
- `references/preflight-automation-comment-ack-pinning.md` — concise fresh-PR recipe for inspecting a Vercel/deployment bot comment, posting a pure ACK, deriving exact conversation-comment `body_evidence`, pinning the ACK post, and validating config before expensive gates.
- `references/operator-pinned-acknowledgement-recovery.md` — recover exact-post pin runs safely when a mixed reconciliation comment clears earlier feedback but leaves its own residual prose unresolved.
- `references/control-plane-stop-and-launcher-recovery.md` — artifact-first wrapper recovery, additive contract clarification, deduplicated blocker packets, repair-cycle accounting, hardened launcher preflight, and detached-child watchdog proof.
- `references/fail-closed-client-revocation-probes.md` — dependency-boundary fault injection for browser consent revocation, including storage and provider-queue failures.
- `references/protected-vercel-preview-evidence.md` — protected Vercel preview access, secret-safe runner handoff, GitHub deployment-status discovery of the immutable exact-head URL, HTTP redirect/404/indexability evidence, and reviewer-evidence relay.
- `references/credential-bearing-network-gate-origin-binding.md` — exact-origin trust binding, injected-sentinel egress probes, shared-platform tenant pitfalls, redirect credential containment, and stop rules for newly discovered security blockers.
- `references/pre-pr-scope-gates-and-same-cycle-correction.md` — enforce approved quantitative scope before opening a PR, withhold over-budget branches, and route a non-destructive same-cycle Claude correction without weakening former-red coverage.
- `references/review-only-post-exception-triad.md` — preserve exhausted prover state for a truly review-only post-exception triad, reconcile new publisher comments by exact-post pin, and bind browser evidence to an immutable runtime commit.
- `references/bounded-human-approved-exception-wrappers.md` — freeze one additional blocker-scoped builder authorization, handle empty instruction ledgers, prove the attempt guard, distinguish prelaunch errors from spent repairs, and stop after the final triad.
- `references/post-edit-verification-denial-takeover.md` — preserve a bounded uncommitted candidate after tool-policy denial, independently verify it, commit only exact tested paths, and split successful transport from failed post-push verification.
