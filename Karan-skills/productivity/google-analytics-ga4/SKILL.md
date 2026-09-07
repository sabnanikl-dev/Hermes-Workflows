---
name: google-analytics-ga4
description: "Use when provisioning, verifying, or monitoring GA4 and paired Search Console measurement."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [google, analytics, ga4, oauth, visibility, jmd]
    related_skills: [google-search-console, local-seo-visibility-ops, productivity-integrations, google-business-profile-api-access]
---

# Google Analytics 4 (GA4) Admin & Provisioning

## When to use

Load this when working on Google Analytics 4 for JMD, Femme Events, or future visibility clients, especially when asked to:

- Provision or verify a client-owned GA4 account/property/web stream.
- Check access roles (who is Administrator vs Editor) on a GA4 account/property.
- Set or verify data retention, timezone, currency, industry category.
- Obtain or hand off a public Measurement ID (`G-…`) for repo/tag configuration.
- Check or create GA4↔Search Console product links.
- Debug Google OAuth loopback/consent flows for any Google API scope.
- Run periodic read-only GA4 + Search Console checkpoints after a deployment or migration.
- Verify whether an attribution repair has produced ordinary live source/campaign rows without overstating sparse data.

## Local context (JMD verified 2026-07-28)

- GA4 OAuth token: `~/.hermes/google_analytics_ga4_token.json` (karanagent20, scopes: `analytics.readonly`, `analytics.edit`, `analytics.manage.users.readonly`; refresh token present, mode 0600).
- Reusable helper: `~/projects/seo-agent/scripts/ga4-api.py` — commands: `accounts`, `property`, `streams`, `bindings`, `retention`, `set-retention`, `links`, `gsc-verify`. Never prints secrets.
- JMD GA4 account: `accounts/400880619` ("JMD Menswear"); property: `properties/545258538` ("JMD-Website", GA4, America/New_York, USD, SHOPPING); web stream: `properties/545258538/dataStreams/15244370633` (display name "JMD Menswear Website — Production"), Measurement ID `G-48R8Q35VGE`, defaultUri `https://jmdmenswear.com` (apex; patched from www on 2026-07-28), retention FOURTEEN_MONTHS (patched from TWO_MONTHS on 2026-07-28).
- karanagent20's GA4 role is Viewer/Analyst, not the Editor the JMD-51 contract requires — proven by `accessBindings` 403 at property AND account level while other reads/writes succeed. Role upgrade + GA4↔GSC link are the two remaining human UI steps.
- GSC write token at `~/.hermes/google_search_console_write_token.json` can check GSC `permissionLevel` for the domain property.
- GCP project 999367204420 ("hermes-492218") had the GA4 Data API disabled on 2026-07-28, but authenticated read-only Data API reports succeeded on 2026-08-28 and 2026-09-04. Treat the old `SERVICE_DISABLED` result as historical; smoke-test live reporting before declaring a current blocker.

## Admin API essentials

Base: `https://analyticsadmin.googleapis.com/v1beta` (most resources) and `/v1alpha` (accessBindings). No API key — OAuth bearer only.

- Discovery list: `GET /v1beta/accountSummaries?pageSize=200` → accounts → propertySummaries.
- Property detail: `GET /v1beta/properties/{id}` → displayName, timeZone, currencyCode, industryCategory, propertyType (GA4 = PROPERTY_TYPE_ORDINARY).
- Streams: `GET /v1beta/properties/{id}/dataStreams` → `webStreamData.defaultUri` + `webStreamData.measurementId`.
- Retention: `GET/PATCH /v1beta/properties/{id}/dataRetentionSettings` with `updateMask=eventDataRetention,resetUserDataOnNewActivity`. Default is `TWO_MONTHS`; contracts usually want `FOURTEEN_MONTHS`. PATCH is an Editor-level mutation.
- Access roles: `GET /v1alpha/{parent}/accessBindings` where parent is `properties/{id}` or `accounts/{id}`. **Requires `analytics.manage.users.readonly` scope** — `analytics.edit` is NOT enough.

