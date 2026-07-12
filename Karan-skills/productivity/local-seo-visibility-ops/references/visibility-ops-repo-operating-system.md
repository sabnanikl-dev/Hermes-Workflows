# Visibility Ops Repo Operating System

Use this when a local SEO / Google visibility project becomes a GitHub-backed operations repo rather than a website/code repo.

## Core shape

A visibility ops repo should make the project legible to future agents without becoming a heavyweight coding harness.

Recommended minimum durable files:

- `AGENTS.md` — short orientation guide and approval boundaries.
- `docs/spec.md` — project goal, purpose, operating model, success criteria, and what the repo is/is not.
- `docs/workflows/linear-issue-management.md` — status semantics and when/how to move Linear issues.
- `docs/<client>/local-seo-source-of-truth.md` — repo copy or public-safe operational copy of the canonical source of truth.
- `docs/<client>/approval-ledger.md` — unresolved decisions, public-use gates, and approval provenance.
- Reuse notes/playbooks only after the pattern survives real execution.

## Spec goal pattern

The spec should reflect the Linear project description in plain language, not just restate internal files.

For owned/client visibility projects, include both goals when applicable:

1. Improve the brand's real local/Google visibility.
2. Build reusable systems, templates, approval patterns, report structures, and light automation candidates for future clients.

Example one-line shape:

> Expand <brand>'s digital reach while building a reusable local-visibility operating system that <agency/company> can adapt for future clients.

## Linear workflow guidance

Do not let the repo README become a moving task tracker. Linear owns execution state.

Good README patterns:

- Link the Linear project.
- Say related Linear issues are linked from artifact headers.
- List durable artifacts under “Current artifacts.”

Avoid:

- A single mutable `Current issue: PAPI-XX` line that changes every PR.
- Temporary progress logs or session narratives.

Linear status guidance should live in a workflow doc and cover:

- Triage: rough/unshaped or needs routing.
- Backlog: valid but deferred.
- Ready: scoped with acceptance criteria, owner/lane, approval boundary, and verification plan.
- In Progress: someone is actively working now.
- In Review: artifact/PR/decision checklist is ready for owner/reviewer input, or parent is paused on human review.
- Done: acceptance criteria verified, comments/links posted, public/account changes verified or split into follow-up issues.
- Canceled/Duplicate: closed with replacement/rationale.

Important user preference: do not leave a parent issue in In Progress when the only remaining blocker is Karan/Amanda input. Move the parent to In Review, create/assign a child human-review issue with a checklist, then resume the parent after the child is Done.

## Proof-bank / asset database pattern

A lightweight SQLite proof bank can be useful for asset/review/proof inventories, but guardrail naming matters.

Recommended structure:

- Reviewable SQL source: `schema.sql` + `seed.sql`.
- Generated query DB: `*.sqlite` only if downstream agents benefit from structured queries.
- Human-readable markdown mirror for owner review.
- README with regeneration commands and query examples.

Validation checklist:

- `git diff --check`.
- `sqlite3 <db> 'PRAGMA integrity_check;'` returns `ok`.
- Regenerate the DB from committed SQL and compare it to the committed DB (`cmp -s`).
- Compare markdown inventory IDs against DB IDs.
- Verify known inclusion/exclusion edge cases by query.
- Check no public uploads/posts/review requests/account mutations happened.

Pitfall: a view named `approved_asset_channels` can be misread as publication-ready if assets still have unresolved credit/permission follow-ups. Prefer names like `channel_permissioned_assets`, include `credit_status`, `privacy_status`, and `required_action`, or add a stricter `publication_ready_assets` view. README query headings should say when results are only channel-permissioned and still require credit/publication checks.

## Review posture

For visibility-ops repo PRs, review as stewardship work, not only syntax:

- Does the PR preserve Linear as the execution tracker?
- Are public/account mutations still approval-gated?
- Are reusable client systems generic enough to avoid leaking client-specific private details?
- Do query/view names prevent unsafe downstream interpretation?
- Are generated artifacts reproducible from committed sources?
