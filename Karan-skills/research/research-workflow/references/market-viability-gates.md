# Market Viability Gates for Offer / Landing-Page Ideas

Use this when a repo-local idea, offer sketch, landing-page draft, or revenue experiment sounds plausible but may not be viable. The key lesson: **a clear landing page is not evidence of market demand**.

## Trigger

Run this gate before continuing to polish or operationalize a market-facing artifact when:

- the artifact is an offer, productized service, lead magnet, landing-page draft, pricing hypothesis, or revenue experiment;
- the user questions whether the idea is actually viable;
- a scheduled scout proposes market-facing copy from internal repo evidence;
- the next step would otherwise drift toward publication, outreach, payment setup, or sales.

## Principle

Separate two questions:

1. **Marketed value:** Can we explain the artifact clearly?
2. **Market viability:** Is there enough external evidence to keep investing?

Do not let a strong marketed-value score substitute for viability. Trend pieces alone are weak evidence unless paired with buyer pain, alternatives, pricing/spend, or distribution signals.

## Bounded research pass

Default budget:

- 5–8 public sources;
- no more than 8 search queries;
- no private communities, private data, client data, outreach, payment setup, or external mutation without explicit approval.

Evidence requirements:

- at least 2 buyer-pain or demand sources;
- at least 2 alternatives, competitors, substitutes, or incumbents;
- at least 1 pricing/spend/willingness-to-pay signal;
- at least 1 distribution path or reachable audience signal;
- explicit evidence against the idea or unresolved caveats.

Useful source types:

- competitor and pricing pages;
- product directories and GitHub topics;
- public forum threads or social snippets;
- job posts / role descriptions;
- analyst/vendor articles;
- review snippets;
- public docs and case studies.

## Output shape

Create a viability brief with:

```md
# <Idea> Viability Brief

## Idea
- Current package:
- Proposed buyer:
- Proposed pain:
- Proposed outcome:

## Evidence table
| Source | Type | What it shows | Supports | Caveats |

## Buyer and pain evidence
## Alternatives and competition
## Differentiation / wedge
## Willingness-to-pay and distribution

## Viability score
| Category | Score 0–3 | Evidence |
| Buyer specificity |
| Pain evidence |
| Alternatives / competition |
| Differentiation |
| Willingness-to-pay signal |
| Distribution path |
| Proof burden |
| Safety / authority fit |
| **Total** |

Decision: continue | narrow | pivot | hold | kill

## Recommended next safe step
- Next repo-local step:
- Human approval required before:
- Validation questions if interviews/outreach are approved:
```

## Decision meanings

- **continue** — enough evidence to keep the current offer direction and propose a human-approved validation step.
- **narrow** — same general direction, but tighten buyer, pain, wedge, or channel before more drafting.
- **pivot** — switch buyer, pain, packaging, or distribution.
- **hold** — keep as internal utility until better demand evidence appears.
- **kill** — archive the market angle; do not keep polishing.

## Example lesson from Hermes Personal

A repo-local “Bounded Autonomy Loop” landing-page draft was clear and had internal proof artifacts, but Karan correctly flagged that clarity did not prove viability. A bounded scan found public demand language around agentic AI governance, guardrails, observability, and audit trails, plus enterprise alternatives and open-source/tooling substitutes. The result was **narrow**, not continue: the broad “AI governance” framing was too crowded; the stronger wedge was “one safe scheduled-agent loop for GitHub-first founders/agencies that need agents to stop before production/outreach/payment/private-data boundaries.”

## Pitfalls

- Do not publish, message prospects, buy tools/domains, or create payment links as part of the gate.
- Do not treat internal repo usefulness as market proof.
- Do not keep polishing a landing page when the gate says narrow/pivot/hold/kill.
- Do not cite only vendor trend articles; pair them with buyer pain, alternatives, spend, or distribution evidence.
- Do not use private/client data as proof unless explicitly approved and sanitized.
