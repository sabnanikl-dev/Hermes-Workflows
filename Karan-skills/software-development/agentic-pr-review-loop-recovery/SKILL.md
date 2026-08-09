---
name: agentic-pr-review-loop-recovery
description: Recover bounded autonomous PR review/fix loops across interrupted runs, shared publisher identities, stale exact-head evidence, and detached background process handles without duplicating work or weakening merge gates.
version: 1.4.10
author: Hermes Agent
metadata:
  hermes:
    tags: [github, pull-requests, review-loop, recovery, exact-head, multi-agent]
    related_skills: [autonomous-pr-prover, cross-tracker-development-execution, integration-audit-review]
---

# Agentic PR Review Loop Recovery

## Trigger

Load this skill when an autonomous PR builder/reviewer loop has already started and any of these occurs:

- a run stops terminally but its PR artifacts must be carried into a fresh run;
- all available authenticated GitHub identities are also configured publishers;
- historical reviewer/builder comments become unresolved feedback in the next run;
- a builder push invalidates the previous A/B/Auditor evidence;
- a background handle reports exit without a trustworthy exit code while the real child may still be alive;
- issue acceptance wording conflicts narrowly with the normative review lifecycle;
- repeated checker/evidence-validator fixes have displaced the shipped product as the review target, requiring a fresh product-first replacement rather than another verifier patch;
- a reviewer needs exact-head hosted behavior evidence but preview access control (SSO/login) intercepts the request before the application responds;
- a platform-protected preview intentionally carries site-wide `noindex`, final indexability belongs to a post-merge immutable production deployment, or a builder push would stale a live gate pinned to the original deployment ID/URL;
- a Prover run exits `needs-Karan`/code 2 and the operator must distinguish malformed reviewer transport from a fully transported substantive triad before spending a repair cycle;
- Karan approves exactly one blocker-scoped exception after the normal cap, requiring a fresh-state guard that cannot open a second repair;
- an exception guard refuses before Claude launches, and the operator must prove whether the substantive exception remains unused before replaying it;
- an opaque-child design still exposes an interceptable first-port handshake, so provider privacy must come from a child-owned fixed grammar rather than assumed port secrecy.

For a normal uninterrupted run, use `autonomous-pr-prover`. This skill is the recovery layer, not a competing prover implementation.

## Product-first replacement stop rule

When repeated review cycles are hardening an archived QA report as if it were hostile runtime input, stop repairing that PR. Freeze a finite recovery contract on the authoritative issue **before** dispatching a replacement builder, create a fresh branch from current default-branch state, and reuse only independently verified product bytes/wiring/scenario knowledge. Separate the shipped-runtime checker, browser-QA producer, and narrow evidence binder; freeze the reviewer blocker rubric and repair budget so optional metadata hardening cannot restart the same loop. In the binder, prove required labels/viewports by presence rather than rejecting harmless extras, while still rejecting duplicate required records that can hide which observation counts. Commit the runtime before producing hash/commit-bound browser evidence, then commit the report separately and rerun the binder plus full suite. Keep the stopped PR only as a temporary reference and close it as superseded once the replacement exists.

See `references/product-first-replacement-after-verifier-churn.md` for the contract language, proof-layer split, reviewer authority, and claim discipline. When the exhausted PR's blocker class is standards parsing or incomplete live observations, also load `references/standards-parser-replacement-after-capped-pr.md` for mature-parser selection, permanent former-red regressions, transport-vs-media-type fail-closed semantics, immutable deployment binding, human trailer gates, and whole-diff proportionality checks.

If that replacement exhausts its one repair cycle and the exact-head triad still reproduces a real blocker, stop it and return the decision to Karan. A later explicit owner continuation may authorize a **new clean replacement**, but it is not a hidden extra cycle: amend the authoritative issue before another builder starts, record the old PR as permanently stopped, start again from current default-branch state, and carry the old blocker forward as a former-red architecture test. For direct browser analytics, do not mistake a conditional top-level queue getter for privacy; isolate provider-owned mutable state from ordinary top-level page code and prove the isolation in a real browser before building. See `references/cap-exhausted-replacement-and-provider-isolation.md`.

