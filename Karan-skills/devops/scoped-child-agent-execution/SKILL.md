---
name: scoped-child-agent-execution
description: "Launch and supervise external coding/worker agents with task-scoped permissions, isolated workspaces, non-redundant user approvals, and independently verified side effects."
version: 1.2.0
author: Hermes Agent
metadata:
  hermes:
    tags: [multi-agent, coding-agents, permissions, approvals, worktrees, security]
    related_skills: [agent-workflow-orchestration, autonomous-pr-prover, autonomous-coding-agents]
---

# Scoped Child-Agent Execution

## Purpose

Use this class-level skill when Hermes launches an external coding or worker agent as a subprocess. It governs the seam between the user's workflow authorization, Hermes' outer terminal approvals, the child's own tool permissions, workspace isolation, and verification of resulting side effects.

The central rule is:

> Do not make the user repeatedly authorize the identity of a child agent when they already approved the bounded workflow. Fix launcher permissions without weakening real merge, deploy, credential, publication, or destructive-action gates.

## Trigger

Load this skill when:

- spawning Claude Code, Codex, another Hermes profile, OpenCode, or a similar worker through the terminal;
- a child launcher triggers an unexpected Hermes approval prompt;
- a non-interactive child blocks on its own permission prompt;
- the user says they do not want to babysit routine builder launches;
- deciding between blanket bypass, allowlisted tools, a sandbox, or global YOLO mode;
- supervising a child that may edit, test, commit, push, or open a PR.

## Non-goals

This skill does not grant authority to merge, deploy, publish, purchase, change credentials, mutate live accounts, or run destructive cleanup. Those remain separate user decisions unless explicitly included in the authorized workflow.

## Two-layer authority model

Keep these independent:

1. **Workflow authority** — the user-approved outcome and external side-effect envelope.
2. **Process permissions** — the files and commands the child can technically access.

Hermes' terminal scanner controls whether the launcher starts. The child agent's permission system controls what happens after startup. A blanket child bypass flag can trigger Hermes even when the workflow itself is already approved. Explain that accurately; do not tell the user they must approve “Claude” as an identity.

### Explain the boundary in plain language first

When Karan asks what a sandbox/launcher problem means, lead with the practical conclusion and a concrete analogy before CLI flags or kernel primitives:

- synthetic `HOME` or scrubbed environment = **hiding the map**;
- OS sandbox = **locking the doors**;
- container/job domain = **a supervised room that also guarantees every helper leaves when time is up**.

Say what remains possible in ordinary language (for example, “the worker can still type the full address of a private file” or “a helper program may detach and keep running”). Then give the technical mechanism only if useful. Do not bury the answer under settings names.

## Procedure

### 1. Freeze the task envelope

Record:

- repository/worktree;
- branch and base;
- allowed files/surfaces;
- verification commands;
- allowed remote mutations, if any;
- explicit prohibitions such as merge/deploy/credentials.

### 2. Isolate the child

Use a dedicated worktree, container, or other disposable task workspace. Verify its starting head and clean status before launch. Do not point a broad-permission child at a shared dirty worktree.

When the original checkout contains live credentials or unrelated setup WIP, an independent `git clone --no-hardlinks <local-repo> <task-clone>` is a useful alternative to a linked worktree: it separates Git metadata as well as working files. Verify the intended base explicitly (a local clone is not proof of current remote main), set the intended remote, and prepare the task branch. Preserve the original checkout in place; selectively stage only reviewed nonsecret inputs and record their provenance. Never copy ignored environment/MCP/linkage files wholesale. Keep launcher policy outside worker-writable paths. This is workspace hygiene, not a replacement for the OS sandbox. See `references/dirty-checkout-builder-preflight.md`.

Distinguish hygiene from confinement:

- synthetic `HOME`, environment allowlists, empty MCP configuration, and a narrow tool list reduce accidental discovery;
- they do **not** prevent a same-UID Bash process from naming absolute paths, inspecting shared runtime surfaces, or connecting to discoverable same-UID Unix sockets;
- when untrusted issue/PR/web content or unrelated workstation credentials are in scope, require an OS-backed sandbox and fail closed if it is unavailable.

For Claude Code, use a fresh launcher-owned strict sandbox policy (`sandbox.enabled: true`, `failIfUnavailable: true`, `allowUnsandboxedCommands: false`) with exact filesystem/network/socket allowances. Run a harmless preflight that proves an authorized worktree file is readable and a private operator path is denied without displaying private contents. See `references/claude-code-strict-child-isolation.md`.

A process group is not a complete lifetime domain: a malicious descendant can call `setsid()` and escape ordinary group termination. Do not claim full descendant cleanup without a container/VM, cgroup/job object, supervised separate OS identity, or equivalent process domain. If the current issue does not own that primitive, state the limitation and move live qualification to an explicit downstream gate or stop for a human scope decision.

