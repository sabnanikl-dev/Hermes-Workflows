# Linear helper response shapes and idempotent closeout readback

Use this when closing a Linear issue from verified GitHub evidence through `scripts/linear_api.py`.

## Command-specific response shapes

Do not assume every helper wraps GraphQL in `.data` or returns the same issue fields.

Observed stable patterns:

- `get-issue ISSUE` returns the issue object at the JSON root: `.identifier`, `.description`, `.state.name`, `.state.type`, `.comments`, `.url`.
- `raw 'query { ... }'` unwraps GraphQL `data`; requested aliases/fields appear at the JSON root, such as `.issue` and `.comment`, not `.data.issue`.
- `update-issue` returns `{success, issue}` but may omit fields not requested by that helper; `.issue.state` can be absent/null.
- `update-status` returns `{success, issue}` and may include `state.name` without `state.type`.
- `add-comment` returns `{success, comment}`. Capture `.comment.id` immediately.

Inspect the actual response file before writing assertions. A parser mismatch after a mutation does not prove the mutation failed.

## Idempotent closeout sequence

1. Fetch the current issue and retain its full description.
2. Update only the intended acceptance lines and append final evidence once, guarded by a unique heading/marker.
3. Run `update-issue`; verify `success`, then re-query the issue to prove the durable description.
4. Run `add-comment`; capture the returned comment ID.
5. Verify that exact comment with a direct `comment(id:)` raw query. Do not use comment ordering.
6. Run `update-status ISSUE Done` only after the contract/evidence is durable.
7. Re-query with `get-issue` and require both `state.name == "Done"` and `state.type == "completed"`.
8. Re-query the exact comment ID again if the final report depends on it.

## Parser failure after mutation

If a command used `set -e` and a `jq` assertion fails after a mutation:

1. Do not retry the mutation immediately.
2. Read the captured mutation response.
3. Re-query live issue/comment state.
4. Retry only if live state proves the mutation did not occur.

This prevents duplicate closeout comments and unnecessary status churn.

## Cross-system ordering

For ready-without-merge work:

1. Finish and read back exact-head GitHub reviewer artifacts.
2. Update stale PR body evidence.
3. Mark the PR ready when authorized.
4. Verify `OPEN`, `isDraft=false`, `mergedAt=null`, exact head, expected merge state/checks/threads/closing references.
5. Then write Linear closeout evidence and move the issue to Done.

Keep “PR ready,” “PR mergeable,” “PR merged,” and “Linear implementation complete” as separate facts.
