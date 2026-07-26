---
name: profile-isolated-work-execution
description: Route tracker-sourced non-coding work through least-privilege Hermes profiles, curate role-native skills, and verify profile isolation before execution.
version: 1.3.0
metadata:
  hermes:
    tags: [profiles, orchestration, least-privilege, linear, skill-isolation, review-gates]
---

# Profile-Isolated Work Execution

Use this skill when work originates in Linear or another task tracker but should not be executed directly by Default Hermes, or when creating/auditing specialist profiles and their permanent skill libraries.

## Operating model

Default Hermes is the control plane:

- reconstructs live source state;
- records the human's version-bound approval and claim;
- prepares a frozen execution packet;
- chooses the least-privilege execution profile;
- creates a short-lived, issue-and-revision-bound grant naming exact temporary skills and credential environment variables when the work requires live systems;
- independently verifies returned evidence and direct mutation readbacks;
- controls final acceptance and review/final tracker transitions.

Specialist profiles execute bounded work. A valid one-time grant may let them perform the exact operational mutations named in the packet, but it does not delegate human approval, claim creation, self-advancement, merge/deploy, outreach, or unrestricted account authority.

## Hybrid routing rule

Route to an existing role-native profile first:

- PM/specification work → `pm-spec`;
- sourced research → `researcher`;
- durable knowledge/wiki work → `wiki-ops`;
- multi-part decomposition/coordination → `orchestrator`;
- repository implementation → `builder` through the normal GitHub workflow.

Use a least-privilege general execution profile such as `linear-worker` only when the task is non-coding, bounded, and does not fit one specialist. Do not let the fallback profile become a broad replacement for role-native lanes.

See `references/hybrid-linear-routing.md` for the recommended execution packet, permanent worker boundary, and example profile matrix.

For blocker-only verification of the hardened launcher itself, follow `references/read-only-task-grant-architecture-audit.md`. It provides a strict no-live-grant workflow using before/after hashes, temp-only tests, CLI bypass probes, synthetic end-to-end grant assertions, residue checks, and a P0/P1/P2 reporting contract.

For implementation and repair of a task-scoped capability launcher, use `references/task-scoped-capability-launcher-hardening.md`. It covers exact CLI allowlisting, source-revision binding, no-follow/single-link grant handling, atomic consumption, process locks, crash residue, standing-environment audits, symlink-safe temporary skills, granted/ungranted E2E verification, and timeout-review recovery.

## Execution packet

Before launch, give the worker a self-contained packet with:

1. source issue/root identifiers and exact body digest or revision;
2. goal, scope, acceptance criteria, and definition of done;
3. allowed outputs, writable paths, and exact approved external mutation classes;
4. prohibited external actions and authority limits;
5. source excerpts, or exact live-read authority, needed for fresh reconstruction;
6. required temporary skill names and credential environment **names**;
7. exact verification commands and direct readback requirements;
8. next checkpoint and expected return format.

If live capabilities are needed, create a one-time grant bound to the same root, issue, body digest/revision, run ID, and expiry. The grant names skills and credential variables but stores no secret values. Start from `templates/task-capability-grant.json`; replace every placeholder and validate the finished file before launch. The sanitized launcher copies/injects only those capabilities from Default Hermes' environment, then removes the grant and temporary skills when the process exits.

Do not make the worker depend on chat history, Default Hermes memory, or a hidden local board. A skill or credential is capability—not authorization—and cannot broaden the packet.

## Curated external skill handoff

An external “awesome skills” repository may be only a catalog of links rather than a vendored tree of loadable `SKILL.md` files. Do not bulk-install it, treat the clone as executable, or permanently widen the worker profile.

Use this funnel when Karan authorizes external catalogs as a source for helpful worker skills:

1. search the catalog for the task-specific capability;
2. inspect the exact linked skill with `hermes skills inspect <URL-or-ID>` and record source, trust level, license, frontmatter name, scripts, credential requirements, and authority surface;
3. reject prompt-injection, broad account authority, hidden downloads, destructive scripts, or unrelated tool requirements;
4. install only the exact vetted skill into Default Hermes' governed skill library when needed, then verify its bytes/frontmatter and that the task launcher resolves the intended skill unambiguously;
5. name only that skill in the issue/revision-bound one-time grant; the worker receives a copied temporary capability and cleanup remains mandatory;
6. prove after exit that an ungranted fresh worker cannot load the temporary skill;
7. retain per-action approval gates for sensitive, client-facing, credentialed, publishing, deployment, messaging, payment, or authority-expanding skills even when the catalog itself was generally approved as a source.

See `references/external-skill-catalog-handoff.md` for the audit record and smoke-test checklist.

## Profile creation and pruning

A profile is state isolation, not a filesystem sandbox. SOUL text is guidance; the actual skill directory and enabled toolsets define practical capability.

