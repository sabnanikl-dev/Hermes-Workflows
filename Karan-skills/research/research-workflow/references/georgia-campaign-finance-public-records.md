# Georgia campaign-finance public records

## Route by record year

Start at https://ethics.ga.gov/records-search-all/ and verify the current routing. The published split is Legacy 2005–2021, EFile 2022–2025, PeachFile 2026 onward. Never treat an empty legacy search as evidence that a current candidate has no contributions.

PeachFile public entry: https://peachfile.ethics.ga.gov/login . Despite the path name, the page has unauthenticated public candidate, contribution, loan, independent-expenditure and filed-report searches. Do not log in or register to read public data. Public candidate UI: https://peachfile.ethics.ga.gov/public/cf/publiccandidate . Search aliases and surnames if an exact ballot name returns no result; inspect ballotFullName and office before linking a legal-name filer to a candidate.

## Public API discovery

Use the browser's resource list to discover the current API host and routes. When necessary, temporarily log XMLHttpRequest open/send/load in the research browser and trigger an ordinary read-only public search to capture its exact JSON payload and response. Do not invent private endpoints or use authentication tokens. The public UI currently calls unauthenticated POST read endpoints at https://api-peachfile.ethics.ga.gov/api/ :

- PublicFilerDetails/GetCandidateDetails: use the exact UI request; filerName identifies the search, pageNumber/pageSize paginate. Results include office, party, filerRegistration GUID, committee, totals and ballotFullName.
- PublicFilerDetails/GetFilerDetailsById: {"filerRegistrationGuid":"<retrieved GUID>"}; includes lastFiledDate.
- PublicFilerDetails/GetFinancialSummaryDetails: {"filerRegistrationGuid":"<retrieved GUID>","filingStatusCode":"FIL"}; monetary/in-kind, loan and period/cumulative fields.
- PublicTransactionDetails/GetTopDonorsAndPayees: {"filerRegistrationGuid":"<retrieved GUID>","transactionTypeCode":"TCON","filingYear":null,"electionTypeCode":""}; reproduce UI scope explicitly, not as a calendar-year filter.
- PublicTransactionDetails/GetTransactionDetails: capture the UI request rather than assuming its filter schema. A filerName search may match multiple registrations: locally filter by the previously verified registration GUID. Page size 100 has worked; larger values can be rejected by request validation.

Save exact requests and responses to the task evidence directory. API POST URLs are not ordinary clickable GET pages; include the public UI filing-search link with citations and make the saved payload reproducible.

## Evidence and money-category rules

- Match enumerated rows to declared totalItems, then check unique transaction GUIDs. Pagination sorted only by date may repeat or omit transactions on date ties; a count match alone does not prove full unique coverage.
- Do not silently reconcile headline totals, cumulative totals and itemized sums. Preserve mismatches and mark the finance section partial when unexplained.
- Treat Top Contributors as portal-reported source records, not automatically consolidated donor identities. Repeated names, capitalization variants and different source records may not be combined. A lower source entry can exceed a displayed top source after legitimate consolidation; avoid definitive rankings without reconciling all records.
- Read transactionSource and transactionSubTypeDesc. Person-looking names may be filed under Corporation / Business / Unregistered Committee. Report that as the filing's category; do not independently assert a corporate treasury contribution or silently recategorize.
- Separate cash and in-kind. An in-kind source is goods/services, not cash in the bank.
- A campaign-named Candidate / Candidate Committee entry, especially unitemized, does not establish a single external donor or personal self-funding. Identify its ambiguity explicitly.
- Treat loans as loans; verify the lender before calling them self-financing. Zero fields in one registered committee do not establish no activity across all historical committees.
- Distinguish contribution-date range, filing date, election cycle and campaign-to-date scope. Unfiltered 2026 registration data can contain contributions dated in earlier years.
- Keep direct candidate contributions, party/PAC contributions and independent expenditures separate. Employer data describes an individual donor unless the source is independently an entity.
- If refunds, name resolution, pagination or carryover remain unresolved, label selected major disclosed sources rather than largest donors; state gross/reported-positive versus net methodology and the precise coverage limitation.
