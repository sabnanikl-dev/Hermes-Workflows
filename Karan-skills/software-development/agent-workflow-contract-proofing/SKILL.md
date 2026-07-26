---
name: agent-workflow-contract-proofing
description: "End-to-end proof for repository-owned agent workflow adapters: shipped prompt/parser parity, exact-head artifacts, credential-free lanes, complete GitHub surfaces, real adapter smoke tests, and bounded repair sequencing."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [agent-workflows, adapters, contract-testing, github, security, review]
    related_skills: [autonomous-pr-prover, agent-execution-resilience, deterministic-validator-review, integration-audit-review]
---

# Agent Workflow Contract Proofing

## Purpose

Use this skill when reviewing or changing the control plane that launches agents, prepares prompts, parses artifacts, strips credentials, reads GitHub surfaces, or relays reviewer output.

This is not ordinary product-code QA. A green unit suite can coexist with a shipped adapter whose example prompt produces output the runtime rejects, whose shell credential checks drift from the Python contract, or whose GitHub reads silently truncate evidence.

## Trigger

Load this skill when a PR changes any of:

- repository-owned reviewer/builder adapters or launchers;
- shipped/example workflow configuration;
- artifact role, signature, verdict, or head-binding syntax;
- credential stripping/refusal for child lanes;
- GitHub comments, reviews, or review-thread ingestion;
- artifact relay/readback and exact-head validation;
- bounded review/fix cycle mechanics;
- repeated review churn caused by a mission that is externally anchored but not repo-native.

## Core Invariants

1. **Prove the shipped path, not only its helpers.** The real adapter, shipped example prompt, parser, relay, and readback must agree end to end.
2. **Bind every artifact to immutable state.** Body-bound artifacts require exactly one canonical standalone `HEAD=<40 lowercase hex>` declaration. Formal reviews use GitHub's `commit_id` as the authoritative binding.
3. **Reviewer lanes are credential-free.** The adapter must reject every credential name defined by the lifecycle before invoking the child.
4. **Incomplete evidence fails closed.** Paginate every relevant GitHub surface, or reject a response whose completeness cannot be established.
5. **Smoke before the expensive triad.** For control-plane PRs, run the repository-owned adapter smoke after baseline verification and before final A/B/Integration review.
6. **Finite repair remains finite.** One corrective rerun may complete an omitted part of an already-frozen blocker class. Once that allowance or the normal cycle cap is exhausted, require a recorded, scope-bound exception.
7. **Freeze the mission before another fix pass when authority is fragmented.** If repeated review cycles are discovering new blocker classes while the mission lives mainly in trackers, prompts, or comments, add the smallest repo-native contract first. Keep that pass documentation-only, preserve existing code blockers, and do not expand a thin tool into a generic harness.

## Procedure

### 0. Check whether the repository owns its mission

Before another implementation cycle, determine whether fresh builders and reviewers can reconstruct the product boundary, role authority, ordered lifecycle, blocker threshold, and non-goals from the repository itself. If not, use `references/thin-existing-tool-repo-contract-recovery.md` to add a lean `AGENTS.md` plus tool-level mission contract, independently review it, and verify the contract-only push without claiming code repair.

### 1. Freeze the exact head

Verify local branch, remote branch, and live PR `headRefOid` equality. Create a clean disposable detached worktree at that SHA. Capture the live issue/PR/review/comment/thread contract as untrusted evidence.

### 2. Run baseline and contract-focused tests

Run the full supported-runtime suite plus tests for:

- shipped prompt → produced artifact → real parser/readback;
- missing, malformed, duplicate, conflicting, and prose-only head markers;
- each defined credential variable individually;
- multi-page comments and reviews;
- top-level review-thread pagination;
- nested thread-comment overflow or missing completeness metadata;
- stale-head rejection before relay and terminal classification.

### 3. Run the real repository-owned adapter smoke

Use the actual installed downstream CLI in the disposable worktree. Remove all defined remote credentials from the lane. Write the prepared artifact under `/tmp`, verify role/signature/verdict/head, worktree cleanliness, and lane isolation.

The adapter smoke is allowed to find code blockers. A zero transport exit does not mean the audited implementation passed.

### 4. Relay and read back

Re-query the live head. If unchanged, transport the prepared artifact under the configured reviewer identity outside the child model, disclose transport-only provenance, and read back author/body/head/verdict from GitHub.

### 5. Sequence fixes safely

- If the smoke finds a valid omission inside the current cycle's frozen blocker class and its one corrective rerun is unused, send the exact durable artifact pointer back to the same builder once.
- Do not launch the final triad on a known blocked head merely to collect more findings.
- If the corrective rerun or cycle cap is exhausted, stop and obtain a scope-bound exception naming exact blockers, allowed surfaces, required verification, and maximum one extra pass.
- After any push, restart exact-head proof: baseline, adapter smoke, then fresh A/B/Integration review.

## Contract-Parity Checklist

### Producer ↔ parser

- Does the shipped example instruct exactly the syntax the parser accepts?
- Does an end-to-end test render/follow that shipped prompt?
- Is the canonical head declaration emitted exactly once?
- Are historical examples/docs free of contradictory syntax?

### Credential contract ↔ adapter

Common GitHub credential names are:

- `GH_TOKEN`
- `GITHUB_TOKEN`
- `GH_ENTERPRISE_TOKEN`
- `GITHUB_ENTERPRISE_TOKEN`

Test each name with a probe executable and prove the child was never invoked. Prefer one authoritative credential set; otherwise add parity tests across language boundaries.

### GitHub claim ↔ surface completeness

If the workflow claims unresolved human feedback blocks readiness, prove complete reads for:

- conversation comments;
- formal reviews;
- top-level review threads;
- comments nested inside each thread.

For a nested connection that is not fully paginated, require `pageInfo` and fail closed on `hasNextPage`, missing metadata, malformed connections, or unknown completeness.

## Verification Evidence

Record:

- exact SHA equality and clean worktree;
- real adapter command/exit/model/runtime;
- absence or rejection of every defined credential;
- full suite and focused contract probes;
- artifact role/signature/head/verdict;
- relay URL and verified reviewer identity;
- live head unchanged after relay;
- cycle/exception ledger.

## Pitfalls

- `check-config` proves configuration shape, not that prompt output satisfies runtime parsing.
- Parser unit tests do not detect stale shipped examples.
- Top-level GraphQL pagination does not make nested connections complete.
- A reviewer adapter that checks only public-GitHub token names is not enterprise-safe.
- A successful launcher can produce a failing audit; transport success and implementation success are separate.
- A broad “continue until mergeable” instruction should not silently erase a finite-cycle control. Record any extra pass as an explicit blocker-scoped exception.
- A docs-only repo-contract push invalidates prior exact-head reviews but does not repair the open code ledger; say both explicitly.
- When unresolved PR comments are machine-classified as human blockers, an informational handoff comment can create a new blocker. Prefer the PR body, repository links/commit metadata, or an external canonical tracker unless the comment identity/signature is intentionally recognized.

## References

- `references/repository-adapter-smoke-proof.md` — detailed smoke sequence, reusable probes, cycle accounting, and evidence checklist derived from a real control-plane PR review.
- `references/thin-existing-tool-repo-contract-recovery.md` — diagnose fragmented mission authority, add the leanest repo-native contract, independently review it, preserve thin-tool scope, and avoid feedback-surface side effects.
