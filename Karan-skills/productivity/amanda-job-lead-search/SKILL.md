---
name: amanda-job-lead-search
description: Use when running Amanda's recurring job-lead search.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [jobs, research, google-sheets, cron, amanda]
---

# Amanda Job Lead Search

## Purpose
Run Amanda Brewton's unattended weekday job search without runaway web-search loops. The Google Sheet is the source of truth.

## Stable resources
- Resume: `/Users/creator/projects/Resume/Amanda Job Search/Amanda Brewton Resume 2026.pdf`
- Candidate summary fallback: Atlanta event/venue manager with weddings, corporate/social/public events, venue tours, proposals/packages, catering/bar upsells, client relationships, F&B logistics, staffing, invoicing, vendors, timelines, styling, and event-day operations. Tools include HoneyBook, AllSeated, Aisle Planner, Caterease/Caterese, Prismm, Adobe, Canva, and Procreate.
- Spreadsheet ID: `1vn5lNu0psLDLt3093tb6SDTK-ChW3_HkFf4nILM0g64`
- Tab: `Job Leads`
- Sheet URL: `https://docs.google.com/spreadsheets/d/1vn5lNu0psLDLt3093tb6SDTK-ChW3_HkFf4nILM0g64/edit`
- Discovery script: `/Users/creator/.hermes/scripts/amanda_job_lead_discovery.py`

## Non-interactive execution contract
Do not ask questions. Do not create cron jobs. Do not apply to jobs, send outreach, or change Sheet permissions. Append only verified, new leads.

### 1. Preflight
1. Get today's Eastern date with `date`.
2. Run `gws auth status`. Continue only when it reports `token_valid: true`, user `karanagent20@gmail.com`, and Sheets/Drive scopes.
3. Read existing data with:
   `gws sheets +read --spreadsheet 1vn5lNu0psLDLt3093tb6SDTK-ChW3_HkFf4nILM0g64 --range 'Job Leads!A:K' --format json`
4. The embedded profile is sufficient. If reading the resume fails, continue from the profile; never search broadly for a replacement resume.

### 2. Bounded discovery
Use the scheduler-injected discovery JSON when it is present; do **not** run the script again. If no discovery JSON was injected, run the discovery script exactly once. The script performs a fixed maximum of nine Serper requests and emits at most 35 deduped candidates.

Hard limits for the entire cron run:
- `web_search`: **maximum 3 calls total**, and only if the discovery script returns zero candidates or a specific finalist needs one direct-link lookup.
- Never repeat an identical query or retry a failed web-search query.
- `web_extract`: at most 2 batches, up to 5 URLs per batch.
- Browser: at most 3 finalist pages, only when extraction is insufficient.
- Do not run per-role salary searches. Prefer the official range. Otherwise use one clearly labeled local-market estimate from available search snippets, or write `Employer did not list pay; verify during screening.`

Stop researching once 4-5 good non-duplicate finalists are verified. If fewer qualify, append fewer. Quality beats quota.

### 3. Eligibility and verification
Prefer direct employer/ATS links. Aggregators are discovery fallbacks only. A lead qualifies only when:
- the role page or reliable current source shows it is open/recent;
- title/responsibilities match event management, venue operations, catering/event sales, meetings/conferences, or a credible corporate-events pivot;
- geography is Atlanta metro, nearby Georgia for a strong fit, or genuinely remote US;
- it is not a server/staff-only role or clearly below Amanda's level unless marked backup;
- Company + Role + normalized Apply URL are not already in the Sheet.

Fit score uses: 35% responsibilities, 25% domain, 20% tools/process, 10% seniority, 10% practical constraints.

### 4. Prepare and append
Columns in order:
1. Date sourced
2. Priority
3. Company
4. Role
5. Location
6. Apply / job link as `=HYPERLINK("url", "label")`
7. Brief job description
8. Salary estimate
9. Fit rating, e.g. `8.8/10`
10. Why Amanda fits
11. Notes

Build one JSON array containing all rows and append once with the raw Sheets API so formulas are interpreted:

`gws sheets spreadsheets values append --params '{"spreadsheetId":"1vn5lNu0psLDLt3093tb6SDTK-ChW3_HkFf4nILM0g64","range":"Job Leads!A:K","valueInputOption":"USER_ENTERED","insertDataOption":"INSERT_ROWS","includeValuesInResponse":true}' --json '{"majorDimension":"ROWS","values":[...]}' --format json`

Do not append one row at a time. Set every field explicitly.

### 5. Verification
A successful command is not enough.
1. Capture the append response's `updatedRange` and `updatedRows`.
2. Read back that exact range with `gws sheets +read` and verify every intended Company, Role, and URL/formula landed.
3. Verify Amanda's writer access read-only:
   `gws drive permissions list --params '{"fileId":"1vn5lNu0psLDLt3093tb6SDTK-ChW3_HkFf4nILM0g64","fields":"permissions(id,type,role,emailAddress)"}' --format json`
4. Never claim the Sheet was updated unless append response and readback both prove it.

## Final response
Keep Discord output short.

On verified append:
`Google Sheet updated. Go check what’s new: <sheet URL>`
`Added N new roles today. Amanda's editor access was verified.`

On zero qualifying leads after a healthy search:
`Google Sheet checked. No new non-duplicate high-fit roles found today: <sheet URL>`

On a blocker:
`Job lead search did not update the Sheet today: <specific failed preflight/source/verification step>. <sheet URL>`

Never surface generic tool-loop text. Do not say `Google Sheet updated` after a blocked or no-write run.
