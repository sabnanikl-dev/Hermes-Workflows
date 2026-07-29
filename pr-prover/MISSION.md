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

A merge-readiness run must configure **exactly one** of each required role in that order. Configuration enforces exactly `reviewer-a`, `reviewer-b`, `integration-auditor`, in that order, and the loop runs the lanes as configured; a missing, duplicated, or reordered required role is a configuration error rather than a run that quietly proves less than it claims. Supporting implementation may use generic internal iteration, but configuration cannot redefine the required acceptance lifecycle.

Reviewer A and Reviewer B are **adversarial** by mandate. On any head that follows a fix, a reviewer whose stance is "does this look correct" shares the builder's framing and its blind spot, so the lanes are prompted to try to *kill* the change — bad-faith passes, weakened or deleted coverage, gamed thresholds, shrunken scope, stale evidence, unproven invariants — and each published artifact must state what it attempted, not only what it confirmed. What is enforced mechanically is the declaration; the judgement stays the reviewer's.

If the frozen ledger contains valid blockers, Claude receives only that ledger. The normal budget is at most two fix cycles. One corrective builder rerun may complete an omitted item inside the current frozen ledger; it does not consume a new fix cycle or broaden scope. Any resulting push still triggers the full exact-head proof. Any further pass requires Karan's explicit blocker-scoped exception.

Each fix cycle starts the builder in a **fresh context**. A builder that carries a failed cycle's reasoning into the next one degrades exactly when the last cycle matters most, so cycle two is launched the way cycle one was — a new process, re-grounded on the live PR and on a blocker file written for that cycle — and everything that must survive between cycles travels through the run state file rather than through conversation history.

Human feedback is reconciled at two guard points, and only two: before a fix attempt opens, and before a run reports `merge-ready`. Fixing against an unread human objection is worse than not fixing, and recommending a merge over one is worse still, so each guard reads the conversation, review, and inline-thread surfaces to completion and clears an item only on evidence the reconciler can prove — a later decisive review by the same author, a thread GitHub records resolved or outdated, or an acknowledgement of an earlier comment by immutable id.

A post published under one of the run's own lane logins does not acknowledge anything: a lane clearing the objection it was told to answer is marking its own homework. Where the operator's account is also a configured publishing login, that denial otherwise leaves no identity able to answer at all, so trusted run configuration may pin *exact immutable acknowledgement post ids* the operator authorized before launch, each bound to bounded evidence for the body that post held when they read it, and those exact posts participate under every other rule unchanged. The authorization is per post and per what that post says; an unpinned post from the same account is refused exactly as before, and a pinned post edited afterwards — into broken grammar or into different, perfectly valid acknowledgement lines — is refused too, because an id survives an edit and an authorization must not. Any post the run itself published is refused whatever is configured. That last refusal is by immutable id, so editing a lane's artifact cannot buy it acknowledgement authority — the edit costs the artifact its ownership and returns it to human classification, and those two answers are deliberately not the same answer. Absent or empty configuration is the strict denial.

