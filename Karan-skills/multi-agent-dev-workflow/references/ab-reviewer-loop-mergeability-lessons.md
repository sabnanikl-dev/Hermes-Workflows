# A/B reviewer loop mergeability lessons

Use this reference when a user explicitly asks for `multi-agent-dev-workflow`, an A/B review loop, or “both reviewers say the PR is mergeable.”

## Durable lesson

A generic single Codex approval is not equivalent to the full multi-agent A/B loop. When the workflow calls for Reviewer A and Reviewer B, Hermes must run and verify both distinct lanes before reporting merge-readiness.

## Required closeout shape

1. **Reviewer A lane**
   - Focus: correctness, tests, security/public-safety, validator robustness, edge cases, regression risk.
   - Required signature: `Reviewed by: Codex Reviewer A via Hermes orchestration`.
   - Final marker: `DONE: REVIEWER=A STATUS=pass|fail BLOCKING=<count> MERGEABLE=yes|no`.

2. **Reviewer B lane**
   - Focus: architecture, maintainability, docs/spec drift, harness compliance, scope control, future-builder clarity.
   - Required signature: `Reviewed by: Codex Reviewer B via Hermes orchestration`.
   - Final marker: `DONE: REVIEWER=B STATUS=pass|fail BLOCKING=<count> MERGEABLE=yes|no`.

3. **If either reviewer blocks**
   - Treat the PR as not mergeable.
   - Send the builder/fix lane back to the live PR feedback, not pasted private summaries, unless GitHub access is unavailable.
   - Verify the fix commit is pushed to the PR branch.
   - Re-run the blocking reviewer on the **new head** until that lane says `MERGEABLE=yes`.
   - Do not run or report final mergeability from stale reviews on an older commit.

4. **GitHub verification**
   - Query the reviews API, not only `latestReviews`, because same-account role reviews can collapse in `latestReviews`.
   - Filter for current `headRefOid` / `commit_id` where possible.
   - Verify both role signatures are present and both bodies explicitly say the PR is mergeable.
   - Verify `reviewDecision`, status checks, `mergeable`, and local-vs-remote head SHA.

5. **Reporting**
   - Say explicitly whether A and B both ran.
   - Include each reviewer’s final status separately.
   - If only one reviewer ran, say so plainly and continue the loop instead of calling the PR merge-ready.

## Example final evidence query

```bash
gh api repos/<owner>/<repo>/pulls/<pr>/reviews \
  --jq '[.[] | select(.commit_id=="<headRefOid>") | {user:.user.login,state,submitted_at,signature:(if (.body|contains("Codex Reviewer A")) then "A" elif (.body|contains("Codex Reviewer B")) then "B" else "generic" end), mergeable_phrase:(.body|test("considers this PR mergeable|considers the PR mergeable")), body:.body}]'
```

Then confirm one `signature:"A"` and one `signature:"B"` with `state:"APPROVED"` and `mergeable_phrase:true` on the current head.
