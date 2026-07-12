# Stakeholder Data in PR Comments

Use this pattern when a PR comment supplies approved business/stakeholder data and some items are deferred.

## Pattern

1. Read issue comments, review comments, and reviews before editing.
2. Translate the comment into ledger rows or source-of-truth doc updates before changing public code.
3. For each field, record value, source/comment link, approver, date, site/JSON-LD usage, and notes.
4. Verify URLs independently before marking them usable.
   - HTTP-check social/profile links.
   - For copied Google Maps URLs with browser/session params, confirm the supplied URL resolves, then prefer a durable `https://www.google.com/maps/dir/?api=1&destination=...` URL if it resolves and contains the approved destination.
5. If the user says "create a new issue for this," immediately create a scoped follow-up issue and mark that ledger item `Deferred`; do not treat the original approval as permission to publish the deferred claim.
6. Push and verify the PR API head SHA matches local HEAD before reporting.
7. Leave a PR comment summarizing changed fields, verification performed, deferred items, follow-up issue links, remote SHA, and merge state.

## Pitfalls

- Do not conflate stakeholder approval with implementation approval. A ledger PR can be updated without also changing site copy.
- Do not publish commerce-sensitive claims such as rental process, stock, price, urgency, sizes, deposits, timing, or guarantees unless exact wording is approved.
- Do not add JSON-LD fields like `geo` from inference; omit unless explicitly verified.
- Do not preserve copied Google Maps URLs with personal/browser parameters when a clean destination URL works.
