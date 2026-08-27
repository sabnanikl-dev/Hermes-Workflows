# Trust-Center and HIPAA Notes

Research example: Plaud + Drata, checked 2026-08-08. Use this as a pattern for future vendor assessments, not as permanent current-state truth about either company.

## Recursive trust pattern

A vendor can link from its own compliance page to a hosted trust center. The host may be a legitimate GRC/compliance-automation company while still not being the auditor or regulator. Verification therefore requires following the chain:

`vendor claim → trust-center artifact → named independent issuer → exact scope/dates/exceptions → observed behavior/contract`

The existence of a locked trust-center document is not evidence of what is inside it.

## Drata-style request gates

Drata's public help documentation described support for:

- Private compliance reports and policies
- Name/email access requests
- NDA acceptance
- Manual approval or denial
- Email delivery to the requester
- Watermarking
- Time-limited access
- Approved email addresses/domains
- CRM matching by email/domain and opportunity context

This supports two simultaneous conclusions:

1. Gating detailed SOC 2 or penetration-test material can have a legitimate confidentiality purpose.
2. The request creates another data-processing relationship and can potentially enter a vendor's procurement or sales workflow.

Do not claim a specific customer enabled CRM enrichment unless verified. Describe it as a platform capability.

Sources:

- https://help.drata.com/en/articles/8067477-submitting-and-approving-requests
- https://help.drata.com/en/articles/8067507-document-access-management
- https://help.drata.com/en/articles/9797456-streamline-your-documentation-access-request

## HIPAA wording

HIPAA does not provide a government-issued certificate analogous to an accredited ISO certificate. Private assessors can issue reports, attestations, or badges, but “HIPAA certified” or “HIPAA obtained” is insufficient without:

- Assessor identity and qualifications
- Assessment criteria
- Exact legal entity and product scope
- Assessment dates
- Exceptions or qualifications
- Subprocessors included or excluded
- A BAA covering the exact intended service where required

Authoritative starting point:

- HHS FAQ: https://www.hhs.gov/hipaa/for-professionals/faq/2003/are-we-required-to-certify-our-organizations-compliance-with-the-standards/index.html

## Plaud example findings

At the time checked, Plaud's public pages claimed SOC 2 Type II, ISO 27001/27701, and HIPAA status and linked to a Drata trust-center URL. Its public trust/privacy materials also described cloud processing, LLM subprocessors, cloud-sync behavior, limited personnel access scenarios, and some advertising/attribution use of identifiers.

These materials were useful for reconstructing stated data flow but did not independently prove absence of undisclosed collection. The correct bounded conclusion was that the public badges and hosted portal were insufficient on their own for a healthcare-risk decision.

Sources:

- https://www.plaud.ai/pages/drata
- https://www.plaud.ai/pages/trust
- https://www.plaud.ai/policies/privacy-policy

## Consumer-readable reporting pattern

For future reports, distinguish:

| Level | Meaning |
|---|---|
| Claim only | Vendor says it |
| Artifact located | A report/certificate exists |
| Independently validated | Issuer, scope, dates, and status checked |
| Behavior observed | Technical/data-handling behavior reproduced |
| Contractually committed | Exact service is covered by DPA/BAA/terms |

A “privacy nutrition label plus receipts” is more useful than a single score because it exposes evidence quality, scope, and freshness.
