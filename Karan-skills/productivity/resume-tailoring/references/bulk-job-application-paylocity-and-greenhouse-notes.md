# Bulk job application portal notes: Paylocity + Greenhouse

Session-derived notes from Amanda job-application execution. Keep this as a portal tactics reference, not a task log.

## Greenhouse email-code gates

- Greenhouse may send an 8-character security code after the first submit click.
- Enter the code exactly and verify each one-character input; case matters, and ambiguous glyphs (`I`/`l`, `O`/`0`) are common.
- If a first attempt was mistyped and the page then reports `Incorrect security code` or `Invalid security code`, do not keep hammering retries.
- If no resend path appears, a clean reload/refill of the same already-approved Greenhouse role can sometimes submit directly and clear the wedged code gate.
- Verification target: `/confirmation` URL and body text like `Thank you for applying. Your application has been received.`

## Greenhouse stale job IDs

- A direct Greenhouse job URL can redirect to the company board with `error=true` even when the role is still active under a new job ID.
- Before marking expired, search the board text/links for the same role title and navigate to the new `jobs/<id>` URL.

## Greenhouse React-select widgets

- Typing text into combobox inputs is not enough; click the real `.select__option` item.
- Pronoun/source values may be formatted differently from the obvious typed value, e.g. `She / Her` instead of `She/her`, `LinkedIn Job Post` instead of `LinkedIn`.
- Always verify `document.querySelectorAll(':invalid')` is empty before stopping for approval or clicking submit.

## Goodwin / Salesforce Sites forms

- Goodwin job pages can route to `goodwinrecruiting.my.salesforce-sites.com/jobboard/Jobregister?...`.
- Fill email/name/phone/zip/country, closest remote availability, upload resume, verify `C:\\fakepath\\<resume>.pdf`, then stop at final Submit for approval.
- The click may time out while navigation continues; wait and verify the thank-you page/body: `We have received your job application`.

## Paylocity applications

- Step 1 may require applicant full address: Address Line 1, city, county, state, zip. Do not infer or fake street address from resume city/zip.
- Resume parsing can auto-create Work History/Education blocks with required nested address fields. If those parsed blocks are incomplete and not necessary for the application, delete them rather than inventing employer or school addresses.
- Custom select widgets can show visible values (`United States`, `Georgia`) while the hidden input stays empty and invalid. Re-check `:invalid` after selection. Typing the option and pressing Enter may satisfy the hidden input; visible text alone is not proof.
- Step 3 may require references: two references with name + phone + Personal/Work type; email may be optional. Block and ask the user for real references.
- If the user provides references without specifying Personal/Work, save the real reference details to a local restricted project artifact for future use, but do not invent the type. Enter name/phone/email and leave the optional type blank when the portal allows it; if the portal requires a type, ask for clarification or use an explicitly user-approved default.
- Paylocity final review can require an acknowledgement checkbox certifying the application is true/complete. Treat that checkbox as the final-submit approval boundary: stop there, summarize title/pay/fit/assumptions, and only check+submit after explicit approval.

## Greenhouse modern custom fields / Lantern-style forms

- Some Greenhouse boards use custom comboboxes that display selected visible text while validation still says `This field is required`. Do not trust visible labels alone; inspect required-field messages after submit-attempt/draft validation and use accessibility snapshots to identify which comboboxes still have validation paragraphs.
- For fields like degree, non-compete, work authorization, sponsorship, referral, location requirements, and state of residence, choose from the real option list, not merely typed text. If validation persists, stop and mark the application as partially filled rather than forcing a final submit or using unsupported DOM mutation.
- If a required referral flow is answered `No`, but conditional referral-name/relationship fields remain required, use explicit neutral values like `N/A` only when the field label says “if applicable”; otherwise ask.
- Greenhouse may show a reCAPTCHA iframe on the page before final submit. Do not bypass it; if the form reaches final submit with a CAPTCHA/manual verification gate, ask the user to complete it or submit manually, then verify confirmation before marking submitted.

## Workday applicant accounts

- Workday applications often require creating/signing into an applicant account before resume upload. Treat account creation/password choice as a credential-bearing approval boundary: stop, mark the lead blocked on Workday account/credentials, and ask the user before creating or using credentials.

## Approval-gated default

- External application submission remains approval-gated. Fill up to final submit, ask with compact title/description/pay/fit, submit only after approval, then verify confirmation text before reporting success.
