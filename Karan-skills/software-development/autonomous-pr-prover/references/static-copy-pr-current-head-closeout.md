# Static copy PR current-head closeout pattern

Use this for static-site copy/content PRs where earlier review comments flagged copy-risk items and the PR later pushed a wording-only fix.

## Pattern

1. **Anchor every judgment to current head.** Old content/SEO reviews can be useful context, but do not carry their blockers forward unless the current `headRefOid` still contains the risky wording.
2. **Verify the builder's follow-up comment against the diff.** If the author says they softened owner-gated claims, inspect the changed HTML/text directly and confirm the current wording now stays inside the approved ledger.
3. **Run deterministic copy probes in addition to repo tests.** For JMD-like static pages, probe changed pages for:
   - required approved facts/phrases from the issue acceptance criteria;
   - residual disclaimer language that the issue intended to remove;
   - forbidden claim classes: live inventory, stock counts, size runs, guaranteed availability, online ordering, hard pricing beyond the approved ledger.
4. **Handle approved negative facts carefully.** A raw forbidden-word search can produce false positives for approved brand positioning such as "when it is gone, it is gone" / "does not reorder fashion garments" when the repo source document explicitly approves that limited-floor concept. Classify by claim meaning, not token presence.
5. **Close the loop with A/B reviews on the fixed head.** If no current-head blockers remain, post/verify signed Reviewer A and Reviewer B artifacts under the reviewer identity, even if an earlier same-PR review was posted from the operator account or against an older commit.
6. **Separate merge-readiness from public approval.** For draft/customer-facing copy, report technical/prover merge-readiness while preserving any brand, commerce, owner, client, or deploy approval gates as load-bearing.

## Compact verification bundle

```bash
gh pr view <PR> --repo <repo> --json headRefOid,commits,mergeStateStatus,statusCheckRollup
npm test
npm run build
git diff --check origin/main...HEAD
gh api repos/<owner>/<repo>/pulls/<PR>/reviews --jq '.[] | select(.commit_id=="<head>") | {user:.user.login,state,commit_id,body}'
gh api graphql -f owner=<owner> -f name=<repo> -F number=<PR> -f query='query($owner:String!, $name:String!, $number:Int!) { repository(owner:$owner, name:$name) { pullRequest(number:$number) { reviewThreads(first:100) { nodes { isResolved isOutdated path line comments(first:10) { nodes { author { login } body createdAt } } } } } } }'
```
