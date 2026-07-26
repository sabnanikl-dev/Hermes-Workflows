# Decision-Issue Closeout When Implementation Is Separate

Use this pattern when a tracker issue owns an approved decision or migration map while another issue owns implementation.

## Ownership boundary

A decision issue can be complete before downstream code only when its contract clearly makes implementation separately owned. Remove contradictory criteria such as “the final manifest exists” beside “this issue does not implement the manifest.” Require an implementation-ready handoff in the downstream tracker and leave that tracker open.

## Canceled dependencies

When a planned destination is canceled, do not infer a homepage redirect or convenient fallback. Get an explicit retirement decision when semantics differ: intentional 404/no redirect, 410 where supported, preserve the old path, redirect to a relevant approved destination, or keep the issue open. Record the choice in both trackers. For intentional 404, state that no redirect row should exist and stale source content must not be copied forward.

## Literal inventory census

Before checking “every known URL/item has a decision,” expand linked source inventories and tracker comments. Include roots, pagination, empty child categories, detailed items, catch-all families, and exceptional rows. A grouped row is safe only when its canonical source packet and membership are unambiguous. Repeat exact high-risk members in both the decision issue and implementation handoff.

Run an independent blocker-only review over the census. If it finds omissions, repair every affected canonical tracker and re-review the frozen blocker ledger rather than opening a new broad critique.

## Verification and closeout

- Verify current implementation evidence from the remote default branch, not a stale local checkout; use an isolated exact-head worktree when needed.
- Treat keyword scans as leads, not semantic proof. Distinguish prohibited positive claims from approved negations and confirm provenance/validators.
- Promote reusable business decisions to the established wiki page, not a parallel tracker.
- Add a closeout inventory with exact issue URLs, wiki paths, revision/commands, lifecycle, and publication/live-action status.
- Move the decision issue to Done only after direct body, state, downstream-tracker, wiki, and closeout-comment-ID readback.
- Keep the downstream implementation issue open until its own acceptance criteria are complete.

## Linear helper reminder

The current `linear_api.py` helper uses positional arguments for these commands:

```bash
python3 scripts/linear_api.py add-comment JMD-50 "<body>"
python3 scripts/linear_api.py update-status JMD-50 Done
```

Check `--help`; do not assume `add-comment --body` exists. Capture the returned comment ID and verify it directly with `comment(id: ...)`.