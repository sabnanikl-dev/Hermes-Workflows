# PR Closing-Linkage Pre-Review Gate

Use this after the builder opens a repo-complete PR and before launching Reviewer A/B.

## Why this gate exists

A builder can be instructed to put `Closes #N` in the PR body yet omit it there while placing the keyword only in the commit message. The PR can look correctly linked to a human, but GitHub may still report `closingIssuesReferences: []`. Body text or commit prose is not proof that merge will close the issue.

## Required gate

1. Read the live PR body and `closingIssuesReferences` after PR creation.
2. Require the issue number to appear in `closingIssuesReferences` for repo-complete work.
3. If the reference is missing, treat it as a **PR-metadata blocker before technical review**:
   - post a signed `BLOCKING` PR-bus comment with the current head and required outcome;
   - send a fresh pointer-first Claude builder/fix lane to read the live PR comment;
   - require metadata-only repair, no repository edit/commit/head change;
   - require a signed fix comment and live readback of `closingIssuesReferences`.
4. Verify the PR head is unchanged and the worktree remains clean.
5. Only then launch Reviewer A/B, so architecture/harness review evaluates the correct issue lifecycle contract.

## Cycle accounting

A metadata-only repair before the first A/B review does not consume a code fix cycle because the repository head is unchanged. If closing linkage is corrected after reviewers already ran, rerun the reviewer lane that covers harness/issue-lifecycle compliance (normally Reviewer B); rerun both lanes only if the code head also changed.

## Verification shape

```bash
LOCAL=$(git rev-parse HEAD)
REMOTE=$(gh pr view <PR> --json headRefOid --jq .headRefOid)
gh pr view <PR> --json closingIssuesReferences,body,headRefOid
# Require LOCAL == REMOTE and closingIssuesReferences includes the intended issue.
```

Prefer `closingIssuesReferences` as the authoritative result. A brittle string check for an exact newline pattern can fail when the closing line is at end-of-file even though GitHub linkage is correct.
