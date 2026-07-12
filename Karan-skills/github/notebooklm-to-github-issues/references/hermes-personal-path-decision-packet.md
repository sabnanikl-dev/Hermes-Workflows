# Hermes Personal Product 001 Path Decision Packet Pattern

Use this reference when Product 001 or another passive-revenue product has accumulated enough repo-local artifacts, evidence maps, validators, and approval packets that further autonomous polish is lower leverage than a human path decision.

## Trigger

Create a path decision packet when all are true:

- product/readiness validators are green or the remaining blocker is strategic, not file completeness;
- the experiment governor or adversarial review says to stop adding more deliverables, proxy evidence, price polish, listing copy, or WTP scans;
- public-live gates remain closed;
- the next meaningful move is a human choice such as keep private, test a free lead magnet, attempt private setup, pivot buyer, or park/kill the paid path.

## Recommended one-run move

Surface: `product direction`

Primary metric: `direction decision completeness`

Artifacts:

```text
products/<slug>/path-decision-packet.md
products/<slug>/experiments/<YYYY-MM-DD>-human-path-decision-packet.md
products/<slug>/experiment-ledger.tsv  # one row if the ledger is not already updated by a sibling/current commit
```

## Packet shape

The packet should be short enough for Karan to choose a path without reading scattered ledger history:

1. Status line: repo-local handoff; no external action approved.
2. Why this packet exists: summarize convergence and the remaining decision bottleneck.
3. Decision question: list 3-5 mutually exclusive next paths.
4. Path comparison table: path, what it means, evidence for it, caveat, approval posture, recommended-if.
5. Recommendation: choose the lowest-risk next learning path, or recommend keeping private when external learning is not needed.
6. Guardrails: restate that public posts, listings, checkout, waitlists, outreach, setup, spend, and claims require explicit approval.
7. One-reply approval shape: make it easy for Karan to reply with exactly one path.
8. Verification anchors: link the current governor, value blocker, launch packet, proof map, and ledger.

## Decision rules

- Do **not** use this packet to smuggle in a public launch request.
- Do **not** bundle multiple external actions. A path approval covers only that path.
- If the active blocker remains open, do not ask for listing/checkout approval. At most ask for a bounded path decision or private/free setup decision, clearly approval-required.
- Prefer `approval-needed` as the ledger decision when the packet successfully moves the bottleneck to Karan.
- If another concurrent/sibling run already appended the ledger row for the same experiment, do not append a duplicate. Commit only the new handoff artifacts or stop if unknown edits are present.

## Verification

Run the repo's normal product scout validation set:

```bash
python3 scripts/validate_repo.py
git diff --check
python3 scripts/local_skill_audit.py --min-score 80
python3 scripts/market_viability_audit.py --min-score 80
python3 scripts/product_experiment_audit.py --min-score 80
python3 scripts/loop_audit.py --min-score 80
python3 scripts/four_cs_audit.py --min-score 80
```

After pushing direct-to-main, verify local HEAD equals `origin/main` with `git ls-remote origin refs/heads/main` before reporting.