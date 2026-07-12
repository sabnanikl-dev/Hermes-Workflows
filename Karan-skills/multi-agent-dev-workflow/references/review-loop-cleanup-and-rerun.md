# Review Loop Cleanup and Rerun

Use this when a prior PR review loop was overstated, incomplete, or process-invalid but left live GitHub review state behind.

## Triggers

- A previous approval came from an incomplete loop (for example: only Reviewer A ran, Reviewer B was skipped, or Hermes applied a blocker fix instead of the builder/fix lane).
- A stale `CHANGES_REQUESTED` review targets an old commit whose blocker has been fixed.
- The user asks to “clean up the reviews” and rerun the loop.

## Cleanup protocol

1. Inspect all review surfaces before mutating anything:
   - `gh pr view <PR> --json comments,reviews,latestReviews,statusCheckRollup,headRefOid,mergeable,reviewDecision`
   - `gh api repos/<owner>/<repo>/pulls/<PR>/reviews`
   - `gh api repos/<owner>/<repo>/pulls/<PR>/comments`
   - GraphQL `reviewThreads(first:...)` for unresolved threads.
2. Dismiss stale or process-invalid reviews instead of hiding the audit trail:
   - dismiss prior approvals if the loop was invalid/incomplete;
   - dismiss old `CHANGES_REQUESTED` reviews only after verifying the blocker is fixed on the current PR head;
   - use an explicit dismissal message naming the superseding rerun/fix.
3. Verify the PR branch/head and checks before re-review:
   - local branch head matches PR `headRefOid`;
   - expected commit appears in `gh pr view --json commits`;
   - relevant checks are green or their status is explicitly handled.
4. Rerun both reviewer lanes from fresh sessions:
   - Reviewer A: correctness/tests/security/regressions/repo hygiene.
   - Reviewer B: architecture/spec drift/harness/process compliance.
5. If either reviewer finds blockers, route fixes to the builder/fix lane (Claude Code in Karan’s default loop). Hermes should not patch directly unless explicitly approved or emergency fallback is documented.
6. If no blockers are found, do not run a fake builder/fix lane just for symmetry. Report that no fix cycle was needed.
7. Final verification must re-read live GitHub state:
   - latest reviews / review decision;
   - all review records, including dismissed stale reviews;
   - unresolved review threads;
   - PR head/checks/mergeability.

## Reviewer self-submission failures

For clean dogfood validation, reviewer agents should submit their own GitHub reviews. If the reviewer completes analysis but cannot submit due a transport/auth quirk:

1. Treat the loop as a disclosed fallback, not a perfect clean pass.
2. Have the reviewer print its final pass/fail and blocker count.
3. If needed, Hermes may submit the prepared reviewer outcome using the separate reviewer identity, but the review body must disclose that it is a fallback submission and summarize exactly what the reviewer checked.
4. Verify the fallback reviews landed via the reviews API and `gh pr view --json reviewDecision,latestReviews`.
5. Report both facts to Karan: PR review state is clean, but the reviewer self-submission path still needs infrastructure follow-up.

## Final report language

Distinguish code quality from loop purity:

- “PR is approved/mergeable” = live GitHub state is clean.
- “Clean dogfood loop pass” = builder and reviewers performed their own handoffs with no Hermes substitution.
- If fallback submission happened, say so directly.