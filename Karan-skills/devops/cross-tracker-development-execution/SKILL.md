---
name: cross-tracker-development-execution
description: Operate coding work that uses Linear for mission acceptance and GitHub Issues/branches/PRs for implementation, with visible pickup state, isolated builders, exact-head review gates, and progressive acceptance evidence.
version: 0.3.1
metadata:
  hermes:
    tags: [linear, github, pull-requests, orchestration, verification, multi-agent]
---

# Cross-Tracker Development Execution

Use this skill when a coding mission is governed by a Linear parent/child contract while GitHub owns the implementation issue, branch, commits, pull request, checks, and reviews.

This skill coordinates systems; it does not replace `github-operations`, `linear`, `multi-agent-dev-workflow`, or `code-review`. Load those domain skills when available.

## Source-of-truth boundaries

- **Linear:** mission hierarchy, dependencies, acceptance criteria, approvals, status, and closeout evidence.
- **GitHub Issue:** executable repository contract and implementation scope.
- **Git branch/PR:** code, commits, review state, checks, and exact-head evidence.
- **Telegram:** progress and human decisions, not durable implementation authority.
- **Local worktree:** execution environment only; local state is never proof of remote visibility or delivery.

Do not build a competing tracker. A fresh session should reconstruct the work from live Linear plus GitHub without relying on chat history.

## Workflow

### 1. Reconstruct live state

Before mutation:

1. Read the Linear parent and intended child, including full description, comments, relations, state, and pagination metadata.
2. Read the GitHub issue, existing branches, open/all PRs, default-branch head, and repository instructions.
3. Verify the operational clone and all relevant worktrees.
4. Resolve stale historical children or conflicting active state before claiming new work.
5. Name the exact authority boundary: repository, issue, branch, allowed outputs, and excluded live effects.

If the active work was intentionally paused or the prior worker stopped mid-migration, resume from a verified durable handoff before selecting or resetting anything. Read `references/cross-session-pause-resume-handoff.md`: it defines the pause/resume tracker packets, stale-evidence rule, diagnostic baseline, deterministic Claude-session continuation check, worker cleanup, and post-resume verification gates.

### 2. Make pickup visibility explicit

Choose one mode and disclose it. For Karan's GitHub-native coding missions, **GitHub-visible is the default** once branch creation is inside the approved scope; use local-first only when explicitly requested or when remote branch mutation is not yet authorized.

- **GitHub-visible (default):** create an issue-linked remote branch at claim time through GitHub's Development flow, then attach the isolated worktree to that remote branch.
- **Local-first (exception):** create an isolated local branch/worktree and publish only after the first coherent commit passes baseline checks.

A local branch does not appear in GitHub's issue Development surface. Never say an issue is visibly claimed or branched in GitHub when only a local ref exists.

For GitHub-visible pickup:

1. From the verified default-branch head, create the issue-linked remote branch—prefer `gh issue develop <N> --repo <owner/repo> --name <branch> --base <base>` when the installed CLI supports it, or use GitHub's native **Create a branch** Development action.
2. Verify both the issue association and remote ref before starting the builder (`gh issue develop <N> --list` when supported, plus `git ls-remote --heads origin <branch>`).
3. Fetch the remote branch and create an isolated tracking worktree from it. Do not separately create a same-named local-only branch first.
4. Produce the first coherent bounded commit and push it to that branch.
5. Open one draft PR with `Closes #N` outside code fences/quotes.
6. Verify the remote ref, PR `headRefOid`, last commit, draft state, base branch, and `closingIssuesReferences`.

An issue-linked baseline branch is visible work-order state, not an empty-commit substitute; do not create a fake commit just to make a PR possible. If native branch association cannot be created or verified, disclose the fallback immediately and use local-first until the first real commit can support a linked draft PR.

If using local-first mode, progress updates must state that GitHub will show no branch/PR until publication.

### 3. Run the builder in isolation

Give the builder a self-contained contract containing:

- exact repository/worktree/branch and baseline SHA;
- live GitHub issue and Linear acceptance scope;
- allowed files/outputs and forbidden systems;
- required tests and exact handoff evidence;
- whether it may commit, push, and open a draft PR;
- explicit no-merge/no-deploy/no-install boundaries unless separately authorized.

The builder owns its implementation handoff when authorized. Hermes independently verifies every claim.

### 4. Verify the builder handoff

Do not trust the builder summary alone. Verify:

- local worktree is on the intended branch and clean after commit;
- local HEAD equals the remote task ref;
- PR `headRefOid` and last PR commit equal local HEAD;
- PR links the intended GitHub issue through live closing references;
- changed paths and diff stay within scope;
- required tests, syntax/static checks, and `git diff --check` pass;
- operational clone and unrelated worktrees remain unchanged;
- excluded live systems were not touched.

### 5. Run an independent exact-head review

After the branch/PR is published:

