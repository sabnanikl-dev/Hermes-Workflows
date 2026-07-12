# Linear Pilot Wrap-up Comments

Use this pattern when a user approves wrapping a multi-issue pilot after GitHub PRs are merged.

## When to Apply

- A set of Linear issues represents one pilot or batch.
- The user explicitly approves finalization/merge/wrap-up.
- Related GitHub PRs have already been verified as `merged: true`.

## Pattern

1. Query each issue by identifier and record current state/team:
   - identifier, title, URL
   - current state name/type
   - team key
2. Query completed workflow states per team; prefer a state named `Done` if present, otherwise the first `type: completed` state.
3. Post a final comment to every issue, including:
   - merged PR links relevant to that issue or batch
   - what changed
   - verification statement (`merged: true` checked on GitHub)
   - safety statement if no live/client/account changes were made
   - explicit pilot wrap-up wording
4. Move issues to Done only after comments are posted and PR merges are verified.
5. Re-query every issue and verify `state.type == completed` before reporting.

## Comment Template

```md
Pilot wrap-up complete.

Merged GitHub PRs:
- [PR title/link]

Final status:
- Karan reviewed the follow-up changes and approved merge.
- PR merge verified on GitHub with `merged: true`.
- [Key outcome bullet 1]
- [Key outcome bullet 2]
- No client-facing, account-changing, or live ops changes were made.

Moving this issue to Done as part of pilot closeout.

from Hermes
```

## Pitfalls

- Linear GraphQL may return HTTP 200 with an `errors` array; always check it.
- Teams can have different completed state IDs. Do not reuse one team's Done state for another team.
- Some issues may already be Done; still post a wrap-up comment if it helps preserve the batch audit trail.