## Non-negotiable boundaries

- Karan remains sole merge authority.
- Never treat a terminal journal as editable state or forge a resumed outcome.
- Never relaunch a quiet lane until the real process tree proves it exited.
- Never grant login-wide acknowledgement authority. Authorize an exact immutable post ID **and**, when the shipped schema supports it, the body/review-state evidence the operator actually read; an ID-only pin follows later edits and is not sufficient proof.
- A push invalidates every prior exact-head gate and reviewer artifact.
- Formal GitHub review state is resolved natively, not through prose ACKs.
- Keep bounded repair-cycle accounting tied to actual repair commits, not failed launcher attempts, and carry the true consumed count into any fresh review-only journal so recovery cannot silently reopen cycle 3.
- Treat an explicit preflight numeric exception (for example, “pre-approve a three-cycle run if needed”) as bounded durable authority rather than asking for the same approval again at the normal cap. Record whether the number is a total-cycle ceiling or additional-cycle allowance. Do not spend the exceptional cycle until the normal budget is exhausted and the remaining blocker class, allowed files/surfaces, and closure matrix are frozen. A new blocker class, broader surface, merge, deploy, or authority expansion still requires a fresh decision.

## Recovery workflow

### 1. Reconstruct live truth

Read the PR head, draft/state/mergeability, commit list, reviews, conversation comments, inline threads, and checks. Verify local feature HEAD, remote branch HEAD, PR `headRefOid`, and worktree cleanliness. Read the retained run report/state but treat GitHub as the current source.

Before the **first** prover run, reconcile pre-existing status/deployment bot comments as carefully as human prose. If a read-only automation post is pure metadata and requires no action, publish and evidence-pin its exact canonical acknowledgement before launching Reviewer A. Do not wait for a terminal `needs-Karan`: resetting afterward makes the first run's reviewer artifacts historical feedback in the next journal. Follow `references/preexisting-automation-comment-first-run.md`.

### 2. Determine whether work is finished, alive, or genuinely failed

A wrapper exit is not proof. Check the exact command/PID in the process table, report/error files, and state-file progress. If the child is alive, attach a watchdog and do not duplicate it. If it exited, validate only persisted artifacts, signed markers, remote readback, and tests.

### 3. Bridge historical feedback into a fresh run

Inventory historical conversation artifacts that the new journal will no longer recognize as run-owned. After operator review, publish one pure canonical ACK post mapping those exact immutable IDs. Read that ACK post back, compute the repository's canonical publication/body evidence over the exact API body and review state, and pin the `{id, body_evidence}` record the current schema expects. If the schema is still ID-only, treat edited-body resistance as unproven and test it adversarially rather than assuming the immutable ID binds mutable content.

When replacing an earlier operator pin, do **not** target only the latest report's bounded unresolved list. Removing the old pin can reactivate both its previously cleared targets and the old bookkeeping post itself. Compute the cumulative target set with the shipped reconciliation engine, retained verified-artifact ownership, and `operator_acknowledgements={}`; simulate the proposed replacement pin and require zero unresolved items before POSTing or spending another triad. Follow `references/replacement-pin-cumulative-feedback-reconciliation.md`.

A previous `CHANGES_REQUESTED` review must be cleared by a later exact-head `APPROVED` or `DISMISSED` review from the same GitHub author; ACK prose cannot clear it.

### 4. Start fresh without reusing terminal state

Create a unique run directory, lock file, worktree root, and current-schema journal. Reuse only schema-validated adapter executables/scripts, not an old terminal journal or its classification.

When the review is occurring after repair cycle 2, initialize the fresh journal through the repository's `RunState` writer/API with the **truthful cumulative** attempt count and exact current head (`attempt=2`, idle phase, no outcome/classification). Load it back through the same parser before launch. This is not resuming or editing a terminal outcome; it is preserving the global cap while discarding stale head-bound evidence. A fresh `attempt=0` journal at this point is a hidden third-cycle bug.

