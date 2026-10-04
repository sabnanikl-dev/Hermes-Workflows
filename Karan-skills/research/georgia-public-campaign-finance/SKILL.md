---
name: georgia-public-campaign-finance
description: "Use when researching Georgia campaign-finance filings."
---
# Georgia public campaign-finance retrieval

Use read-only public sources. Preserve request bodies and query scope, not credentials or donor addresses.

Start with Georgia Ethics records search and the PeachFile public interface. Observe current request schemas before calling APIs. Observed base: `https://api-peachfile.ethics.ga.gov/api/`.

Public POST routes:
- `PublicFilerDetails/GetCandidateDetails`: match office, candidate, committee and GUID.
- `PublicFilerDetails/GetFilerDetailsById`: identity verification.
- `PublicTransactionDetails/GetTransactionDetails`: contribution query and counts.
- `PublicGridDownload/DownloadPublicGridData`: CSV exports.
- `PublicTransactionDetails/GetPublicLoanReceived`: loan receipts AND repayments.
- `PublicIndependentExpenditureDetails/GetIndependentExpenditureDetails`: candidate/measure spending.

Observe the export request with `publicGridName=ContributionsPublicGrid`, `transactionDetailsSearchFilter`, `fileName=ContributionDownload`, `type=CSV`, `openInNewTab=false`. Set candidate `filerRegistrationGuid`, committee `filerName`, transaction dates and election year explicitly. UTF-8-BOM CSV has a heading line before column headers.

Prefer full CSV exports to concatenated date-sorted API pages: tied dates can yield repeated GUIDs across pages. Matching advertised row counts alone does not prove completeness. Validate filer identity and export attribution.

If an unrestricted export times out, try itemized subtype exports `TCON-ITMY`, `TCON-INKIND`, `TRCON-ITMY`, `TRCON-INKIND`; verify counts against matching fresh queries. State that unitemized rows were not retrieved.

Aggregate with Decimal. Explain cash/in-kind/refund treatment and exact name normalization. Separate personal contributions, loans, own-committee transfers and external donations. Preserve ambiguous name variants; do not merge employers/employees or related entities without evidence. Label rankings as source-name aggregates where identity resolution is incomplete.

Cross-check top-donor widgets against itemized records; conflicting assignments require explicit warnings. Equal donor/date/amount records are not automatically duplicates. Totals across election types are not proof of excess contributions.

Audit timed-versus-periodic overlap using normalized source, date, amount, subtype, election type and election year; equal name/date/amount with different election designations is not enough to delete a row. A single export row linked to both reports is counted once. Treat exclusion of timed-only rows as a sensitivity test, never as corrected fundraising: unchanged displayed amounts/ranks support bounded export rankings, while material sensitivity warrants illustrative totals until reconciliation. State explicitly when no duplicate was proved.

Distinguish the request cutoff from the latest transaction actually returned. A January–September query whose saved rows end in July does not establish complete January–September disclosure coverage. Recalculate returns before ranking: a gross leader can fall below displayed leaders after refunds, and within-window net flows are not lifetime net donations.

The loan endpoint includes `TLOAN` and `TLPAY`: never add repayments to new loan receipts. Reconcile balances separately.

Independent-spending surname searches often match unrelated candidates; require candidate GUID or exact county-candidate identity. Do not allocate an entire multicandidate transaction to every beneficiary. Zero matches do not prove zero support.

For Fulton County, use `https://fultoncountyga.easyvotecampaignfinance.com/home/publicfilings` and observe its public filing-index request. Observed index: `https://ecf-api.easyvoteapp.com/filer/documentsearch/2462fffbb7c64fc0824698140abba7d8`. Direct PDF route: `https://ecf-api.easyvoteapp.com/documents/{documentid}/viewfinalredactedpdf`. Text extraction may work when direct document access fails.

Read the reporting period inside amendments, not just filing-index order. Historical threshold affidavits do not establish current-year exemptions or receipts. OCR may repeat cells, omit names/amounts or corrupt font text; do not sum extracted lines naively. Give filing-period examples rather than largest-donor claims until all relevant filings are reconciled.

Deliver candidate-specific sources, periods, methodology, categories, separate self-funding and outside spending, and precise remaining gaps. Verify syntax, roster coverage, citations and arithmetic before publication.
