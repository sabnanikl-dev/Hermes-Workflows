# Passive-Revenue Digital Product Validation

Use this when Karan wants a passive or low-fulfillment revenue product, especially a PDF, prompt pack, source map, spreadsheet/checklist, NotebookLM/AI query pack, or marketplace-ready digital download.

## Core lesson

Do not let the work drift into a service offer. The product should be an immediate-value asset that can be bought once and used without Karan providing custom fulfillment.

Good product shape:

```text
narrow expensive question
  -> NotebookLM synthesis from an owned/specific notebook
  -> bounded public market research
  -> source map
  -> viability + marketability scoring
  -> product pack files
  -> non-public setup using agent-owned accounts
  -> approval-ready external drafts
  -> Telegram approval
  -> human-approved launch only
```

Bad product shape:

```text
generic AI money idea
  -> broad prompt dump or hype PDF
  -> unsupported income/ROI claims
  -> custom consulting or implementation burden
```

## Research pattern

1. **Use NotebookLM as one input, not the authority**
   - Query the specific notebook the user names.
   - Ask for product formats, buyer segments, painful questions, anti-patterns, and one recommended next artifact.
   - Do not commit raw NotebookLM output; distill it.

2. **Pair NotebookLM with public marketplace research**
   - Search Gumroad/Payhip/Etsy/product pages for comparable digital downloads.
   - Capture real pricing, page count/format, deliverables, buyer promise, and saturation signals.
   - Treat marketplace counts and vendor claims as directional, not proof of sales.

3. **Separate viability from marketability**
   - Viability: buyer specificity, pain evidence, alternatives, differentiation, willingness-to-pay, distribution, proof burden, safety.
   - Marketability: hook, channel, buyer language, why it does not look like generic AI slop, and what external approvals are needed.

4. **Prefer a product-pack workspace**

```text
products/<slug>/
  README.md
  brief.md
  source-map.md
  prompts.md
  workflow-blueprint.md
  validation-checklist.md
  landing-copy-draft.md
  sample-posts-for-approval.md
  launch-approval-packet.md
  external-setup-checklist.md
```

5. **Keep public-live action gated**
   - Draft X/Threads/Reddit/LinkedIn posts, Gumroad/Payhip/Etsy listings, waitlist copy, and outreach only as approval-required artifacts.
   - Non-public account/workspace/listing setup may proceed only when the user has explicitly allowed it for the repo/project.
   - Do not publish, list publicly, message, activate checkout/payment/waitlist links, buy domains/tools, enter paid plans, or make income/ROI/legal/compliance claims without explicit approval.

## Agent-owned account setup pattern

When Karan wants the agent to handle external setup without using his personal accounts:

- record the approved agent-owned account identity in the repo harness and product checklist;
- default to `karanagent20@gmail.com` only when the user has explicitly named it for that experiment;
- create or configure only non-public/draft accounts, workspaces, listings, forms, and checkout/product-delivery setup before approval;
- stop and ask when a setup flow requires CAPTCHA, phone verification, tax/bank/KYC, paid-plan decisions, or missing credentials;
- do not ask Karan to do platform work unless one of those blockers requires him.

Approval requests should go to the Telegram origin chat when Karan asks for approvals there. Write them so he can simply reply `approve`:

```md
Approval requested: <one-line public-live action>

What will go live:
- ...

Account/platform:
- ...

Public URL or draft target:
- ...

Claims included:
- ...

Risk/caveat:
- ...

If approved, I will:
- ...
```

## Evidence targets before selling

A candidate product should not move toward external launch until it has:

- 5+ public pain/demand sources for the specific use case;
- 5+ alternatives/substitutes/competitors;
- 2+ pricing or willingness-to-pay signals;
- 2+ distribution/channel signals;
- explicit caveats/evidence against;
- a buyer for the product artifact itself, not only for the underlying service/workflow.

## Positioning rules

Avoid broad claims like:

- “AI money pack”;
- “make passive income with AI”;
- “100 prompts to make money”;
- “get paywalled info for cheap”;
- “AI automation for everyone.”

Prefer narrow, outcome-specific language:

- “one specific local-business automation offer, researched and packaged”;
- “source map + prompts + workflow blueprint so you can validate before building”;
- “a buyer-safe product pack, not a done-for-you service.”

## NotebookLM-grounded product scout pattern

When a scheduled product scout uses NotebookLM plus repo state:

