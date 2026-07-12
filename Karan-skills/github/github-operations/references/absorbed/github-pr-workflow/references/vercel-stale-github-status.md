# Vercel deployment succeeds but GitHub PR check stays pending

Use when a Vercel-connected PR shows `Vercel` pending in GitHub even though the deployment may have completed.

## Symptom

`gh pr checks <PR>` shows something like:

```text
Vercel Preview Comments  pass
Vercel                  pending  Vercel is deploying your app
```

The PR may show `mergeStateStatus: UNSTABLE` because GitHub is still waiting on the commit status context.

## Diagnosis sequence

1. Get the PR head SHA and rollup checks:

```bash
gh pr view <PR> -R OWNER/REPO \
  --json headRefOid,mergeStateStatus,mergeable,statusCheckRollup \
  --jq '{headRefOid,mergeStateStatus,mergeable,checks:[.statusCheckRollup[]?|{name,status,conclusion,detailsUrl}]}'
```

2. Check the commit status context GitHub uses for branch protection:

```bash
SHA=<head sha>
gh api repos/OWNER/REPO/commits/$SHA/status \
  --jq '{state,total_count,statuses:[.statuses[]|{context,state,description,target_url,updated_at}]}'
```

3. Separately check GitHub deployment objects for that same SHA:

```bash
gh api "repos/OWNER/REPO/deployments?sha=$SHA" \
  --jq '[.[]|{id,environment,sha,ref,creator:.creator.login,created_at,updated_at,statuses_url}]'

DEPLOYMENT_ID=<id>
gh api repos/OWNER/REPO/deployments/$DEPLOYMENT_ID/statuses \
  --jq '[.[]|{state,description,environment_url,target_url,log_url,updated_at}]'
```

## Interpretation

- If commit status is `pending` but deployment status is `success` / `Deployment has completed`, Vercel likely finished the deploy but failed to finalize the GitHub commit status.
- If the preview URL returns `401`, that usually indicates Vercel preview protection/auth gating. Treat that as a smoke-test access limitation, not proof that the deployment failed.
- Do not report “Vercel failed” from a pending commit status alone. Distinguish:
  - GitHub check status: pending/stale
  - GitHub deployment object: success/failure
  - Preview URL accessibility: public vs protected

## Recommended actions

1. Wait/re-query once or twice; stale status sometimes catches up.
2. If still stuck, prefer a Vercel redeploy/re-run or push an empty commit to retrigger the integration.
3. If branch protection allows merge and the user explicitly approves, you may base the recommendation on successful deployment object plus local/visual QA, but state the stale check clearly.
4. Avoid merging on your own when the user only asked what the hold-up is.
