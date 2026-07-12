---
name: github-issues
description: Create, manage, triage, and close GitHub issues. Search existing issues, add labels, assign people, and link to PRs. Works with gh CLI or falls back to git + GitHub REST API via curl.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Issues, Project-Management, Bug-Tracking, Triage]
    related_skills: [github-auth, github-pr-workflow]
---

# GitHub Issues Management

Create, search, triage, and manage GitHub issues. **Default to `gh` CLI instead of GitHub MCP tools** because it is more token-efficient and can return compact, filtered JSON. Each section shows `gh` first, then the `curl` fallback.

## Tool Selection Rule

1. Use `gh issue` for normal issue list/view/create/edit/comment/close flows.
2. Use `gh api` with `--jq` for field-specific reads or updates.
3. Use GitHub MCP only when `gh` auth is unavailable, when MCP provides a safer structured write for a complex operation, or when shell quoting/security tooling blocks the CLI path.
4. For long issue bodies, write markdown to a temp file and use `gh issue create --body-file` or `gh issue edit --body-file` instead of inlining markdown in a command.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repo with a GitHub remote, or specify the repo explicitly

### Setup

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi

REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## 1. Viewing Issues

**With gh:**

```bash
gh issue list
gh issue list --state open --label "bug"
gh issue list --assignee @me
gh issue list --search "authentication error" --state all
gh issue view 42
```

**With curl:**

```bash
# List open issues
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?state=open&per_page=20" \
  | python3 -c "
import sys, json
for i in json.load(sys.stdin):
    if 'pull_request' not in i:  # GitHub API returns PRs in /issues too
        labels = ', '.join(l['name'] for l in i['labels'])
        print(f\"#{i['number']:5}  {i['state']:6}  {labels:30}  {i['title']}\")"

# Filter by label
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?state=open&labels=bug&per_page=20" \
  | python3 -c "
import sys, json
for i in json.load(sys.stdin):
    if 'pull_request' not in i:
        print(f\"#{i['number']}  {i['title']}\")"

# View a specific issue
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42 \
  | python3 -c "
import sys, json
i = json.load(sys.stdin)
labels = ', '.join(l['name'] for l in i['labels'])
assignees = ', '.join(a['login'] for a in i['assignees'])
print(f\"#{i['number']}: {i['title']}\")
print(f\"State: {i['state']}  Labels: {labels}  Assignees: {assignees}\")
print(f\"Author: {i['user']['login']}  Created: {i['created_at']}\")
print(f\"\n{i['body']}\")"

# Search issues
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/search/issues?q=authentication+error+repo:$OWNER/$REPO" \
  | python3 -c "
import sys, json
for i in json.load(sys.stdin)['items']:
    print(f\"#{i['number']}  {i['state']:6}  {i['title']}\")"
```

## 2. Creating Issues

### Linear/PAPI spec-to-GitHub handoff preference

For PAPI/Linear-style work, Karan prefers the Linear issue to produce/spec GitHub issues only. Do **not** turn the Linear issue or Hermes Kanban card into the coding execution lane by default.

Default flow:
1. Linear/PAPI issue defines the product/ops need and asks for GitHub issue specs.
2. Hermes drafts or creates implementation-ready GitHub issues with context, acceptance criteria, likely files, validation, and sequencing.
3. Coding happens from the GitHub issue through normal GitHub branch/PR workflow, Codex/Claude Code, or a direct repo session outside Linear/Kanban.
4. Linear gets a concise tracker update linking the GitHub issues/PRs, not a nested coding task graph.

Only use Hermes Kanban for coding if Karan explicitly asks for Kanban as the execution lane.

### Conversational UX / feature follow-up issues

When Karan describes a desired website/product behavior conversationally (e.g. “does that make sense?”), treat it as enough intent to create a clear implementation-ready issue unless the ambiguity would change the product direction. Do not ask for boilerplate details if they can be discovered.

Recommended sequence:
1. Search all issues, including closed issues, for likely duplicates and prior partial work.
2. Inspect the relevant code/files enough to name exact current behavior and likely touch points.
3. If a prior issue mentions the idea as an optional follow-up, explicitly reference that context in the new issue rather than reopening the old completed tracker.
4. Write the issue as a product+implementation handoff: context, user flow, recommended approach, acceptance criteria, likely files, edge cases, and validation steps.
5. Prefer concrete field names and payload expectations when the issue affects forms or analytics (e.g. `interestedService` in Formspree), while preserving privacy rules.
6. Before creating, list/confirm available repo labels if the requested labels are not known-good for that repo. Do not assume common labels like `seo`, `brand`, or `design` exist. If a label is missing, either map to existing labels (`enhancement`, `frontend`, `quick-win`, etc.) or ask before creating new repository labels when label taxonomy matters.
7. Create with labels that reflect type and surface area (for example `enhancement`, `frontend`, `quick-win`), then read the issue back and verify key body substrings before reporting.
8. If `gh issue create` fails because a label is missing, search/list issues before retrying to confirm no partial issue was created, then retry with valid labels and verify the final issue.

