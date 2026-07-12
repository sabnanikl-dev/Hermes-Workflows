# GBP Email Performance Report Baseline

Use this when Google Business Profile sends a monthly email such as "Your performance report for <month>" and the user asks how to improve the numbers.

## Pattern

1. Treat the email as a quick baseline, not a full audit.
2. Extract the raw monthly figures from the email body:
   - interactions
   - calls
   - website visits from profile
   - chat/message clicks
   - profile views
3. Calculate simple rates before recommending work:
   - interaction rate = interactions / profile views
   - website click rate = website visits / profile views
   - call rate = calls / profile views
4. If the action rate is strong but profile views are tiny, frame the problem as **discovery/trust/relevance**, not just CTA/conversion.
5. Convert “order of magnitude” into explicit targets. Example: 22 profile views → 220/month; 8 interactions → 80/month.
6. Use the email to trigger the normal visibility sequence:
   - read-only GBP/API or dashboard baseline
   - Search Console baseline
   - UTM and conversion tracking check
   - GBP completeness/category/services/photo/review action list
   - review velocity workflow
   - primary local service page before page sprawl
   - directory authority and monthly reporting cadence

## Interpretation heuristic

- Low profile views + good interaction rate: prioritize surfacing more often via category/service relevance, photos, reviews, directories, Search Console-indexed service pages, and local authority.
- Profile views up + actions flat: prioritize profile conversion, photos, services, CTA, messaging readiness, and website friction.
- Website clicks up + inquiries flat: prioritize inquiry form/CTA/conversion tracking.
- No chat clicks: decide whether messaging is operationally safe before enabling; bad response times can hurt trust.

## Guardrails

- The email does not authorize GBP edits, directory submissions, review replies, posts, or public changes.
- Keep public mutations approval-gated: current value → proposed value → reason → explicit approval → mutate → verify.
- Do not over-index on blog volume when reviews, proof, photos, and the primary local service page are still immature.
