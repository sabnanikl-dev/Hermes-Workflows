# GA4 Consent and Data-Minimization Decision Gate

Use this pattern when a business must approve GA4 behavior before a website integration or activation. It records an operational measurement choice; it is not legal advice or authorization to publish legal copy.

## 1. Separate "denied consent" from "no pre-consent network traffic"

Google consent mode with `analytics_storage='denied'` can still send cookieless pings if the Google tag is loaded. If the approved posture is **no GA4 traffic before opt-in**, the implementation must use a basic/tag-blocking design: do not insert or initialize the tag, call `gtag`, or dispatch events until explicit analytics consent.

Record the chosen behavior literally. Do not call an advanced consent-mode implementation “basic” merely because storage defaults to denied.

Google reference: <https://support.google.com/analytics/answer/13802165>

## 2. Make the measurement inventory executable

For each measurement option, record **on/off**, the post-consent condition, and its parameter boundary.

- GA4 automatic outbound-click measurement can report `link_classes`, `link_domain`, `link_id`, `link_url`, and `link_text`.
- If the approved policy excludes raw URLs or free text, turn off the generic automatic click option and measure only controlled destination categories/placements through the site wrapper.
- Disable unused automatic features (file downloads, site search, video, form interactions) explicitly rather than assuming “the page has none” is a permanent safeguard.

Google reference: <https://support.google.com/analytics/answer/9216061>

## 3. Treat payload design and URL handling separately

Require custom-event values to be allowlisted enum-like fields; do not send names, emails, phone numbers, form values, free text, raw hrefs, raw link text, or user IDs. A safe default page field is `location.pathname`, not the full location.

If standard acquisition needs UTM reporting, name that narrow exception explicitly and do not add a redundant custom UTM landing event. GA4 stream data redaction can redact likely email addresses and **named** query parameters across URL-bearing event parameters including `page_location`, `page_referrer`, and `link_url`; it is a required configuration/verification step, not a substitute for safe event design.

Google reference: <https://support.google.com/analytics/answer/13544947>

## 4. Keep public disclosure as an independent activation gate

Before production collection, require a reviewed public privacy disclosure at a stable URL and a consent-control link to it. If a migration deliberately retires stale legal pages, do not revive, copy, or redirect them just to satisfy the analytics implementation. Open a separately reviewed content/legal work item instead.

## 5. Record the decision across the right systems

1. Update the Linear policy issue body with the exact approved settings and checked decision criteria; leave public-disclosure, implementation, and production-proof criteria unchecked until evidenced.
2. Add a concise GitHub implementation handoff comment stating the policy and no-live-change boundary. Capture its comment ID/URL and read it back directly.
3. Promote only durable business rules (consent posture, data-minimization rules, persistent activation gates) into the canonical client wiki page. Keep tracker state, raw validation output, and temporary evidence in Linear/GitHub.
4. Keep the issue In Progress until the disclosure, implementation, and production/cutover evidence exist. Policy approval alone is not activation approval.