### Batch website QA issue drafting

When Karan gives a batch of visual/UX complaints for a website and asks to “draft up GitHub issues,” default to drafting implementation-ready issue bodies first, not mutating GitHub immediately, unless he explicitly says to create them. Issue creation is an external repo mutation and needs explicit approval.

Recommended sequence:
1. Search all issues, including closed issues, for duplicates and prior regression context. Call out related closed issues in the draft body when the bug is a follow-up/regression.
2. Inspect the likely component/page files so each issue includes concrete “Likely Files” and, where useful, “Current Code Clue” snippets/classes. This makes the issue ready for a builder agent without over-specifying the fix.
3. Split distinct user-facing failures into separate issues unless one implementation fix clearly covers them (e.g. route scroll restoration for both About and Journal may still be drafted separately if Karan named them separately, with a note that they can share a PR).
4. Use concise, handoff-friendly sections: Bug Description, Current Behavior, Expected Behavior, Likely Files, Recommended Approach, Acceptance Criteria, Validation.
5. For visual/mobile bugs, include exact viewport QA targets when obvious (commonly 375px, 390px, 430px) and require “no horizontal overflow” when nowrap/spacing fixes are involved.
6. Save the drafts to a local markdown file when there are many issues, then summarize titles and ask for explicit approval before creating them on GitHub.

### Follow-up issues extracted from PR notes / human action sections

When the user asks to create an issue from a PR section such as “Setup steps Karan must complete,” “follow-up,” “manual steps,” or “known gaps”:

1. Fetch the referenced PR body, comments, review comments, and reviews — the section may live outside the PR body.
2. If the exact text is not found on the stated PR, search nearby/open PRs for the quoted phrase before asking the user; users may reference the wrong PR number casually.
3. Search existing issues first with `--state all` and keywords from the section to avoid duplicate trackers.
4. Create a separate issue that preserves the operational intent, not just the quoted prose: context, recommended owner/action, concrete tasks, acceptance criteria, and references back to the source PR + original issue when applicable.
5. Label the issue according to the nature of the work. Use `blocked` when the task requires Karan/provider-dashboard/Vercel/account action before code can proceed.
6. Verify the created issue by reading it back with JSON fields (`number`, `title`, `state`, `url`, `labels`, and key body substrings) before reporting success.

For long bodies, write a temp markdown file and use `gh issue create --body-file` to avoid shell quoting problems.

### Follow-up implementation issues after scaffold/approval PRs

When a scaffold issue/PR and later approval/data PR unlock implementation work, use `references/absorbed/github-issues/references/follow-up-implementation-issues.md`. Key rule: re-read the scaffold, source-of-truth approval docs, and repo-local staged skill guidance (`skills/staged-external-skills.md` when present) before creating issues. Include both local Hermes skills and optional staged external skill links in the issue body, with a safety note to review external skill sources before installing or using them.

**With gh:**

```bash
gh issue create \
  --title "Login redirect ignores ?next= parameter" \
  --body "## Description
After logging in, users always land on /dashboard.

## Steps to Reproduce
1. Navigate to /settings while logged out
2. Get redirected to /login?next=/settings
3. Log in
4. Actual: redirected to /dashboard (should go to /settings)

## Expected Behavior
Respect the ?next= query parameter." \
  --label "bug,backend" \
  --assignee "username"
```

**With curl:**

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues \
  -d '{
    "title": "Login redirect ignores ?next= parameter",
    "body": "## Description\nAfter logging in, users always land on /dashboard.\n\n## Steps to Reproduce\n1. Navigate to /settings while logged out\n2. Get redirected to /login?next=/settings\n3. Log in\n4. Actual: redirected to /dashboard\n\n## Expected Behavior\nRespect the ?next= query parameter.",
    "labels": ["bug", "backend"],
    "assignees": ["username"]
  }'
```

### Bug Report Template

```
## Bug Description
<What's happening>

## Steps to Reproduce
1. <step>
2. <step>

## Expected Behavior
<What should happen>

## Actual Behavior
<What actually happens>

## Environment
- OS: <os>
- Version: <version>
```

### Feature Request Template

```
## Feature Description
<What you want>

## Motivation
<Why this would be useful>

## Proposed Solution
<How it could work>

## Alternatives Considered
<Other approaches>
```

## 3. Managing Issues

### Add/Remove Labels

**With gh:**

```bash
gh issue edit 42 --add-label "priority:high,bug"
gh issue edit 42 --remove-label "needs-triage"
```

**With curl:**

```bash
# Add labels
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42/labels \
  -d '{"labels": ["priority:high", "bug"]}'

# Remove a label
curl -s -X DELETE \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42/labels/needs-triage

# List available labels in the repo
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/labels \
  | python3 -c "
