---
name: github-pr-workflow
description: Full pull request lifecycle — create branches, commit changes, open PRs, monitor CI status, auto-fix failures, and merge. Works with gh CLI or falls back to git + GitHub REST API via curl.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, CI/CD, Git, Automation, Merge]
    related_skills: [github-auth, github-code-review]
---

# GitHub Pull Request Workflow

Complete guide for managing the PR lifecycle. **Default to local tools (`git` + `gh` CLI) instead of GitHub MCP tools** because local commands are more token-efficient, easier to batch, and keep large JSON/diffs out of model context. Each section shows the `gh` way first, then the `git` + `curl` fallback for machines without `gh`.

## Tool Selection Rule

1. **Use `git` for local repo state and diffs**: status, branches, commits, logs, diffs, worktrees, rebases, cherry-picks, pushes.
2. **Use `gh` CLI for GitHub API workflows**: PR/issue list/view/create/edit/comment/merge, checks, runs, releases, labels.
3. **Use `gh api` + `--jq` for compact API queries** when exact fields are needed.
4. **Use GitHub MCP only as a fallback or special-purpose tool**: when `gh` auth is unavailable, when adding inline pending review comments through MCP is specifically required, or when shell quoting/security wrappers block a needed API call.
5. **Reduce context**: prefer `--json <fields> --jq <filter>` and write large outputs to temp files instead of pasting full API responses into model context.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository with a GitHub remote

### Quick Auth Detection

```bash
# Determine which method to use throughout this workflow
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  # Ensure we have a token for API calls
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
echo "Using: $AUTH"
```

### Fine-Grained vs Classic PAT Limitations

- Fine-grained PATs (`github_pat_`) CANNOT create PRs (403 error) or set branch protection
- Classic PATs (`ghp_`) with `repo` scope are required for PR creation and branch protection
- Issues and read operations work fine with either

### Using Python `requests` Instead of curl

When `curl | python3` triggers security warnings, use Python's `requests` library directly:

```python
import requests

token = "your_github_token"  # Read from .env
repo = "owner/repo"
headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

# Create issue
requests.post(
    f"https://api.github.com/repos/{repo}/issues",
    headers=headers,
    json={"title": "My Issue", "body": "Description", "labels": ["bug"]},
    timeout=30
)

# Create PR
requests.post(
    f"https://api.github.com/repos/{repo}/pulls",
    headers=headers,
    json={"title": "My PR", "head": "branch-name", "base": "main", "body": "Description"},
    timeout=30
)

# Merge PR
requests.put(
    f"https://api.github.com/repos/{repo}/pulls/{pr_number}/merge",
    headers=headers,
    json={"merge_method": "squash", "commit_title": f"Merge PR #{pr_number}"},
    timeout=30
)
```

**Extracting token from .env in Python:**
```python
with open('/Users/creator/.hermes/.env') as f:
    for line in f:
        if line.startswith('GITHUB_TOKEN='):
            token = line.split('=', 1)[1].strip()
            break
```

### Extracting Owner/Repo from the Git Remote

Many `curl` commands need `owner/repo`. Extract it from the git remote:

```bash
# Works for both HTTPS and SSH remote URLs
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"
```

---

## 1. Branch Creation

This part is pure `git` — identical either way:

```bash
# Make sure you're up to date
git fetch origin
git checkout main && git pull origin main

# Create and switch to a new branch
git checkout -b feat/add-user-authentication
```

Branch naming conventions:
- `feat/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

### Parallel Agent Safety: Use Git Worktrees

When another agent is actively working in the main checkout (dirty `git status`, active feature branch, or the user says Claude/Codex is working there), do **not** stash/reset/checkout in that working tree. Create an isolated worktree from latest `origin/main` instead:

```bash
# From the original repository checkout
git status --short
git branch --show-current
git fetch origin main --prune

mkdir -p ~/projects/<project>/worktrees
git worktree add ~/projects/<project>/worktrees/<task-name> origin/main -b fe/hermes-<task-name>
```

Then do all edits, installs, validation, commits, pushes, and PR creation from the worktree path. Before reporting, verify:

```bash
# Worktree has only your intended committed changes
git status --short

