# Consent-gated GA4 collection architectures

Use this reference when evaluating alternatives to a directly loaded browser `gtag.js` for a consent-gated website, especially when the goals include automatic GA4 web events, no pre-consent Google requests, and a private command or script-authority boundary.

## Decision matrix

| Architecture | Removes browser Google tag? | Preserves automatic web collection? | Provides browser-script isolation? | Small static-site fit |
|---|---:|---:|---:|---|
| Server-side Google Tag Manager (SGTM) | No, not for ordinary automatic web measurement | Yes, when the browser Google tag/GTM sends events to SGTM | No; it controls processing and egress after receipt | Usually disproportionate unless multi-vendor routing, redaction, enrichment, or egress governance is required |
| Google tag gateway / first-party serving | No; it serves the Google tag from the site's domain | Yes | No; origin/routing changes do not sandbox page-executed Google JavaScript | Not a consent-gating or isolation solution |
| GA4 Measurement Protocol (MP) | Only with a custom browser collector and trusted backend | No; MP-only reporting can be partial and automatic collection is not replaced | It can remove Google JavaScript, but only by replacing automatic collection with a bespoke pipeline | Poor fit for ordinary page views/interactions; reserve for genuine server-side or offline events |

No supported Google option simultaneously removes the browser tag, preserves GA4 automatic web collection, and creates a private browser-script authority boundary.

## Server-side GTM

Primary docs:

- https://developers.google.com/tag-platform/tag-manager/server-side/overview
- https://developers.google.com/tag-platform/tag-manager/server-side/intro
- https://developers.google.com/tag-platform/tag-manager/server-side/send-data

Exact Google statements:

> “Server-side tagging allows you to move measurement tag instrumentation from your website or app to a server-side processing container on Google Cloud Platform (GCP), or any other platform of your choosing.”

> “We recommend using Google Analytics tag on a web page to send data to the server container.”

> “You have full control over how that data is shaped, and where it is routed from the server.”

> “Tags are built using the sandboxed JavaScript technology. Permissions give you the visibility into what the tag can do, and policies allow you to set boundaries around the container.”

Interpretation:

- SGTM moves processing, destination routing, and optional transformation to a controlled server environment.
- Google's standard website architecture still uses a browser Google tag or GTM container to observe activity and send events to SGTM.
- SGTM therefore creates a meaningful downstream data/egress boundary, not a security sandbox around the browser collector.
- A custom browser collector could send directly to SGTM, but then the site owns collection semantics instead of retaining GA4's automatic web behavior.
- Google's overview says upgraded Cloud Run deployments can cost `$30-$50 per server per month`; include operational overhead in proportionality decisions.

## Google tag gateway / first-party serving

Current primary docs call the feature **Google tag gateway for advertisers**:

- https://developers.google.com/tag-platform/tag-manager/gateway/setup-guide
- https://developers.google.com/tag-platform/tag-manager/gateway/sgtm-and-cdn
- https://developers.google.com/tag-platform/tag-manager/server-side/dependency-serving

Exact Google statements:

> “Google tag gateway for advertisers lets you deploy a Google tag using your own first-party infrastructure, hosted on your website's domain.”

> “With Google tag gateway for advertisers, your website loads the Google tag from your first-party domain. When the tag fires, some measurement requests will be sent to Google using your first-party domain.”

> “The CDN serves Google scripts directly from your first-party domain for durability. Data is sent to Google through your first-party domain.”

Interpretation:

- Gateway changes where the Google script and some measurement requests appear to originate and how they are routed.
- It preserves automatic collection because the Google browser tag still executes.
- First-party delivery is not first-party authorship and does not restrict the loaded script's page authority.
- Gateway can be combined with SGTM for downstream transformations and egress control, but the combination still does not isolate the browser Google tag.
- Evaluate gateway for first-party transport/durability only when that is an explicit requirement; do not present it as a consent-blocking mechanism.

## GA4 Measurement Protocol

Primary docs:

- https://developers.google.com/analytics/devguides/collection/protocol/ga4
- https://developers.google.com/analytics/devguides/collection/protocol/ga4/sending-events
- https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference

Exact Google statements:

> “The intent of the Measurement Protocol is to augment automatic collection through gtag, Tag Manager, and Google Analytics for Firebase, not to replace it.”

> “While it's possible to send events to Google Analytics solely with the Measurement Protocol, only partial reporting may be available.”

> “The api_secret is private. Don't expose it in the client-side code of your website or app.”

Interpretation:

- Never embed the MP API secret in public browser code.
- A browser-to-owned-backend-to-MP architecture can avoid Google JavaScript, but it requires a custom collector and a secret-holding backend or edge function.
- That custom system must own page-view and interaction listeners, client/session identity, engagement timing, attribution, consent state, retry/deduplication, payload validation, and observability.
- Some event/parameter names are reserved for automatic collection, and Google warns that MP-only reporting may be partial.
- MP is appropriate for offline and genuine server-side events, not as a drop-in replacement for automatic browser GA4 on a small brochure site.

## Automatic collection dependency

Primary docs:

- https://support.google.com/analytics/answer/9234069?hl=en
- https://support.google.com/analytics/answer/9216061?hl=en

Exact Google statements:

> “As long as you use the Google tag or the Google Analytics for Firebase SDK, you don't need to write any additional code to collect these events.”

> “When you enable these options for a web data stream, your Google Analytics tag starts sending events right away.”

Treat automatic and enhanced web events as browser-tag capabilities. If the browser tag is removed, do not promise equivalent automatic collection without explicitly scoping and implementing a replacement collector.

## Recommended pattern for a small static consent-gated site

Prefer the ordinary browser Google tag behind a strict basic consent/tag-blocking gate:

1. Do not fetch or execute the Google tag until explicit analytics consent.
2. Keep advertising-related consent states denied unless separately approved.
3. Load the tag through one narrowly scoped, site-owned loader.
4. Expose only allowlisted analytics commands to the rest of the site's code.
5. Distinguish this application-governance boundary from a true JavaScript sandbox: after consent, the Google tag executes in page context.
6. Verify both negative behavior (no Google script/request before or after denial) and positive behavior (expected bounded events after grant).

Google's basic-consent documentation states:

> “When you implement consent mode in its basic version, you prevent Google tags from loading until a user interacts with a consent banner. This setup transmits no data to Google prior to user interaction with the consent banner.”

Source: https://developers.google.com/tag-platform/security/concepts/consent-mode

## Research workflow note

When Google primary pages must be quoted exactly:

- Retrieve the canonical official page, not a search snippet.
- Preserve the exact URL and quote verbatim from fetched page text.
- Separate what Google explicitly claims from the architecture inference.
- Evaluate three dimensions independently: browser-tag presence, automatic-collection continuity, and authority/isolation. “Server-side” or “first-party” alone does not answer all three.
