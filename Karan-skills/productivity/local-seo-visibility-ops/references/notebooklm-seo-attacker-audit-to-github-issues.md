# NotebookLM SEO Attacker Audit → GitHub Issues

Use this pattern when Karan asks for an SEO/search visibility audit grounded in specific Google Search / SEO NotebookLM notebooks, with repo-backed GitHub issues as the deliverable.

## When this applies

- User provides one or more SEO/Search NotebookLMs as the primary source of truth.
- Target is a website repo/current code state.
- Deliverable is ranked, source-grounded GitHub issues, not direct website source changes.
- User requests a reviewer/checker gate before issue creation.

## Workflow

1. **Load the right skills first**
   - `notebooklm-to-obsidian-synthesis` for NotebookLM auth/list/query mechanics.
   - `github-issue-specs` and `github-operations` for repo and issue creation discipline.
   - `local-seo-visibility-ops` for local-search priority, approval boundaries, and no-overbuild guardrails.
   - Domain/client skill when applicable, e.g. `jmd-menswear`.

2. **Query each named NotebookLM as source of truth**
   - Refresh NotebookLM auth if expired.
   - List notebooks and identify the exact SEO notebooks.
   - Ask each notebook for a citation-backed checklist of Google requirements relevant to the repo: crawlability, indexation, canonical/sitemap/robots/noindex, structured data, images/rendering, content intent, ecommerce/local-retail constraints.
   - Do not invent issues from general SEO vibes; every proposed issue must map to a NotebookLM/Google concept.

3. **Audit current repo state before drafting**
   - Verify repo identity, branch, remote/default branch, existing open/all-state issues, and labels.
   - Inspect the actual SEO surfaces: `robots.txt`, `sitemap.xml`, canonical/meta/OG, JSON-LD, route/page structure, static/JS-rendered content, validation scripts, and docs/source-of-truth constraints.
   - Run the baseline test if cheap, e.g. `npm test`.

4. **Synthesize findings as attacker-style gaps**
   - Rank by `Expected Impact × Effort`.
   - Include both repo evidence and source requirement.
   - Reject findings that contradict business constraints or Google accuracy guidance. Example: do not recommend Product/Merchant listing schema when a showroom page has no visible prices, stock, availability, checkout, or product pages.

5. **Reviewer gate before opening issues**
   - Send draft specs to Codex Reviewer (or equivalent) before GitHub mutation.
   - Reviewer must reject issues that are vague, subjective, unsupported by NotebookLM/Google concepts, lacking current repo evidence, or conflicting with client constraints.
   - Apply reviewer edits before opening issues. If reviewer says “drop,” drop it.

6. **Create issues only after duplicate search**
   - Search open and closed issues for overlapping terms.
   - Prefer focused implementation tickets over broad “improve SEO” issues.
   - Verify each created issue with `gh issue view` before reporting.

7. **Audit state artifact**
   - If requested, write `SEO-AUDIT-STATE.md` recording audit date, source notebooks, reviewer decisions, opened issue IDs/URLs, rejected findings, and verification performed.
   - This file is a repo artifact. Commit it on a branch from the default branch and push/verify the remote branch commit. Do not merge without human approval.

## Issue quality bar

Each issue should include:

- Goal and source-backed Google/NotebookLM requirement.
- Current state verified with concrete file paths and observed gaps.
- Scope and out-of-scope boundaries, especially no-live-change/no-deploy/no-account-mutation.
- Acceptance criteria that are pass/fail, not “make it better.”
- Verification commands, usually `npm test` plus a manual smoke where rendering/search surfaces are involved.

## Pitfalls

- Do not treat NotebookLM as live repo state. NotebookLM supplies source-grounded Google requirements; repo inspection supplies current failures.
- Do not open an implementation issue for facts that are intentionally absent and awaiting approval. Example: blog byline/date schema should wait for approved visible author/date source data.
- Do not overstate the current failure. If content auto-mounts via JS, say the initial/no-JS HTML lacks content rather than claiming Google must click controls.
- Do not let a “verification-only” acceptance path satisfy an issue title that promises a static/no-JS projection.
- Do not encode Product/Merchant schema for showroom-only content unless visible, approved commerce facts exist and the business model supports it.
