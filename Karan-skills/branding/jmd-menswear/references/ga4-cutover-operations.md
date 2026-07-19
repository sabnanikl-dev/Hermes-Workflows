# JMD GA4 Cutover Operations

Use this reference when planning or executing analytics around the JMD WordPress-to-new-host migration.

## Verified legacy state (2026-07-12)

Read-only inspection of the live WordPress homepage found:

- legacy Universal Analytics destination `UA-57032133-1`;
- Google Ads destination `AW-982486914`;
- a phone-conversion configuration for JMD's public store number;
- no GA4 `G-...` destination.

Treat the UA destination as legacy, not as current measurement continuity. Do not silently copy or remove the Ads/phone-conversion setup: first verify ownership/activity and record an owner-approved **preserve / replace / retire** decision.

## Architecture decision

- Provider: Google Analytics 4.
- Install through the direct Google tag (`gtag.js`) and public `G-...` Measurement ID.
- Defer Google Tag Manager until multiple approved destinations justify the extra container/permission surface.
- Keep repo calls behind one provider-agnostic wrapper/helper.
- Use GA4's standard campaign/source dimensions for UTM landings; do not add a redundant `gbp_utm_landing` event.
- Google Ads, remarketing, campaigns, conversion actions, billing, and legacy phone conversion remain separately approval-gated.

## Ownership and setup contract

Prefer durable business ownership:

- Analytics account: `JMD Menswear` (only if no suitable JMD-owned account exists).
- GA4 property: `JMD Menswear Website — GA4`.
- Timezone: Eastern Time; currency: USD.
- Production stream URL: `https://jmdmenswear.com`.
- Stream name: `JMD Menswear Website — Production`.
- `jmdmenswear@gmail.com`: permanent business Administrator.
- Karan's normal Google account: Administrator backup.
- `karanagent20@gmail.com`: Editor only when Hermes needs configuration access; never sole Administrator.
- Retention: 14 months.
- Keep Google Signals/advertising features off until separately approved.

The Measurement ID is public configuration, not a secret. Numeric Property ID and Stream ID are useful for internal evidence/API work. Never request or store passwords, recovery codes, OAuth secrets, or service-account keys in repo/issues.

## Work split

Keep account/operations work in the JMD Visibility Linear project and coding in GitHub:

1. Provision/confirm account, property, production stream, roles, retention, and Search Console link.
2. Approve consent/privacy, Enhanced Measurement, PII, key-event, and traffic-filter policy.
3. Audit legacy Ads/UA/phone-conversion configuration and decide preserve/replace/retire.
4. Implement the direct GA4 tag and event wrapper in the website repo.
5. Run pre-cutover/cutover continuity verification.
6. Monitor GA4 + GSC for 4–8 weeks and produce owner-facing reporting.

For the 2026 migration packet, Linear JMD-49 is the parent; JMD-51 through JMD-55 own those non-coding slices, and GitHub #102 owns implementation. Treat those identifiers as historical pointers, not universal naming requirements.

## Privacy and event rules

Before production activation, explicitly decide consent behavior. Conservative default: basic consent mode, with Analytics not loading before analytics consent. Do not invent legal conclusions in code.

Never send names, emails, phone numbers, form values, free text, or other PII. Keep parameters to public-safe values such as page path, CTA location, section, and public content slug/category.

High-value candidate key events:

- `cta_call_click`
- `cta_directions_click`
- `cta_contact_click`
- `cta_rentals_click`
- `cta_wedding_group_click`

Ordinary events unless separately approved:

- `social_instagram_click`
- `showroom_section_view`
- `showroom_photo_view`
- `showroom_lightbox_open`
- `blog_article_view`

## Pre-cutover and cutover checks

If several useful days remain, approval may be sought to add the **same** production GA4 destination to WordPress for a short baseline. Since WordPress already loads `gtag.js`, ensure there is still only one loader. If cutover is imminent, explicitly waive this short GA baseline rather than delaying migration; retain the GSC before-state.

At cutover verify:

- production tag loads exactly once;
- collection is restricted to approved production hostname behavior;
- preview/local traffic is no-op or debug-only;
- Realtime/DebugView receives representative page and action events;
- no PII/form values are transmitted;
- UTMs survive HTTP/HTTPS, www/apex, and legacy redirects;
- no duplicate page views, analytics errors, self-referrals, or preview hostnames appear.

Normal reports may lag 24–48 hours. Save browser/network and Realtime/DebugView evidence; do not call implementation-only evidence production continuity.

## Post-cutover interpretation

Monitor weekly for at least four weeks and continue to eight when unstable. Pair GA4 with GSC:

- impressions + clicks down: investigate visibility/indexing;
- impressions stable but GA4 sessions down: investigate tag/attribution/redirects;
- sessions stable but key actions down: investigate landing-page/CTA behavior;
- GA4 flat while GSC clicks continue: suspect analytics implementation before declaring lost traffic.

Owner-facing reporting for Lucky/Danny should emphasize calls, directions, contact/rental actions, GBP/organic landings, and evidence-backed next actions—not raw GA terminology.