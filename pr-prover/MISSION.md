# `pr-prover` Mission Contract

- **Status:** Normative v3 repository contract
- **Product owner:** Karan
- **Primary operator:** Hermes
- **Governing work:** [PAPI-84](https://linear.app/papi-consultants/issue/PAPI-84/mission-contract-v3-reliable-autonomous-pr-prover) and [GitHub issue #1](https://github.com/sabnanikl-dev/Hermes-Workflows/issues/1)

## Product definition

`pr-prover` is a thin, repository-owned command-line coordinator that helps Hermes get an **existing** pull request to one of three evidence-backed outcomes: `merge-ready`, `blocked`, or `needs-Karan`.

It does not build features from vague requests, manage a fleet of agents, replace GitHub, or merge pull requests. It makes the already-proven review/fix/re-review loop repeatable and binds every claim to live GitHub evidence for one exact head.

## Product boundary

The complete product is:

1. inspect one live pull request and bind a run to its full `headRefOid`;
2. run repository-native gates, plus visual/browser gates when configured;
3. run Reviewer A, Reviewer B, and Integration Auditor against that exact head;
4. let Hermes classify and freeze the valid blocker ledger;
5. when the ledger is non-empty and the cycle budget allows it, launch trusted Claude to fix only that ledger, verify, commit, push, and comment;
6. read the resulting branch, commit, PR head, and signed comment back from GitHub;
7. invalidate all prior evidence and repeat the gates and review sequence on the new head;
8. report the exact-head outcome to Karan, who alone decides whether to merge.

The implementation should remain standard-library Python with no install step and one small local state file plus one run lock. New machinery must be justified by a current step above, not by a hypothetical future lane.

## Trusted operating model

- Claude Code is trusted for scoped builder/fix work in the bound repository and PR branch.
- Reviewer lanes are trusted to judge one exact head. When publication is relayed, the judging lane remains credential-free and the parent performs transport plus GitHub readback.
- Hermes is the verifier and final integrator. Hermes does not accept an agent's statement about a push, identity, artifact, or head without direct evidence.
- Karan alone may approve a merge or broaden the mission.

This is ordinary trusted-agent orchestration, not a hostile same-UID zero-trust system.

## Explicit non-goals

The mission does not include:

- generic workflow engines, agent registries, plugin APIs, dashboards, services, queues, or orchestration DSLs;
- capability sockets, custom credential brokers, per-lane bearer secrets, or channel authentication protocols;
- synthetic HOME, reimplementation of Claude sandbox policy, arbitrary host-path denial proofs, or cross-lane same-user isolation;
- executable fingerprints, launcher byte attestation, container/VM/cgroup/job-object qualification, or detached-descendant security proofs;
- force push, automated merge, install, release, deploy, preview, client/live-system mutation, account changes, purchases, or external public/client communication other than the required repository-scoped PR artifacts;
- compatibility layers for hypothetical agents or script lanes not required by the proven workflow.

Isolated worktrees, task-scoped commands, realistic timeouts, redaction, and direct GitHub verification are execution hygiene—not a reason to grow the product into a security platform.

## Normative lifecycle

For every candidate head, the acceptance lifecycle is ordered:

```text
baseline/visual gates
→ Reviewer A
→ Reviewer B
→ Integration Auditor
→ Hermes classification and frozen ledger
```

A merge-readiness run must configure **exactly one** of each required role in that order. Configuration today rejects fewer than two independent named reviewer lanes and runs the lanes in configured order; the ordered three-role check is held by Hermes when it writes the run config until the configuration lifecycle check lands. A missing, duplicated, or reordered required role is a run Hermes must not start. Supporting implementation may use generic internal iteration, but configuration cannot redefine the required acceptance lifecycle.

If the frozen ledger contains valid blockers, Claude receives only that ledger. The normal budget is at most two fix cycles. One corrective builder rerun may complete an omitted item inside the current frozen ledger; it does not consume a new fix cycle or broaden scope. Any resulting push still triggers the full exact-head proof. Any further pass requires Karan's explicit blocker-scoped exception.

A push starts a new exact-head proof. Old gates, artifacts, reviews, and readiness claims remain historical evidence only.

## Outcome meanings

- **`merge-ready`** — the final live exact head passed required gates, the ordered review lifecycle, GitHub artifact/readback checks, and human-feedback reconciliation with zero unresolved blockers. This is advice, not merge permission.
- **`blocked`** — the exact head has one or more confirmed contract, correctness, safety, test, or shipped-path blockers.
- **`needs-Karan`** — evidence is ambiguous or incomplete, live state changed, authority would need to expand, human feedback needs judgment, or infrastructure failed in a way the tool cannot safely classify.

GitHub's mechanical `MERGEABLE`/`CLEAN` state is not a `merge-ready` verdict. Demonstrating that one capability works or checking a tracker acceptance box is not final implementation acceptance while current-head blockers remain.

## Load-bearing invariants and proof map

This table is the behavioral contract for the finished product. The status column records what the shipped tool proves **today**, so no reader mistakes a contract obligation for an implemented one; `owed` rows name the slice that must land them and must not be claimed as enforced until it does.

| ID | Required behavior | Status | Current proof seams |
| --- | --- | --- | --- |
| M1 | Every gate, artifact, classification, and report binds to one full current PR `headRefOid`; live PR number, state, head branch, and base branch remain unchanged at terminal decisions. | shipped | `github.py`, `loop.py`, stale-head tests |
| M2 | Any push invalidates all prior evidence and requires gates plus the full ordered review lifecycle on the new head. | shipped for invalidate-and-re-prove; the ordered three-role part is tracked by M8 | `loop.py`, `state.py`, loop and verdict tests |
| M3 | A builder push counts only when local worktree HEAD, verified remote branch, PR `headRefOid`, PR commit list, and a new signed comment from the configured builder identity agree. | shipped | `github.py`, `loop.py`, push-agreement and readback tests |
| M4 | A reviewer result counts only when role, verdict, and exact head are valid, and the lane's exit status agrees with its marker. | shipped for marker-bound verdicts; GitHub-published reviewer artifacts (author, signature, review `commit_id`) owed by PAPI-90 | `verdicts.py`, `loop.py`, verdict tests |
| M5 | GitHub feedback surfaces are complete or the run fails closed. Missing, null, malformed, truncated, or unknown-completeness thread data is not an empty complete result. | owed by PAPI-97 | `github.py` holds the comment reads the completeness rule will bind |
| M6 | An acknowledgement clears only an existing earlier comment by immutable ID, with chronology evidence; missing, equal, or ambiguous ordering fails closed. | owed by PAPI-97 | none yet |
| M7 | A configured login is not by itself proof that feedback is agent-authored. Exclusion requires positive run-owned evidence; unattributed or colliding-account feedback remains human feedback. | shipped for the builder fix comment (new comment id, pinned author, signature, head); reviewer-side identity owed by PAPI-90 and PAPI-97 | `config.py`, `github.py`, `loop.py`, readback tests |
| M8 | Merge-readiness configuration contains exactly Reviewer A, Reviewer B, and Integration Auditor in that order. A missing auditor, duplicate role, or auditor-first order is invalid. | partial: at least two distinct named lanes are required and run in configured order; the ordered three-role check is owed by PAPI-90 | `config.py`, `loop.py`, configuration tests |
| M9 | Operational clone state is not mutated. Each lane uses a fresh run-owned worktree at a verified head; unsafe or reused paths and worktree-root filesystem failures become sanitized fail-closed results rather than raw exceptions. | shipped | `worktrees.py`, `errors.py`, worktree and real-git integration tests |
| M10 | One configured value is the lane's timeout everywhere it is enforced and reported, and a timed-out lane fails closed rather than having its marker read. Quiet output alone is not failure. | shipped for single-value enforcement and fail-closed timeout; per-lane elapsed/quiet progress reporting owed by PAPI-90 | `commands.py`, `loop.py`, command and verdict tests |
| M11 | State and lock creation/read/write/replace/cleanup failures are deterministic, sanitized, and fail closed while preserving the original stop reason. | shipped | `state.py`, `errors.py`, state tests |
| M12 | The normal fix budget is two cycles; attempt three is unreachable without an explicit Karan exception recorded outside the automatic path. | shipped | `state.py`, `loop.py`, cycle-cap tests |
| M13 | Reports are recursively redacted and distinguish transport success, implementation verdict, exact-head readiness, and human merge authority. | shipped for recursive redaction and for separating the implementation verdict from exact-head readiness; a report field distinguishing lane/artifact transport success from GitHub readback is owed by PAPI-90, and explicit human-merge-authority reporting is owed by PAPI-97 | `redaction.py` sanitizes the whole assembled payload; `report.py` renders outcome, head, verdicts, and classification; redaction and boundary tests. `report.py` carries no transport-status or merge-authority field yet |
| M14 | The tool never merges, force-pushes, deploys, installs, releases, or mutates client/live/account systems. | shipped | reachable command surfaces, boundary scans |

The table defines behavioral proof obligations, not a mandate for one class, file, or abstraction per row. Prefer strengthening an existing seam and its focused tests over adding framework code.

## Review contract

Reviewer A focuses on correctness, safety, failures, tests, and regressions. Reviewer B focuses on architecture, maintainability, mission drift, and proportionality. Integration Auditor checks the shipped configuration, prompts, parsers, readback, GitHub surfaces, and exact-head outcome as one end-to-end contract.

A finding is blocking only when it demonstrates at least one of:

- violation of this mission or the linked issue's acceptance criteria;
- incorrect or unsafe behavior in a supported path;
- a false success/readiness claim;
- missing deterministic proof for a load-bearing invariant the current slice ships;
- scope contamination or prohibited authority.

Alternative designs, generalized hardening, style preferences, and hypothetical future-agent requirements are non-blocking. A row this slice does not own is not a blocker against it. Reviewers must not revive the superseded zero-trust platform or demand implementation-total formality beyond this behavioral contract.

After the three required reviews complete on one head, Hermes freezes their deduplicated valid blocker ledger. Fixes target that ledger holistically. Re-review verifies closure and detects regressions against this frozen mission; it is not a new architecture tournament.

## Completion gate

The product slice is acceptable only when, on the final exact head:

- both supported Python suites, both compile checks, shipped config validation, and diff hygiene pass;
- any changed adapter path passes its real repository-owned smoke;
- the invariants the slice ships have executable coverage appropriate to the changed surfaces;
- Reviewer A, Reviewer B, and Integration Auditor complete in order with zero valid blockers;
- Hermes verifies live GitHub head, commits, artifacts, identities, feedback resolution, and clean worktree evidence;
- the PR remains unmerged until Karan explicitly approves merge.

When evidence is incomplete, the correct product behavior is to stop and ask—not to infer success or add a new platform layer.