1. Freeze the exact PR `headRefOid`.
2. Launch an independent Codex/reviewer lane read-only against that SHA.
3. Require inspection of the full base-to-head diff and real verification commands.
4. Ask for blocking findings with stable IDs and `file:line` evidence plus a machine-readable final marker.
5. Treat passing builder tests as necessary, not sufficient.
6. Route valid blockers back to the builder.
7. Any push invalidates the prior review; re-read the new head and re-run review.
8. When the independent reviewer runs credentialless/read-only, Default Hermes may relay the substantive verdict through the configured reviewer identity. Label it as relayed; do not pretend the model posted it directly.
9. Verify the resulting GitHub review by direct API readback: reviewer login, `state`, exact `commit_id`, body marker, and review URL must all match the current head. Do not accept an authority-expanding artifact state merely because its author/head/tag match—for a neutral reviewer lane, require the intended neutral state (normally GitHub `COMMENTED`) and reject approval/request-changes states.
10. Do not call the issue review-ready until the exact-head reviewer is green or an explicit human decision resolves the blocker.
11. For PRs that implement agent launchers, credential brokers, role isolation, or prompt-injection controls, run the effective-authority probe matrix in `references/credential-bearing-agent-launcher-review.md`. Passing unit tests and local capability enums are not proof that raw provider credentials, parent HOME, descendant processes, shared reviewer worktrees, model-auth bypasses, or legacy script lanes are actually contained.

Keep P0/P1 blockers separate from optional hardening so the review loop does not expand scope indefinitely.

### 6. Update Linear acceptance criteria progressively

Acceptance checkboxes are live evidence bookkeeping, not a ceremonial closeout step.

- Check a criterion as soon as it has sufficient verified implementation/test/readback evidence.
- Do not check a behavioral criterion from a worker self-report alone.
- Do not wait until final closeout to check unrelated criteria that are already proven.
- Change only the exact satisfied checkbox lines in the full current description.
- Re-read the issue after every body mutation and assert the exact checked and unchecked sets.
- Linear may normalize Markdown `[x]` to `[X]`; verification must accept both.
- A reviewer blocker prevents checking the affected criterion but should not automatically uncheck unrelated criteria whose evidence remains valid.
- Keep the issue `In Progress` while behavioral criteria or mandatory reviews remain open.

Examples of criteria that may be provable before final review include verified single-PR containment and operational-clone non-mutation. Core correctness criteria usually wait for independent review.

### 7. Close the loop

When all child criteria are proven:

1. Re-run the final exact-head test/check suite.
2. Re-read every GitHub review surface and unresolved thread.
3. Verify remote/PR/local head equality.
4. Check the remaining Linear criteria and read them back.
5. Move the child to `In Review` or `Done` only as its contract allows.
6. Update the parent roll-up criterion only after the child is fully accepted—not merely because a draft PR exists.
7. Preserve human gates for merge, deploy, install, client/live mutation, credentials, purchases, and publication.

### 7.1 Close out a deliberately blocked PR

When exact-head review still blocks and the authorized repair cycles/exceptions are exhausted, do not treat a general “continue until mergeable” instruction as unlimited exception authority. Finish the currently authorized evidence, then ask whether to approve another bounded pass, keep blocked, or close/split.

If Karan chooses **keep blocked**:

1. Preserve the PR as open/draft and do not merge or mark ready.
2. Publish/read back the final exact-head reviewer artifacts and verify local/remote/live SHA equality.
3. Update stale PR-body language so mechanical `MERGEABLE/CLEAN` is clearly separated from blocked review readiness.
4. Keep the Linear issue `In Progress` unless its contract explicitly defines another blocked state.
5. Add a durable Linear handoff with the frozen blocker ledger, consumed budget, evidence links, and exact resumption contract.
6. Verify the handoff through its returned comment ID, not comment ordering.

Use `references/exact-head-blocked-pr-handoff.md` for the full checklist and trusted-agent boundary probes.

## Failure rules

Stop or report blocked when:

- Linear shows conflicting active children or stale authority;
- the GitHub issue/branch/PR targets the wrong repository;
- local and remote heads diverge;
- the PR lacks a verified issue linkage;
- the reviewer is bound to a stale head;
- a worker modified the operational clone or unrelated worktree;
- acceptance boxes are ahead of evidence;
- a required external/live action lacks explicit approval.

Never repair ambiguous remote state by guessing.

## Progress reporting

Use concise milestone updates:

- **Picked up:** Linear child/state + local-first or GitHub-visible mode.
- **Published:** branch, draft PR URL, exact head, linkage readback.
- **Verified:** tests/checks and scope evidence.
- **Reviewing:** reviewer identity/lane and exact head.
- **Blocked:** finding IDs and next bounded action.
- **Accepted:** Linear checkbox/readback summary and remaining parent gate.

Avoid saying “running automatically” when only a one-time poll occurred. Distinguish the active process, one-time polling, and completion notification/watchdog.

## References

- `references/cross-session-pause-resume-handoff.md` — durable Linear/GitHub/repository pause packets and safe fresh-session resume for uncommitted or mid-migration work, including stale-evidence handling and deterministic Claude continuation.
- `references/visible-pickup-and-progressive-acceptance.md` — compact command/readback patterns and the Linear `[X]` checkbox normalization pitfall.
- `references/credential-bearing-agent-launcher-review.md` — effective-authority review matrix for agent launchers: provider permissions, raw credential/HOME containment, model-auth exceptions, descendant cleanup, reviewer isolation, artifact state, and legacy-lane parity.
- `references/exact-head-blocked-pr-handoff.md` — exact-head blocked closeout across GitHub and Linear: mechanical-vs-acceptance state, final artifact readback, frozen blocker ledger, repair-budget stop, direct comment verification, resumption contract, and adversarial trusted-agent boundary probes.
