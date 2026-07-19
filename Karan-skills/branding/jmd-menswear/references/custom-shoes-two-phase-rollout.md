# JMD Custom Shoes — Two-Phase Static-Page Rollout

Use when turning the made-to-order shoe catalog into JMD website work.

## Authority

Karan has confirmed that Lucky's answers are sufficient stakeholder approval for JMD website copy and commerce-adjacent made-to-order handoffs. Karan still owns deploy/public-launch approval.

## Phase 1: crawlable Made-to-Order inspiration page

Ship a focused static `/custom-shoes-conyers-ga/` page before any per-shoe commerce-adjacent buttons:

- Use a small, provenance-recorded curated subset of owner-supplied metadata. For the 2026 packet, the allowed v1 selection is the Patina Goodyear Welt subset.
- Present the six shoes as **inspiration from the JMD Made-to-Order range**. They are not stocked or physically available as in-store examples; do not invite visitors to come see them or discuss their leathers/lasts in the showroom.
- The approved collection destination is **Build your custom shoes** → `https://jmdmenswear.made-to-order.com/get-inspired/?_cfg=1&idc=4341`, opened in a new tab with `rel="noopener"`.
- That exact URL is Phase 1's **sole page-specific conversion destination**. Repeating the same destination in the hero, carousel handoff, and closing section is acceptable; page-specific Call, Directions, visit, or showroom-first alternatives are not. Global site nav/footer contact boilerplate is outside this page-specific contract.
- It is safe to say shoes are handmade in Spain; typical delivery is 3–6 weeks depending on style, with basic styles sometimes under 4 weeks.
- State that payment and delivery occur on the separate made-to-order site; never describe a JMD-hosted checkout.
- Exclude prices, inventory, size/availability claims, carts, accounts, Product/Merchant schema, and raw vendor marketing copy.

## Phase 2: model-level Customize / Order CTAs

Keep these separate from the page PR.

1. Capture each exact image/customize/order tuple in a repo-visible allowlist keyed by model ID.
2. Pin the tuple, not merely its URL shape; shape-valid substitutions are unsafe.
3. Fresh-QA each exact customization and order destination in a real browser at desktop and mobile widths. Confirm it reaches the intended product-specific flow, not an error/no-results/generic state.
4. Do not submit an order, enter payment, create an account, or send customer data during QA.
5. Enable only rows with fresh recorded browser evidence; missing, failed, stale, future-dated, or otherwise invalid QA must fail closed and render no per-shoe external CTA.
6. Render enabled CTAs in a new tab with `target="_blank" rel="noopener"`. Because model-level destinations would intentionally change Phase 1's sole-destination contract, update the source packet, machine-readable allowlist, validator invariants/self-tests, page copy, and PR description together in the separate Phase 2 PR. Do not reintroduce Call/Directions/visit alternatives as part of that work.

## Legacy migration boundary

Legacy WordPress shoe URLs redirect to the page route through the dedicated redirect issue. Do not mix redirect configuration, page UI, or external-account changes into either phase.

## Pitfalls

- Do not use the stale `http://jmdmenswear.made-to-order.com/getinspired/#` endpoint; it is blocked.
- Do not treat a collection builder URL as interchangeable with a product-specific configurator/order link.
- Do not turn a curated source packet into 1,582 public product routes without a separate catalog/SEO decision.
- A copy correction is not complete if executable contracts still encode the rejected behavior. Sweep visible copy, metadata, FAQ/JSON-LD, source packet, PR body, allowlist JSON, validator comments/invariants/messages, and negative self-tests. A green validator can be wrong when it certifies a stale contract.
