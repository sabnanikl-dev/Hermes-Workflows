# GBP Read-Only API Baseline

Use this when a local SEO source-of-truth needs Google Business Profile fields verified from API/dashboard state. This is a read-only pattern; public GBP edits, media uploads, category/service changes, Q&A, posts, and review replies require explicit approval.

## Prerequisites

- OAuth user consent includes `https://www.googleapis.com/auth/business.manage`.
- The active token has been refreshed/reissued after adding the scope.
- The active token/profile identity has been verified against the intended account for the task before *any* Google API call. If the token belongs to the wrong account, stop, quarantine/remove the active token, and reauthorize the correct account before continuing.
- Google Cloud APIs are enabled in the same project as the OAuth client, especially:
  - My Business Account Management API: `mybusinessaccountmanagement.googleapis.com`
  - My Business Business Information API: `mybusinessbusinessinformation.googleapis.com`
  - Business Profile Performance API: `businessprofileperformance.googleapis.com` when reporting metrics
- Existing Workspace/Google OAuth stack is preferred over creating a separate credential system, unless the user explicitly wants separation.

## Smoke test sequence

1. Verify the signed-in identity with the OAuth/userinfo/profile endpoint or equivalent CLI/profile command; confirm the email matches the intended agent/workspace account.
2. Verify token scopes include `business.manage`.
3. Call Account Management `accounts.list`:
   - REST: `GET https://mybusinessaccountmanagement.googleapis.com/v1/accounts`
   - Python client: `build("mybusinessaccountmanagement", "v1", credentials=creds).accounts().list().execute()`
4. For each returned account, call Business Information `accounts.locations.list` with a read mask.
5. Match the target business by title, website URI, phone, place metadata, or user-provided GBP/dashboard context.
6. Output JSON or markdown evidence; do not mutate GBP.

## Suggested Business Information read mask

Use a field set like:

```text
name,title,websiteUri,phoneNumbers,categories,regularHours,specialHours,moreHours,openInfo,profile,serviceArea,serviceItems,storefrontAddress,latlng,metadata,relationshipData,labels,languageCode
```

## Source-of-truth fields to update

Capture these as API-derived observations, not approved public changes:

- GBP account resource name
- Location resource name
- Location title
- Website URI
- Primary and secondary categories
- Phone numbers
- Service-area vs storefront/address posture
- Regular/special/more hours
- Open status and opening date if present
- Business profile/description
- Service items
- Labels/store code/language code if present
- Metadata such as maps/place/profile state fields returned by the API

## Troubleshooting patterns

- `ACCESS_TOKEN_SCOPE_INSUFFICIENT`: re-run the OAuth setup/consent flow after adding `business.manage`; verify the saved token now includes the scope.
- `SERVICE_DISABLED`: enable the named API in the exact Google Cloud project used by the OAuth client, then wait for propagation and retry. Do not record this as a durable tool failure.
- Public Google/GBP share links may trigger CAPTCHA or anti-bot pages. Record stable share links/redirect IDs if visible, but use API/dashboard data for baseline fields.
- Google My Business legacy v4 discovery may not be available through the standard Python discovery path; prefer Account Management v1 and Business Information v1 for baseline profile reads.

## Guardrails

- Read-only API calls are safe to run under this workflow.
- Any write endpoint or dashboard/public-profile mutation requires explicit user approval.
- Keep unknowns and conflicts visible for human decision, especially address privacy, package/service naming, categories, descriptions, review policy, and claims.
