# Hermes Personal private setup provenance pass

Use this pattern in passive-revenue Product 001 scout runs when evidence/readiness has advanced to a private setup decision but the setup protocol or handoff still points at stale artifact state.

## Trigger

- Product packet is not public-live approved, but is ready or near-ready for a **private platform draft/setup** decision.
- NotebookLM recommends a handoff/launch/proof-stack artifact, but public launch remains approval-gated.
- Setup docs such as `gumroad-draft-protocol.md`, `external-setup-checklist.md`, or `launch-approval-packet.md` refer to an older commit, stale dist artifacts, or file sizes only.
- Current bottleneck is preventing accidental upload/staging of the wrong artifact, not more buyer-facing copy polish.

## One-move shape

Treat setup-protocol integrity as the single experiment surface: `product format` / private setup handoff.

1. Verify repo state is clean and current.
2. Compute current commit and artifact identity for the private dist files:
   - `git rev-parse --short HEAD`
   - `git rev-parse HEAD`
   - byte counts for the intended Markdown/HTML/PDF files
   - SHA-256 hashes for each upload candidate
3. Patch only the relevant setup protocol/handoff file to pin:
   - current short and full commit
   - file path
   - byte count
   - SHA-256
4. Add one experiment note under the product `experiments/` directory.
5. Append exactly one ledger row with:
   - surface: `product format`
   - metric: `approval-packet completeness`
   - baseline: stale/missing provenance
   - result: current commit + sizes + hashes recorded
   - decision: usually `promote`
6. Run the full cron-required validation suite, commit, push, and verify local HEAD equals `origin/main`.

## Why this matters

This turns a fuzzy “ready for setup” packet into a deterministic handoff. The next approved platform setup run can verify it is staging the exact repo-approved artifact rather than relying on stale commit IDs, regenerated files, or agent memory.

## Boundaries

Do **not** open/login to Gumroad/Payhip/etc. as part of this move unless the cron explicitly selected external setup and approval exists. This is repo-local provenance only:

- no public listing
- no checkout/payment activation
- no waitlist/preorder link
- no outreach/posting
- no paid setup
- no new claims

## Example ledger row pattern

```tsv
YYYY-MM-DD	<id>	product format	current artifact provenance/checksums in private setup protocol	approval-packet completeness	setup protocol provenance 1/3: current commit and checksums stale/missing	3/3: current commit, byte counts, and SHA-256 hashes recorded for private dist artifacts	promote	NotebookLM-grounded private setup handoff integrity pass; no public-live action, platform login, listing, checkout, waitlist, outreach, paid setup, or claims.
```
