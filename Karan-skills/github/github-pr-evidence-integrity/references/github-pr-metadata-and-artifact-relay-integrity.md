# GitHub PR metadata and artifact-relay integrity recipes

## 1. Detect hidden issue-closing linkage

Inspect the live PR's closing references, not only its body. An issue-development branch created with `gh issue develop` can make the resulting PR a closing reference even when the body contains plain `Refs #N`.

Required assertion for an interim/staged PR:

```text
state = OPEN
headRefOid = expected full SHA
closingIssuesReferences = []
body contains plain "Refs #N"
```

Do not treat `Refs` as sufficient without the metadata check.

### Clean replacement recipe

When closing linkage is discovered after the PR exists:

1. Verify and preserve the current accepted commit SHA.
2. Create an ordinary unlinked branch at that exact commit.
3. Push the new branch without force.
4. Open a replacement draft PR with the same reviewed scope and plain `Refs #N`.
5. Verify local HEAD, upstream, remote ref, replacement PR head, and final commit all match.
6. Require `closingIssuesReferences == []` on the replacement.
7. Close the incorrectly linked PR unmerged with a supersession note.
8. Delete the obsolete branch only after the replacement is verified live.

This changes metadata lineage without changing accepted code bytes.

## 2. File-body semantics for `gh api`

These forms are different:

```bash
# WRONG for file upload: sends the literal string '@/tmp/review.md'
gh api repos/OWNER/REPO/issues/NUMBER/comments -f body=@/tmp/review.md

# RIGHT: reads file contents
gh api repos/OWNER/REPO/issues/NUMBER/comments -F body=@/tmp/review.md

# Also right for PR conversation comments
gh pr comment NUMBER --repo OWNER/REPO --body-file /tmp/review.md
```

The same `-F body=@file` rule applies when creating a formal review through the REST endpoint.

## 3. Transport-only reviewer sequence

1. Reviewer runs credential-free in a clean exact-head worktree.
2. Reviewer returns the full artifact and `ARTIFACT=relay-required`.
3. Default Hermes validates role, verdict, blocker count, runtime declaration, and head.
4. Default Hermes rechecks the live PR head.
5. Resolve the scoped reviewer token without printing it.
6. Verify the token's login and target-repository permissions.
7. Submit the intended artifact type.
8. Fetch the exact created review/comment by returned ID.
9. Compare the live body to the local file and verify author/head/state.
10. Unset the scoped token.

A URL or successful HTTP response is only a transport claim until readback passes.

## 4. Repair a malformed conversation comment

Conversation comments can be updated in place:

```bash
gh api --method PATCH \
  repos/OWNER/REPO/issues/comments/COMMENT_ID \
  -F body=@/tmp/correct-body.md
```

Then fetch the comment and compare its body to the local file.

## 5. Repair a malformed submitted formal review

A submitted formal review usually cannot be edited. Preserve the audit trail:

1. Dismiss the malformed review with a reason such as: the transport posted a literal file path instead of the independently produced body.
2. Revalidate the same live exact head.
3. Submit a replacement formal review using the correct file-reading field.
4. Fetch the new review and verify:
   - reviewer login;
   - requested state (`CHANGES_REQUESTED`, `APPROVED`, or intended alternative);
   - exact `commit_id`;
   - complete body equality;
   - role signature and expected head.
5. Keep the dismissed record visible as transport-correction history.

## 6. Body equality normalization

Prefer exact string equality. If GitHub normalizes a single trailing newline, compare both exact lengths and `rstrip()` equality, record the normalization explicitly, and still verify every substantive byte, author, role, state, and head.

Never accept a 30–50 byte body where the local artifact is thousands of bytes; that is a strong signal that a literal file path was posted.
