# Approval-gated PR evidence + screenshot proof pattern

Session-derived from a JMD Sanity Studio PR where repo-side work was complete but the hosted Studio deploy remained blocked on Karan approval.

## Problem class

Some issues have two separable states:

1. **Repo-side implementation is ready** — code, docs, tests, reviewer loop, PR approval.
2. **Live/operator-visible completion is still blocked** — deploy, hosted Studio update, account config, content mutation, OAuth/CORS/dev-host registration, etc.

In this state, a PR can be merge-ready while the issue must remain open until the approval-gated live step is performed and evidenced.

## Closing keyword rule

Do not only remove `Closes #N` from the PR body. GitHub can also close issues from commit-message closing keywords when commits land on the default branch via merge/rebase/squash paths.

Before final re-review or merge recommendation, verify both surfaces:

```bash
# PR body should not create closing issue refs
gh pr view <PR> --json closingIssuesReferences --jq '.closingIssuesReferences'

# Branch commit subjects/bodies should not contain closing keywords
git log --format='%s%n%b' origin/main..HEAD | grep -Ei '\b(close[sd]?|fix(e[sd])?|resolve[sd]?) #[0-9]+' && exit 1 || true
```

Use non-closing wording such as `Refs #N` and explicitly say the issue remains open until the gated step is approved/performed.

## Screenshot proof when live UI is gated

If the user asks for screenshot proof but the actual live UI requires an external mutation to view (for example Sanity Studio asks to “Add development host” or hosted deploy is not approved):

1. Do **not** click/register/deploy/configure anything without approval.
2. Capture the gate screen if useful, but be explicit that it is not proof of the final live UI.
3. Provide repo-side visual proof instead: a small generated evidence page or screenshot showing:
   - issue/PR/current head;
   - the expected navigation or UI structure from committed code/evidence;
   - review/merge status;
   - verification commands that passed;
   - a clear boundary note: “no hosted deploy/dev-host/content mutation performed.”
4. Deliver it as `MEDIA:/absolute/path.png` on Telegram and state the limitation plainly.

This is honest evidence: it proves the committed repo state and avoids falsely implying a hosted deploy or account mutation happened.
