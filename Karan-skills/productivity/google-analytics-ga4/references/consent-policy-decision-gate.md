# GA4 Consent and Data-Minimization Decision Gate

Use this pattern when a business must approve GA4 behavior before a website integration or activation. It records an operational measurement choice; it is not legal advice or authorization to publish legal copy.

## 1. Separate "denied consent" from "no pre-consent network traffic"

Google consent mode with `analytics_storage='denied'` can still send cookieless pings if the Google tag is loaded. If the approved posture is **no GA4 traffic before opt-in**, use Google's **Basic Consent Mode** architecture and gate the external Google library/container itself.

### Documented Basic-mode sequence

Google's website guide explicitly permits an inline, top-level-page queue before consent:

1. High in the page `<head>`, create `window.dataLayer` and the local `gtag()` push function.
2. Queue `gtag('consent', 'default', …denied…)` before the banner; queuing `gtag('js', …)` and `gtag('config', …)` is also shown in Google's Basic example.
3. Do **not** request `gtag.js` or the GTM container yet. Google says this queue “doesn't trigger your Google tag, since you haven't loaded the Google tag library yet.”
4. Run the consent UI outside the blocked GTM container.
5. On grant, persist the choice, queue the `consent update`, then dynamically load `gtag.js` or GTM. On later pages with stored grant, restore the state and load normally.

Do not overstate the gate as “never call `gtag()` before consent”: the inline `gtag()` shim only appends to the local data layer and is part of Google's documented Basic implementation. The network boundary is the external Google script/container and all measurement/event dispatch paths.

Google's definitions are decisive:

- Basic: “This setup transmits no data to Google prior to user interaction with the consent banner” and Google tags are blocked.
- Advanced: tags load immediately and, while denied, “send measurements without cookies.”

Record the chosen behavior literally. Do not call an advanced implementation “basic” merely because storage defaults to denied.

Primary Google references:

- Overview: <https://developers.google.com/tag-platform/security/concepts/consent-mode#basic-vs-advanced>
- Basic implementation guide: <https://developers.google.com/tag-platform/security/guides/consent?consentmode=basic>
- Advanced implementation and command ordering: <https://developers.google.com/tag-platform/security/guides/consent?consentmode=advanced>

### Grant, revoke, and teardown boundaries

Documented: update consent on the page where the choice occurs before navigation; persist it; use `gtag('consent','update', …)` for any change, including granted → denied. With GTM consent templates, use `setDefaultConsentState` / `updateConsentState`; do not substitute queued `gtag()` calls because they may miss the next trigger.

For a stricter product policy that forbids even a local pre-consent `dataLayer`, create the queue only after a verified grant, but preserve Google's consent lifecycle inside that startup transaction: queue **default denied → update the approved types to granted → `js`/fixed `config` → load the external tag**. Do not jump directly to a `default` state of granted merely because storage already contains a grant; doing so omits the documented update semantics and makes implementation review ambiguous. This no-queue-before-consent variant is a product extension of Basic tag blocking, not Google's only documented Basic shape.

Not documented by Google: a denied update unloading `gtag.js`/GTM, deleting existing first-party GA cookies, or providing a general tag teardown API. If the business requires **no Google traffic after revocation**, first stop application-owned event dispatch, then issue a consent update denying every governed type, persist the non-granted choice, and reload to discard the in-memory runtime. Verify that the transition itself emits no disallowed request and that the fresh document stays at zero egress. Decide and disclose separately whether existing GA cookies are retained or explicitly cleaned up; reload alone is not cookie deletion. An immediate reload or explicit cookie cleanup is an implementation/policy decision, not a documented Consent Mode guarantee; label it as inference and verify it separately.

### Iframe boundary

Google's installation and Consent Mode guides place the data layer, consent queue, and tag in the measured top-level page. They do not document or recommend putting `gtag.js` inside a sandboxed iframe as the GA4 website architecture. Search hits about “sandboxed JavaScript” and hidden iframes concern GTM custom templates, not GA4 tag isolation. Treat “no official iframe recommendation found” as a bounded documentation-search result—not proof that no Google page anywhere mentions one—and label origin/storage consequences as browser-behavior inference rather than Google guidance.

