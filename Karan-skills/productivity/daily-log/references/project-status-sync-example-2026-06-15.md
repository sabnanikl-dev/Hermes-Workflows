# Project Status Sync Example — 2026-06-15

Use this as a compact example for unattended weekday Project Status syncs.

## Pattern that worked

1. Determine today and previous weekday with local Python/date tooling.
2. Read only the relevant inputs:
   - latest daily logs, prioritizing previous weekday and today if present;
   - `wiki/shared/projects/Project Status.md`;
   - `wiki/shared/projects/Archived Project Summaries.md`;
   - `log.md` only if edits are made.
3. Browse/search recent sessions for durable project state, not raw transcript details.
4. For GitHub-owned work mentioned in logs/sessions, do a late-closure verification pass before editing:
   - `gh issue view <n> --json state,closedAt,closedByPullRequestsReferences`
   - `gh pr view <n> --json state,mergedAt,mergeCommit,statusCheckRollup,closingIssuesReferences`
   - `gh issue list --state open` for remaining next actions.
5. Update the dashboard only for durable state:
   - active project rows and next actions;
   - completed-recent rows for newly verified merged/closed work;
   - blockers/waiting-on items;
   - verification snapshot dates.
6. Archive completed-recent rows older than the active window into `Archived Project Summaries.md`; do not recreate root `shared/` or `ARCHIVED.md`.
7. If dashboard/archive changed, update `log.md` and create/update the current daily log.
8. Verify with Python:
   - touched files exist;
   - expected headings/key phrases are present;
   - daily log `len(path.read_text()) < 3000`;
   - root `shared/` remains absent.

## Pitfall

Do not use brittle verification needles copied from your intended prose if the file uses different but correct wording. Verify the actual durable facts/key headings that matter (for example `issue #43 closed`, `Remaining open core issues: #38...`, `Dashboard Rows Archived YYYY-MM-DD`) rather than forcing unnecessary re-edits to satisfy an exact phrase.

## Example outcome

On 2026-06-15, the sync verified GodMode PRs #44/#50/#51/#52 as merged and issues #35/#39/#41/#43 as closed, refreshed remaining GodMode next actions (#38/#40/#42), archived aged JMD completed rows, updated `log.md`, created the daily log, and verified root `shared/` stayed absent.