Run `check-config` and require it to name every evidence-bound acknowledgement ID. Directly read back each pinned GitHub post immediately before launch and recompute its evidence; any mismatch stops before review/fix work.

Then perform a **local reconciliation preflight** against the live complete comments/reviews/threads using the repository's own `RunConfig`, `RunArtifacts`, and `reconcile` implementation. For a genuinely fresh run, use no retained artifacts. For a bounded same-head feedback replay, preserve the state's verified artifacts so the replay's already-published lane outputs remain run-owned, but remove all operator pins while computing a replacement cumulative bridge. Require the proposed final-pin simulation and the subsequent live readback reconciliation to each reach `unresolved == 0` before spending reviewer lanes. `check-config` validates a pin's shape and evidence, but does not prove that the pinned post's `PR-PROVER: ACKNOWLEDGED <id>` lines actually clear every historical item. This catches stale/missing targets, bounded-report truncation, and replacement-pin reactivation before an expensive A → B → Auditor pass reaches the builder barrier.

### 5. Preserve all three identity/evidence predicates

Keep these questions separate:

- content ownership may lapse after body/state mutation so edited material re-enters human feedback;
- immutable run-publication identity must survive mutation so an artifact this run ever published can never gain ACK authority;
- historical operator authorization must match both the immutable ID and the body/review-state evidence the operator read, so a same-ID valid-body edit cannot inherit authority.

Run two valid-ACK mutation probes through the real config/loop path before accepting a repair: an edited run-published artifact and an edited historical pinned publisher post. Both must fail closed without a builder launch or `merge-ready`.

### 6. Re-prove the new head

After any builder push, independently verify remote/PR commit presence, run the full gate suite, then freeze fresh packets for Reviewer A → Reviewer B → Integration Auditor. Read every relayed artifact back from GitHub and verify role, author, exact head, state, body marker, and immutable ID.

#### Rebind staged live-deployment proof

Do not disable a hosting platform's preview `noindex` safeguard merely to satisfy a production-indexability assertion. Split the executable contract explicitly:

- **preview stage** proves routes, canonicalization, redirects, sitemap, robots, and branded 404 behavior while verifying the broad platform safeguard remains present; page-owned meta noindex still fails;
- **production stage** runs against an immutable deployment after merge and before DNS cutover, requiring both header and meta noindex to be absent on indexable routes.

A green preview can support technical PR merge advice, but it is never final migration/cutover readiness. Record the outstanding immutable-production gate in the PR and tracker so merge cannot silently become DNS authority.

If the Prover may launch a builder, never pin the baseline permanently to the initial preview deployment ID or URL. A repair push changes `{head}` and makes that otherwise-sound binding stale. Instead, make the gate resolve deployments by the current exact `{head}`, require the expected environment, bounded-poll provider/GitHub status to a terminal result, select a successful immutable URL, re-check deployment SHA/ref and URL association, and only then run the preview checker. A static deployment ID/URL is safe only for a truly review-only run where no builder can change the head. Keep bypass credentials out of reviewer packets and process output; a trusted gate wrapper may load the secret locally and pass it only to the checker child.

After every repair push, require a new exact-head deployment and fresh preview result before rerunning A/B/Auditor. Do not carry forward the previous head's 63/63. For deterministic live checkers, preserve former-red probes for inbound query retention, completeness of every hop (not only content-bearing terminal responses), and global-vs-crawler-scoped directives; a happy-path matrix alone does not prove these predicates.

See `references/staged-deployment-proof-and-head-rebinding.md` for the executable gate shape, evidence ledger, and false-pass probes.

If one known timing-sensitive gate fails while every changed-surface gate and an independent full run pass, do not weaken or edit the gate. Verify the failing test **and its implementation path** have no base-to-head diff, rerun the exact test/module several times on the same clean exact head, and allow at most one fresh review-only retry with identical gate definitions.

