# Bulk Job Application Portal Verification Notes

Session-derived notes for job-application batches where portals add human-verification, email-code, or recruiter-site hurdles after a form is otherwise complete.

## Greenhouse email security code after submit

Some Greenhouse job boards allow the full application to be filled and the submit button clicked, then pause on an email security-code challenge:

- The page may say: `A verification code was sent to <email>. To submit your application, enter the 8-character code to confirm you're a human.`
- The code fields can be eight separate one-character inputs (`security-input-0` through `security-input-7`).
- Preserve exact case and watch ambiguous characters (`I` vs `l`, `O` vs `0`). Verify the values in the fields before retrying.
- If a correct-looking code returns `Incorrect security code` / `Invalid security code`, do **not** keep hammering retries. Likely causes are expiration, invalidation after a failed attempt, or a newer code replacing the old one.
- Best next move: trigger a fresh code if possible and ask the user to send the newest code immediately; otherwise have the applicant submit that portal manually from their email/browser session.
- If there is no visible resend button and the code path seems wedged, try a clean Greenhouse application attempt: reload/navigate to the job URL, refill from the saved resume/defaults, select React-select options again, verify `:invalid` is empty, then submit. In at least one Roo/Greenhouse case, a fresh refilled form reached `/confirmation` directly without another email-code gate. Only do this when it does not create duplicate-submission risk beyond the user-approved role, and verify the final confirmation text before marking submitted.

## Paylocity full-address requirement

Paylocity applications can require full postal address fields on Step 1: address line 1, city, county, state, and zip. Do not infer or fabricate a street address from resume city/zip context. If street address is missing, mark the role blocked/pending-address and ask the user for Amanda's full address; city/county/state/zip may be prefilled only when user-provided or already known from a trusted source.

## Greenhouse / React-select dropdowns

Greenhouse forms often use React-select inputs rather than native `<select>` controls. Filling the visible input text is not enough; the hidden required input remains invalid unless an option is selected.

Reliable pattern:
1. Click the combobox input.
2. Type a search term.
3. Wait for `.select__option` options.
4. Click the matching option text.
5. Check `:invalid` before final approval.

For pronoun fields, option labels may include spaces/slashes (`She / Her`), so searching `She/her` can return no options. Open the menu and inspect options if selection fails.

## Greenhouse resume upload verification

After upload, Greenhouse may remove the original resume file input from the normal query results and show the filename in body text instead. Verify by page text such as `amanda_brewton_resume_2026.pdf`, not only by `input[type=file]` value.

## Goodwin Recruiting / Salesforce job board

Goodwin Recruiting role pages may route to a Salesforce Sites application form. The form can be simple and submit directly to a Goodwin thank-you page.

Useful checks:
- Verify form fields contain email/name/phone/zip/country and selected remote availability.
- Upload resume and verify fakepath/filename before approval.
- After submit, success confirmation may be a Goodwin page with: `Thank You! We have received your job application.`

## Approval-gated handling

Even when an application is fully filled, treat CAPTCHA, invisible reCAPTCHA, hCaptcha, and email security-code checks as manual/human verification gates. Do not report success until a confirmation page or message is actually visible after the gate.