1. Verify repo/remotes and stop on unknown dirty edits before querying.
2. Build a compact current-state digest from repo context, active product workspace, launch-readiness gaps, experiment ledger, validation/audit status, open issues/PRs, and approval boundaries. NotebookLM cannot see live repo state.
3. Query each required notebook separately. Use strategic notebooks for loop/harness/work-system advice and AI-money/product notebooks for buyer insight, offer clarity, pricing, distribution, and launch readiness.
4. If NotebookLM auth is expired and the project has an established browser-cookie/account flow, refresh auth through that flow, then rerun `auth check`; treat the durable lesson as the refresh-and-verify pattern, not as a claim that auth is broken.
5. Synthesize outside NotebookLM. Do not commit raw NotebookLM answers; commit distilled product artifacts, experiment files, validators, or approval packets.
6. Choose exactly one concrete move per run. If product readiness is the bottleneck, prefer a product/revenue artifact over generic harness work even when the strategic notebooks suggest new validators.

## Buyer-safe calculator / preview-sample pattern

For digital products about business workflows, a calculator worksheet can be a strong preview/sample surface when it is framed as a hypothesis generator, not an ROI promise.

Use this pattern when the product needs to convert abstract pain into concrete buyer understanding:

- inputs should come from the buyer/prospect where possible;
- formulas must keep assumptions visible;
- worked examples should be synthetic or clearly sourced;
- public vendor metrics are category evidence, not proof of buyer outcomes;
- include explicit forbidden phrases like “guaranteed revenue,” “pays for itself,” and “never miss a lead again” when the domain has claim risk;
- pair the calculator with objection handling for at least three likely blockers, such as AI risk, existing tools/processes, and pressure to make revenue/ROI claims.

Good pre-public metric: `objection coverage` — count explicit buyer objections handled by the sample artifact. Log it in the product experiment ledger with `preview/sample` as the surface.

## Autoresearch-style product experiment loop

When adapting autonomous research-loop ideas (for example `karpathy/autoresearch`) to passive-revenue product work, preserve the experimental contract rather than copying the technical domain:

```text
fixed budget/window
  -> one editable surface
  -> one primary metric
  -> baseline first
  -> TSV/ledger row
  -> promote / hold / discard / retest / blocked decision
  -> simplicity review
```

Product experiment rules:

- Change exactly one surface per test: title, price, audience, hero promise, CTA, product format, preview/sample, distribution channel, post/listing angle, or risk-reversal copy.
- Use one primary metric. Before public launch, use proxy metrics like launch-readiness, buyer-clarity, claim-safety, source support, objection coverage, or approval-packet completeness. After Telegram approval for public exposure, use market metrics like impressions, clicks, qualified replies, checkout starts, purchases, refunds/support burden, or conversion rate.
- Keep a product-local `experiment-ledger.tsv` with a baseline row before variants.
- Decisions should be constrained vocabulary such as `baseline`, `promote`, `hold`, `discard`, `retest`, `approval-needed`, `blocked`.
- Prefer the simpler variant unless the more complex variant produces a meaningful metric win.
- Do not call a multi-variable change an A/B test.

Useful repo artifacts:

```text
docs/research/<external-pattern>-product-experimentation.md
skills/product-experiment-loop/SKILL.md
templates/product-experiment.md
products/<slug>/experiment-ledger.tsv
scripts/product_experiment_audit.py
```

Wire this into sprint/product crons so every run can choose a product-experiment move and validators enforce the ledger/template exist.

## Deadline sprint pattern

When the user sets a near-term public launch deadline:

1. Write the deadline into the repo, not only chat memory.
2. Add or update a launch-readiness tracker for the active product.
3. Update cron prompts so every run prioritizes deadline work over generic improvements.
4. Add a temporary high-frequency sprint cron with a finite repeat count.
5. Add a one-shot final approval-packet cron for the target day.
6. Keep the public-live gate intact: sprint cadence accelerates preparation, not publication authority.

A useful sprint cadence is:

- keep the normal product scout running;
- add a temporary every-60-to-90-minute sprint cron through the deadline;
- add a target-day final approval request cron;
- require each sprint run to choose exactly one high-leverage move: product substance, packaging, non-public setup, approval packet, or blocker.

## Repo-local autonomy pattern

When the user explicitly grants autonomy for one repo, encode it in that repo’s harness rather than broadening global Hermes authority:

- add repo-local skills under `skills/`;
- add a local skill audit script;
- add focused cron prompts;
- add product workspaces under `products/`;
- add decision records for deadline/account/approval changes;
- preserve external release gates in AGENTS/docs/prompts/validators;
- verify commits, cron prompts, delivery targets, and remote HEAD like normal repo work.