## 2. Make the measurement inventory executable

For each measurement option, record **on/off**, the post-consent condition, and its parameter boundary.

Keep three inventories separate during architecture and acceptance review:

1. **Application-owned events** — only fixed wrapper names and enum-like parameters callable by site modules.
2. **GA4 automatically collected events** — for example `first_visit`, `session_start`, and `user_engagement`; these are not prevented by an application event allowlist.
3. **Enhanced Measurement events** — page/history views, scrolls, outbound clicks, site search, video, downloads, and form interactions, each adjudicated explicitly.

`send_page_view: false` controls the config-triggered page view; it does not prove that the resulting network inventory contains only the explicit `page_view` and wrapper events. If the approved policy names a behavior such as 90% scroll while generic Enhanced Measurement is disabled, specify the controlled replacement listener/event and its one-shot/idempotency behavior. Acceptance evidence should capture the observed post-consent event/request inventory and reconcile every automatic event with the approved disclosure and policy.

- GA4 automatic outbound-click measurement can report `link_classes`, `link_domain`, `link_id`, `link_url`, and `link_text`.
- If the approved policy excludes raw URLs or free text, turn off the generic automatic click option and measure only controlled destination categories/placements through the site wrapper.
- Disable unused automatic features (file downloads, site search, video, form interactions) explicitly rather than assuming “the page has none” is a permanent safeguard.

Google references:

- <https://support.google.com/analytics/answer/9234069>
- <https://support.google.com/analytics/answer/9216061>
- <https://developers.google.com/analytics/devguides/collection/ga4/views>

## 3. Treat payload design and URL handling separately

Require custom-event values to be allowlisted enum-like fields; do not send names, emails, phone numbers, form values, free text, raw hrefs, raw link text, or user IDs. Use `location.pathname` as the input to a sanitizer, not as a bare `page_location` value: GA4's `page_location` override is a full URL. Construct it from the fixed canonical origin plus an allowlisted/normalized pathname, and omit query and fragment unless the approved acquisition contract defines a narrow exception.

Specify `page_referrer` independently. Its default is `document.referrer`, which may contain a full URL; choose an explicit sanitized full URL, an intentionally fixed/empty value if supported by the reporting contract, or another documented bounded transformation. Do not say merely “sanitized page fields” without exact examples and browser assertions.

If standard acquisition needs UTM reporting, name that narrow exception explicitly and do not add a redundant custom UTM landing event. Removing every query parameter while promising standard GA4 campaign attribution is contradictory. Define exactly how approved `utm_source`, `utm_medium`, and `utm_campaign` values survive—such as a registry/allowlist plus fixed campaign config fields—while every other query key and the fragment remain excluded. GA4 stream data redaction can redact likely email addresses and **named** query parameters across URL-bearing event parameters including `page_location`, `page_referrer`, and `link_url`; it is a required configuration/verification step, not a substitute for safe event design.

Google references:

- <https://developers.google.com/analytics/devguides/collection/ga4/views>
- <https://developers.google.com/analytics/devguides/collection/ga4/reference/config>
- <https://support.google.com/analytics/answer/13544947>

## 4. Keep public disclosure as an independent activation gate

Before production collection, require a reviewed public privacy disclosure at a stable URL and a consent-control link to it. If a migration deliberately retires stale legal pages, do not revive, copy, or redirect them just to satisfy the analytics implementation. Open a separately reviewed content/legal work item instead.

## 5. Record the decision across the right systems

1. Update the Linear policy issue body with the exact approved settings and checked decision criteria; leave public-disclosure, implementation, and production-proof criteria unchecked until evidenced.
2. Add a concise GitHub implementation handoff comment stating the policy and no-live-change boundary. Capture its comment ID/URL and read it back directly.
3. Promote only durable business rules (consent posture, data-minimization rules, persistent activation gates) into the canonical client wiki page. Keep tracker state, raw validation output, and temporary evidence in Linear/GitHub.
4. Keep the issue In Progress until the disclosure, implementation, and production/cutover evidence exist. Policy approval alone is not activation approval.
