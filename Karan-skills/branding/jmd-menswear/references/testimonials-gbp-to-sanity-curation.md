# JMD Testimonials: GBP Review Candidates → Sanity Curation → Website Carousel

Use this when populating JMD's homepage testimonials carousel from Google review data.

## Durable workflow

The correct publishing path is:

```text
Google review candidate
→ Sanity `testimonial` draft
→ Karan/Lucky approval
→ `status = "published"`
→ generated `site/assets/js/testimonials.data.js`
→ homepage `#reviews` carousel
```

Do **not** hand-author Google review copy directly into `site/assets/js/testimonials.data.js` as the durable website path. The site already has the right CMS/data-contract architecture; Sanity is the curation and approval layer.

## Repo anchors

- Website repo: `sabnanikl-dev/jmd-6-holding-page-harness`
- Frontend carousel added by issue/PR #112/#121.
- Population tracker opened as issue #122: "Populate homepage testimonials from approved Sanity review records".
- Backend/schema contract from #113:
  - `studio/schemaTypes/testimonial.ts`
  - `docs/api/sanity-testimonials-contract.md`
  - `scripts/validate-testimonials-contract.mjs`
- Empty public artifact by design until approved records exist:
  - `site/assets/js/testimonials.data.js`

## Candidate selection criteria

Prefer initial cards that are:

- 5-star reviews only.
- Specific, positive, and trust-building.
- Service/showroom/fitting/formalwear focused.
- Concise enough for homepage cards or safely excerptable without changing meaning.
- Free of private/sensitive personal detail unless Karan/Lucky explicitly approve the excerpt boundary.
- Free of claims that imply live inventory, prices, stock counts, size availability, checkout, or exact item availability.

## API access pattern

1. Try the dedicated GBP OAuth / Business Profile Reviews API path first when available.
2. Verify token identity, granted `business.manage` scope, account discovery, **and target JMD location visibility** before trusting results. A valid token can still be insufficient if Account Management / Business Information only returns unrelated locations.
3. If the dedicated GBP token refreshes but JMD is absent from accessible locations, treat the blocker as an access/manager-location visibility gap — not as a broken token. Report the visible account/location evidence without printing secrets, then use a read-only public Google listing fallback for candidate discovery only.
4. If the dedicated GBP token fails refresh or full GBP inventory access is blocked, a read-only Google Places API lookup or Google Maps reviews panel can provide public review samples for candidate discovery only.
5. Make clear in the issue/comment whether candidates came from full GBP Reviews API inventory, public Places API sample, or public Google Maps review panel.

Do not encode transient auth failures as permanent limitations. If the GBP token fails, the durable next step is to reauthorize the dedicated token with:

- `https://www.googleapis.com/auth/business.manage`
- `openid`
- `https://www.googleapis.com/auth/userinfo.email`

If the token is valid but JMD is not visible, the durable next step is to ensure the OAuth account has Manager/Owner access to the JMD location/account, then rerun Account Management + Business Information discovery before attempting Reviews API pulls.

## Google Maps review-panel fallback technique

When full GBP review inventory is blocked but public candidate discovery is still useful:

1. Open the listing's reviews panel directly when possible. For JMD, a known working pattern is a Google Maps place URL with the reviews tab segment `!9m1!1b1` for the listing/place ID.
2. Record listing-level evidence visible in the panel: business name, rating, total review count, 5-star count when shown, and the exact Maps URL used.
3. Use browser/DOM inspection to read visible reviews; scroll the inner Maps panel, not only the page. Google Maps often lazy-loads more reviews after setting the review panel container scroll position near the bottom.
4. Click visible `More` buttons before copying long reviews so excerpts are grounded in full observed text.
5. Select only 5-star candidates matching the testimonial criteria. For homepage excerpts, avoid operational promises such as exact alteration speed, last-minute turnaround, stock/availability, price, or sensitive personal context unless Karan/Lucky explicitly approve that boundary.
6. In GitHub issue comments, label this clearly as a **read-only public Maps fallback**, not full GBP Reviews API coverage, and keep all records as Sanity `draft` candidates pending approval.

## Places fallback output to persist

When using Places fallback, persist enough metadata in the GitHub issue/comment for later Sanity drafting:

- reviewer display name
- rating
- full observed review text
- recommended excerpt
- publish time if available
- review resource name / ID if available
- listing identity and Maps CID URL
- note that Karan/Lucky approval is required before publishing

## Strong initial candidates observed in session

The Google listing matched:

- Business: `JMD Menswear`
- Address: `Conyers Exchange Shopping Center, 1543 Hwy 138 SE Ste a, Conyers, GA 30013`
- Rating observed: `4.8`
- Review count observed: `133`
- Maps CID URL: `https://maps.google.com/?cid=8674831763365312196`

Good first candidate themes:

1. **Guided process / first-time confidence** — best for customers who do not know where to start.
2. **Customer service + attention to detail** — clean service-quality proof.
3. **Tuxedo rental / fitting confidence** — supports rental conversion.
4. **Owner/community proof** — strong but screen carefully for sensitive context.
5. **One-stop-shop proof** — useful backup card, often less polished.

## Recommended persistence choice

If the user asks whether to include candidate reviews in the issue, docs, or a PR:

- Put candidate review notes in the GitHub population issue first.
- Open a PR only when adding actual implementation: Sanity draft seeding scripts, artifact generation scripts, validation, or docs contract updates.
- Avoid a docs PR that merely stores customer review copy unless it has a clear operational purpose and approval boundary. The source of truth should become Sanity, not markdown.
