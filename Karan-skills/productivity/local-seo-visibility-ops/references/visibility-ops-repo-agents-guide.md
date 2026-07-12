# Visibility Ops Repo AGENTS.md Pattern

Use this when a local SEO / Google visibility project has a GitHub-backed operations repo that stores docs, approval ledgers, read-only baselines, templates, and reusable client playbooks.

## When to use

- The repo is an operations/artifact repo, not an application or coding harness.
- Agents need enough context to maintain SEO/GBP/Search Console/directory/review artifacts without reading the entire wiki or chat history.
- The user wants future agents to work safely in the repo while preserving approval boundaries.

## Recommended shape

Keep `AGENTS.md` lightweight: about 100 lines, table-of-contents style, and focused on orientation + boundaries. Do not turn it into a full harness manual.

Include:

1. **Project description**
   - Business/client name and market.
   - What the visibility project is trying to accomplish.
   - Explicit statement that the repo is a visibility-ops artifact repo, not a code harness.

2. **Source-of-truth map**
   - `README.md`.
   - The active local SEO source-of-truth artifact.
   - Approval ledger.
   - Reuse notes / template notes.
   - Canonical private wiki/source, if relevant.

3. **Operating principles adapted from harness engineering**
   - Progressive disclosure: keep `AGENTS.md` short and link to docs.
   - One artifact, one reviewable change.
   - Separate drafting from evaluation/review.
   - Define done before editing.
   - Repo context should be recoverable in roughly three reads.
   - Avoid performative scaffolding.

4. **Approval boundaries**
   - No GBP/account mutations without explicit approval.
   - No directory submissions or edits without explicit approval.
   - No review requests/replies, LocalPosts, outreach, social posts, paid listings, website changes, merge/deploy, or DNS changes without explicit approval.
   - No invented claims: awards, rankings, review counts, venue relationships, team size, pricing, event volume, luxury positioning, or “best/top-rated.”
   - No secrets, OAuth tokens, raw exports, or private address data.

5. **Expected agent workflow**
   - Confirm cwd, branch, and remotes.
   - Read `README.md`, `AGENTS.md`, and the task-specific artifact.
   - Check approval ledger before using facts publicly.
   - Make the smallest useful docs change.
   - Self-review for NAP consistency, canonical URLs, service/package naming, claim safety, approval labels, and secret leakage.
   - Use a separate reviewer for public claims, directory copy, GBP recommendations, or reusable templates.
   - Do not push/open PR/merge/publicly mutate without approval; after approved push, verify remote commit.

6. **Validation checklist**
   - `git diff --check`.
   - Markdown link/path sanity.
   - Every public-facing fact labeled as observed, approved, unknown, blocked, or do-not-use when relevant.
   - Public actions remain approval-gated.
   - Reusable templates do not leak client-specific/private details.

## What not to scaffold by default

Do not add CI, app boot scripts, generated progress logs, feature lists, autonomous loops, or heavyweight harness directories unless the repo actually runs code/tools or has repeated evidence-heavy multi-site work. For a docs-first visibility repo, `AGENTS.md` plus a small `docs/` package is usually enough.

## README cross-link

After adding `AGENTS.md`, update `README.md` so future agents discover it immediately, e.g. under “Current artifacts”:

- `AGENTS.md` — lightweight operating guide for agents maintaining this visibility-ops repo.
