# Job application final-submit workflow notes

Use when Karan asks Hermes to apply to saved roles for Amanda/Karan from a tracker or job-lead sheet.

## Pattern learned

1. Verify the resume source exists and extract enough text to answer common form questions honestly.
2. Pull the saved lead list including hidden hyperlink URLs from Google Sheets; preserve row numbers and de-dupe by URL before processing.
3. Triage live status before filling:
   - 404 / “page does not exist” / “job expired” / “closed to new applications” = record as expired/closed.
   - If an old aggregator link is active but blocks apply, search the exact company + title for an employer-hosted or ATS link.
4. Fill only viable applications to final submit, using the resume as-is when the user says not to tailor.
5. Stop and ask for approval per role before submission.
6. After approval, submit and verify the confirmation message/page.
7. Maintain a local status artifact for batch continuity, e.g. `_application_ops/application_status.json` near the resume/project folder.

## Approval prompt shape

Keep it short and decision-ready:

```md
## Approval needed: Company — Role

**Job title:** Role — Company
**Brief description:** One sentence on responsibilities.
**Pay:** Official range if listed; otherwise sheet/source estimate with caveat.
**Fit:** Rating + one line explaining why it fits or where the stretch is.

Filled: concise bullet list of completed fields and any caveats.
Reply “approve <company>” to submit.
```

## Default-answer packet for bulk applications

Before attempting high-volume final-submit work, collect reusable defaults once so active portals do not repeatedly block the queue:

- street address/city/state/ZIP
- salary expectation or acceptable range
- start date / notice period
- work authorization and sponsorship answer
- 18+ confirmation
- schedule and shift availability
- prior-employer defaults for common portals
- EEO/race/gender/ethnicity, veteran, and disability responses, if the user wants them answered rather than declined
- SMS/recruiter text opt-in preference
- account-creation policy and password strategy

If the user provides a job-portal password and asks to save it locally, write it to a separate file in the project folder with restrictive permissions (`chmod 600`). Do **not** put passwords in JSON status trackers, chat summaries, approval prompts, or final reports.

## Upload/browser quirks

- Playwright MCP can only upload files inside its allowed roots. If the resume path is outside allowed roots, copy it to an allowed upload path such as `.playwright-mcp/uploads/` and upload that copy.
- Google Forms file upload requires modal state: click the form’s Upload button, then click the picker’s Browse button, then call file upload. Calling file upload before the file chooser is active fails.
- Workable forms can often be handled directly with `page.setInputFiles('input[type="file"][data-ui="resume"]', copied_resume_path)` when normal clicks are intercepted.
- Phenom/Four-Seasons-style application flows may parse resume data, then require a multi-step sequence: My Information → My Experience → Application Questions → Voluntary Disclosures → Self Identify → Review. Hidden or custom widgets sometimes ignore generic evaluate-based value setting; use stable IDs/labels with Playwright locators, force-check custom checkboxes/radios when needed, and verify `:invalid` fields before retrying Next.
- SuccessFactors-style portals may enforce password rules before final submit. Check the visible rule text early (for example, max 18 characters); if the user-provided shared password violates it, stop and ask for a compliant password rather than inventing a new one.
- Lever forms can contain long custom-question sections and hCaptcha. Fill required custom answers from source-backed adjacent experience, verify `:invalid` is empty, then stop at `Submit application`; if hCaptcha is visible, tell Karan it may require manual completion after approval.
- On final review pages, verify both the visible `Submit` button and the attached resume filename before asking for approval.

## Honesty guardrails

- Do not invent exact quota/revenue targets, LinkedIn URLs, work authorization details, sponsorship answers, demographics, or legal attestations.
- If a required question asks for a fact not present in the resume/source material, use a transparent answer or stop for user input if the answer has legal/personal significance.
- Cover letters and tailored answers are skipped when the user explicitly says to skip tailoring.
- Treat sensitive contact details, addresses, EEO answers, and portal credentials as form-fill data only. Avoid repeating them in summaries unless the user specifically asks; refer to them as “provided defaults” or “Amanda’s contact details” instead.