### 3. Prefer scoped permissions

Keep Hermes' global approval mode at `smart` by default. Configure the child deny-by-default and allow only the file and command families needed for the task. Check the child's current `--help` before relying on flag names.

A Claude tool allowlist is an authorization layer, not necessarily an OS sandbox. Claude's OS-backed sandbox applies to `Bash` and Bash descendants; built-in `Read`, `Edit`, `Write`, `Glob`, `Grep`, and web tools use Claude's permission system. If the safety claim depends on OS confinement, expose `Bash` only and edit/test through sandboxed commands, or apply and test equivalent exact permission rules for every non-Bash tool.

If a trusted child needs `git`, `gh`, `npm`, and `node`, allow those families rather than all shell commands. For an authority-sensitive no-credential repair lane, prefer no child GitHub token/network at all: let the child edit and test, then have Hermes inspect the full diff, rerun checks, perform the already-authorized commit/push, and verify remote readback. Disclose that transport accurately. Do not include merge/deploy, destructive cleanup, credential management, or unrelated account commands.

### Credential-free live evidence for public repositories

When a repair lane needs original live GitHub findings but must receive no GitHub token, verify that the exact repository and PR are publicly readable through an unauthenticated request. If the task permits that egress, provide exact public REST GET endpoints and immutable review/comment IDs through the strict sandbox's API-domain allowance. Keep commit/push/publication parent-owned unless separately authorized. A domain allowlist is not a method/path boundary; use a narrow read broker or frozen evidence when stronger confinement is required.

Verify actual sandboxed tool output for authorized project read/write, denied private read, denied operator-control write, denied unrelated network, and allowed exact live PR read. A model summary or generic CLI permission-mode label is not the probe result. See `references/public-repo-credential-free-repair.md` for the tested preflight and honest partial-live evidence handoff.

### Evidence handoff for file-only workers

When a scoped worker has `Read`/`Edit` but no directory-discovery or network tool, give **exact absolute filenames**, not just a packet directory or live URLs. Name each review artifact and its readback (for example, `review-a.md`, `review-a-live.json`, `review-b.md`, `review-b-live.json`) and the specific source files to inspect. A readable directory alone is not a usable evidence pointer. Verify those files exist and validate their content shape before launch: `reviewer-A.txt` may be a launch prompt, not a verdict. Label prompts, exact final-message artifacts and original API readbacks distinctly; preserve original review/comment IDs and head. Do not make the worker guess filenames or widen its permissions merely to discover them.

If live-source access is intentionally unavailable, disclose the frozen-artifact fallback, preserve exact reviewer text and source URLs/IDs, and distinguish parent verification from worker verification. A worker admitting it never opened the signed artifacts has not satisfied the evidence-reading contract, even if its edit looks correct. Independently compare the change against every actual finding before accepting the handoff; do not claim the worker consumed evidence it did not read.

### 4. Launch non-interactively and supervise

Use realistic timeouts and completion notification. Verify the process actually starts.

Validate launcher control-file schemas during the harmless preflight, not during implementation. For a strict empty Claude MCP configuration, use `{"mcpServers": {}}`, not a bare `{}`. If startup rejects a control file before work begins, correct only that launcher-owned input and rerun the same boundary probes; do not loosen isolation or request redundant workflow approval. Inspect the runtime's reported model, exposed tools, effective permission mode and actual probe tool results rather than assuming requested flags took effect. A hardening layer can override the requested permission mode while explicit tool allowances and the OS sandbox remain active. See `references/claude-code-strict-child-isolation.md` for the verified retry pattern.

Be exact about supervision semantics:

- `notify_on_complete` is a one-shot exit notification, not continuous polling or streamed progress.
- After one manual poll, do not tell the user that Hermes is continuously “watching” unless a real periodic poll, stream, or watch pattern exists. Name the active mechanism precisely: worker process, completion watcher, periodic poll, or output watcher.
- One-shot CLIs such as `claude --print` may buffer the assistant response until process exit. Empty stdout alone is not a stall signal.
- If the user asks whether **work** stopped or only **polling** stopped, verify both process liveness and bounded progress evidence such as worktree changes, new tests/files, commits, child-process activity, or fresh log timestamps.
- Do not use a live PID as indefinite evidence of healthy progress. If runtime is unexpectedly long and artifacts stop changing, inspect logs/process state and set a concrete checkpoint.

Inspect progress at meaningful intervals rather than killing a healthy worker early. In user updates, separate verified facts (`process running`, `files appeared`) from unverified pending outcomes (`tests green`, `push complete`, `PR opened`).

