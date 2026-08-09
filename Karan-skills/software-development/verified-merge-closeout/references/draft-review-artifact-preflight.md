# Draft PR Review-Artifact Preflight

Use this before marking a review-complete draft PR ready or merging it.

## Why aggregate state is insufficient

GitHub can leave `reviewDecision` blank while a PR is draft, even when a dedicated reviewer has submitted a formal `APPROVED` review on the current commit. Conversely, an aggregate approval can hide stale-head or same-account role collapse. Treat `reviewDecision` as a convenience field, not the proof source.

## Exact-head evidence readback

Fetch and reconcile all relevant surfaces:

```bash
gh pr view <PR> --repo <owner>/<repo> \
  --json state,isDraft,headRefOid,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,commits,closingIssuesReferences

gh api repos/<owner>/<repo>/pulls/<PR>/reviews?per_page=100
gh api repos/<owner>/<repo>/issues/<PR>/comments?per_page=100
gh api repos/<owner>/<repo>/pulls/<PR>/comments?per_page=100
# Also query reviewThreads and prove pagination is complete.
```

Require:

- local head, fetched remote branch, PR `headRefOid`, and the final PR commit all equal the reviewed SHA;
- the formal reviewer artifact has the expected login, state, role signature, and exact `commit_id`;
- comment-only reviewer lanes have expected login, role signature, runtime, exact head, verdict, and blocker count;
- no unresolved review thread or later human objection exists;
- all result pages are complete, not merely the first page.

When parent Hermes relays a prepared reviewer body, verify the GitHub readback against the raw prepared body exactly. Do not `rstrip()` either side: GitHub may preserve the trailing newline from `-F body=@file`, and normalizing only one side creates a false mismatch.

## Draft-state wording and authority

Until ready-marking is explicitly authorized, report:

> review-complete / draft-ready for Karan's decision

Do not call the PR already GitHub merge-ready solely because mechanical state is `MERGEABLE/CLEAN` and the exact-head review chain passes. Ready-marking is a distinct external mutation. After approval:

1. re-run the exact-head artifact preflight;
2. mark ready;
3. re-query head, draft state, mergeability, checks, reviews, comments, and threads;
4. stop if any state or head changed before merge.

## Stale metadata

If the PR body still contains a pre-fix test count or evidence claim, first determine whether a signed current-head correction comment durably binds the old and new heads and whether every required reviewer explicitly classified the stale body as non-blocking. Surface the discrepancy in the handoff. Do not silently edit the body unless that metadata mutation is authorized. If the stale prose materially changes scope, acceptance, or what a human will believe is shipped, it remains blocking until reconciled.
