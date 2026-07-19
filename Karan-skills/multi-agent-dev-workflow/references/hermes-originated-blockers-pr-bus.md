# Hermes-Originated Blockers on the PR Bus

Use this when Hermes independently finds a blocker that builder or evaluator lanes missed.

## Rule

The PR remains the coordination source of truth. Do not keep Hermes findings only in chat and then paste them privately into the builder prompt.

1. Verify the finding against the current PR head and an authoritative source (issue AC, merged policy PR, repo contract, test output, or exact rendered evidence).
2. Post a clearly labeled, signed PR conversation comment with:
   - `BLOCKING` label;
   - exact `file:line` or affected surface;
   - authoritative source/reference;
   - narrow required outcome;
   - explicit scope guard when older unrelated regressions exist.
3. Read the comment back from GitHub and verify its URL/body before starting the fix lane.
4. Keep the Claude fix prompt pointer-first: PR number, branch, issue, current-head verification, instruction to read all live reviews/comments/threads, and test/push/comment requirements. Do not repeat the blocker prose privately unless GitHub access failed; label any fallback capsule as degraded.
5. Verify the fix commit appears in the PR and the builder posts a signed fix comment mapping each live blocker to the change and verification.
6. Refresh exact-head UI evidence when visible copy/layout changed, even if the patch is text-only.
7. Rerun both Reviewer A and B on the new head. Old-head approvals do not close the loop.

## Scope hygiene

If the same durable rule reveals pre-existing violations outside the task diff, do not silently expand the current PR. Fix the newly introduced violation and route older regressions into separate follow-up work unless they directly block the task acceptance criteria.
