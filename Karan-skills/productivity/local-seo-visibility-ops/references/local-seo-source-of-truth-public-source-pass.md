# Local SEO Source-of-Truth Public Source Pass

Use this reference when turning a private local SEO source-of-truth artifact from a blank draft into a useful approval packet.

## Pattern

Before asking the human for every missing field, inspect public read-only sources and prefill what is safely observable.

Good sources:

- Live homepage and obvious about/contact/inquiry routes.
- Public bio/link-in-bio pages owned by the business/person.
- Existing schema/JSON-LD in the deployed site.
- User-supplied GBP public/share links.

## What to capture from the website

- Canonical website URL and canonical route form.
- Visible phone, email, location, Instagram/social links.
- Inquiry URL or anchor, including service-prefill URL patterns if present.
- Form processor endpoint only as internal/private implementation detail, not customer-facing copy.
- CTA language.
- Live package/service names and service timing/details.
- Meta title, meta description, canonical link.
- JSON-LD type, locality, areaServed, priceRange, sameAs, service/offer catalog basics.
- Visible asset URLs and alt text to seed the later photo/proof inventory.

## Reconcile instead of overwrite

If the live website differs from older business plan/wiki language, preserve the conflict as a decision point:

- Mark old terms as legacy/internal until approved.
- Prefer live website terms for current public-facing draft fields.
- Add a required-input item for the human to retire or revive legacy wording.

## GBP share link handling

For a user-supplied GBP share/search link:

- Record the original share link.
- If the redirect reveals a knowledge graph/place ID or query, record it.
- If Google returns a CAPTCHA/anti-bot/sorry page, do not treat that as a profile audit failure and do not guess fields.
- Mark GBP profile fields as needing read-only API/dashboard verification.

## Safety rule

Observed public facts can be used to improve the private source-of-truth artifact, but they are not authorization to mutate GBP, directories, website code, review replies, social profiles, or public listings. Keep those approval-gated.