# Original checkout still has the other agent's branch/work intact
cd <original-checkout>
git status --short
git branch --show-current
```

Only clean files you created yourself (e.g. screenshots or `.playwright-mcp/` artifacts). Never remove or reset another agent's modified files.

### Closed/Conflicting PR Follow-up Fixes

When a reviewed PR is closed, stale, or `mergeable=CONFLICTING`, and the user asks you to implement a reviewer fix, do **not** open a follow-up PR that is based on the stale PR branch unless the user explicitly wants to resurrect the whole old branch. That reproduces the original conflicts and makes the fix hard to merge.

Default safer sequence:

```bash
# Inspect the old PR and identify the minimal fix
OLD_PR=29
gh pr view "$OLD_PR" --json state,mergeable,headRefName,baseRefName,headRefOid,url

# Start clean from current upstream main
git fetch origin main --prune
git worktree add /tmp/<repo>-fix-clean origin/main -b ci/<short-fix-name>
cd /tmp/<repo>-fix-clean

# Apply only the reviewer-fix diff (manual patch/cherry-pick selected commit with -n, not the whole old branch)
# ... edit files ...

git diff --stat origin/main...HEAD
git add <minimal files>
git commit -m "ci: exclude live integration tests from PR CI"
```

If upstream branch push is denied, fork and push the clean branch from current `origin/main`:

```bash
gh repo fork OWNER/REPO --clone=false || true
git remote add fork https://github.com/<you>/REPO.git 2>/dev/null || git remote set-url fork https://github.com/<you>/REPO.git
git push -u fork HEAD:<branch>
gh pr create --repo OWNER/REPO --head <you>:<branch> --base main --title "..." --body-file /tmp/pr-body.md
```

Verification before reporting:
- `git diff origin/main...HEAD --name-only` shows only the intended minimal files.
- `git ls-remote fork refs/heads/<branch>` matches local `HEAD`.
- `gh pr view <new-pr> --json headRefOid,mergeStateStatus,mergeable,files,commits` shows the pushed SHA and does **not** inherit the old PR's unrelated files/conflicts.
- Comment back on the old PR with the clean follow-up PR link and note whether direct upstream push was denied.

## 2. Making Commits

Use the agent's file tools (`write_file`, `patch`) to make changes, then commit:

```bash
# Stage specific files
git add src/auth.py src/models/user.py tests/test_auth.py

# Commit with a conventional commit message
git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes
- Add unit tests for auth flow"
```

Commit message format (Conventional Commits):
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

## 3. Pushing and Creating a PR

### Push the Branch (same either way)

```bash
git push -u origin HEAD
```

### Create the PR

**With gh:**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

The response JSON includes the PR `number` — save it for later commands.

To create as a draft, add `"draft": true` to the JSON body.

## 4. Monitoring CI Status

### Check CI Status

**With gh:**

```bash
# One-shot check
gh pr checks

# Watch until all checks finish (polls every 10s)
gh pr checks --watch
```

**With git + curl:**

```bash
# Get the latest commit SHA on the current branch
SHA=$(git rev-parse HEAD)

