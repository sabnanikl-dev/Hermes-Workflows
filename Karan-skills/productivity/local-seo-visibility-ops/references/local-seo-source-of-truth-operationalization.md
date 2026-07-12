# Local SEO Source-of-Truth Operationalization Pattern

Use when Phase 0 produces more than a private note: a client/owned brand needs a durable source-of-truth, approval gates, and issue/repo traceability before GBP, directory, or public copy work.

## Pattern

1. **Start with the canonical wiki note**
   - Keep the private/business source-of-truth in the wiki/knowledge base when it contains approval-sensitive fields, unresolved claims, access notes, or account posture.
   - Link it from the relevant work tracker issue before moving the issue to active execution.

2. **Create a repo-facing docs package**
   - Copy only the operational, shareable version into the project/visibility repo.
   - Recommended files:
     - `README.md` or package index
     - `docs/<brand>/local-seo-source-of-truth.md`
     - `docs/<brand>/approval-ledger.md`
     - `docs/<brand>/reuse-notes.md`

3. **Separate observed facts from approvals**
   - Mark public website/API/dashboard-derived values as observed.
   - Keep unresolved decisions in an approval ledger instead of burying them in prose.
   - Approval ledger should include owner/decision, current recommendation if any, blocker, and public-change risk.

4. **Track blockers explicitly**
   - GBP role/access for the agent account.
   - Public phone/email.
   - Address/privacy/service-area posture.
   - Package/service naming conflicts between website, business plan, and older notes.
   - Inquiry URL + UTM standard.
   - Hours/opening date/category choices.
   - Claims, awards, venue/vendor relationships, photos/proof rights.

5. **Use Git/Linear discipline**
   - Work on a named branch tied to the tracker issue.
   - Commit the docs package locally.
   - Do not push, open PRs, or mutate the remote until the user explicitly approves external repo mutation.
   - After push approval, verify the remote commit/branch before reporting success.

6. **Update the tracker issue only with verified state**
   - Link the canonical wiki note.
   - Link repo artifact paths/branch/commit after they exist.
   - Move the issue to in-progress only once the source-of-truth link and first artifacts are actually present.

## Why this matters

This keeps Phase 0 from becoming either a loose note or a public-action trap. The wiki remains the canonical sensitive context, the repo gets an auditable implementation package, and the tracker reflects real state without implying public edits were made.
