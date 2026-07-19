# Refreshing a dependency-ordered GitHub roadmap

Use this pattern when a repository already has a roadmap PR or roadmap document but the live issue set has grown or changed.

## Reconstruction

1. Verify the exact repository and inspect the default branch.
2. List every open issue with number, title, body, labels, and update time.
3. Extract each issue's `Dependencies`, `Sequencing`, `Prerequisites`, blockers, trigger conditions, and explicit phase notes.
4. Inspect open PRs, especially the existing roadmap PR, and distinguish fresh checks from checks attached to an older head commit.
5. Read the repo's agent/process instructions before choosing whether the roadmap permits parallel PRs.

## Sequencing model

Build two views:

- **Hard dependency graph:** only true blockers, such as `A -> B`.
- **Recommended execution queue:** includes independent work ordered to reduce rework, deliver early value, or correct stale agent guidance.

Keep these concepts distinct. An independent issue can have a recommended position without being presented as a hard prerequisite.

Classify work that should not be blindly queued:

- **Optional lane:** experiments that can move earlier when they become the current focus.
- **Trigger-gated:** work that starts only after a scale/client/duplication threshold is met.
- **Speculative/reassess:** work that should be re-evaluated after an earlier runtime or architecture surface exists.

## Roadmap content

A useful refreshed roadmap contains:

- delivery policy (`one issue / one branch / one PR` when repo instructions require it);
- hard dependency diagram;
- one complete numbered execution queue;
- pull-forward rules for changed business context;
- phase start and exit gates;
- explicit authority/safety boundaries;
- remaining genuinely untracked gaps rather than stale claims that already-filed work is untracked.

GitHub Issues remain the implementation contracts. The roadmap records order and gates; it should not duplicate every issue body.

## Deterministic coverage check

Before committing, compare all live open issue numbers with all issue references in the roadmap. Fail if an open issue is missing. Also inspect unexpected references to closed/nonexistent issues rather than assuming they are intentional.

A simple Python check can:

1. retrieve open issue numbers with `gh issue list --json number`;
2. parse `#N` references from the roadmap;
3. print `MISSING_FROM_ROADMAP` and `NON_OPEN_REFS`;
4. exit non-zero when coverage is incomplete.

## PR refresh and verification

When updating an existing roadmap PR:

1. Work on the PR's existing head branch unless the branch is unsafe or diverged.
2. Keep the change roadmap/docs-only unless another issue explicitly authorizes implementation.
3. Refresh the PR title and body so they describe the new issue inventory, dependency graph, scope boundaries, and validation evidence.
4. Run the repository's complete named validation suite plus `git diff --check`.
5. Push and verify all three identifiers match:
   - local `HEAD`;
   - raw remote branch ref (`git ls-remote`);
   - live PR `headRefOid` / last commit.
6. Do not treat old green checks shown on the PR as evidence for the refreshed commit. Query workflow runs or commit check-runs by the new head SHA and require fresh success.
7. Re-read the live PR title/body/head/status before reporting completion.

## Common pitfalls

- Updating only the roadmap file while leaving the PR body/title stale.
- Calling an issue a blocker merely because it is convenient to do first.
- Treating trigger-gated work as immediately actionable backlog.
- Leaving “untracked gap” prose after corresponding issues have been filed.
- Reporting old CI runs as proof for a new pushed commit.
- Merging the refreshed roadmap when the user only asked to refresh it.
