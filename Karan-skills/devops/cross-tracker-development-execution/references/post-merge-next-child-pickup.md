# Post-Merge Next-Child Pickup

Use this when a human merges one child PR between sessions and Hermes must select and start the next Linear-owned coding slice.

## 1. Prove the merge and landed snapshot

Read the pull request through GitHub's API and require:

- `merged: true` (or `state: MERGED` plus non-null `mergedAt`);
- exact `merged_at` and `merge_commit_sha`;
- captured pre-merge PR head SHA.

Fetch `origin/main`. Do not use `merge-base --is-ancestor <pr-head> origin/main` as the sole proof: squash merges create a new commit and the former PR head may not be an ancestor. For a squash merge, compare trees:

```bash
git rev-parse 'origin/main^{tree}'
git rev-parse '<pr-head>^{tree}'
```

Equal trees prove the accepted PR snapshot landed exactly at that main revision. If the trees differ, inspect the merge method and diff before advancing.

## 2. Reconcile tracker truth before selecting

Read the live Linear parent, every direct child, relations, comments, and pagination metadata, plus the GitHub umbrella issue.

Before claiming the next child:

1. update stale parent sequence/status wording and the completed child checkbox;
2. update the GitHub umbrella recovery/status section and matching checkbox;
3. directly read both bodies back and assert the merge SHA and next-child wording are live;
4. preserve historical PR/child evidence rather than deleting or rewriting it.

A child can remain `In Progress` only because a superseded mega-PR lane left stale state. Demote it to the parent-prescribed waiting state only when the live parent order, merge dependencies, and superseded-PR evidence make the conflict unambiguous. Add a concise reconciliation comment explaining why; never silently erase the old evidence.

## 3. Claim the deterministic next slice

Choose the earliest child that is both next in the live parent sequence and unblocked by the now-verified merge. Move only that child to `In Progress`; directly read back both its state and any displaced stale child's state.

The pickup comment should bind:

- merged-main baseline SHA;
- execution mode and isolated worktree;
- intended repo-owned outputs and lifecycle;
- excluded downstream/live effects;
- next checkpoint.

## 4. Make pickup visible in GitHub

When the coding mission uses one umbrella GitHub issue rather than one issue per Linear child:

1. create the child-named branch through `gh issue develop <umbrella>` from verified `main`;
2. verify `gh issue develop --list` shows the association;
3. verify the remote ref with `git ls-remote --heads`;
4. create a clean tracking worktree from that remote branch;
5. use plain `Refs #<umbrella>` in the interim PR; reserve `Closes` for the parent-designated final integration PR.

An empty remote baseline branch is visible claim state, not delivery. The first coherent builder commit and draft PR still require normal local/remote/PR-head verification.

## 5. Start the bounded builder

Smoke the configured builder model/auth, then launch it in the isolated worktree with:

- exact Linear child and GitHub umbrella contracts;
- current-main baseline and historical extraction sources identified as evidence only;
- allowed output paths and verification commands;
- commit/push/draft-PR authority when already approved;
- explicit no-merge/no-install/no-downstream-child/no-live-system boundary.

Record branch/worktree/builder-start evidence on the active Linear child and verify the comment by ID. Do not claim a PR exists until it has been opened and directly read back.
