# Stakeholder Verification Ledger Pattern

Use when a Linear issue is explicitly non-coding or stakeholder-coordination work, but the deliverable is a repo-local document that unblocks later implementation (for example: verifying client business data before replacing TODOs in a website).

## When this applies

Signals:
- Linear issue says non-coding, stakeholder coordination, data verification, approval ledger, or blocker.
- GitHub issues track implementation, but Linear tracks cross-stakeholder approvals.
- The repo needs a durable file before later code can safely change.
- Missing values should remain TODO-gated until approved.

## Process

1. Query the Linear issue by identifier and read the full description, labels, state, comments, project, and stakeholders.
2. Inspect the target repo docs/spec to identify the exact approval gates and TODO fields.
3. Create a docs-only PR in the repo that adds a ledger file rather than prematurely changing implementation.
   - Good examples: `docs/verified-business-data.md`, `docs/approval-ledger.md`, `docs/source-of-truth.md`.
   - Include fields for value, source, approver, date, site/use target, and notes.
   - Include stakeholder ownership and unlock criteria.
   - Include an explicit blocker statement that unverified values remain TODO/omitted.
4. Validate the document contains every field requested by Linear and does not imply approval.
5. Open a PR and verify remote commit visibility via `gh pr view --json commits,headRefOid` and `git ls-remote`.
6. Update Linear only after the PR exists:
   - Move issue to In Progress if stakeholder data is still missing.
   - Comment with PR URL, what the ledger added, and what remains blocked.
   - Do not mark completed until values are actually verified/approved and recorded.

## Pitfalls

- Do not search the web and treat unapproved public listings as approved client data.
- Do not remove visible TODOs or add JSON-LD/CTA fields just because a draft contained plausible values.
- Do not mark stakeholder-verification issues Done when the PR only creates the ledger; the real blocker is still stakeholder approval.
- Keep credentials, account changes, DNS/hosting, GBP edits, and live/public changes out of this pattern unless explicitly approved as a separate workstream.
