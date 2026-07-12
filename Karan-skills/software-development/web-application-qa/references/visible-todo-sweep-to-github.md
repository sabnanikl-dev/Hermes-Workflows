# Visible TODO Sweep → GitHub Issues

Use when auditing a website for user-facing TODO/TBD/placeholder labels and opening GitHub issues for each actionable gap.

## Goal
Find TODO markers that render to users, not every developer TODO in docs, comments, CSS, or historical handoff files.

## Recommended sequence

1. **Ground target and repo**
   - Confirm the canonical repo and default branch.
   - Search open/all GitHub issues first for likely duplicates (`TODO`, `verify before deploy`, `coordinates`, `placeholder`, section names).
   - Inspect the default branch, preferably with a clean worktree or read-only checkout if the local branch has unrelated WIP.

2. **Separate source TODOs from visible TODOs**
   - Source search is useful for discovery, but do not create issues from raw matches alone.
   - Filter to rendered/user-facing text. Prefer explicit visual seams such as `span.todo`, TODO chips, badges, or labels.
   - Exclude comments, docs, fixtures, CSS variable names, AGENTS guidance, and test-only placeholders unless they are surfaced in the UI.

3. **Audit live routes**
   - Fetch the sitemap and check every public route when cheap.
   - If sitemap `<loc>` values point at the production/apex domain but the test target is non-prod, map only the paths onto the non-prod host before fetching.
   - Use browser/DOM inspection for at least one positive finding so the issue reflects the real visible location.

4. **De-duplicate findings**
   - Group repeated instances by root cause and page/section.
   - Open one issue per actionable gap/root cause, not one issue per string occurrence.

5. **Issue body shape**
   - Context/evidence: URL, route, repo branch/SHA if known, source file/section, exact visible text.
   - Goal: remove or replace the TODO with a final-looking, truthful UI.
   - Scope: what may change.
   - Out of scope: live deploy/DNS/CMS/account mutations unless explicitly approved.
   - Acceptance criteria: no visible TODO remains, surrounding CTAs/content still work, data is verified or intentionally omitted.
   - Verification: baseline tests, text/DOM scan, desktop/mobile manual check.

## Pitfalls

- A raw grep for `todo|placeholder` will over-report because comments and docs often intentionally describe guardrails.
- `placeholder` can be legitimate internal wording; require visible/user-facing impact before filing.
- Do not silently convert a verification gate into a factual claim. If a coordinate, price, review, inventory claim, or business fact is unverified, the issue should ask for either verified data or an intentionally non-specific final UI.
- Opening issues is a mutation: verify the created issue by reading back title, labels, state, URL, and a body excerpt before reporting success.
