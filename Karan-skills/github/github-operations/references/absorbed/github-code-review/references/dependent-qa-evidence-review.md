# Dependent QA Evidence / Handoff PR Review Notes

Use this when reviewing evidence packs, handoff docs, deploy-readiness docs, or any PR whose claims depend on another unmerged PR.

## Common failure pattern

A QA/evidence PR can be internally valid but still not acceptable if it was captured against a branch/commit that is not on `main`, or if the dependency PR has moved since evidence capture.

Example symptoms:
- Evidence headers say `Source under test: <branch> @ <old-sha>`.
- PR body says merge order like `#29 -> #26 -> #27`.
- The dependency PR is still open, or its head SHA is newer than the evidence SHA.
- Handoff PR says evidence is completed/under `evidence/`, but the evidence PR is not merged to `main`.
- PR body uses `Closes #N` even though a required upstream issue/PR is still unresolved.

## Review probes

```bash
REPO=OWNER/REPO
PR=<evidence-or-handoff-pr>
DEP_PR=<dependency-pr>

gh pr view "$PR" -R "$REPO" --json number,title,headRefName,headRefOid,baseRefName,body,files

gh pr view "$DEP_PR" -R "$REPO" --json number,state,headRefName,headRefOid,mergeable,mergeStateStatus,commits \
  --jq '{number,state,headRefName,headRefOid,mergeable,mergeStateStatus,commits:[.commits[] | {oid,messageHeadline}]}'

# Find provenance claims inside evidence/docs.
rg -n "Source under test|Recommended merge order|captured against|Closes #|Refs #|@ [0-9a-f]{7,40}" evidence outputs docs || true

# Confirm the claimed evidence SHA is actually in main or the dependency branch.
CLAIMED_SHA=<sha-from-evidence>
git merge-base --is-ancestor "$CLAIMED_SHA" origin/main; echo "ancestor_of_main=$?"
git merge-base --is-ancestor "$CLAIMED_SHA" origin/<dependency-branch>; echo "ancestor_of_dependency=$?"
```

## Review guidance

Treat as blocking when:
- Evidence was captured against a commit that is not in `origin/main` and is not the current dependency PR head.
- A handoff/deploy-readiness PR states evidence is complete before the evidence PR is accepted and merged.
- A PR would auto-close the final handoff issue (`Closes #N`) before required upstream evidence exists on `main`.

Suggested fixes:
- For evidence PRs: merge/update the dependency first, then recapture evidence against the actual post-merge `main` commit and update provenance text.
- For handoff PRs: mark the evidence dependency as pending, change `Closes #N` to `Refs #N`, and state that final closeout waits for the evidence PR to land.
- Post a follow-up comment mapping the fix to the blocker and verify the remote PR head SHA after pushing.
