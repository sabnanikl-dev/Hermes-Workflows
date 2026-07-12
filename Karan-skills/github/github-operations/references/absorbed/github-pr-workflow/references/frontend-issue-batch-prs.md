# Frontend Issue Batch PR Pattern

Use when a user asks to work through several GitHub issues in one frontend repo and open clean PRs without merging.

## Discovery first

1. Re-read every target issue before editing.
2. Inspect repo state, open PRs, and existing remote branches before creating work:
   - `git status --short --branch`
   - `git fetch origin --prune`
   - `gh pr list -R OWNER/REPO --state open --json number,title,headRefName,baseRefName,url,author`
   - `git branch -r | grep -E '<issue numbers or keywords>' || true`
3. Read package scripts and lockfile to determine validation commands.

## Work isolation

Default to one worktree and one branch per issue from latest `origin/main`:

```bash
git fetch origin main --prune
mkdir -p ~/projects/<repo>-worktrees
git worktree add ~/projects/<repo>-worktrees/<issue-topic> origin/main -b fe/hermes-<issue-topic>
```

Only combine issues when they are clearly the same code path and safer as one review unit.

## Root-cause discipline

For each issue, record the root cause before fixing. For frontend bugs this often means:
- Trace the affected component/config with `read_file`/search.
- Confirm whether the symptom is code-side or provider/config-side.
- Prefer the smallest durable code change over broad refactors.

For provider-side blockers, do not fake a PR. Leave an issue comment with:
- Exact command/probe used.
- Exact response/error.
- Origins/settings/manual actions required.
- Why repo code cannot complete the fix honestly.

Example Sanity CORS probe:

```bash
curl -sS -D - -o /tmp/sanity_probe.json \
  -H 'Origin: https://production-origin.example' \
  'https://PROJECT.apicdn.sanity.io/vYYYY-MM-DD/data/query/production?query=*%5B0%5D%7B_id%7D'
```

If it returns `403` / `CORS Origin not allowed`, the durable fix is Sanity project CORS allowlist, not a frontend PR.

## Validation layering

For every PR branch run package-script validation at minimum:

```bash
npm ci
npm run lint
npm run build
```

When the issue is visual/routing/interaction-related, add a local preview and browser probe:
- Start Vite in that worktree on a unique port.
- Use Playwright/browser evaluation to measure the specific failure mode, not just eyeball the page.
- Capture objective values in the PR body/test plan: anchor top, overflow styles, scrollTop, card bounds, missing asset references, etc.

Useful probes:
- Anchor landing: URL hash, target `getBoundingClientRect().top`, visible input locations.
- Carousel vertical scroll: `overflowX`, `overflowY`, `clientHeight`, `scrollHeight`, `scrollTop` before/after wheel.
- Card clipping: compare child item bounds against card bounds.
- Asset 404 cleanup: grep built CSS for old URL and expected local asset path.

## PR creation and remote verification

After commit and push:

```bash
LOCAL_SHA=$(git rev-parse HEAD)
git push -u origin HEAD
REMOTE_SHA=$(git ls-remote origin refs/heads/$(git branch --show-current) | awk '{print $1}')
test "$REMOTE_SHA" = "$LOCAL_SHA"
```

Open PR with a body containing:
- Summary.
- Root cause.
- Test plan.
- `Closes #N`.

Then verify the PR API sees the pushed commit:

```bash
gh pr view <PR> -R OWNER/REPO --json number,url,headRefName,headRefOid,commits,mergeable,mergeStateStatus,files \
  --jq '{number,url,headRefName,headRefOid,mergeable,mergeStateStatus,commits:[.commits[]|{oid,messageHeadline}],files:[.files[].path]}'
```

Require `headRefOid == LOCAL_SHA` before reporting the PR as opened/pushed.

## End-session audit

Before final response:
- Re-run open PR listing.
- Confirm every issue branch ahead of `origin/main` has an open PR or a documented blocker comment.
- Confirm all worktrees are clean.
- Report validation commands, browser checks, remote commit verification, blockers, and manual follow-up.
