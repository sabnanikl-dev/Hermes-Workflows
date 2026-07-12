# Hermes Personal product scout: NotebookLM rate-limit fallback

Use this reference when a Hermes Personal passive-revenue/product-scout cron is required to query AI OS, Strategic Engineering, and Ai money, but NotebookLM `ask` is rate-limited or rejected.

## Durable pattern

1. Verify NotebookLM auth first; do not assume auth is the issue.
2. Attempt each required notebook separately with the required full digest/prompt.
3. If a notebook fails with rate-limit/rejection, retry once with a compact prompt and plain-text output.
4. If the compact retry also fails, mark that notebook as `blocked + rate-limited/rejected` in the final response and continue with repo-local work.
5. Do not fabricate NotebookLM grounding and do not stall the whole run.
6. Use the best available repo-local evidence: current product workspace, validators, experiment ledger, open issues/PRs, and read-only adversarial reviewer findings when present.
7. Choose exactly one safe repo-local move. If adversarial findings identify unresolved P0/P1 product blockers, prefer a product experiment/gate that addresses the blocker over more copy polish.
8. Record the blocker in the experiment ledger only if it is the experiment/blocker being tested; otherwise report it in the final NotebookLM grounding section.

## Good fallback move example

When copy-layer buyer clarity is mostly fixed but adversarial review flags the selected buyer as possibly thin/low-WTP, run an audience-segment comparison experiment instead of polishing more artifacts:

- Surface: `audience segment`
- Metric: buyer-segment evidence score
- Score both candidate buyers on: evidenced pain, budget/WTP evidence, channel/accessibility, and low-fulfillment digital-pack fit.
- Decision is usually `hold` unless one segment clearly wins and the public-live gates remain closed.

This turns a blocked NotebookLM run into a useful repo-local decision gate without pretending proxy metrics are market proof.

## Final-report wording

Use explicit blocked status per notebook:

```text
NotebookLM grounding:
- AI OS: blocked — auth passed, but ask was rate-limited/rejected on full prompt and compact retry.
- Strategic Engineering: blocked — same.
- Ai money: blocked — same.
```

Then state the repo-local grounding used instead, especially adversarial findings and validator evidence.
