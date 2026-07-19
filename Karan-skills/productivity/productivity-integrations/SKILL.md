---
name: productivity-integrations
description: "Use for productivity SaaS and document integrations: Airtable, Google Workspace, Linear, Notion, maps/geocoding, email actions, documents/OCR/PDFs, and meeting pipelines."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [productivity, airtable, google-workspace, linear, notion, documents, maps]
    related_skills: [google-workspace, github-operations]
---

# Productivity Integrations

## Overview
This umbrella covers operational productivity systems and document workflows. Use it for SaaS CRUD, calendars/email/Drive, issue trackers, databases, maps/geocoding, PDFs, OCR, presentations, and meeting pipelines.

## When to Use
- Airtable, Google Workspace, Linear, Notion, or Maps API tasks.
- Email action workflows or terminal email via Himalaya.
- PDF, OCR, slide deck, document, or resume workflows.
- Teams meeting summary pipeline operation.
- Cross-system operations that require careful read-before-write verification.

## Subworkflows

### SaaS CRUD and trackers
Search/read before creating or updating. Use stable IDs and verify mutations by reading back the changed record/item.

### Local automation servers: n8n
For local n8n requests, start the server as a tracked background process, verify port `5678` and HTTP readiness before reporting success, and treat password resets as explicit account mutations. See `references/n8n-local-operations.md` for exact commands and password/account inspection guidance.

#### Linear API notes
- Use GraphQL with `LINEAR_API_KEY` when available; never print token values.
- Read issues by identifier with `issue(id: "JMD-23")` (or aliases for several identifiers). `IssueFilter` may not support `identifier`, so avoid `issues(filter:{identifier:{...}})` unless introspection confirms it.
- Common mutations: `issueUpdate(id: ..., input: { stateId: ... })` for status changes and `commentCreate(input: { issueId: ..., body: ... })` for comments.
- After updating Linear, read back each issue’s `state { name type }` and recent comments to verify links/notes landed.

### Google Workspace and email
Respect contact-confirmation rules. For email actions, read the source thread/message before drafting or sending.

### Google Search Console API checks
When asked whether Google Search Console API access works, verify the dedicated Search Console OAuth token and call the live API rather than relying on broad Google Workspace auth. `gws auth status` can prove the Google Workspace identity, but its OAuth grant may omit `webmasters.readonly` and the CLI may not expose Search Console resources. Use `references/google-search-console-api-checks.md` for the token paths, direct `webmasters/v3/sites` probe, Search Analytics smoke test, and common error interpretation.

### Gmail triage
Use the absorbed Google Workspace helper scripts for read-only checks:
- `references/absorbed/google-workspace/scripts/setup.py` for auth validation
- `references/absorbed/google-workspace/scripts/google_api.py` for Gmail search/get calls
- `references/absorbed/google-workspace/scripts/gws_hermes.sh` for advanced Gmail API endpoints when the Python wrapper does not expose a needed method (for example, `users.threads.get` to verify replies)
- See `references/gmail-triage-notes.md` for the canonical unread/sent/reply-check queries and thread-search pitfalls.
- See `references/gmail-reply-verification.md` for the thread-level reply check workflow and the sent-message metadata pitfall.

### Google Sheets shopping-list workflow

Use this when turning a plan, build-out, event, or purchase roadmap into a Google Sheet.

1. **Resolve the subject first.** A shopping list without its build/event/use case is underspecified; retrieve prior context if possible, otherwise ask one focused question.
2. **Research before pricing.** Use current retailer/manufacturer sources for pivotal items and present ranges rather than pretending a volatile SKU price is fixed. Include purchase links as formulas (`HYPERLINK`) or dedicated link columns.
3. **Use a decision-ready schema.** Default columns: Phase, Category, Priority, Item, Recommended Buy, Cheaper Alternative, Premium Alternative, Target Price Range, three purchase links, and Buy Trigger/Notes. Keep a separate Sources & Notes tab for date-stamped pricing and compatibility evidence.
4. **For hardware lists, verify compatibility from primary specs.** Do not merely label parts “compatible”: compare the exact enclosure, motherboard, GPU, cooler, and storage-form-factor limits. Preserve conditional constraints in the sheet (for example, a 4U case may have one clearance with a card retainer installed and another without it). Prefer the native desktop storage form factor (usually M.2 2280); call out when smaller M.2 sizes require a board-specific standoff or adapter.
5. **Write safely and read back.** Read the destination sheet first. After creating/updating, verify row count, key inserted/replaced rows, and intentionally removed rows with a Sheets API readback. If the sheet is agent-owned, share it only with the known intended collaborator and verify the resulting permission.
6. **Revision discipline.** When a user changes a build direction, replace or remove the affected rows rather than appending contradictory choices. Keep optional pivots as explicitly named, lower-priority rows next to the default decision.

See `references/google-sheets-shopping-lists.md` for a reusable row model and compatibility/pivot checklist.

### Scheduled deal watches and quiet alerts
For recurring product-price monitoring, use a script-only (`no_agent: true`) cron wrapper that emits stdout only for a verified qualifying deal; empty stdout stays silent. For Telegram-specific alerts, resolve the configured Telegram home destination and set an explicit `telegram:<chat_id>` delivery target rather than fan-out. See `references/quiet-price-watch-cron.md` for the reusable prompt, parsing, verification, and delivery pattern.

### Documents and presentations
Prefer format-specific tooling. Verify output files exist and, where possible, inspect the resulting content.

### Maps and local operations
Geocode explicitly, cite coordinates/providers, and avoid overclaiming business/local SEO effects without source evidence.

### Grocery / cart APIs
For Kroger cart testing, service-to-service product search is only a preflight; real cart writes require customer OAuth Authorization Code flow, an exactly registered redirect URI, and cart scope. See `references/kroger-api-cart-testing.md` for the credential smoke test, OAuth sequence, endpoint/payload shape, and common 401/redirect pitfalls. For a reusable local OAuth + cart mutation helper, copy/run `scripts/kroger_oauth_cart_add.py` with a local credential file and explicit `--item UPC:quantity:PICKUP` arguments.

## Package References
Historical source skill packages were re-homed under `references/absorbed/<skill-name>/`.

## Verification Checklist
- [ ] Read-before-write for external systems.
- [ ] Mutations verified with IDs/URLs/readbacks.
- [ ] Files generated or edited are inspected after creation.
- [ ] Sensitive contact/email/calendar data is minimized in summaries.