A failed identical retry normally remains terminal evidence. One narrow exception exists when an earlier retained run on the unchanged exact head already completed **every configured gate**, and the later terminal condition is reviewer transport/control-plane drift or the same unchanged timing seam—not a substantive blocker. In that case, preserve the complete successful gate evidence and continue through the shipped lower-level A → B → Integration lifecycle; do not restart gate roulette, hand-author artifacts, alter the gate, or reopen a builder cycle. Load `review-artifact-relay-and-state-barriers` and follow `references/gate-evidence-preserving-review-transport-recovery.md` for the eligibility and ordered proof barriers. Any changed-path failure, contract/head change, missing complete gate run, or failed canonical relay/readback remains terminal.

If that recovered ordered triad produces blockers and a real repair attempt remains, do not improvise a prose-only handoff or launch from A/B consensus alone. Parse all three authoritative final messages with the shipped parser, adjudicate and deduplicate with the shipped classifier while preserving every origin/lineage record, verify tracker/status findings against their live authoritative source, then freeze the current-schema blocker payload through repository-owned models, sanitizer, and round-trip validators. Open only the truthful remaining attempt in a fresh exact-head worktree; after any push, invalidate the recovered evidence and rerun the full gates and ordered triad. Follow `references/recovered-triad-to-bounded-builder-handoff.md`.

### 7. Close out conservatively

Only recommend/mark ready after the current head is zero-blocker, historical formal review state is cleared, all conversation/thread feedback reconciles, and tracker evidence is updated/read back. Do not merge without Karan.

When the truthful repair cap is exhausted and the recovered exact-head A → B → Integration triad converges on blockers, finish a terminal **blocked** closeout instead of leaving the run labeled only by its earlier transport failure:

1. canonically validate, sanitize, publish exactly once, and directly read back every lane artifact;
2. re-query local/remote/PR head equality, current-base ancestry, open/merged state, worktree cleanliness, and the absence of surviving lane processes;
3. write one durable terminal report that separates passing gates, recovered transport, substantive blocker ledger, exhausted attempt count, and Karan's merge boundary;
4. publish and directly read back one PR terminal-disposition comment, recording exact body equality and SHA-256;
5. update both control-plane and implementation trackers: close the qualification ticket as completed-with-result-`blocked`, but keep the substantive implementation ticket open/in progress;
6. check off only acceptance criteria actually satisfied (including terminal-preservation criteria), leave unfixed implementation and post-merge criteria open, and read the tracker descriptions/comments/statuses back byte-for-byte.

Mechanical `mergeable/clean` state never overrides a converged blocking triad. Do not start a third builder cycle, mark the implementation ticket Done, or promote disputed implementation facts into durable business knowledge.

## Pitfalls

