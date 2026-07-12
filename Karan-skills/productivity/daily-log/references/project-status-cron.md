# Project Status Cron

## Purpose
Automated weekday/on-demand review of the Hermes Brain project dashboard. Keep the wiki's project snapshot aligned with durable project state without recreating retired tracker files.

## Canonical Files
- Dashboard: `~/obsidian-vault/hermes-brain/wiki/shared/projects/Project Status.md`
- Archive: `~/obsidian-vault/hermes-brain/wiki/shared/projects/Archived Project Summaries.md`
- Activity log: `~/obsidian-vault/hermes-brain/log.md`
- Daily logs: `~/obsidian-vault/hermes-brain/logs/YYYY/MM/YYYY-MM-DD.md`

Retired paths that must **not** be recreated:
- `~/obsidian-vault/hermes-brain/shared/`
- `~/obsidian-vault/hermes-brain/shared/projects/*.md`
- `ARCHIVED.md` outside the canonical archive path above

## Execution Workflow

### Step 1: Determine review window
1. Determine today and the previous weekday.
2. Read the previous weekday daily log and today's log if present.
3. Read 2-3 prior daily logs only if needed for continuity.
4. Use `session_search()` recent browse first, then targeted discovery queries for project-changing work since the last run.
5. When scrolling a discovered session, use the returned `match_message_id`; do not assume message id `1` exists in that session.

Focus on durable state changes:
- completed or merged work that has been verified
- new active workstreams
- blockers / waiting-on items
- paused or intentionally stopped work
- strategic decisions that affect project direction
- changed next actions

Do not copy raw chat transcript detail into the dashboard.

### Step 2: Read only canonical status files
Read:
- `wiki/shared/projects/Project Status.md`
- `wiki/shared/projects/Archived Project Summaries.md`

Do not read or create retired root tracker files. If a root `shared/` tree reappears, treat it as a hygiene issue to report/fix, not as source of truth.

### Step 3: Verify before marking done
Do not trust notes alone for implementation state.

- For GitHub PRs: use `gh pr view <N> --json state,mergedAt,url,title,headRefName` or REST `gh api repos/<owner>/<repo>/pulls/<N> --jq '{state, merged, merged_at, merge_commit_sha}'` before marking merged/completed.
- If verification is unavailable, mark the item pending verification rather than completed.
- For cron/job decisions, use the best available job state if the tool is available; otherwise cite only the verified session outcome and avoid inventing scheduler state.
- For env vars/API keys, report only `PRESENT`/`MISSING`; never print values.

### Step 4: Update dashboard conservatively
Update only rows supported by logs/sessions and, where relevant, live verification.

Allowed changes:
- move verified completed items to `Completed (Recent)`
- add/update active work rows with concise next actions
- add blockers/waiting-on items
- add paused/cold rows when the user explicitly pauses or de-prioritizes a workstream
- update `updated:` frontmatter and visible `Updated:` date
- refresh verification snapshot dates when actually checked

Keep dashboard rows concise. Linear/GitHub/project repos own granular task details; the wiki summarizes durable state.

**Busy repo batching:** when one project has many closely related verified PRs/issues since the last sync (for example a GodMode self-dogfood reliability burst), prefer one grouped `Completed (Recent)` row plus an updated active project row instead of one row per PR. Archive aged individual rows separately, but keep the dashboard readable by summarizing the durable outcome, representative PRs/issues, verification category, and next action.

### Step 5: Archive aged completed rows
If `Completed (Recent)` rows are older than the active recent window (normally 3 days), append them to `Archived Project Summaries.md` and remove them from the active dashboard. Do not create `ARCHIVED.md` or root `shared/` files.

### Step 6: Log the sync
If the dashboard/archive changes, also:
1. Append a concise row to `log.md`.
2. Create/update today's daily log with:
   - what was reviewed/verified
   - wiki files changed
   - decisions reflected
   - next steps
3. Verify today's daily log length with Python `len(path.read_text())` and keep it under 3,000 chars.

If no dashboard/archive changes were needed, do not create a daily log solely for the check; final output can say no updates were needed.

### Step 7: Verify closeout
Before final report:
- confirm touched files exist
- confirm key dashboard sections are present: `Verification Snapshot`, project domains, `Completed (Recent)`, `Archived`, `Paused / Cold`
- confirm root `shared/` is absent when doing root-hygiene-sensitive syncs
- confirm daily log length if one was created/updated

## Output Style
Brief cron report:
- files updated
- 3-5 bullets of dashboard changes
- verification performed
- if no files changed, state the reason

Use `[SILENT]` only when the job's delivery instructions explicitly require silence and there is genuinely nothing new to report.