1. Confirm no run is active for the target profile.
2. Back up its current `skills/` directory outside that directory.
3. Derive an explicit permanent allowlist from the profile's role.
4. Remove out-of-role skills and copy only allowlisted skills, dereferencing symlinks.
5. Add `.no-bundled-skills` so bundled seeding does not repopulate the profile.
6. Clear stale `.skills_prompt_snapshot.json` files.
7. Restrict toolsets separately; skill pruning alone is not isolation.
8. Start a fresh real profile session.
9. Recount installed `SKILL.md` files.
10. Prove required skills load and representative out-of-role skills fail to load.

If `.no-bundled-skills` exists but many bundled skills remain, treat the profile as already polluted: the marker prevents reseeding but does not prune existing files.

If launch silently restores removed bundled skills, maintain a profile-local `skills/.bundled_manifest` using bundled **frontmatter skill names** and current origin hashes, then repeat the fresh-session check.

## Least-privilege defaults

For a bounded non-coding worker, prefer:

- toolsets: `file`, `terminal`, `web`, `skills`, `todo`;
- launch only through a sanitized one-shot wrapper; direct `hermes -p <worker>` launches are forbidden when they can inherit credentials;
- no **standing** tracker, GitHub, messaging, client-system, or vendor credentials in the worker profile;
- a small permanent role skill set;
- issue-bound grants lasting at most eight hours, containing credential variable names rather than secret values;
- only credentials and task/domain skills needed for the current packet, injected/copied at launch and removed on exit;
- no messaging, memory, session search, cron, delegation, or browser-automation toolset unless Karan separately revises the profile architecture;
- explicit packet authorization plus direct readback for every live mutation.

The worker may be credentialed and skilled enough to complete real work. Least privilege means time-, issue-, skill-, credential-, object-, and action-bounded capability—not a permanently powerless executor.

## Safe fallback when a role-native profile is over-credentialed

Before feeding an untrusted source packet to a specialist, inspect **credential variable names only** and verify the exact launch wrapper—not prompt wording—enforces the intended boundary. If the role-native profile has standing credentials beyond the packet:

1. do not launch it directly and do not rely on SOUL/tool instructions as access control;
2. prefer the governed sanitized wrapper when available;
3. otherwise use a fresh functional-role process restricted to the task directory, exact read/write paths, and minimum tools, with operational credentials removed while preserving only the model-auth channel needed to run;
4. smoke-test that exact sanitized invocation before the real packet;
5. record the runtime substitution in execution evidence and keep the logical execution role unchanged;
6. verify the process wrote only the allowed outputs and performed no external mutation.

If model authentication fails under the sanitized invocation, repair the model-auth channel without restoring unrelated operational credentials. Do not encode the transient auth failure as a permanent tool limitation.

## Review and status gate

For durable non-code specifications, architecture contracts, playbooks, or reports, follow `references/exact-hash-contract-artifact-acceptance.md`. It covers tracker-body normalization, per-connection pagination evidence, semantic blocker checks, context-preserving worker repair loops, unchanged-byte promotion, and complete output inventory.

**Context-preservation rule:** Default Hermes is the integrator, not the long-running artifact repair lane. When a candidate needs repeated whole-file reads, multiple blocked semantic reviews, or extended line-by-line fixes, dispatch a task-scoped author/fixer worker with frozen local inputs and one new output path. Verify its returned artifact, then send the exact hash to a different reviewer. Keep only governance, handoffs, hashes, verdicts, promotion, and tracker closeout in the control-plane context. Direct Default-Hermes edits are limited to small one-shot corrections.

Before dispatch, apply the role-native routing rule to the **repair work itself**. A PM/spec contract repair goes to a clean `pm-spec` process; it must not be disguised as generic `linear-worker` execution. Use the hardened `linear-worker` wrapper only for work that genuinely fits that fallback role. If a generic worker fails its pre-input attestation or rejects an out-of-role packet, treat that as a routing correction: do not weaken the guard, and relaunch through the correct sanitized specialist lane.

For large local artifact repairs, separate **specialist authoring** from **control-plane mechanics**. If a background one-shot worker cannot surface terminal approval prompts, do not keep retrying invisible approvals and do not grant broad terminal bypass by default. Default Hermes verifies the frozen input identity, pre-seeds a full writable copy, and launches the role-native specialist with file tools only and a targeted patch-only contract. After exit, Default Hermes computes hashes/counts, runs validators, and rejects any truncated or condensed rewrite before spending a reviewer cycle. The detailed pattern is in `references/exact-hash-contract-artifact-acceptance.md`.

Bind every asynchronous worker/reviewer completion to its process/session ID, candidate path, and exact SHA-256. Delayed notifications from an older candidate are historical evidence only; they must not overwrite the active candidate's status or verdict. See `references/exact-hash-contract-artifact-acceptance.md` for the detailed repair-loop and stale-completion procedure.

