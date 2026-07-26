# Product Deal Watcher Validation

Use this pattern when a recurring scout should alert only on genuinely actionable purchases—not every listing under a nominal budget ceiling.

## Core distinction

A **budget-qualified listing** is not necessarily a **buy-worthy deal**. Encode both:

- **Eligibility:** exact product family, capacity, form factor/interface, component technology, condition, and seller class.
- **Value:** a price threshold appropriate to that exact tier and intended use.

If either side is uncertain, fail closed and emit no alert.

## Layered design

1. **Research prompt:** State exact model/capacity/technology allowlists, explicit denylists, price bands, condition, retailer rules, and direct-page verification requirements. Say plainly that this is a buy-worthy-deal watcher rather than generic inventory search.
2. **Strict output protocol:** Require one machine-readable candidate line or a no-alert marker. Suppress prose.
3. **Deterministic parser:** Reject malformed output before delivery formatting.
4. **Product gate:** Independently validate tier, capacity, and model against explicit allowlists. Add known-ineligible families to a denylist for defense in depth.
5. **Retailer gate:** Parse and normalize the URL hostname, then require an approved retailer/manufacturer domain. A plausible retailer label in model output is insufficient. Marketplace hosts still need first-party seller verification from the live product page.
6. **Active-offer verifier:** Check structured product/variant data for current one-time purchase price and availability. Ignore MSRP, crossed-out prices, installment amounts, recommendation cards, and stale snippets. Fail closed on disagreement.
7. **Silent delivery:** Empty stdout means no notification. Lookup, parsing, and verification failures should stay silent rather than emit pseudo-deals.

## Regression matrix

| Case | Expected |
|---|---|
| Original false-positive product and retailer | Silent rejection |
| Ineligible product from an approved retailer | Silent rejection |
| Eligible product from an unknown retailer | Silent rejection |
| Eligible product above its tier ceiling | Silent rejection |
| Eligible product, retailer, price, and capacity | One formatted alert |
| Malformed scout output | Silent rejection |

Provide dependency overrides such as `SCOUT_BIN`/`HERMES_BIN` and `PRICE_VERIFIER` so tests inject deterministic output without live shopping requests or messaging delivery.

## Script and scheduler closeout

- Run shell/parser syntax checks.
- Verify the script remains executable after edits; restore its intended mode if needed.
- Run the fixture matrix and require zero failures.
- Re-read scheduler state and verify the enabled job still references the expected script, schedule, delivery target, and future next-run time.
- Avoid using a live scheduled run as the primary regression test when it could deliver a false alert; fixture-test first.

## Pitfalls

- Broad brand-level eligibility lets low-end or wrong-technology products leak into alerts.
- A permissive phrase such as “other established retailers allowed” defeats a retailer allowlist.
- Reusing a general budget ceiling as a deal threshold creates technically valid but poor-value alerts.
- Prompt-only controls are insufficient for unattended delivery; enforce key criteria again in deterministic code.
- Do not trust a successful prior cron run as proof that a newly edited script is executable and valid.