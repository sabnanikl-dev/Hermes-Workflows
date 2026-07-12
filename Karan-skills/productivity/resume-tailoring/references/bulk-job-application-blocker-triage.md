# Bulk job application blocker triage notes

Use when continuing Amanda/Karan job-application queues and many roles are not immediately submit-ready.

## What to do when the next role blocks

- Do not stop the whole queue after the first non-submittable role unless the user explicitly asked to focus on that one role.
- If a role is blocked by missing reusable defaults, account creation, CAPTCHA, or portal sign-in, record it in the local status ledger and keep triaging/filling later leads.
- Prefer progress categories over vague `blocked` labels:
  - `blocked_missing_required_defaults` — legal/personal/form defaults needed before honest completion.
  - `blocked_manual_recaptcha` / `blocked_manual_hcaptcha` — human verification needed before submit.
  - `blocked_successfactors_account_required` / `blocked_workday_account_required` — account creation/sign-in required.
  - `blocked_ziprecruiter_account_or_alerts` — ZipRecruiter Quick Apply requires candidate account/email flow or alert consent.
  - `blocked_missing_zip` / `blocked_missing_linkedin_and_defaults` — a specific source fact is missing.
  - `expired_not_available`, `closed`, `expired_not_accepting` — verified dead posting.
- Preserve the exact verification phrase/source in `reason` (for example, “This job is closed to new applications”, “This job is no longer available”, “No longer accepting applications”).

## Reusable default packet gaps that repeatedly block portals

Collect once when possible instead of asking piecemeal every application:

- Full home address and ZIP/postal code.
- LinkedIn URL, or explicit permission to enter `N/A` / leave blank when allowed.
- Education/degree/school defaults.
- Non-compete / non-solicitation answer.
- Work authorization and sponsorship answers.
- Start date / notice period.
- Age 18+ confirmation.
- SMS recruiting opt-in preference.
- Relocation willingness and preferred locations.
- Employment gap answer.
- Prior employer / friends-or-relatives-at-company defaults.
- Permission and credential strategy for Workday, SuccessFactors, iCIMS, ZipRecruiter, and similar account-gated portals.
- EEO, veteran, disability, race/ethnicity, gender, sexual orientation, and demographic-consent choices if the user wants those answered rather than skipped/declined.

## Portal-specific notes

- JazzHR / ApplyToJob may allow contact fields and resume upload, then block final submit on visible reCAPTCHA. Mark as manual CAPTCHA rather than claiming ready/submitted.
- iCIMS can trigger hCaptcha immediately after entering the email, before any actual application fields are available. Mark as manual hCaptcha and move on.
- ZipRecruiter Quick Apply can introduce account/email flows and job-alert consent. Treat that as approval-gated; do not proceed just because the posting is active.
- Greenhouse/Ashby postings often look simple but require legally sensitive defaults or source-backed facts such as LinkedIn, country, sponsorship, restricted-country status, SMS consent, travel willingness, privacy/AI acknowledgements, and demographics consent.
- SuccessFactors/Workday account requirements are not dead postings; mark them account-gated with the target role still active.

## Ledger practice

- Update `_application_ops/application_status.json` as soon as a role is classified, even if no application was submitted.
- If a role was partially filled/tested, say exactly what was verified (e.g. resume upload showed `C:\\fakepath\\...pdf`) and what stopped submission.
- Avoid storing credentials, sensitive demographic answers, or unnecessary PII in the ledger; reference “provided defaults” where possible.
