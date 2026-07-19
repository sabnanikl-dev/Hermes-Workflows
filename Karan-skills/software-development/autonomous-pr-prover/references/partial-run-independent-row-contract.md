# Partial-run evidence with independently enabled rows

Use this pattern when a large evidence producer has an overall `partial` status while a reviewed subset of entities has complete evidence and may be enabled independently.

## Model three separate states

Do not collapse these into one boolean:

1. **Run completeness** — whether the producer observed the whole catalog/universe.
2. **Per-item completeness** — whether one entity has every required slot/proof.
3. **Enablement authority** — whether the separately reviewed allowlist/action gate accepts that complete item, including freshness and exact identity binding.

A partial 315-item run can legitimately mean “six complete items enabled; 309 incomplete items pending/disabled.” The statement “partial means every row disabled” is wrong when independent-row enablement is part of the contract.

## Cross-surface reconciliation checklist

After enabling a subset, sweep all current-state surfaces—not just implementation code:

- evidence JSON run note and per-item statuses;
- the producer/template that regenerates that note;
- validator messages and fixtures;
- allowlist and generated browser action artifact;
- source/header comments describing the generated-artifact boundary;
- spec, build plan, live-capture/handoff docs;
- PR body summary, matrices, verification tables, and browser-smoke text;
- friction/history notes that still use the old failure framing.

Search for stale claims such as:

- `0 enabled`, `every row disabled`, `none render`, or `enabled is {}`;
- obsolete failure labels presented as current truth;
- aggregate `partial` wording that accidentally overrides complete per-item evidence.

Preserve useful chronology by adding a prominent **SUPERSEDED/HISTORICAL** banner rather than rewriting the original observation. Present-tense handoff sections must state current truth.

## Producer/generated-artifact parity

If a generated evidence note changes, update the producer template in the same commit and prove the committed note matches what the producer will emit. Otherwise the next run silently restores stale wording. Keep the wording precise:

- incomplete/pending items remain fail-closed;
- complete exact-tuple/four-pass items support the separately reviewed enablement gate;
- overall `run.status: partial` remains honest and does not itself grant enablement.

## Review-loop closeout

A broad first reconciliation often leaves one narrow generated or handoff claim behind. Before current-head A/B re-review:

1. run a full-branch stale-token sweep;
2. inspect the live PR body separately (it is not in the git search);
3. verify local HEAD = remote branch = PR head;
4. rerun determinism/validator/browser gates;
5. require both role-signed reviews on the new exact head.

Old request-changes reviews remain useful audit history but cannot count against or approve the new head. Final merge-readiness requires current-head A/B outcomes and no unresolved current review threads.