- `exec` can detach a child from Hermes' background handle; `exited` with a null code can coexist with a live PID.
- In zsh, `status` is read-only. Do not let an outer wrapper mask the prover's real return code; use `rc` or invoke the tool directly.
- A fresh journal does not retain old run-owned artifact identities. Old reviewer/builder conversation comments become ordinary live feedback.
- A pure ACK bridge must contain no explanatory prose; residual text becomes another unresolved item. A substantive contract/probe/status comment that also carries ACK lines is `acknowledged-and-raised-more` even when its exact body is operator-pinned: the pin authorizes the ACK targets but does not resolve the comment's added substance. Publish the contract first, then a strictly later ACK-only bridge; see `references/operator-ack-feedback-resume-and-process-tracking.md`. A config pin grants that exact post authority to acknowledge—it is **not** an acknowledgement by itself. Each canonical line must name one still-unresolved, strictly earlier post under the final replacement-pin model. When replacing a prior pin, first reconcile with **all operator pins removed**: targets that looked already cleared can become unresolved again, and the old bookkeeping post can become residual feedback. Generate one cumulative bridge from that no-pin result, simulate it to zero unresolved, then POST/read back/pin the exact evidence. Never hand-type or reuse a digest from pre-POST bytes without API-body equality proof.
- A malformed ACK mutation is weak proof. Use a syntactically valid edited ACK body for both historical pinned posts and run-published artifacts.
- Do not count launcher usage/config/path failures as repair cycles when no code commit was produced. For an exceptional-cycle guard refusal, verify that Claude never launched, no signed builder comment appeared, no commit/push occurred, the live head and commit-list tail are unchanged, and the retained worktree has no builder mutation before replaying the still-unused substantive exception. A classified reviewer blocker file may validly have `next_instructions: []`; synthesize bounded instructions from the exact approved blocker records instead of refusing it. See `references/explicit-exception-guard-and-prebuilder-refusal.md`.
- A reviewer transport stop does not erase a substantive parsed fail verdict. Report both layers separately: the code disposition (including blocker IDs) and the publication/readback failure. When the repair cap is exhausted, recover and publish the artifact and finish the ordered triad for the terminal ledger, but never route those findings into an implicit third builder cycle.
- A malformed reviewer verdict can still contain a concrete candidate defect in retained raw output. Do not promote that prose into a formal reviewer artifact or claim a completed triad. Instead, reproduce the candidate independently against the exact shipped head with a minimal deterministic probe. If reproduction succeeds, the **transport** remains incomplete but the **product blocker** is real; an exhausted repair cap still forces a stop and owner decision. If reproduction fails, preserve it only as transport diagnostics.
- For child-owned numeric command grammars, truthy array lookup is not validation: `array["__proto__"]`, `array["constructor"]`, and inherited/prototype keys can return objects. Require `Number.isInteger(value) && value >= 0 && value < array.length` before every array index, and regression-test inherited keys, strings, objects/arrays, fractions, non-finite values, negatives, and out-of-range integers in both literal and browser producers.
- Conversely, do not manufacture a substantive failure from non-blocking prose in a `STATUS=pass` / `BLOCKING=0` artifact. A parser/relay that invents a finding ID without a canonical `FINDING:` line is a control-plane failure; preserve the artifact, refresh stale PR metadata if needed, and repair/retry the transport.
- Resetting a finished prover state does not authorize reuse or deletion of a retained reviewer worktree. Confirm its lane is dead, preserve its evidence, and create/remove worktrees through the governed recovery path before a fresh exact-head run.
- Do not create a fresh `attempt=0` final-review journal after two repair commits. Preserve the cap with a validated current-schema idle journal at the exact head; never copy a terminal outcome/classification forward. Do not fake review-only mode by replacing the builder adapter with `/usr/bin/false`: that leaves the truthful consumed count out of state and changes the control plane instead of preserving it.
- One intermittent unchanged timing test may justify one identical review-only retry only after exact-head multi-run reproduction and base-diff proof. Do not alter the gate, add retries inside it, or keep relaunching until green. If a prior unchanged-head run already has a complete all-gates pass, a later transport-only stop may continue through the governed lower-level reviewer lifecycle described in `references/gate-evidence-preserving-review-transport-recovery.md`; this is evidence preservation, not a gate waiver.
- Narrow tracker contradictions should be resolved by a dated additive clarification with direct readback, not by silently rewriting historical contract text.
- Do not run baseline or final verification in a worktree while a delegated builder is actively mutating it. A test can observe half-written product code paired with stale checker logic and produce a false failure ledger. Run baseline before dispatch, isolate the builder, or wait for the lane to finish and verify the stable diff.

## Verification output

Report:

- live exact head and local/remote/PR equality;
- run directory/state identity;
- pinned ACK post ID and readback URL;
- real process/watchdog status;
- repair cycles actually consumed;
- gate results and exact-head triad disposition;
- PR draft/merge state and remaining human authority gate.

## References

- `references/explicit-exception-guard-and-prebuilder-refusal.md` — execute one Karan-approved blocker-scoped exception without weakening the normal cap; handle valid empty `next_instructions`, prove a pre-Claude guard refusal did not consume the substantive cycle, and reconcile fresh-run artifacts before replay.
- `references/replacement-pin-cumulative-feedback-reconciliation.md` — replace chained one-off operator pins with one no-pin-derived cumulative bridge, simulate zero unresolved feedback before publication, and preserve same-head verified-artifact ownership and attempt caps.

