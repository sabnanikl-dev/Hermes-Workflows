# GitHub → Linear Merge Closeout Recipe

This reference captures the durable mechanics behind a verified exact-head merge closeout. Replace placeholders; do not preserve session-specific PR IDs or SHAs in the reusable command layer.

## Preflight matrix

Read in parallel where safe:

- PR state: `state`, `isDraft`, `headRefOid`, final commit, `mergeable`, `mergeStateStatus`, checks, reviews, comments;
- repository merge settings: merge/squash/rebase allowed, delete-branch-on-merge;
- full live feedback surfaces: reviews, inline comments, conversation comments, review threads and pagination;
- current tracker issue state/body;
- recent first-parent merges when multiple merge methods are allowed.

The tracker read is context only. Fetch it again after the merge before mutating.

## Ready and merge sequence

```bash
# Draft only
gh pr ready <PR> --repo <OWNER>/<REPO>

# Re-check exact head and mechanical state
gh pr view <PR> --repo <OWNER>/<REPO> \
  --json state,isDraft,headRefOid,mergeable,mergeStateStatus

# Use repository-consistent method
gh pr merge <PR> --repo <OWNER>/<REPO> --merge   # or --squash/--rebase
```

Do not add `--delete-branch` unless branch deletion is separately authorized.

## Required merge readbacks

```bash
gh api repos/<OWNER>/<REPO>/pulls/<PR> \
  --jq '{state,merged,merged_at,merge_commit_sha,head:{ref:.head.ref,sha:.head.sha},base:{ref:.base.ref,sha:.base.sha}}'

gh pr view <PR> --repo <OWNER>/<REPO> \
  --json state,mergedAt,mergeCommit,headRefOid,baseRefName

git fetch origin --prune
git rev-parse origin/<BASE>
git ls-remote origin refs/heads/<BASE>
git log -1 --pretty=format:'%H%n%P%n%s' origin/<BASE>
```

Acceptance:

- REST `merged == true`;
- PR view says `MERGED`;
- merge commit matches across both APIs and both base refs;
- for merge commits, parent list includes pre-merge base and reviewed head.

## Closing-reference proof

Read `closingIssuesReferences` and the umbrella issue state independently. A `Refs #N` PR should normally produce an empty closing-reference list and leave issue `#N` open. Record both facts in the closeout when the distinction matters.

## Linear sequencing

1. `get-issue` after GitHub proof. With the shipped `linear_api.py` helper, the issue fields are at the JSON root (`data["identifier"]`, `data["state"]`, `data["description"]`), not under `data["issue"]`.
2. If already `Done` / `completed`, skip `update-status`; an integration-driven state transition does not check acceptance boxes or append completion evidence.
3. Count the contract's unchecked acceptance lines, update only evidence-backed boxes, and update the description with one merge checkpoint. Verify semantic markers because Linear may normalize `- [x]` to `- [X]`.
   - If the body already contains a dated “merge-ready but unmerged” checkpoint, preserve it. Append a later heading such as `## Verified merge closeout — YYYY-MM-DD`; do not mutate the earlier checkpoint into a claim that was not true when written.
   - The later checkpoint should bind the reviewed head, merge commit, merge timestamp, merge parents/ancestry, linked-issue outcome, branch/ref deletion proof when authorized, worktree cleanup, and explicit no-deploy/downstream boundary.
4. When another issue is conditionally blocked by the repair, re-read it after merge and add a narrow disposition: “merge prerequisite satisfied; successor/candidate adoption still pending.” Preserve its workflow state and do not start a rerun unless the user separately approves adoption/execution.
5. Add one closeout comment. The helper returns a mutation envelope such as `{"success": true, "comment": {"id": ...}}`; capture the nested stable ID.
6. Directly query `comment(id:)` and compare issue ID/body.
7. Re-fetch the issue; verify state/type, zero unchecked contract boxes, expected checked count, checkpoint heading, reviewed head, merge commit, dependent issue state/boundary when applicable, and umbrella/closing note.

When a state lookup is needed, the helper syntax is `list-states --team <TEAM_KEY>`; the team key is not positional.

Do not require description bytes to match: Linear can normalize Markdown. Use semantic markers. Comment bodies may be compared exactly when direct readback preserves them, including their actual trailing-newline bytes.

## Ambiguous external mutation

If a command prints a concrete URL or ID and then exits nonzero, do not retry. First query that immutable object and verify:

- target repository/issue;
- author identity;
- exact body where possible;
- head/role binding when it is a review artifact;
- `created_at == updated_at` when immutability matters.

Retry only when direct readback proves the intended object is absent.

For GitHub review/comment bodies posted from a file, compare the raw file text to the raw API body first. GitHub may preserve the file's final newline; applying `rstrip()` to only one side creates a false mismatch and can tempt a duplicate post.

## Final boundary statement

Explicitly say what did **not** happen: branch deletion, umbrella closure, parent mutation, downstream execution, deploy, release, or account change. This prevents a verified child closeout from being misread as broader authority.