Key gaps (verified against discovery doc):
- **No Search Console link endpoints exist in the Admin API** (v1alpha or v1beta — confirmed by walking the discovery doc). GA4↔GSC linking is UI-only: GA4 Admin → Product Links → Search Console Links, done by a verified GSC owner (typically the client's business Google account, not the agent). Plan it as a manual checklist step with instructions, not an API task.
- AccessBindings under `/v1beta` returns an HTML 404 — use `/v1alpha`.
- **`reportingIdentitySettings` does NOT prove Google Signals state.** `BLENDED` is the GA4 default and is returned whether Signals is on or off; `DEVICE_OBSERVED` would confirm Signals off, but the default doesn't confirm either way. Record Signals as "nothing enabled by us" rather than "verified off" unless checked in the UI.
- **Stream displayName and defaultUri are Editor-patchable** via `PATCH /v1alpha/properties/{id}/dataStreams/{streamId}` with `updateMask=displayName` / `webStreamData.defaultUri` — useful for aligning a stream to its contract without UI access.
- **Enhanced Measurement and data-redaction singleton resources are live even when omitted from the REST discovery document.** Use `/v1alpha/properties/{property}/dataStreams/{stream}/enhancedMeasurementSettings` and `/dataRedactionSettings`, and verify field names against the current authoritative `googleapis` proto before mutating.
- **Data-redaction query keys use `queryParameterKeys` in JSON / `query_parameter_keys` in the update mask.** `redactedQueryParameters` is not a valid field and is rejected with HTTP 400. Pair it with `queryParameterRedactionEnabled=true`; query-key matching is case-insensitive and keys cannot contain commas.
- **Protobuf false/default booleans may disappear from JSON readback.** For a setting patched from explicit `true` to `false`, preserve before/patch/after evidence: successful PATCH plus omission from post-readback is the expected false/default representation, not missing proof.
- **Current DataFilter automation is unavailable.** The current Admin API discovery and authoritative `googleapis` proto expose no DataFilter resource, and historical `/properties/{id}/dataFilters` calls return HTTP 404. Treat Developer/Internal Traffic filters as manual GA UI evidence/action unless a current documented API returns; do not guess private endpoints. For Developer Traffic, verify the saved property-scoped filter reads `Developer traffic` / `Exclude` / `Testing`, avoid duplicates, and do not silently promote it to Active. If authenticated screenshot attachments cannot be fetched outside the tracker, directly read back the operator's tracker comment and attachment links, disclose that independent pixel inspection was unavailable, and never overclaim the screenshot review.
- Key-event creation is available at `POST /v1beta/properties/{id}/keyEvents` with `eventName` and explicit `countingMethod`. Google Ads link personalization is patchable through `/v1alpha/{googleAdsLink.name}` with `updateMask=adsPersonalizationEnabled`; preserving the link while turning personalization off is distinct from deleting/unlinking it. Both are live mutations and require explicit issue/user approval plus direct list readback.

For the complete manual DataFilter evidence pattern and the staged production-disabled → separately approved activation → web-record cutover workflow, including split analytics-only vs DNS rollback, see `references/manual-data-filter-and-cutover-gates.md`.

For post-deploy proof that keeps deployment binding, public byte identity, consent-negative behavior, positive network collection, bounded events, GA4-side readback, and attribution authority distinct, see `references/post-deploy-consent-network-proof.md`. A stored grant or mounted private provider is an intermediate state—not evidence that GA4 collected. For the validated production-execution techniques—privacy-safe request reduction, bounded remote-browser scenarios, mixed beacon interpretation, revocation/new-document separation, Realtime schema limits, empty campaign-registry disposition, and durable report+JSON packet creation—also load `references/live-proof-packet-techniques.md`.

For recurring migration checkpoints that pair GA4 Data API windows with Search Console performance/indexing evidence, including clean-worktree isolation, independent freshness boundaries, attribution guardrails, and the Search Analytics aggregation-type compatibility pitfall, use `references/ga4-gsc-periodic-checkpoints.md`.

## OAuth loopback mint pattern (any Google scope)

Reusable for minting a new least-privilege token from an existing installed-app client secret. Working recipe + diagnosis: `references/google-oauth-loopback-mint.md`.

Core rules:

1. Client secret `~/.hermes/google_client_secret.json` is an **installed-app** client with registered redirect `http://localhost` — use `localhost`, never `127.0.0.1`, and a bare path is fine.
2. Bind the capture server to `localhost` on a fixed port and set `redirect_uri='http://localhost:<port>/'`; handle exactly one request.
3. `export OAUTHLIB_INSECURE_TRANSPORT=1` before `flow.fetch_token` (http loopback raises InsecureTransportError otherwise).
4. Keep the auth request minimal: `access_type='offline', prompt='consent'`. Avoid `include_granted_scopes='true'` — it has produced generic, code-less **Error 400** pages.
5. **Generic 400 with no error code** — two distinct causes, disambiguate before "fixing": (a) a stale/zombie consent tab from a previous timed-out run colliding with the new flow (observed: user had an old errored tab open; the fresh URL with identical scopes then rendered fine — always ask the user to close all consent tabs and retry the newest link first); (b) the newly added scope not configured on the OAuth consent screen (testing-mode apps must list scopes explicitly — fix in Cloud Console → OAuth consent screen → Scopes). If the exact same scope set worked minutes earlier, it's (a), not (b).
6. Save the token JSON (token, refresh_token, token_uri, client_id, client_secret, sorted scopes) with mode 0600; persist rotated access tokens back into the same file on refresh.
7. Verify immediately: tokeninfo email + scopes, then one live read call.

## Provisioning checklist (per client)

Work from the client's Linear/issue contract; typical order:

- [ ] `accounts` — find existing client-owned account; never create a duplicate.
- [ ] `property` — confirm displayName, timezone (ET for JMD), currency (USD), category.
- [ ] `streams` — record stream name, stream ID, Measurement ID, defaultUri. Flag www-vs-apex mismatches; Measurement ID works on both hosts, but canonical-host alignment matters for clean reporting (see pitfalls).
- [ ] `bindings` — verify business owner is permanent Administrator, agent account is Editor-only, agent is never sole Administrator.
- [ ] `retention` — set FOURTEEN_MONTHS if contract requires (Editor-sufficient).
- [ ] Google Signals / ads features: read-only note; leave off unless separately approved.
- [ ] Search Console link: verify in UI if present; creating it is a manual step by the verified GSC owner — write instructions, don't attempt via API.
- [ ] Hand off Measurement ID to the repo issue (public config, not a secret). Never hand off tokens or secrets.

## Pitfalls

- **Default retention is 2 months** — always check; provisioning isn't done until it matches contract.
- **`analytics.edit` cannot read access roles.** Mint with `analytics.manage.users.readonly` added, or role verification silently blocks.
- **403 on `accessBindings` at BOTH property and account level (while other reads/writes succeed) = the caller's GA4 role is Viewer or Analyst, not Editor.** Editor+ includes the user-management read permission. This is a usable remote role-detection heuristic when you can't read the bindings themselves — but note the role upgrade itself is always an Administrator's manual UI step.
- **Stream URL recorded at creation time may not match the contract** (JMD stream was created as `https://www.jmdmenswear.com` vs contract's apex). The `G-…` ID is host-agnostic; decide explicitly whether to edit defaultUri, add a second stream (fragments reporting), or accept and note it.
- **GA4 "Editor" ≠ GSC verified owner.** Linking GA4↔GSC needs verified-owner on the GSC side; a GSC `siteFullUser` (what karanagent20 has) is not sufficient.
- **Account/property/stream IDs and the Measurement ID are public-safe configuration** — fine to record in Linear/wiki. Tokens, client secrets, refresh tokens never are.
- The measurement tag only collects after the tag actually ships and consent policy (e.g. JMD-52) is satisfied — provisioning ≠ activation.

## Consent and privacy decision gates

When the website must not make **any** GA4 request before explicit analytics opt-in, do not equate `analytics_storage='denied'` with no collection: a loaded Google tag can still issue cookieless pings. Write the policy as a tag-blocking/basic implementation requirement, then make the wrapper load and event paths no-op until consent.

Turn approved measurement into an executable option-by-option inventory. In particular, GA4 automatic outbound-click collection can include raw URL/text fields; if the policy prohibits those values, keep it off and use a controlled wrapper event with allowlisted categories/placements instead. Keep custom payloads enum-like and pathname-only; state any narrow UTM acquisition exception separately, and configure/verify GA4 data redaction for email and known sensitive query keys before activation.

A reviewed public privacy disclosure and consent-control link are independent activation gates. Do not revive retired/stale legal pages just to attach analytics. Record the approved policy in the tracker, provide a verified implementation handoff, promote only durable business rules to the client wiki, and leave production activation/cutover evidence as downstream work.

See `references/consent-policy-decision-gate.md` for the official Basic-vs-Advanced architecture, exact script/GTM ordering, grant/revoke boundaries, iframe documentation finding, payload rules, disclosure gates, and cross-system-recording pattern.

When evaluating supported alternatives to a directly loaded browser `gtag.js`, including server-side GTM, Google tag gateway/first-party serving, Measurement Protocol, and provider iframes, use `references/consent-gated-ga4-collection-architectures.md`. It separates three questions that must not be conflated: whether the browser tag remains, whether automatic web collection survives, and whether the design provides a real browser-script authority boundary. Reject a cross-origin provider iframe as a **default** on proportionality and lack of documented Google baseline—not as technically impossible. If browser-enforced isolation remains a hard requirement, retain it as a viable custom architecture requiring separate compatibility, storage, cookie, payload-relay, DNS/hosting, and browser-matrix proof.

## Approval boundary

Read-only OK: all discovery, retention GET, bindings GET, tokeninfo, GSC permission checks.

Mutations — require explicit issue/user approval and direct readback:
- PATCH dataRetentionSettings.
- PATCH Enhanced Measurement or data-redaction settings.
- Create/patch/delete key events.
- PATCH Google Ads link personalization; distinguish this from deleting/unlinking the Ads account.
- Any access-role change (add/remove users) — business owner must stay Administrator.

Always-manual (UI or human) unless a current documented API is independently verified: GA4↔GSC product links, Google Signals/global ads-feature toggles, DataFilter/Internal/Developer Traffic configuration, and account creation under the client's identity.