- `references/preexisting-automation-comment-first-run.md` — preflight status/deployment bot comments before Reviewer A, publish a pure evidence-bound ACK when appropriate, and avoid turning a terminal reset into a larger historical-feedback bridge.
- `references/operator-ack-feedback-resume-and-process-tracking.md` — exact-ID ACK bridging, immutable publication vs mutable ownership, additive contract clarification, and detached-child watchdog procedure.
- `references/evidence-bound-ack-cap-preserving-final-review.md` — bind ACK authority to API-read body evidence, preserve a consumed repair cap in a fresh validated review-only journal, and adjudicate one unchanged timing-gate flake without weakening gates.
- `references/gate-evidence-preserving-review-transport-recovery.md` — preserve one complete unchanged-head all-gates run through a transport-only failure, rerun only the affected role with shipped validators/relay/readback, and refreeze ordered A/B/Auditor packets without gate roulette or a hidden repair cycle.
- `references/detached-reviewer-transport-continuation.md` — operational continuation when the orchestration handle detaches, the real reviewer process is still alive, or final-message/prepared-artifact `FINDING:` parity blocks relay; includes PID watchdog, shipped-parser/sanitized-copy validation, immutable GitHub readback, and fresh ordered packet barriers.
- `references/recovered-triad-to-bounded-builder-handoff.md` — convert a manually recovered exact-head A/B/Auditor triad into one current-schema deduplicated blocker ledger and the truthful remaining builder attempt without losing provenance, fabricating failure records, or resetting the global repair cap.
- `references/live-preview-evidence-access-and-relay-failure.md` — exact-head live redirect/status evidence, SSO-intercepted preview handling without bypassing access controls, adjacent-preflight handoffs, and the separate substantive/transport disposition of a Prover relay failure.
- `references/staged-deployment-proof-and-head-rebinding.md` — split protected-preview functional proof from post-merge production indexability, dynamically rebind live gates after repair pushes, and pin former-red query/hop/directive probes.
- `references/product-first-replacement-after-verifier-churn.md` — stop verifier/framework churn, freeze a finite product contract, and replace an overgrown proof target from a fresh default-branch base.
- `references/standards-parser-replacement-after-capped-pr.md` — replace capped custom-parser proof targets with mature standards libraries, permanent former-red regressions, explicit incomplete-observation semantics, immutable deployment binding, human trailer gates, and whole-diff scope controls.
- `references/identity-bound-relay-and-contract-conflict-split.md` — bind relay publication to the configured reviewer identity, keep acknowledgement bridges pure and evidence-bound, and stop for a Karan design split when a converged exact-head triad exposes a safety/requirements conflict after the repair cap.
- `references/owner-decision-to-bounded-repair.md` — turn a newly recorded Karan policy decision into one frozen, bounded Claude repair and a fresh exact-head proof without rerunning the mismatching head or resetting repair accounting.
- `references/fail-closed-client-analytics-repairs.md` — review and repair reviewed-destination activation and storage-write-failure consent revocation without weakening the repair cap or browser no-op guarantees.
- `references/disposable-node-browser-gate-recovery.md` — restore lockfile-pinned Node/Playwright dependencies inside disposable reviewer gates, preflight and evidence-pin pure automated-status ACK bridges, contain browser producers that rewrite tracked evidence without hiding source mutations, and require exact-head/UI-surface plus non-vacuous visible-focus proof.
- `references/review-only-cap-and-mutable-authority-churn.md` — create a truthful attempt-cap-preserving final review state (never a fresh attempt-0 run with a deliberately failing builder), reconcile reset artifacts before spending lanes, mutation-probe every page-reachable payload authority, and stop repeated same-class exception churn.
- `references/cap-exhausted-replacement-and-provider-isolation.md` — turn an owner-authorized continuation after an exhausted replacement into a new clean attempt, and isolate direct-provider mutable state from top-level page code with closed-shadow/opaque-sandbox former-red proof.
- `references/malformed-verdict-and-fixed-child-grammar.md` — distinguish a malformed reviewer transport stop from a fully transported substantive triad; harden an interceptable opaque-child first-port seam with child-owned fixed commands; regenerate exact-runtime evidence and restart the final ordered review without reopening the repair cap.
