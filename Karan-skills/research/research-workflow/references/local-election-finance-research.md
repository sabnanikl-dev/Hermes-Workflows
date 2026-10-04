# Local-election campaign-finance research

Use for neutral candidate research involving county/local reporting portals.

- Treat the supplied ballot as roster scope, then verify identities against official qualifying lists or published sample ballots. Preserve exact supplied names and distinguish nonpartisan ballot status from partisan endorsements.
- Read an election-law change's effective-date section before alleging a contradiction with current ballot labels; enacted legislation may first apply in a later cycle.
- Start with the jurisdiction's candidate-information page and public finance portal. County candidates may file locally rather than in the statewide search.
- For EasyVote portals, inspect the public browser resource requests and page bundle to discover the jurisdiction's anonymous filer/document index. Use only endpoints observed from the public application; do not guess credentials or reuse private tokens. A publicly exposed `filer/documentsearch/<jurisdiction-id>` response can associate exact candidates, committees, offices, document IDs and submission labels.
- Public document downloads may use `documents/<document-id>/viewfinalredactedpdf`. Use the redacted public document, never attempt to reconstruct unredacted information. The browser can open a blob that obscures its source URL; the application's public request list or bundle can reveal the download endpoint.
- Check office and committee identity before combining records. One candidate can have a former-district account and a separate account for a different office under a legal-name variant.
- Prefer amended reports over their originals for the same reporting period. Preserve both for audit evidence but never add them together.
- PDF table extraction can repeat a single amount across every address/occupation row and lose checkbox alignment. Count a donor record once, not every occurrence of the amount. Use selected readable entries when complete reconciliation is not defensible, and label them examples rather than largest donors.
- Label cash gifts, in-kind support, candidate loans, loan repayments, other debt, and outside independent expenditures separately. Cumulative contribution-summary totals can include loans and carryovers; do not call them outside donations.
- Distinguish a report's signature/date, public index upload/submission date and legal filing deadline. A later public upload alone does not prove late filing or an ethics violation.
- Historical exemption affidavits do not establish current-cycle spending levels or current filing obligations. Missing reports or a missing candidate in one portal do not prove zero money, noncompliance or a clean record.
- Save exact source URLs, readable excerpts, dates and retrieval scope before drafting. Keep personal addresses and contact details out of the voter-facing synthesis even when they appear in public source PDFs.
