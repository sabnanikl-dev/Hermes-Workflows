# Interim PR Closing-Link Contamination

Use this when a staged-train child must use `Refs #N`, but GitHub reports a non-empty `closingIssuesReferences` list.

## Prevention

Before `gh pr create`, scan the whole PR body case-insensitively for ordinary prose beginning with GitHub closing verbs—not merely explicit `Closes #N` lines:

- `close`, `closes`, `closed`
- `fix`, `fixes`, `fixed`
- `resolve`, `resolves`, `resolved`

For interim PR prose, prefer neutral verbs such as `addresses`, `implements`, `covers`, or `repairs`. Keep only the required standalone `Refs #N` relationship line. Reserve `Closes #N` for the designated final integration PR.

## Immediate readback

After creation, verify:

```bash
gh pr view <PR> --repo <owner/repo> \
  --json state,isDraft,headRefOid,baseRefName,body,closingIssuesReferences,url
```

An interim PR is clean only when the expected head/base/draft state match **and** `closingIssuesReferences` is exactly empty. Also re-read the umbrella issue state.

## Recovery

If editing the body does not clear the live closing reference:

1. Preserve the branch and exact commit.
2. Comment on the contaminated PR with the metadata-recovery reason.
3. Close it unmerged.
4. Create a replacement draft PR from the same branch and exact head using neutral prose plus `Refs #N`.
5. Verify the replacement has zero closing references and the umbrella issue remains open.
6. Preserve the closed PR URL as historical evidence; any PR-number-bound reviews/comments from it do not transfer to the replacement.

Do not force-push, rewrite code, or create a fake commit solely to obtain a clean PR number. This is metadata recovery, not implementation repair.
