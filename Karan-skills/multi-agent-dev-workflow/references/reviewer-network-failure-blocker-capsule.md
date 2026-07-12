# Reviewer Network Failure + Blocker Capsule Recovery

Session-derived pattern for multi-agent PR loops when a reviewer identifies a real blocker but fails before it can post a GitHub review/comment.

## Trigger

Use this when all are true:

- A reviewer lane has inspected the PR and clearly surfaced a real blocking issue.
- The reviewer process cannot complete or post to GitHub because of a transport/auth/session failure.
- The finding is specific and actionable enough to hand to the builder without inventing reviewer detail.

Do **not** use this to bypass normal PR-bus coordination when the reviewer can still post normally.

## Recovery pattern

1. **Preserve the finding honestly.** Treat the reviewer output as a fallback blocker capsule, not as a formal GitHub review.
2. **Stop the broken reviewer lane if it is stuck reconnecting.** Do not wait indefinitely for a process that has already exhausted reconnect attempts or is clearly no longer progressing.
3. **Launch the builder/fix lane with disclosure.** The prompt should instruct the builder to read the live PR state first, then include a clearly labeled fallback capsule only for the unposted blocker.
4. **Keep the fix narrow.** The builder should fix only the blocker identified by the failed reviewer lane and preserve all original issue constraints.
5. **Require a signed PR comment from the builder.** The comment should explain what blocker was fixed, what verification passed, and that the source was a fallback capsule when applicable.
6. **Verify push on GitHub.** Confirm local HEAD, PR `headRefOid`, and the PR commit list all match the follow-up commit.
7. **Rerun both reviewer lanes on the new current head.** A prior approval on the old head is stale after any follow-up commit. Require current-head signed outcomes from Reviewer A and Reviewer B before reporting merge-ready.
8. **Verify all review surfaces.** Use the reviews API filtered by `commit_id == headRefOid`, regular PR comments, and review threads; do not rely only on `latestReviews`.

## Reporting language

Report this as a recovered/degraded review-posting path, not a clean first-pass loop. It can still be merge-ready if:

- The builder fixed the blocker.
- Verification passed on the follow-up commit.
- Both reviewers passed on the new current head.
- GitHub surfaces show no unresolved review threads/blockers.

## Example builder prompt fragment

```text
Fallback blocker capsule (because Codex Reviewer B hit a network reconnect before it could post its GitHub review): <specific blocker>. Inspect the relevant file and update only the narrow stale source needed. Do not broaden scope.

After fixing, run verification, commit, push, and post a signed PR comment summarizing the blocker fixed and verification.
```
