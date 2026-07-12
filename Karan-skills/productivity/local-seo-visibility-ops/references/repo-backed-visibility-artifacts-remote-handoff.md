# Repo-backed visibility artifacts: remote handoff discipline

Use this when local SEO / GBP / visibility work creates a local Git repo or repo-backed docs package, especially when approval gates prevent an immediate push or PR.

## Problem pattern

A visibility task can be truthfully completed locally while the GitHub repo remains empty or stale. This is dangerous because Linear may show Done/In Review while GitHub has no branch, no commits, and no default branch.

Typical shape:

- Local repo has commits and artifacts.
- Remote repo exists but has no branches/commits.
- Linear comments say local update/verification is complete.
- A human later opens GitHub and sees an empty repo.

## Rule

Remote state is part of the deliverable whenever a task names a GitHub repo, repo copy, PR, branch, or “push/PR” decision.

If push/PR is approval-gated, do **not** let the task read as fully complete. The handoff must explicitly say:

- local path
- local branch
- local commit SHA(s)
- remote repo URL
- remote branch/commit status
- exact approval needed to push directly vs open PR
- what state Linear should remain in until that decision is made

## Verification checklist

Before reporting Done/In Review for a repo-backed visibility artifact:

```bash
git -C <repo> status --short --branch
git -C <repo> log --oneline --decorate -5
git -C <repo> remote -v
git -C <repo> ls-remote --heads origin
```

For GitHub:

```bash
gh repo view <owner>/<repo> --json defaultBranchRef,pushedAt,updatedAt,url
gh api repos/<owner>/<repo>/contents || true
gh api repos/<owner>/<repo>/commits || true
```

Interpretation:

- No remote heads + local commits = not remotely delivered.
- Empty remote repo + local commits = ask/record whether to seed `main` or push a review branch.
- PR requested but no base branch exists = either seed `main` directly with approval, or create an initial branch and guide GitHub compare flow.

## Recommended handoff language

If approval blocks pushing:

```md
Local artifacts are complete but the GitHub repo is intentionally not updated yet.

Local path: `<path>`
Local branch: `<branch>`
Local head: `<sha>`
Remote: `<url>`
Remote heads: none / `<heads>`

Approval needed: choose one:
1. Seed `main` directly with these docs.
2. Push `<branch>` and open/prepare a PR.
3. Keep local-only for now.

Until this is chosen, do not mark the repo-delivery portion Done.
```

## Linear handling

- If the remaining blocker is human push/PR choice, move the parent to In Review and create/assign a child approval issue.
- If the user already approved “commit after review” but did not specify push/PR, ask or leave a clear approval gate instead of closing silently.
- Never imply GitHub has been updated until `git ls-remote` or GitHub API verifies the remote commit/branch.
