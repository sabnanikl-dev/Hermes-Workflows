# Thin Existing-Tool Repo Contract Recovery

Use this pattern when an existing agent-operated CLI or workflow PR keeps accumulating fresh blocker classes even though tests are green and the governing mission exists mainly in chat, Linear, GitHub issues, or PR comments.

## Diagnose the structural gap

A missing repo-native contract is usually a **contributor**, not proof that code findings are false. Check separately:

1. Is the mission fragmented across trackers, prompts, comments, and an implementation-shaped README?
2. Can a fresh builder/reviewer discover the product and authority boundary from the repo root?
3. Is there one normative repo-owned mission independent of the current implementation?
4. Do behavioral invariants map to current proof seams, or are green tests being mistaken for semantic acceptance?
5. Are reviewers judging a frozen blocker threshold or restarting an architecture tournament on every head?

Do not say “no spec” when a strong external issue or README exists. Call the contract **fragmented and externally anchored** when that is accurate.

## Lean artifact set

For an existing thin tool, default to:

```text
AGENTS.md
<tool>/MISSION.md
```

Add one-line discovery pointers from the root and package READMEs. Keep role/review rules in `MISSION.md` unless a separate file has a real operational consumer. Do not add `.agentic/`, workflow configuration, dashboards, plugins, or a docs hierarchy merely because a full harness template supports them.

`AGENTS.md` should define read order, repo shape, mission lock, roles/authority, change discipline, and verification.

`MISSION.md` should define product boundary, trusted-agent model, ordered lifecycle, outcome meanings, repair budget, explicit non-goals, blocker threshold, behavioral invariant-to-proof map, and completion gate.

Label filenames in the proof map as **current informative proof seams**, not normative architecture. This preserves refactor freedom and prevents a specification from requiring one abstraction per row.

## Recovery workflow

1. Re-read the live parent mission, implementation issue, current PR, exact head, and latest handoff.
2. Verify a clean worktree bound to the live PR head.
3. Make a **docs-only contract pass**. Do not mix in repairs for the open code ledger.
4. Encode accepted behavior and known blocker classes as invariants without claiming they are fixed.
5. Explicitly exclude the architecture that caused drift while preserving ordinary execution hygiene.
6. Independently review for contradictions, accidental scope expansion, and implementation-total wording.
7. Repair only that contract-review ledger, then run a narrow independent re-review.
8. Run full repository verification when the branch contract requires exact-head gates even for docs-only work.
9. Commit and push only when authorized.
10. Verify local HEAD, remote branch, PR `headRefOid`, and PR latest commit equality; read back the new files remotely.
11. State that the push invalidated prior exact-head reviews and that existing code blockers remain.
12. Record the result in the canonical tracker without overstating issue state.

## Convergence rules

- A blocker must identify a mission/acceptance/supported-behavior/safety violation.
- Generalized hardening, alternative designs, and hypothetical future lanes are non-blocking.
- The first complete review freezes one deduplicated ledger.
- Repair targets that ledger holistically.
- Re-review proves closure and catches mission regressions; it does not restart product discovery.
- A corrective builder rerun may complete an omitted item without consuming another fix cycle, but any resulting push still triggers the full exact-head proof.

## Feedback-surface pitfall

When unresolved GitHub conversation comments are machine-classified as human blockers, an informational handoff comment can create a new blocker. Prefer repository links/commit metadata, a PR-body update when appropriate, or an external canonical tracker not consumed by the feedback classifier. Post a PR comment only when its identity/signature is intentionally recognized or when it is meant to require human acknowledgement.

## Verification checklist

- Only intended documentation paths changed.
- Discovery links resolve.
- Owner, operator, authority, lifecycle, outcomes, non-goals, and blocker threshold are explicit.
- Thin-tool exclusions are explicit.
- No code blocker is described as repaired by documentation.
- Independent re-review passed.
- Required test suites/checks passed.
- Remote files exist at the verified PR head.
- PR remains draft/open/unmerged when merge was not authorized.
- Tracker readback says old reviews are historical and implementation blockers remain.
