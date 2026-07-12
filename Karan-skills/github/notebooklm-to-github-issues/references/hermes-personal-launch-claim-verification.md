# Hermes Personal launch claim verification handoff

Use this pattern for Product 001 / Hermes Personal passive-revenue scout runs when:

- the product has cleared or improved a hard evidence gate such as `scripts/wtp_governor.py`;
- NotebookLM strategic/product answers converge on provenance, maker/checker discipline, evidence-based delivery, or claim safety;
- public-live approval is still blocked, but the next bottleneck is no longer raw evidence collection — it is converting evidence into a human-reviewable launch proof packet;
- the cron must choose exactly one repo-local move and avoid public posting, listing, checkout, waitlist, outreach, paid setup, or claim-bearing external action.

## Decision rule

Do **not** jump from WTP evidence to a public approval request. First create a deterministic claim-to-evidence handoff so Karan can review actual promises, source support, caveats, and excluded claims without re-reading the whole repo.

Choose exactly one surface: `product format` or `approval proof format`.

## Artifact shape

Create one internal proof artifact under the active product workspace, for example:

```text
products/local-service-missed-call-recovery-pack/launch-claim-verification.md
```

Include:

1. Status line: repo-local approval handoff; not public; no external action without Karan approval and a fresh source check.
2. Purpose: convert WTP/source evidence into a launch-review handoff.
3. Verification result table:
   - count of buyer/use claims checked;
   - count mapped to evidence/artifacts;
   - claim classes still excluded;
   - current hard-gate output such as `wtp_governor.py` result;
   - public-live approval remains blocked.
4. Claim-to-evidence map with columns:
   - buyer-facing claim under review;
   - evidence/artifact anchor;
   - allowed wording;
   - caveat/excluded wording.
5. WTP proof handoff that clearly distinguishes comparable/exact-category marketplace proof from proof that the exact kit already sold.
6. Explicit excluded claims: revenue/ROI/savings/booked jobs, “never miss a lead,” compliance/legal advice, replacement claims, exact-kit-sales claims, private/client data proof.
7. Future approval-request shape, but do **not** ask for approval unless the cron/user explicitly asks.
8. Next safe repo-local actions if no external approval is granted.

## Experiment file and ledger row

Create an experiment file under:

```text
products/local-service-missed-call-recovery-pack/experiments/YYYY-MM-DD-launch-claim-verification.md
```

Use:

- surface: `product format` or `approval proof format`;
- primary metric: `approval-packet completeness`;
- decision: usually `promote` if the handoff maps all claims and keeps public gates closed;
- approval boundary: repo-local only.

Ledger row pattern:

```text
YYYY-MM-DD	YYYYMMDD-launch-claim-verification	product format	launch claim verification handoff	approval-packet completeness	0 dedicated claim-to-evidence handoff after WTP governor passed; claims/evidence/exclusions scattered across landing copy, proof map, source map, and WTP candidate TSV	N/N buyer-facing claims under review mapped to evidence/artifacts with allowed wording and caveats; observed-WTP governor PASS X/Y; public-live action still gated	promote	NotebookLM strategic + Ai-money synthesis grounded proof handoff; no public post, listing, checkout, waitlist, outreach, platform setup, or revenue/ROI/compliance claim.
```

## Verification

Run normal cron validators plus the relevant hard gate:

```bash
python3 scripts/wtp_governor.py --require-pass
python3 scripts/validate_repo.py
git diff --check
python3 scripts/local_skill_audit.py --min-score 80
python3 scripts/market_viability_audit.py --min-score 80
python3 scripts/product_experiment_audit.py --min-score 80
python3 scripts/loop_audit.py --min-score 80
python3 scripts/four_cs_audit.py --min-score 80
```

If committing directly to main, verify `git rev-parse HEAD` equals `git ls-remote origin refs/heads/main` before reporting success.

## Pitfalls

- Do not treat a passing WTP governor as approval to publish, list, activate checkout, create a waitlist, or send outreach.
- Do not ask Karan to approve “launch everything.” Future approval requests should be one external action at a time.
- Do not allow source evidence to become stronger public copy than it supports. Keep “allowed wording” and “excluded wording” side by side.
- Do not claim the exact product has sold unless it has.
- Do not rebuild dist artifacts unless the claim verification changes buyer-facing content or the selected single move is specifically artifact rebuild.