A head already proven blocked still reports `blocked`; the blockers are real whatever the conversation says, and refusing to answer is not the same as answering carefully. But feedback that is unresolved, incomplete, or ambiguous is never flattened into a readiness claim: it stops the run as `needs-Karan`.

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
| M1 | Every gate, artifact, classification, and report binds to one full current PR `headRefOid`; live PR number, state, head branch, and base branch remain unchanged at terminal decisions. | shipped | `github.py`, `loop.py`, stale-head tests; the integration matrix holds a required visual gate to image files it must really produce, decoded in full and validated for chunk type, order, format, size, and head binding, so missing, unreadable, corrupt, mis-typed, mis-ordered, wrong-size, and wrong-head evidence are each refused; `tests/test_visual_semantics.py` adds the semantic half, holding a configured visual gate to required print detail bodies read out of the PDF, mobile field labels measured per required column, and small-text contrast recomputed from the recorded colours, so a rendering whose files are all present and well-formed still fails when what they existed to show is absent |
| M2 | Any push invalidates all prior evidence and requires gates plus the full ordered review lifecycle on the new head. | shipped for invalidate-and-re-prove; the ordered three-role part is tracked by M8 | `loop.py`, `state.py`, loop and verdict tests; the integration matrix re-renders each gate against the new head and refuses a post-push verdict that answers about the old one |
| M3 | A builder push counts only when local worktree HEAD, verified remote branch, PR `headRefOid`, PR commit list, and a new signed comment from the configured builder identity agree. | shipped | `github.py`, `loop.py`, push-agreement and readback tests |
| M4 | A reviewer result counts only when role, verdict, and exact head are valid, and the lane's exit status agrees with its marker. | shipped | `verdicts.py`, `reviewers.py`, `loop.py`, verdict and relay tests; the integration matrix proves the loop consults that parser on the publishing path, so an artifact declaring another lane's role or no attempted kill-switch stops the run instead of reaching the PR; `scripts/codex-reviewer.sh` hands that parser only Codex's `--output-last-message` file and prefixes the narration it keeps, so a prompt echo cannot add a verdict candidate, and the adapter smoke round-trips the finding grammar the prompt states through the parser that reads it on a nine-blocker fixture; `reviewers.py` accepts a prepared artifact with no structured records, renders the final-message records deterministically into the publication copy, and treats any prepared-artifact records as a second claim that must match exactly; a conflicting, rewritten, duplicated, or malformed record fails closed. `artifact_matches()` applies the canonical comparison to the body GitHub actually shows, so a relay-side truncation or substitution that keeps the declaration block intact is a readback failure instead of transport this run may call complete; and the summary grammar is the exact 1–300 the prompt states, preserved character for character apart from real secret redaction, because a comparison against a shortened record cannot see a record that was changed where the shortening fell |
| M5 | GitHub feedback surfaces are complete or the run fails closed. Missing, null, malformed, truncated, or unknown-completeness thread data is not an empty complete result. | shipped | `github.py` pages conversation comments and reviews to the last page and walks the review-thread cursor with its page sequence checked rather than assumed; `loop.py` re-reads all three surfaces until two consecutive passes agree; thread-read, stable-observation, and human-feedback tests |
| M6 | An acknowledgement clears only an existing earlier comment by immutable ID, with chronology evidence; missing, equal, or ambiguous ordering fails closed. A post written under a configured publishing login acknowledges nothing unless the operator pinned that exact immutable post id before launch *and* it still holds the body they pinned it over, and a post this run published acknowledges nothing at all, whatever it is later edited to say. | shipped | `feedback.py` holds one finite classifier — six questions, no serial special cases — over candidates ordered globally by UTC-aware timestamp, surface, then id; `loop.py`; the acknowledgement truth-table tests. The operator seam is one bounded, validated list of exact id/`body_evidence` pins in `config.py`, carried through `RunArtifacts` by `loop.py` and printed back by `check-config` and by every human-feedback stop; `tests/test_operator_acknowledgements.py` drives the two-publisher deadlock through the real config file → loop → reconciliation path and holds the negative half — unpinned, omitted, altered, unlisted, lane-published, and id-names-nothing — to stopping before any builder launch. The pin is an id *and* the `publication_evidence` digest of the body the operator read, the same pair `verified` keeps, because an id survives every edit: pinning by id alone authorized whatever the post was rewritten to say, and on a repository where the operator's account is the publishing login that edit is one the login can make for itself. A pinned post whose current evidence differs is refused and named back as `operator_pinned_acknowledgements_changed`; the truth table and a loop-level regression drive that edit — into different, still-valid acknowledgement grammar under the same id — through the real config file, and the same file re-pinned to what the post now says runs, so the refusal is proved to be the evidence rather than the edit. Acknowledgement authority asks `RunArtifacts.published`, the id-only half of identity, rather than the content-bound `owns` that M7 needs to be able to lapse, so an artifact the run published and somebody then rewrote into valid acknowledgement grammar loses ownership without gaining authority; the truth table and the loop-level edited-artifact regression drive that edit through the real config file, the published-and-verified artifact, and the reconciler together |
| M7 | A configured login is not by itself proof that feedback is agent-authored. Exclusion requires positive run-owned evidence; unattributed or colliding-account feedback remains human feedback. | shipped | `state.py` retains each artifact by immutable id *and* the publication evidence readback verified, so an edited artifact re-enters human classification; `feedback.py` ownership, `config.py`, `github.py`, `loop.py`, readback, edited-artifact, and human-feedback tests |
| M8 | Merge-readiness configuration contains exactly Reviewer A, Reviewer B, and Integration Auditor in that order. A missing auditor, duplicate role, or auditor-first order is invalid. | shipped | `config.py`, `loop.py`, configuration tests; the integration matrix runs inspection, gates, the three roles, and the rendered report as one ordered pass, so an ordering break with every step still correct fails there; the adapter smoke runs that same ordered pass with the reviewer lanes really executing `scripts/codex-reviewer.sh`, whose Codex-shaped execution writes the external artifact its prompt named, so the three roles, the configured relay, and the readback are proved over artifacts a reviewer lane actually produced rather than ones a test wrote for it |
| M9 | Operational clone state is not mutated. Each lane uses a fresh run-owned worktree at a verified head; unsafe or reused paths and worktree-root filesystem failures become sanitized fail-closed results rather than raw exceptions. | shipped | `worktrees.py`, `errors.py`, `loop.py` gives every gate and reviewer lane its own checkout and proves it clean and on the bound SHA before and after that lane; worktree, lane-isolation, and real-git integration tests |
| M10 | One configured value is the lane's timeout everywhere it is enforced and reported, and a timed-out lane fails closed rather than having its marker read. Quiet output alone is not failure. | shipped | `commands.py`, `loop.py`, `report.py`, command, trusted-agent, and verdict tests; the integration matrix carries a half-hour-quiet builder through to the report as a lane that succeeded, against the same silence under a timeout, which fails closed |
| M11 | State and lock creation/read/write/replace/cleanup failures are deterministic, sanitized, and fail closed while preserving the original stop reason. | shipped | `state.py`, `errors.py`, state tests |
| M12 | The normal fix budget is two cycles; attempt three is unreachable without an explicit Karan exception recorded outside the automatic path. Each cycle starts the builder in a fresh context, with continuity carried only by the run state file. | shipped | `state.py`, `loop.py`, `scripts/claude-builder.sh`, cycle-cap and builder-cycle tests |
| M13 | Reports are recursively redacted and distinguish transport success, implementation verdict, exact-head readiness, and human merge authority. | shipped | `redaction.py` sanitizes the whole assembled payload; `report.py` renders per-lane transport, `transport_complete`, outcome, head, verdicts, classification, and a constant `merge_authority` line in both renderings; redaction, boundary, and report-separation tests |
| M14 | The tool never merges, force-pushes, deploys, installs, releases, or mutates client/live/account systems. | shipped | reachable command surfaces, boundary scans; the removal scan now reads the two shipped adapter launchers as well as the modules, and every rejected token is held to a sample it must still catch |

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
