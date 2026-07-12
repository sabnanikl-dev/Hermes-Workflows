# JMD showroom cutover pattern — critical-path split + production smoke prep

Use this as a concrete example when a client automation depends on a CMS/admin foundation and a slower, non-critical CMS/content slice appears in the same issue.

## Critical-path issue splitting

When an issue combines:

- automation-critical foundation work (for example, Sanity project/dataset/Studio + `showroomPhoto` backend readiness), and
- slower non-critical content modeling (for example, blog CMS schemas/migration),

split the non-critical slice into a follow-up issue rather than letting it block the automation path.

Pattern:

1. Read the original issue and parent tracker.
2. Create a follow-up issue for the non-blocking slice.
3. Narrow the original issue title/body to the critical-path PR.
4. Add explicit “out of scope / split to #N” language to the original issue.
5. Comment on both issues and update the parent tracker/build order.
6. Re-read all mutated issues and verify the links/clauses are live.

Example outcome:

- Critical path: “Deploy JMD Sanity Studio + showroom backend readiness.”
- Follow-up: “Add Sanity blog CMS backend schemas and query contract.”
- Parent tracker notes the follow-up as non-blocking for showroom automation completion.

## Production cutover prep after upstream foundation merges

Once the foundation PR merges, do **not** jump directly to real production reads/writes. First prepare and verify the cutover lane without touching production resources.

Steps:

1. Verify the upstream PR merge with GitHub API, not memory or issue state alone:
   `gh api repos/<owner>/<repo>/pulls/<PR> --jq '{state, merged, merged_at, merge_commit_sha}'`.
2. Pull public operational identifiers from repo docs/config (project IDs, dataset names, Studio URLs). These may be public, but tokens and Drive folder IDs are still sensitive.
3. Refresh any local repo-contract mirror to the upstream merge SHA so builders do not use stale docs.
4. Create a gitignored production-smoke overlay (for example `.env.<issue>-production`) with:
   - `DRY_RUN=false` or equivalent production selector;
   - approved source env var names/values stored only locally;
   - public target identifiers;
   - token placeholders until an approved production token is supplied.
5. Create a redacted local inventory under an ignored secret directory with purpose, source PR/issue, public target identifiers, token status, and `access_verified: false`.
6. Add a no-mutation preflight script that checks local overlay + runtime inactive state + expected credential-slot/node shape. It must **not** list/read the production source, query the production target, run the workflow, bind credentials, or activate schedules.
7. Run normal static validators/tests and scan tracked/public files for raw production source identifiers.
8. Post tracker status with evidence and the explicit no-live-change boundary.

## Readiness wording

Use wording like:

> Prepared for production smoke testing; blocked only on approved production write token and explicit approval for the first 1–3 photo mutation test. No production source read, target query/write, credential binding, workflow execution, schedule activation, deploy, or client-facing change was performed.

## Final import, archive, and activation issue shape

When a limited smoke test proves the path but intentionally leaves production data partially imported, add a final import child before closing the import parent. For JMD this pattern was:

- import parent child (`JMD-26H`): persist/import the nested-capable workflow into live n8n while keeping `active=false`, run the full approved-parent-folder import with explicit approval, run a second idempotency pass, re-export/sanitize, and open the website repo PR;
- archive parent children (`JMD-27A`/`JMD-27B`): split deterministic archive/removal logic + sanitized artifact PR from credentialed/live archive smoke and safety verification;
- activation child (`JMD-39`): separate issue under the broader automation parent (`JMD-23`), because activation spans both import readiness and archive/removal readiness.

For repo PR contracts, spell out exact close/link behavior in the child issue and mirrored GitHub issue comment. Example: import artifact PR includes `Closes #64`; archive/removal artifact PR includes `Closes #65`; neither closes schedule activation, deploy, DNS/account changes, or client-facing communication.

Schedule activation should be a final operations gate. Its criteria should require fresh approval after the issue starts, pre-activation `active=false` verification, dependency checks (completed sibling vs user-approved deferral), first scheduled-run evidence, Sanity read-back, and post-run duplicate/unsafe-mutation checks.

## Hard gate reminder

Supplying a real Drive folder URL or confirming a real Sanity project/dataset does **not** authorize:

- listing/reading the folder;
- binding production credentials;
- running a production smoke test;
- writing Sanity assets/docs;
- activating a schedule;
- publishing/deploying the website.

Each remains a separate explicit approval gate.
