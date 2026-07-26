# Visible Pickup and Progressive Acceptance

## GitHub visibility: local is not remote

A local worktree can be active while the GitHub issue Development section is empty. Verify each layer separately:

```bash
# Local execution state
git branch --show-current
git rev-parse HEAD
git status --short --branch

# Remote visibility
git ls-remote --heads origin <branch>
gh pr list --repo <owner/repo> --state open \
  --json number,url,isDraft,headRefName,headRefOid,closingIssuesReferences
```

Interpretation:

- Local branch present + empty `ls-remote` = execution exists only locally.
- Remote branch present + no PR/association = branch is published but may not appear as issue-linked work.
- Draft PR with verified `closingIssuesReferences` = GitHub-native implementation linkage is visible and reconstructable.

A plain `Closes #N` line in the PR body is the preferred issue linkage once a real commit supports a PR. Text presence is not proof; read `closingIssuesReferences`.

### Preferred immediate visible claim

For Karan's GitHub-native coding queue, create the branch through GitHub's issue Development flow before launching the builder:

```bash
BRANCH=feat/issue-<N>-short-slug

gh issue develop <N> --repo <owner/repo> --name "$BRANCH" --base main
gh issue develop <N> --repo <owner/repo> --list
git ls-remote --heads origin "$BRANCH"

git fetch origin "$BRANCH"
git worktree add --track -b "$BRANCH" <worktree-path> "origin/$BRANCH"
```

If the installed CLI does not expose `gh issue develop`, use GitHub's native **Create a branch** action. If neither route is available or authorized, say that pickup is local-first and do not imply the Development surface is populated. After the first coherent commit, push and open the linked draft PR.

Do not create an empty commit merely to force a PR. The issue-linked remote branch is the visible claim; the draft PR becomes the durable implementation linkage after real code exists.

Pitfalls:

- `git worktree add -b <branch>` creates only a local branch and does not notify GitHub.
- A pushed remote ref is not necessarily issue-associated; verify the Development listing when available.
- Once a PR exists, verify `closingIssuesReferences`, not only `Closes #N` text.
- After every push, re-prove local/remote/PR head equality.

## Builder handoff equality

After push, prove:

```bash
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git ls-remote origin refs/heads/<branch> | cut -f1)
PR_HEAD=$(gh pr view <N> --repo <owner/repo> --json headRefOid --jq .headRefOid)
PR_LAST=$(gh pr view <N> --repo <owner/repo> --json commits --jq '.commits[-1].oid')
test "$LOCAL" = "$REMOTE"
test "$LOCAL" = "$PR_HEAD"
test "$LOCAL" = "$PR_LAST"
```

Do not report a push from local state alone.

## Exact-head reviewer gate

Capture the PR head before launching the reviewer and include it in the prompt and final marker:

```text
DONE: STATUS=pass BLOCKING=0 HEAD=<40-char-sha>
```

After any builder push, re-read `headRefOid`; old verdicts are stale even if their findings still look relevant.

If the reviewer executable is intentionally read-only/credentialless, relay its verdict through the configured reviewer identity and mark the body as relayed in substance. Then prove the formal review is bound to the intended head:

```bash
gh api repos/<owner>/<repo>/pulls/<N>/reviews \
  --jq '[.[] | select(.user.login=="<reviewer-login>") | {state,commit_id,html_url,body}] | last'
```

A successful reviewer process exit proves only that the command completed. The machine-readable verdict determines pass/fail, and the GitHub `commit_id` readback determines whether the published review is current.

## Progressive Linear checkbox update

Use the issue's current full description as the mutation base. Replace only exact satisfied lines:

```markdown
- [ ] Proven criterion
```

with:

```markdown
- [x] Proven criterion
```

Then read the live issue body back. Linear may return uppercase:

```markdown
- [X] Proven criterion
```

Case-insensitive verification pattern:

```python
checked = re.findall(r"^- \[[xX]\] (.+)$", body, re.M)
unchecked = re.findall(r"^- \[ \] (.+)$", body, re.M)
```

Assert both sets, not only counts. A failed verifier caused by `[X]` normalization is a verifier bug, not proof the mutation failed; inspect the exact live lines and rerun the corrected assertion.

For Linear evidence comments, the helper uses positional arguments:

```bash
python3 scripts/linear_api.py add-comment PAPI-88 "$(< /tmp/closeout.md)"
```

Do not pass `--body`. Capture the returned `comment.id`, then verify that exact comment with `comment(id: ...)`; do not rely on collection ordering such as `comments(last: 1)`.

## Evidence order

A practical progression:

1. **Containment/non-mutation criteria:** may be checked after local/remote/worktree readback and targeted tests.
2. **Behavioral correctness criteria:** wait for independent exact-head review plus real tests.
3. **Review/qualification criteria:** wait for reviewer artifacts and GitHub readback.
4. **Parent roll-up criterion:** wait until the child contract is fully accepted.

Never check all boxes merely because a builder opened a draft PR or reported green tests.