# Query the combined status
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Overall: {data['state']}\")
for s in data.get('statuses', []):
    print(f\"  {s['context']}: {s['state']} - {s.get('description', '')}\")"

# Also check GitHub Actions check runs (separate endpoint)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/check-runs \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for cr in data.get('check_runs', []):
    print(f\"  {cr['name']}: {cr['status']} / {cr['conclusion'] or 'pending'}\")"
```

### Poll Until Complete (git + curl)

```bash
# Simple polling loop — check every 30 seconds, up to 10 minutes
SHA=$(git rev-parse HEAD)
for i in $(seq 1 20); do
  STATUS=$(curl -s \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])")
  echo "Check $i: $STATUS"
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failure" ] || [ "$STATUS" = "error" ]; then
    break
  fi
  sleep 30
done
```

## 5. Addressing User Review Comments Across One or More PRs

Use this when the user says they reviewed PRs and left comments, especially for multi-repo pilots or batches.

For follow-up requests after a repo/process audit such as "submit that PR and any PR you deem necessary," also consult `references/absorbed/github-pr-workflow/references/lean-harness-and-website-pr-followup.md`. It captures the lean multi-repo pattern: one generic template/process PR, only unblocked product-site PRs, no premature QA/handoff PRs, per-PR remote SHA verification, and explicit "no checks reported" wording when CI is absent.

For PR comments that supply stakeholder-approved business data or defer claims into follow-up work, also consult `references/absorbed/github-pr-workflow/references/stakeholder-data-pr-comments.md`. It captures the ledger-first pattern, URL verification, clean Google Maps directions URLs, deferred-issue handling, and closeout comment contents.

### Repo-wide PR/Issue Audit Pattern

Use this when Karan asks to inspect what issues were created/closed, what PRs were made, what comments/reviews happened, what work got done, and what remains. Prefer REST endpoints via `gh api` for repo-wide audits; `gh pr list --json ...` can hit GraphQL traversal limits when requesting nested author/comment data.

```bash
REPO=OWNER/REPO
OUT=/tmp/repo_audit_$(date +%Y%m%d_%H%M%S)
mkdir -p "$OUT"

gh api -X GET "repos/$REPO/issues?state=all&per_page=100" --paginate > "$OUT/issues_all.json"
gh api -X GET "repos/$REPO/pulls?state=all&per_page=100" --paginate > "$OUT/prs_all.json"

python3 - <<'PY' "$OUT" "$REPO"
import json, pathlib, subprocess, sys
out = pathlib.Path(sys.argv[1]); repo = sys.argv[2]
issues = json.load(open(out/'issues_all.json'))
prs = json.load(open(out/'prs_all.json'))
plain_issues = [i for i in issues if 'pull_request' not in i]

print('ISSUES')
for i in sorted(plain_issues, key=lambda x: x['number']):
    labels = [l['name'] for l in i['labels']]
    print(f"#{i['number']} {i['state']} {i.get('state_reason')} labels={labels} title={i['title']} closed={i.get('closed_at')}")

print('\nPRS')
for p in sorted(prs, key=lambda x: x['number']):
    n = p['number']
    def gh_json(path):
        return json.loads(subprocess.check_output(['gh','api','-X','GET',f'repos/{repo}/{path}','--paginate'], text=True))
    details = json.loads(subprocess.check_output(['gh','api','-X','GET',f'repos/{repo}/pulls/{n}'], text=True))
    issue_comments = gh_json(f'issues/{n}/comments?per_page=100')
    reviews = gh_json(f'pulls/{n}/reviews?per_page=100')
    review_comments = gh_json(f'pulls/{n}/comments?per_page=100')
    commits = gh_json(f'pulls/{n}/commits?per_page=100')
    files = gh_json(f'pulls/{n}/files?per_page=100')
    json.dump({'pull': details, 'issue_comments': issue_comments, 'reviews': reviews, 'review_comments': review_comments, 'commits': commits, 'files': files}, open(out/f'pr_{n}.json','w'), indent=2)
    print(f"#{n} {details['state']} merged={details['merged']} base={details['base']['ref']} head={details['head']['ref']} title={details['title']}")
    print(f"  commits={[c['commit']['message'].splitlines()[0] for c in commits]}")
    print(f"  files={[f['filename'] for f in files]}")
    for c in issue_comments:
        print(f"  issue_comment {c['user']['login']}: {c['body'][:160].replace(chr(10),' | ')}")
    for r in reviews:
        print(f"  review {r['state']} {r['user']['login']}: {(r.get('body') or '')[:160].replace(chr(10),' | ')}")
    for rc in review_comments:
        print(f"  review_comment {rc['path']}:{rc.get('line') or rc.get('original_line')} {rc['user']['login']}: {rc['body'][:160].replace(chr(10),' | ')}")
print(f"\nArtifacts: {out}")
PY
```

When synthesizing the audit, group findings by: completed issues, open issues, merged/closed/open PRs, review comments that changed the work, what remains blocked, risks/what could go wrong, and lean process/template fixes. Do not turn the audit into a parallel tracker; link back to GitHub as source of truth.

1. Discover open PRs and comments before editing. For each likely repo, include issue comments, inline review comments, and formal PR reviews. Do not ignore `COMMENTED` reviews from the PR author/account: GitHub may prevent the same account from requesting changes on its own PR, so agents often record blocking self-review findings as plain review comments.

```bash
gh pr list -R OWNER/REPO --state open --json number,title,headRefName,baseRefName,url
PR_NUMBER=1
gh api repos/OWNER/REPO/issues/$PR_NUMBER/comments --paginate \
  --jq '.[] | select(.user.login != "linear[bot]") | {id, user: .user.login, created_at, body}'
gh api repos/OWNER/REPO/pulls/$PR_NUMBER/comments --paginate
gh api repos/OWNER/REPO/pulls/$PR_NUMBER/reviews --paginate \
  --jq '.[] | {user:.user.login,state,submitted_at,body}'
```

2. Treat the user's PR comments as acceptance criteria. Convert each comment into concrete file changes, then search the repo for stale wording that would violate the spirit of the review, not just the exact quoted line.
   - If the comment provides stakeholder-approved business data, update the repo's verification ledger/source-of-truth doc first; do **not** jump straight into public site/code changes unless the PR/issue explicitly asks for implementation too.
   - Verify user-supplied URLs before recording them as usable. For copied Google Maps URLs that include browser/session parameters (`rlz`, `um`, `fb`, etc.), prefer documenting a cleaner `https://www.google.com/maps/dir/?api=1&destination=...` URL after confirming it resolves and contains the approved destination.
   - If the comment says "create a new issue for this" or explicitly defers part of the scope, create focused follow-up issues and mark those ledger rows as `Deferred`; do not treat the original PR as approving that copy/claim.
   - If the blocker is an unmerged dependency (e.g. QA evidence PR must land before handoff PR), do not paper over it as completed. Mark dependent docs/gates as `pending`, update any premature `Closes #N` in the PR body to `Refs #N`, and state the closeout condition explicitly.
   - If the PR unblocks or implements fields that were previously deferred in a source-of-truth ledger/current TODO map (canonical URLs, OG images, JSON-LD fields, business-data rows, approval gates, etc.), update that ledger in the same PR. Search for stale phrases like "blocked", "deferred", "intentionally omitted", and the issue number before pushing; stale repo docs are blocking because the next builder will treat them as truth.
   - Post a follow-up PR comment that maps what changed, what was verified, which items remain deferred, and the exact remote head SHA/merge state.
3. Keep reusable references/absorbed/github-pr-workflow/templates/harnesses task-agnostic. Remove issue-specific artifacts from template repos; move reusable details into generic templates, umbrella docs, or domain-specific libraries.
4. For harness/spec repos that may be handed to other agents, avoid requiring private/local skills or one agent's internal workflow terms. Required guidance should live in repo files; tool-specific skills can be optional references only.
5. After committing and pushing, verify the pushed commit is visible on the remote PR before reporting success. If `git push` succeeds but `gh pr view` still shows the old `headRefOid`, do not report failure or success from stale GraphQL data; first check the raw remote ref with `git ls-remote`, wait a few seconds, then re-query the PR until the PR API sees the new SHA.

```bash
LOCAL_SHA=$(git rev-parse HEAD)
git ls-remote origin refs/heads/<head-branch>
sleep 5
gh pr view $PR_NUMBER -R OWNER/REPO --json commits,headRefOid,mergeStateStatus,url \
  --jq '{url, headRefOid, mergeStateStatus, commits: [.commits[] | {oid, messageHeadline}]}'
test "$(gh pr view $PR_NUMBER -R OWNER/REPO --json headRefOid --jq .headRefOid)" = "$LOCAL_SHA"
```

6. Post a concise PR comment summarizing: user concern addressed, files/behavior changed, local validation, and remote commit verification. Use `--body-file` for markdown containing backticks.
7. If multiple PRs are updated, verify every PR independently. Do not generalize one successful push/check to the whole batch.

## 6. Frontend Issue Batches With Clean PRs

When a user asks to work through multiple frontend GitHub issues and open PRs without merging, use `references/absorbed/github-pr-workflow/references/frontend-issue-batch-prs.md`. It covers discovery-first branch/PR collision checks, one-worktree-per-issue isolation, provider-side blocker comments instead of fake PRs, local browser probes for visual/routing bugs, and per-PR remote `headRefOid` verification before reporting success.

## 7. Closing Content-Only Issues With Verification

Use this when an issue is not a code PR but a content/data operational task, such as populating CMS records, uploading assets, or verifying Studio-managed content.

1. Re-read the issue body and comments first; treat acceptance criteria as the closeout checklist.
2. Verify the source of truth directly, not just the UI. For Sanity-backed content, query the production dataset with the repo's configured project/dataset/env and assert the relevant fields are populated. Example checks: total published record count, missing required asset fields, and representative CDN URLs.
3. Verify the website code path that consumes the content still maps the expected fields (for example `image.asset->url` for vendor photos) and run local validation (`npm run lint`, `npm run build`) when the repo has a frontend build.
4. If a live custom domain is redirected, parked, or otherwise not the deployed app, do not claim production-domain verification. State the limitation explicitly and verify the CMS/source data plus current build path instead.
5. Post a concise closeout comment that lists: direct data verification, local/build verification, any production-domain caveat, and the exact result count (e.g. `16/16 published vendors have image.asset`).
6. Close the issue with a completed reason. Note: some `gh` versions support `gh issue close --comment` but not `--comment-file`; use `gh issue comment --body-file /tmp/closeout.md && gh issue close --reason completed` or `gh issue close --reason completed --comment "$(cat /tmp/closeout.md)"`.
7. Re-query the issue after closing and require `state: CLOSED` before reporting completion.

## 7. Auto-Fixing CI Failures

When CI fails, diagnose and fix. This loop works with either auth method.

### Step 1: Get Failure Details

**With gh:**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

# List workflow runs on this branch
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python3 -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
    print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

# Get failed job logs (download as zip, extract, read)
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt
```

### Step 2: Fix and Push

After identifying the issue, use file tools (`patch`, `write_file`) to fix it:

```bash
git add <fixed_files>
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

### Step 3: Verify

Re-check CI status using the commands from Section 4 above.

### Auto-Fix Loop Pattern

When asked to auto-fix CI, follow this loop:

1. Check CI status → identify failures
2. Read failure logs → understand the error
3. Use `read_file` + `patch`/`write_file` → fix the code
4. `git add . && git commit -m "fix: ..." && git push`
5. Wait for CI → re-check status
6. Repeat if still failing (up to 3 attempts, then ask the user)

## 7. Merging

For batch/multi-repo pilot wrap-ups, also consult `references/absorbed/github-pr-workflow/references/batch-pr-pilot-closeout.md` before merging: it covers per-PR prechecks, merge verification, deleted-branch verification, local checkout cleanup, and tracker closeout sequencing.

For stale branches that appear ahead of `main` after their PR was already merged, consult `references/absorbed/github-pr-workflow/references/stale-merged-branch-cleanup.md` before opening/merging anything. It covers REST merge verification, conflict checks, safe remote deletion, and local branch deletion after confirming the branch tree matches `origin/main`.

### Comment-and-merge closeout

When the user explicitly approves an external-side-effect action like "comment and merge":

1. Post the review/closeout comment first, using `--body-file` for markdown/backticks.
2. Re-query PR state immediately before merging and confirm it is still open, mergeable, and targeting the expected base/head. In a batch, do this again before every single merge; an earlier merge can turn a later PR from `CLEAN` into `DIRTY`/conflicting. If GitHub reports `mergeable_state: unknown` or GraphQL `mergeStateStatus: UNKNOWN` after a prior merge, wait/re-query until it recomputes to `clean`/`CLEAN` (or a clear blocked state) before merging; do not treat `unknown` as approval evidence even though `gh pr merge` may sometimes still succeed.
3. If the PR has review comments or top-level comments that mention blockers, read the whole thread before merging. Confirm there is a later fix/re-review comment or commit that addresses each blocker. In same-account agent repos where GitHub blocks formal self-approval, a top-level “no remaining blocking issues” re-review comment is acceptable only after you also run targeted local probes for the corrected behavior.
4. When merging “the rest of the open PRs,” sequence related PRs deliberately instead of treating them as independent. If PR A fixes a blocker or prerequisite for PR B, merge and verify PR A first, then re-check PR B against the new `origin/main` before merging. Use an isolated worktree and an actual `git merge --no-commit --no-ff <pr-ref>` test when you need to confirm combined state preserves both changes. Before running the test merge, print/verify `pwd`, `git worktree list`, and `git status --short --branch` so you do not accidentally mutate the main checkout; after the test, always `git merge --abort` or discard the throwaway worktree before final reporting. Avoid `git merge-tree` for PRs containing binary assets because it can dump huge binary content into the terminal/context; a real no-commit test merge is clearer and safer.
5. If the user explicitly includes draft PRs in the merge request, review and validate the draft normally. Only mark it ready and merge if it is objectively clean, mergeable, and passes applicable local checks; otherwise leave it as draft and report the blocker. If the user did not explicitly include drafts, do not merge draft PRs.
5. Run the merge command. Note: `gh pr merge` may print no output on success; do not infer failure from empty stdout or success from exit alone.
6. Verify with the REST boolean before reporting: `gh api repos/$OWNER_REPO/pulls/$PR_NUMBER --jq '{state, merged, merged_at, merge_commit_sha, head_ref: .head.ref}'` and require `merged: true`.
7. Fetch `origin main` and show the latest remote commit.
8. If `--delete-branch` was used, verify `git ls-remote --heads origin "$HEAD_BRANCH"` returns empty.
9. If the PR body says `Closes #N`, verify the linked issue state after merge before reporting tracker closeout.

**With gh:**

```bash
# Squash merge + delete branch (cleanest for feature branches)
gh pr merge --squash --delete-branch

# Enable auto-merge (merges when all checks pass)
gh pr merge --auto --squash --delete-branch
```

**With git + curl:**

```bash
PR_NUMBER=<number>

# Merge the PR via API (squash)
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{
    \"merge_method\": \"squash\",
    \"commit_title\": \"feat: add user authentication (#$PR_NUMBER)\"
  }"

# Delete the remote branch after merge
BRANCH=$(git branch --show-current)
git push origin --delete $BRANCH

# Switch back to main locally
git checkout main && git pull origin main
git branch -d $BRANCH
```

Merge methods: `"merge"` (merge commit), `"squash"`, `"rebase"`

### Verify Merge Actually Succeeded

Never report a merge as complete until GitHub confirms `merged: true` (or `state: MERGED` plus a merge commit). `gh pr view --json merged` is not valid in some `gh` versions; use the REST API for the explicit boolean:

```bash
PR_NUMBER=<number>
OWNER_REPO=$(git remote get-url origin | sed -E 's|.*github\.com[:/]||; s|\.git$||')

gh api repos/$OWNER_REPO/pulls/$PR_NUMBER \
  --jq '{state, merged, merged_at, merge_commit_sha, head_ref: .head.ref}'
# Required before reporting success: "merged": true
```

Also verify remote main advanced to the merge commit:

```bash
git fetch origin main --prune
git log origin/main -1 --oneline
```

For Vercel-connected frontend repos, merging to `main` usually triggers production deployment automatically. Verify the post-merge deploy from GitHub commit status before telling the user it is live:

```bash
SHA=$(git rev-parse origin/main)
gh api repos/$OWNER_REPO/commits/$SHA/status \
  --jq '{state,statuses:[.statuses[]|{context,state,target_url,description,updated_at}]}'
# If state is pending, poll until success/failure. Vercel success typically says "Deployment has completed".
```

If GitHub deployment objects are empty, the commit status can still be the source of truth for the Vercel GitHub integration. If the commit status is stuck `pending`, cross-check GitHub deployment objects for the same SHA before calling it a failed deploy; a deployment object may say `success` even while the commit status remains stale. See `references/absorbed/github-pr-workflow/references/vercel-stale-github-status.md` for the exact diagnosis sequence and how to explain Vercel preview-protection `401`s. After success, smoke-test the canonical Vercel URL. Treat custom-domain failures separately from deployment success: a custom domain returning `403`, `400`, parked hosting, or non-Vercel server headers is DNS/domain configuration, not evidence the Vercel deployment failed.

If `--delete-branch` was used, confirm the remote branch is gone:

```bash
HEAD_BRANCH=$(gh api repos/$OWNER_REPO/pulls/$PR_NUMBER --jq '.head.ref')
git ls-remote --heads origin "$HEAD_BRANCH"
# Empty output means the remote branch was deleted.
```

### Stacked PR Merge Workflow

Use this when PR B targets PR A's feature branch instead of `main` (e.g. #59 base = #58 branch). Goal: preserve clean diffs and avoid duplicating PR A changes in PR B.

1. Review both PRs before merging. Confirm PR B is truly stacked on PR A and only contains follow-up commits:

```bash
gh pr list --state open --json number,title,baseRefName,headRefName,mergeable,mergeStateStatus
```

2. Merge PR A first. Prefer `--rebase` when PR B is stacked on PR A so PR A's commit lands on `main` with the same patch history shape. Do **not** use `--delete-branch` yet if any downstream PR still names PR A's branch as its base; keep the branch available until every dependent PR has been rebased/retargeted.

```bash
gh pr merge <PR_A> --rebase
```

3. Verify PR A with the REST boolean before proceeding:

```bash
gh api repos/$OWNER_REPO/pulls/<PR_A> \
  --jq '{state, merged, merged_at, merge_commit_sha, head_ref: .head.ref}'
# Required: "merged": true
```

4. Rebase PR B onto the updated `main`, force-push with lease, and retarget PR B to `main`. If you retarget before rebasing, GitHub may temporarily show scaffold/base commits and conflicts; this is expected until the force-pushed rebase lands and GitHub recomputes.

```bash
git fetch origin main <pr-b-branch>
git checkout -B pr-b-clean origin/<pr-b-branch>
# OLD_BASE_SHA is PR A's original head SHA before it was merged.
git rebase --onto origin/main <OLD_BASE_SHA>
git push --force-with-lease origin HEAD:<pr-b-branch>
gh pr edit <PR_B> --base main
```

After a force-push, verify both the raw remote branch and the PR API. `gh pr view` can lag for a few seconds and show the old `headRefOid`; sleep/re-query rather than assuming the push failed if `git ls-remote` shows the new SHA.

```bash
NEW_SHA=$(git rev-parse HEAD)
git ls-remote origin refs/heads/<pr-b-branch>
sleep 5
gh pr view <PR_B> --json headRefOid,commits,files,mergeable,mergeStateStatus \
  --jq '{headRefOid, mergeable, mergeStateStatus, commits: [.commits[] | .messageHeadline], files: [.files[] .path]}'
test "$(gh pr view <PR_B> --json headRefOid --jq .headRefOid)" = "$NEW_SHA"
```

5. Verify PR B now has only its own commits and files, then wait for GitHub to recompute mergeability:

```bash
sleep 5
gh pr view <PR_B> --json baseRefName,headRefOid,commits,files,mergeable,mergeStateStatus \
  --jq '{baseRefName, headRefOid, mergeable, mergeStateStatus, commits: [.commits[] | .messageHeadline], files: [.files[] .path]}'

git fetch origin main <pr-b-branch>
git diff origin/main...origin/<pr-b-branch> --stat
```

6. Re-run local validation on PR B after the rebase, then merge and verify normally:

```bash
npm run lint && npm run build
gh pr merge <PR_B> --rebase --delete-branch
gh api repos/$OWNER_REPO/pulls/<PR_B> --jq '{state, merged, merged_at, merge_commit_sha}'
```

7. Clean up PR A's branch manually if the first merge method did not delete it, but only after all downstream PRs have been rebased/retargeted and merged or no longer depend on it. Also delete any intermediate stacked branches that were intentionally kept alive during the sequence, then verify each remote branch is gone:

```bash
for b in <pr-a-branch> <pr-b-branch>; do
  if git ls-remote --heads origin "$b" | grep -q .; then
    git push origin --delete "$b"
  fi
  git ls-remote --heads origin "$b"
done
# Empty output for each branch means it is deleted.
```

8. After a stacked sequence, verify every PR independently with the REST `merged: true` boolean, verify linked issues closed if `Closes #N` was used, sync local `main`, and check local status is clean:

```bash
for n in <PR_A> <PR_B>; do
  gh api repos/$OWNER_REPO/pulls/$n --jq '{state, merged, merged_at, merge_commit_sha, head_ref: .head.ref}'
done
git checkout main && git pull --ff-only origin main
git status --short --branch
```

### Enable Auto-Merge (curl)

```bash
# Auto-merge requires the repo to have it enabled in settings.
# This uses the GraphQL API since REST doesn't support auto-merge.
PR_NODE_ID=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['node_id'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/graphql \
  -d "{\"query\": \"mutation { enablePullRequestAutoMerge(input: {pullRequestId: \\\"$PR_NODE_ID\\\", mergeMethod: SQUASH}) { clientMutationId } }\"}"
```

## 8. Complete Workflow Example

```bash
# 1. Start from clean main
git checkout main && git pull origin main

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (Agent makes code changes with file tools)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR (picks gh or curl based on what's available)
# ... (see Section 3)

# 7. Monitor CI (see Section 4)

# 8. Merge when green (see Section 7)
```

## Useful PR Commands Reference

| Action | gh | git + curl |
|--------|-----|-----------|
| List my PRs | `gh pr list --author @me` | `curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open"` |
| View PR diff | `gh pr diff` | `git diff main...HEAD` (local) or `curl -H "Accept: application/vnd.github.diff" ...` |
| Add comment | `gh pr comment N --body "..."` | `curl -X POST .../issues/N/comments -d '{"body":"..."}'` |
| Request review | `gh pr edit N --add-reviewer user` | `curl -X POST .../pulls/N/requested_reviewers -d '{"reviewers":["user"]}'` |
| Close PR | `gh pr close N` | `curl -X PATCH .../pulls/N -d '{"state":"closed"}'` |
| Check out someone's PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |
