# Post-merge copy approval gates for JMD website PRs

Use this when a repo PR lands draft customer-facing JMD copy but owner approval is still required before public/client-facing use.

## Pattern

1. Merge only after Karan explicitly approves and normal repo review/prover gates pass.
2. Verify the merge through GitHub API/readback before reporting success:
   - PR `merged: true`, `state: closed`, `merged_at` present.
   - Main branch tip equals the merge commit when relevant.
   - Linked GitHub issue auto-closed if the PR said `Closes #N`.
3. Create a Linear issue in the `JMD` team for owner approval. Default shape:
   - State: `Ready` unless the user wants it active immediately.
   - Project: `JMD - 90-Day Digital Storefront Revival` for website/client-facing copy work when applicable.
   - Assignee: Karan if he is the approval coordinator.
   - Labels: `jmd-menswear`, `website-build`, `handoff` (avoid mutually exclusive label-group combinations like `website` + `content`).
4. Linear issue body should include:
   - PR URL, GitHub issue URL, merge commit URL.
   - What copy/pages changed.
   - Technical/prover evidence summary.
   - Explicit owner approvals:
     - Lucky: final brand voice/customer-facing wording.
     - Danny: rental, availability, appointment, price, limited-floor wording.
     - Karan: public deploy/go-live after owner approvals.
   - Acceptance checklist for sharing preview/copy, recording exact approval evidence/date, and opening a follow-up PR if edits are requested.
   - Non-goals: no deploy/DNS/hosting/GSC/GBP/account change; no new facts/pricing/inventory/stock/AI imagery/stories.
5. Comment back on the merged PR with the Linear issue URL and the boundary: merge lands the repo draft, not public/client-facing approval.
6. Verify the Linear issue after creation: identifier, URL, state, project, assignee, labels, PR link, merge commit, and approval checklist.

## Why this matters

For JMD, a merged website-copy PR is often a repo readiness step, not permission to publish. Lucky and Danny approval gates are part of the client workflow and need a visible tracker so a future agent does not treat merged code as approved public copy.