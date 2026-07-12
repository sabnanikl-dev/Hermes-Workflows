# Google Surfaces Baseline Package

Use this when a local-visibility phase needs a Google Business Profile + Search Console baseline without unsafe account mutations.

## Goal

Produce a reviewable repo/wiki artifact package that separates:

- Read-only Google Business Profile facts that can be verified now.
- Search Console metrics that are verified, exported, or clearly blocked.
- Production public checks such as `robots.txt` and `sitemap.xml`.
- Exact approval gates for any future GBP/Search Console/public-account mutation.

## Recommended artifact set

For a docs-backed visibility repo, create or update:

1. `gbp-readonly-baseline.json` — machine-readable read-only GBP API snapshot.
2. `<issue>-gbp-completeness-audit.md` — human-readable GBP field inventory, mismatches, safe notes, approval-needed edits, and blocked/unknowns.
3. `<issue>-search-console-baseline.md` — Search Console metrics if available, or a precise access/scope/property blocker plus public robots/sitemap checks.
4. `<parent>-google-surfaces-baseline.md` — parent phase summary linking the child artifacts, blockers, sequencing, and verification.
5. The folder `README.md` index.

Keep raw private exports/screenshots out of public repos unless the repo is explicitly allowed to hold them.

## GBP baseline steps

1. Verify the OAuth/API identity before reading GBP data.
2. Use read-only Account Management + Business Information API calls.
3. Capture account, location resource, title, website, phone, category, service area, services, hours, profile description, metadata, place ID/maps/review links, and service/profile mutability flags.
4. Compare against the local SEO source of truth and approval ledger.
5. Split recommendations into:
   - Safe notes / matches current baseline.
   - Approval-needed edits.
   - Blocked/unknown decisions.
6. State explicitly that no GBP mutation was performed.

## Search Console baseline steps

1. Try a read-only Search Console `sites.list` or equivalent property query only with an appropriate token.
2. If it fails for missing scope/property access, document the blocker precisely rather than guessing that no property exists.
3. Capture what scope/access is needed, for example Search Console read-only scope plus access to the `https://example.com/` URL-prefix or domain property.
4. Independently verify public crawlability inputs:
   - Fetch `https://domain/robots.txt`.
   - Fetch `https://domain/sitemap.xml`.
   - Record HTTP status, content type, sitemap entries, and any obvious mismatch.
5. Do not submit sitemaps, change verification settings, or mutate Search Console without explicit approval.

## Linear handoff pattern

When artifacts are ready but external/account work remains blocked:

- Move the relevant child issues to **In Review**, not Done.
- Comment with artifact paths, what was verified, what remains blocked, and what approval/access is needed.
- Move the parent phase to **In Review** with a summary of child artifacts and blockers.
- Do not close the parent unless required metrics/actions are actually verified or split into follow-up issues.

## Review checklist

Before handoff, run a separate review or self-check for:

- NAP consistency.
- Canonical website/inquiry URL consistency.
- Service/package naming consistency.
- No invented claims, awards, ratings, rankings, partnerships, or event counts.
- Every public/account action remains approval-gated.
- JSON baselines parse.
- `git diff --check` passes for repo docs.
- Folder indexes list new artifacts.

## Pitfalls

- Do not let a successful public `sitemap.xml` fetch imply Search Console submission/status is complete.
- Do not treat missing Search Console OAuth scope as evidence that the property is absent.
- Do not recommend secondary GBP category edits until valid category availability and competitor/category research are done.
- Photo/channel approval can still be insufficient for upload if exact credit treatment, final asset list, or the upload action itself is not approved.
