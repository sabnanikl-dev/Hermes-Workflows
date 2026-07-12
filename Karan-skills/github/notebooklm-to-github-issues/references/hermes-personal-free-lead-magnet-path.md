# Hermes Personal free lead-magnet path pattern

Use this pattern for Product 001 / Hermes Personal passive-revenue scout runs when:

- the product has useful private artifacts and green repo validators;
- adversarial or human review still blocks public paid launch;
- the observed-WTP governor remains below pass threshold, especially `0/3` `WTP-VERIFIED` markers;
- the latest useful options are exact-WTP evidence, hold/kill/pivot, free lead-magnet path, or Karan override.

## Decision rule

Do **not** keep polishing paid-listing surfaces when observed WTP is blocked. If another bounded evidence pass is unlikely to clear the gate during the run, the safest repo-local product/revenue move is a **distribution-channel experiment** that drafts an approval-required free lead-magnet interest path.

This is not public exposure and does not ask for approval by default. It creates a clearer next experiment if Karan later wants public testing.

## Artifact shape

Create one experiment file under the active product workspace, for example:

```text
products/local-service-missed-call-recovery-pack/experiments/YYYY-MM-DD-free-lead-magnet-path.md
```

Include:

1. Current WTP baseline, ideally from `python3 scripts/wtp_governor.py`.
2. Surface under test: `distribution channel`.
3. Hypothesis: when paid WTP is unverified, test interest in a free sample before checkout/listing work.
4. Variant: keep paid kit private; if Karan later approves public exposure, test one concrete free sample first.
5. Sample artifact: choose the most immediately useful buyer artifact, not an abstract source map. For Product 001, prefer `buyer-deliverables/use-this-in-30-minutes-discovery-audit.md` or a shortened worksheet derived from it.
6. Primary metric for the repo-local run: `direction decision completeness`.
7. Future market metric, approval-required: qualified clicks, saves, replies, download intent, or request-for-full-kit signals.
8. Explicit gates: no post, listing, waitlist/download page, checkout, outreach, paid setup, or market-facing claim without approval.

## Ledger row pattern

Append exactly one `experiment-ledger.tsv` row:

```text
YYYY-MM-DD	YYYYMMDD-free-lead-magnet-path	distribution channel	approval-required free lead-magnet interest path	direction decision completeness	paid-current-buyer direction held at 0/3 observed-WTP markers; next options scattered across hold/free/pivot/kill notes	5/5 criteria covered for a safer free-sample learning path; paid launch remains blocked at 0/3 WTP	hold	NotebookLM + adversarial-review grounded direction experiment; no public-live action, post, waitlist, listing, checkout, outreach, or approval request.
```

Use `hold`, not `promote`, because repo-local direction clarity is not market validation and does not clear the WTP governor.

## Verification

Run the normal cron validators. Include `python3 scripts/wtp_governor.py` in the evidence when the decision depends on WTP. It should remain blocked unless valid `WTP-VERIFIED` markers were actually added.

## Pitfalls

- Do not turn the free lead-magnet path into an active approval ask unless the user explicitly asks for it.
- Do not create a public page, waitlist, post, checkout, or marketplace draft as part of this move.
- Do not label the free path as a solved revenue experiment; it is only a safer next market-learning path.
- Do not use this pattern to avoid the stronger decisions forever. If repeated free-path/evidence passes fail, escalate to explicit hold/kill/pivot or Karan override.