import sys, json
for l in json.load(sys.stdin):
    print(f\"  {l['name']:30}  {l.get('description', '')}\")"
```

### Assignment

**With gh:**

```bash
gh issue edit 42 --add-assignee username
gh issue edit 42 --add-assignee @me
```

**With curl:**

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42/assignees \
  -d '{"assignees": ["username"]}'
```

### Updating long issue bodies safely

For long issue descriptions containing code fences, backticks, URLs, or shell-sensitive characters, prefer the GitHub MCP `issue_write(method="update")` tool when available. It avoids shell quoting problems and Hermes security false positives that can block `gh issue edit --body '...'` commands.

If using `gh`, write the body to a temp markdown file and pass `--body-file`; do **not** inline huge markdown bodies in a shell command.

```bash
cat > /tmp/issue-body.md <<'EOF'
## Summary
Long markdown body with `backticks`, URLs, and code fences safely quoted.
EOF

gh issue edit 42 --body-file /tmp/issue-body.md
```

### Commenting

**With gh:**

```bash
gh issue comment 42 --body "Investigated — root cause is in auth middleware. Working on a fix."
```

**With curl:**

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42/comments \
  -d '{"body": "Investigated — root cause is in auth middleware. Working on a fix."}'
```

### Closing and Reopening

**With gh:**

```bash
gh issue close 42
gh issue close 42 --reason "not planned"
gh issue reopen 42
```

**With curl:**

```bash
# Close
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42 \
  -d '{"state": "closed", "state_reason": "completed"}'

# Reopen
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/42 \
  -d '{"state": "open"}'
```

### Linking Issues to PRs

Issues are automatically closed when a PR merges with the right keywords in the body:

```
Closes #42
Fixes #42
Resolves #42
```

To create a branch from an issue:

**With gh:**

```bash
gh issue develop 42 --checkout
```

**With git (manual equivalent):**

```bash
git checkout main && git pull origin main
git checkout -b fix/issue-42-login-redirect
```

## 4. Issue Triage Workflow

When asked to triage issues:

### Avoid Duplicate Trackers Across GitHub and Linear

When the user says notes “probably need to become issues,” first search existing GitHub issues with `--state all` and relevant keywords, not just open issues. Closed GitHub issues may have been migrated to Linear. If a GitHub issue says “Migrated to Linear: TEAM-N,” verify that Linear issue with the Linear skill/API before creating a new GitHub issue. Prefer adding a clarifying comment to the existing active tracker over creating a duplicate. Report the final tracker mapping clearly: e.g. “business-data TODOs → GitHub #21; product-card TODOs → Linear JMD-22.”

When the user remembers a generic idea/automation “saved somewhere” but cannot find it in GitHub/Linear, do not conclude it is missing after tracker searches alone. Search session history/Hindsight, daily logs, wiki pages, and repo docs/plans (`docs/research/`, `plans/`, `deliverables/`) for draft plans that may contain issue bodies marked “not created yet.” Report both the artifact path and whether GitHub issues were actually created.

1. **List untriaged issues:**

```bash
# With gh
gh issue list --label "needs-triage" --state open

# With curl
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?labels=needs-triage&state=open" \
  | python3 -c "
import sys, json
for i in json.load(sys.stdin):
    if 'pull_request' not in i:
        print(f\"#{i['number']}  {i['title']}\")"
```

2. **Read and categorize** each issue (view details, understand the bug/feature)

3. **Apply labels and priority** (see Managing Issues above)

4. **Assign** if the owner is clear

5. **Comment with triage notes** if needed

## 5. Bulk Operations

For batch operations, combine API calls with shell scripting:

**With gh:**

```bash
# Close all issues with a specific label
gh issue list --label "wontfix" --json number --jq '.[].number' | \
  xargs -I {} gh issue close {} --reason "not planned"
```

**With curl:**

```bash
# List issue numbers with a label, then close each
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?labels=wontfix&state=open" \
  | python3 -c "import sys,json; [print(i['number']) for i in json.load(sys.stdin)]" \
  | while read num; do
    curl -s -X PATCH \
      -H "Authorization: token $GITHUB_TOKEN" \
      https://api.github.com/repos/$OWNER/$REPO/issues/$num \
      -d '{"state": "closed", "state_reason": "not_planned"}'
    echo "Closed #$num"
  done
```

## Quick Reference Table

| Action | gh | curl endpoint |
|--------|-----|--------------|
| List issues | `gh issue list` | `GET /repos/{o}/{r}/issues` |
| View issue | `gh issue view N` | `GET /repos/{o}/{r}/issues/N` |
| Create issue | `gh issue create ...` | `POST /repos/{o}/{r}/issues` |
| Add labels | `gh issue edit N --add-label ...` | `POST /repos/{o}/{r}/issues/N/labels` |
| Assign | `gh issue edit N --add-assignee ...` | `POST /repos/{o}/{r}/issues/N/assignees` |
| Comment | `gh issue comment N --body ...` | `POST /repos/{o}/{r}/issues/N/comments` |
| Close | `gh issue close N` | `PATCH /repos/{o}/{r}/issues/N` |
| Search | `gh issue list --search "..."` | `GET /search/issues?q=...` |
