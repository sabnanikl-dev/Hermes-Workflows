# Hermes Personal launch thesis handoff pattern

Use this when a Product 001/passive-revenue scout run has moved beyond evidence gathering and needs to convert scattered proof artifacts into a single human decision packet.

## Trigger

Apply after these repo-local gates are materially improved or passing:

- observed-WTP governor or equivalent proof gate passes, but exact-product demand remains caveated;
- launch claim verification maps near-public claims to evidence/caveats;
- adversarial P0/P1 findings have repo-local answers;
- setup/listing docs are stale or contradictory about readiness, price, or approval state;
- the next useful move is a narrow approval decision, not more copy/artifact polish.

## Recommended single move

Create or refresh a **launch thesis handoff** instead of asking for broad public launch approval.

Good artifact shape:

```text
products/<slug>/launch-thesis-memo.md
products/<slug>/launch-approval-packet.md
products/<slug>/experiments/<date>-launch-thesis-memo.md
products/<slug>/experiment-ledger.tsv
```

## Content contract

The memo should include:

1. Status line: `APPROVAL REQUIRED — DO NOT PUBLISH, LIST, POST, OR ACTIVATE CHECKOUT.`
2. Current value thesis in one compact block.
3. Proof stack table:
   - buyer/use clarity;
   - practical utility;
   - WTP/proof governor result;
   - claim-safety result;
   - external setup/blocker state.
4. Adversarial objection coverage table mapping each P0/P1 finding to evidence or caveat.
5. Recommended next decision as one narrow action, usually private platform draft/setup only.
6. Explicit list of what remains unapproved: public listing, checkout, waitlist, posts, outreach, paid plans, revenue/ROI/compliance claims.
7. Known blockers such as CAPTCHA, password/passkey, tax/KYC, paid-plan, or draft/private ambiguity.
8. Alternatives if Karan does not approve setup: keep private, free lead magnet, pivot, or kill.

## Ledger rule

Log exactly one experiment row for the handoff surface.

Typical row shape:

```text
date	experiment_id	surface	variant	primary_metric	baseline	result	decision	notes
YYYY-MM-DD	YYYYMMDD-launch-thesis-memo	product format / approval handoff	launch thesis memo plus refreshed approval packet	objection coverage	<before: proof scattered / stale approval packet>	<after: N/N blockers mapped; next action narrowed>	approval-needed	NotebookLM + adversarial-review grounded decision handoff; no public-live action...
```

## Sync stale setup docs

When the handoff changes readiness or price, update adjacent setup/protocol docs in the same move if they are part of the **same approval-handoff surface**. This avoids future agents following stale protocol values.

Common stale fields:

- old artifact sizes/commit refs in draft setup protocols;
- old price (`$27`) when pricing-hypothesis now says `$19` private validation / `$29` later public candidate;
- language saying “no active approval request” when the new request is private setup only;
- public-live checklist implying checkout/listing activation is the next approval instead of private draft setup.

## Boundaries

Do not use this as approval to launch. The handoff may ask for a specific approval, but no public/live/account mutation happens unless Karan explicitly approves.

Avoid overclaiming WTP: state whether proof is exact-product demand, exact-category marketplace evidence, or comparable proxy evidence.

## Verification

Run the repo's full product-scout validation set:

```bash
python3 scripts/validate_repo.py
git diff --check
python3 scripts/local_skill_audit.py --min-score 80
python3 scripts/market_viability_audit.py --min-score 80
python3 scripts/product_experiment_audit.py --min-score 80
python3 scripts/loop_audit.py --min-score 80
python3 scripts/four_cs_audit.py --min-score 80
python3 scripts/wtp_governor.py --require-pass  # when WTP pass is part of the handoff
```

If pushing, verify local HEAD equals `origin/main` with `git ls-remote origin refs/heads/main` before reporting.
