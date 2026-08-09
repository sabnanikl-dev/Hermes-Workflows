# Owner decision → bounded repair

Use after PR Prover stops `needs-karan` because a required policy/scope/privacy decision is missing, and Karan subsequently resolves it.

1. Capture the exact decision, exclusions, and remaining prerequisites.
2. Record it as a concise attributed PR comment; read back URL, author, and exact body through the live API.
3. Compare that decision to the frozen head. If the head implements a different policy, do **not** reset/review unchanged code again.
4. Freeze a repair ledger containing the prior SHA, approval-comment URL, deduplicated reviewer findings, required behavior, adversarial regressions, docs/PR-claim reconciliation, scope guard, and true repair budget.
5. Launch the repository's governed Claude builder adapter—not manual edits—then independently prove local SHA, remote branch SHA, and PR `headRefOid` match. Read back its signed fix comment.
6. Start a fresh exact-head review run after the push. Old reviewer artifacts are historical; include the owner decision in the new packet.

## Exact-registry privacy pattern

For a human-approved reviewed UTM registry, the browser-safe unit is the complete decoded tuple. Retain it only if it equals one active reviewed record; never preserve individual keys. Test raw/encoded token-shaped PII, arbitrary text, duplicate/missing keys, retired/unknown records, and cross-record mixes; also retain a reviewed ordinary non-enum record so the result is not a disguised fixed vocabulary.

## Pitfalls

- A decision comment can resolve `needs-karan`, but it does not make a mismatching old implementation correct.
- Do not silently reset the PR Prover attempt count after a repair commit. Preserve the true cumulative repair budget in any fresh review-only journal.
- Same-publisher GitHub identities need evidence separation: prove the decision post is outside the new run's own relayed artifact IDs and preserve its URL.