**Reconcile ambiguous or delayed completion once.** When a restored process handle reports `exited` with no exit code but the expected final artifact is absent, do not immediately relaunch or classify the lane as failed. Cross-check the recorded PID against its command/workdir and bounded log/artifact progress; a PID alone is insufficient because it can be reused. If the original lane is still active, retain it and use one bounded completion watcher rather than repeated status calls. Accept a result only after process completion, exact final-artifact validation, worktree integrity and any required external readback. A later notification for a lane whose result was already validated is duplicate delivery: absorb it silently unless it changes the conclusion, and never republish its review or repeat the approval request. See `references/completion-reconciliation.md`.

### 5. Verify independently

Never trust the child's success marker alone. Read the diff, run required checks, compare local and remote heads, inspect the PR's live commit list, and read back comments/reviews. A child process exiting zero is not proof that a push, PR, or external write succeeded.

For hardened multi-lane execution, also verify the launch boundary itself:

- each lane has a fresh launcher-owned runtime/shim directory and a minimal trusted PATH with pre-resolved absolute executables;
- capability channels use per-lane authentication plus exact socket allowances; mode 0700 alone does not separate same-UID processes;
- server shutdown stops acceptance, drains/terminates in-flight handlers and subprocesses, and joins them before cleanup/return;
- reviewer integrity checks exact HEAD, tracked bytes/tree, index entries, skip-worktree/assume-unchanged flags, and relevant Git config rather than relying on `git status` alone;
- builder progression compares committed old-head→new-head paths against the frozen allowed-path envelope before accepting the new head.

## Approval timeout recovery

If Hermes returns `BLOCKED: Command timed out without user response`:

1. Stop and honor any no-retry-until-response instruction.
2. Explain which launcher characteristic triggered the outer gate.
3. Do not ask for redundant magic wording if the workflow itself was already authorized.
4. After the user responds, replace blanket child bypass with scoped permissions.
5. Continue the existing authorized workflow and preserve its original authority boundaries.

If the user explicitly says they do not want per-child prompts, treat that as a durable workflow correction. The answer is a safer scoped launcher—not globally disabling Hermes approvals.

## When blanket bypass is justified

Use a child's blanket permission bypass only when all are true:

- the workspace is genuinely disposable and isolated;
- broad command access is necessary;
- the workflow is explicitly authorized;
- the outer approval channel is available and expected;
- external authority gates are independently enforced and verified.

Global YOLO/off is a separate security decision and should not be enabled merely to smooth routine coding-agent launches.

## Pitfalls

- **Redundant approval theater:** asking the user to repeat approval after they already authorized the bounded workflow.
- **Identity confusion:** saying “approve Claude” when Hermes actually flagged a shell command shape.
- **Blanket global workaround:** disabling all approvals to fix one launcher false-positive.
- **Silent denied tools:** using a non-interactive deny mode without explicitly allowing required validators or Git commands.
- **Overbroad allowlist:** allowing every shell command because one build command was missing.
- **Unverified success:** reporting pushed/opened/posted based only on child output.
- **Authority leakage:** letting a builder merge or deploy because its shell permissions technically permit it.
- **Synthetic-home overclaim:** describing hidden default credential locations as filesystem isolation even though same-UID absolute paths remain reachable without an OS sandbox.
- **Tool/sandbox confusion:** assuming Claude `Read`/`Edit`/`Write` are covered by the Bash sandbox.
- **Socket-permission overclaim:** treating a random mode-0700 Unix socket as lane authentication against another same-UID process.
- **Process-group overclaim:** promising that every descendant dies at timeout even though a child can self-`setsid` outside the group.
- **Status-only reviewer proof:** using a clean `git status` as proof of exact tracked bytes despite index flags, config, or modify/restore seams.
- **Self-validating sandbox policy:** asserting plausible JSON keys in unit tests without confirming that the current agent runtime documents and enforces those exact keys and nesting.
- **Synthetic-path blind spot:** testing `/work/tree` while the real authorized worktree lives beneath the broadly denied operator home and therefore fails at launch.
- **Shared-scratch authority leak:** giving every lane write access to the launcher scratch root that also holds settings, MCP files, runtimes, broker payloads, or later lanes' material; mode bits do not fix same-UID access.
- **Worker-marker acceptance:** treating exit zero, a `DONE` line, or worker-reported test totals as proof before trusted-parent tests, repository inspection, and remote readback.

## References

- `references/claude-code-scoped-noninteractive-launch.md` — concrete Claude Code pattern using `dontAsk` plus a narrow tool allowlist, including timeout recovery. Use for ordinary trusted lanes; it is not a hard filesystem-confinement claim.
- `references/claude-code-strict-child-isolation.md` — strict OS-backed Claude sandboxing for authority-sensitive lanes, Bash-vs-built-in-tool boundaries, no-credential repair workers, lane-authenticated capabilities, exact reviewer integrity, changed-path containment, and the residual self-`setsid` lifetime limit.