**User-facing progress during long repair loops:** keep Telegram/control-plane updates compact—current stage, process/session ID, exact candidate hash when available, PASS/BLOCKED state, and next gate. Preserve line-cited findings, full blocker prose, repair packets, and reviewer reasoning in durable files rather than replaying them into the main chat/context. Expand only when Karan asks or a decision/approval is required.

The executor never self-advances the source issue.

1. Run a fresh independent reviewer lane against the exact output and source revision.
2. If Karan names a reviewer runtime (for example, a separate Claude Code reviewer), use that actual runtime in a fresh process; do not substitute executor self-review, Default Hermes self-review, or a generic subagent.
3. Freeze a complete contract packet: live issue body/digest, approval and claim markers, relations/pagination, implementation and test hashes, run/recovery evidence, forbidden actions, and adjacent-issue boundaries.
4. Require the reviewer to classify every contract clause and acceptance criterion as `PASS`, `FAIL`, `NOT YET`, or `NOT APPLICABLE`, with evidence. A code-diff-only review is insufficient.
5. Check source fidelity, security, scope, real execution evidence, cleanup, idempotency, revision safety, and authority boundaries.
6. P0/P1 findings keep the issue active and return it for repair.
7. Read and validate the completed review artifact and its final marker; process exit alone is not a verdict.
8. Only a green exact-hash review permits the already-approved status transition. Any reviewed-byte change invalidates the pass and requires a fresh review.
9. Default Hermes performs and reads back the tracker mutation.

## Verification checklist

- [ ] Source revision/digest is frozen and current.
- [ ] Existing active work was resumed before new selection.
- [ ] Profile choice follows role-native-first routing.
- [ ] Permanent skills match the declared allowlist.
- [ ] Any one-time grant matches root, issue, body digest/revision, run ID, expiry, exact temporary skills, and credential environment names.
- [ ] Temporary skills and the consumed grant were removed after execution.
- [ ] Real producer/consumer dogfood verified residue manifest owner, private mode, hard-link count, path type, and exact root/issue/run/digest binding; fixture helpers did not silently create safer artifacts than production.
- [ ] Toolsets exclude unneeded authority surfaces.
- [ ] Profile has no unintended standing credentials; task credentials appear only in the granted run.
- [ ] Fresh-session smoke test succeeds.
- [ ] Required permanent and granted skills load; out-of-role/ungranted skills do not.
- [ ] Every authorized live mutation has direct ID/path/state readback.
- [ ] Tracker body/digest evidence was computed from the exact live readback, not only the local draft or mutation response.
- [ ] Per-connection pagination exhaustion is evidenced for every collection used in the decision.
- [ ] Deterministic presence/format checks passed without being substituted for semantic acceptance review.
- [ ] Independent review is green against the exact candidate hash before status advancement.
- [ ] The reviewed bytes were promoted unchanged and candidate/canonical hashes match.
- [ ] Default Hermes controls and verifies the review/final tracker transition.

## Pitfalls

- Do not treat SOUL wording as an access control.
- Do not clone a broad profile and assume `.no-bundled-skills` will clean it.
- Do not prune a profile while its process is running.
- Do not give a general worker every domain skill or credential "just in case."
- Do not put secret values in grant files; grants contain names and bindings only.
- Do not confuse an injected credential with authorization for arbitrary actions.
- Do not let an executor create human approval/claim markers or self-advance to review/final status.
- Do not describe a candidate as reviewed, promoted, indexed, or accepted before those actions are verified.
- Do not treat a deterministic presence/format validator as semantic acceptance; exact-hash independent review is still required.
- Do not let Default Hermes absorb a prolonged author → review → repair loop; delegate the repair lane once repeated full reads or blocked reviews begin, then verify the worker's artifact and use a separate reviewer.
- Do not ask a background one-shot specialist to run commands whose approval UI cannot reach the user; move safe mechanical identity/validator checks to Default Hermes and keep the specialist file-only when practical.
- Do not let a file-only worker replace a large canonical candidate with a shortened rewrite. Pre-seed a verified full writable copy, require targeted patching, and reject suspicious line/byte collapse before semantic review.
- Do not trust a worker's claimed path/hash/check result without direct local readback.
- Do not reuse a green review after any byte changes; hash again and re-review.
- Do not reuse a consumed or expired grant.
- Do not treat a timed-out independent review as either green or empty: extract completed findings from its transcript, repair blockers, freeze new hashes, and run a narrower blocker-only re-review.
- Do not reuse a PR-specific reviewer profile for unrelated artifact review if its role contract forbids that scope.
- Do not report isolation complete until a fresh runtime proves both positive and negative skill access.
