# Bulk job application execution notes

Session pattern captured from Amanda Brewton job-search application work.

## User preference learned

Karan may explicitly prefer execution over tailoring for high-volume job applications:

- Use the provided/master resume as-is.
- Skip per-role resume tailoring and cover letters unless a portal requires them.
- Walk each application to final submit, then ask for approval.
- Approval copy should be compact:
  - brief job title
  - brief job description
  - one pay line
  - one fit line

## Durable workflow

1. **Verify resume source**
   - Confirm the file exists and, if possible, extract text to understand only source-backed facts.
   - Do not infer unsupported facts like salary target, legal status, EEO, or exact revenue quota.

2. **Extract the lead queue**
   - For Google Sheets job lead trackers, fetch grid data with cell hyperlinks/textFormatRuns, not only displayed values.
   - Save a local JSON/CSV queue with row numbers and apply URLs.
   - Deduplicate by URL, then by company + role.

3. **Process leads in order**
   - Check the live apply URL.
   - Mark dead states precisely: expired, closed, not available, redirected to unrelated lower-quality roles, or employer page error.
   - Prefer direct employer apply pages over aggregators if search reveals them.

4. **Prepare viable applications**
   - Fill source-backed contact and resume facts.
   - Use transparent wording when a field asks for a metric not present in the resume rather than inventing a number.
   - Upload resume and verify selected filename.
   - Stop before submit for approval.

5. **Approval prompt shape**

```md
## Approval needed: Company — Role

**Job title:** Role — Company
**Brief description:** One concise sentence.
**Pay:** Pay/range/source note.
**Fit:** X/10 — one concise reason and any stretch caveat.

Filled: short bullet list of what was entered.
Reply “approve <company>” and I’ll submit, verify, then continue.
```

6. **Post-submit verification**
   - Wait for confirmation.
   - Quote the exact confirmation text.
   - Update the local tracker with `status=submitted`, `submitted_at`, and `verification`.

## Portal-specific tactics

- **Google Forms file upload:** The Google account used for upload/submit may be recorded. Warn before final submit if it is not the applicant’s account.
- **Playwright file uploads:** If upload fails because the source file is outside allowed roots, copy the resume to the Playwright output/upload directory and upload from there.
- **Workable:** Can usually upload by setting the hidden `input[type=file]` directly; verify the filename appears before submitting.
- **SuccessFactors / Workday-like portals:** Often require account creation, passwords, salary expectations, work authorization, age confirmation, EEO/veteran/disability, SMS opt-in, and terms. Stop and gather reusable defaults; do not guess.
