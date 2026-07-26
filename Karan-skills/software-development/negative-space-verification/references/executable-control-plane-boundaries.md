# Executable Control-Plane Boundaries

Use this reference when repeated PR review failures reveal that workflow guarantees exist mainly as prompt prose, agent memory, or duplicated skill instructions.

## First-principles split

Critical guarantees belong in different layers:

1. **Versioned control plane** — enforces legal states, exact-head binding, cycle limits, process locks, runtime/model pins, scope decisions, and push/readback verification.
2. **Skill package** — explains when to run the workflow and how to interpret its outcomes. Keep the main SKILL.md concise; place optional prompts in `templates/`, domain notes here in `references/`, and small deterministic probes in `scripts/`.
3. **Agent judgment** — classifies product/architecture tradeoffs and blocker validity, but cannot silently bypass control-plane gates.

Prompt text naming a model, cycle cap, worktree, or permission boundary is not runtime proof. The launcher or state machine must record and enforce it.

## Minimum state model

A PR prover should terminate every inspection in one named state:

```text
INSPECT
→ SCOPE_DECISION
→ REVIEW
→ FIX
→ VERIFY_PUSH
→ REREVIEW
→ READY | ESCALATE | REPLACE
```

Persist repository/PR identity, base/head SHA, phase, cycle, risk classes, frozen blocker set, required gates, builder runtime, worktree lock, remote readback, reviewer artifacts, and stop reason in an atomic machine-validated manifest.

Illegal transitions fail closed. In particular:

- FIX cannot start without exact-head findings and a frozen blocker envelope.
- REREVIEW cannot start until local HEAD, remote branch, and PR head agree.
- READY cannot be entered from stale reviews, failed checks, unresolved blockers, or dirty mergeability.
- Cycle 3 requires a separate human-approved exception; it is never inferred from urgency.

## Scope reset before repair

Before consuming a fix cycle, classify the PR:

```text
PATCH | RECONSTRUCT_SAME_PR | SPLIT | REPLACE | HUMAN_DECISION
```

Escalation signals include:

- stale/conflicted branch plus major current-main movement;
- a fix introducing a parser, sanitizer, policy engine, or producer schema;
- broad claims about arbitrary language, HTML, secrets/PII, URLs, or config implemented by finite heuristics;
- production controls and tests sharing the same detector or assumption;
- rapid diff growth that changes a user feature into a generalized regression framework;
- a new risk class appearing after the blocker envelope was frozen.

A scope reset is not automatically a new PR. `RECONSTRUCT_SAME_PR` can rebuild the bounded feature from current main and force-with-lease the existing PR branch while preserving the PR as the coordination surface.

## Hardened builder boundary

Mirror hardened reviewer launchers with a builder wrapper that:

- pins the actual model in the command;
- rejects model/permission/runtime overrides;
- takes an exclusive per-worktree lock;
- records starting SHA, process identity, timestamps, and result;
- uses a bounded non-interactive tool allowlist and strict/empty MCP configuration;
- verifies branch/head before launch;
- exposes no silent raw-command or alternate-model fallback.

Never launch a wrapper and a direct builder concurrently in one worktree.

## Source-of-truth discipline

Keep the executable control plane and canonical skill package in one versioned repository. Active profile copies and local launcher binaries are installed artifacts. Installation should be deterministic, detect dirty/diverged source, and verify installed hashes/readback.

Do not solve source drift by independently editing both the repository and active runtime. Change the canonical source, review it, then install/sync it.

## Pilot acceptance

A control-plane implementation is not proven by unit tests alone. Pilot it on a real bounded PR and require:

- exact-head state reconstruction;
- explicit scope decision;
- no raw/manual orchestration bypass;
- at most the configured number of complete review/fix cycles;
- independent reviewer and integration-auditor PASS on the final head;
- clean mergeability and successful checks;
- no merge or live-system mutation without the human gate.

If the pilot cannot pass within the configured cap, report control-plane or task failure honestly. Do not weaken the gate to manufacture a successful demonstration.

## Library-maintenance lesson

When the user rejects a process correction because it merely enlarges SKILL.md, do not append another subsection. Move enforceable behavior into versioned tooling, keep the class-level skill as the operator interface, and preserve detailed incident lessons in references rather than the main procedural spine.