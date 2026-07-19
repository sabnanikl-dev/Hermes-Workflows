# Browser-QA Evidence: Producer/Validator Parity

Use this for PRs that add a real-browser evidence producer plus an offline validator, especially external-link allowlists and catalog-scale enablement gates.

## Core rule

A checked-in evidence artifact is not trustworthy merely because its schema validates. The committed producer, candidate source, classifier, evidence, and offline validator must form one executable contract.

## Required closeout sequence

1. **Run the committed producer itself.** Do not substitute Firecrawl scrape output, HTTP probes, Browser Use observations, or hand-authored evidence for a promised Playwright/Puppeteer producer. Those tools can provide independent comparison evidence, but the committed runner must generate the canonical artifact.
2. **Make the producer reproducible from a clean checkout.** Pin the browser automation dependency in the repo lockfile, provide the browser-engine install command, run a clean dependency install, and prove the runner launches. Do not claim a repeatable harness from `--dry-run` or classifier self-tests alone.
3. **Finish every required matrix slot.** If the scoped pilot requires destination × viewport coverage, canonical evidence must contain a terminal observed result for every slot. `pending` is valid for resumability but not for claiming the pilot run complete. Record a specific observed failure reason for disabled slots.
4. **Compare independent observations.** If an independent browser session contradicts canonical evidence, treat the evidence as blocked and rerun with the committed producer. Bot/proxy/session differences can send the same URL to different surfaces; record the exact method and current result rather than defending stale evidence.
5. **Pin every classifier identity input to authority.** If classification may pass using model title, slug, SKU, or other human-readable identity, the validator must cross-check that field against the authoritative candidate contract. Exact URL pairing alone is insufficient: otherwise evidence can replace the expected title with whatever wrong product the destination rendered and still pass. Add mismatch and repeated-title fixtures.
6. **Require real-browser methods for failures too.** A failed destination is still evidence. Apply the same real-browser/not-HTTP method validation to `fail` records as to `pass` records; otherwise curl output can be laundered into accepted failure evidence.
7. **Keep producer and validator on the same candidate contract.** A producer that accepts `--source=<catalog>` while the validator hardcodes a pilot allowlist is not catalog-scale. Both must consume the same versioned candidate schema, while preserving exact tuple pairing and fail-closed enablement.
8. **Keep the full candidate universe distinct from the selected work subset.** A bounded flag such as `--models=4000,4001` should select which pending slots run; it must not redefine candidate membership, `candidateSource.count`, or summary totals. Reconcile/retain evidence for the full source contract, write the full source count, and schedule only selected rows. Otherwise sequential batches retain old evidence while rewriting the declared contract to the latest subset, producing checkpoints the validator rejects.
9. **Prove scale offline.** Add a deterministic full-scale fixture (for example 315 candidates) showing that generated partial/resumable evidence remains validator-consumable without implementing the catalog UI itself.
10. **Prove subset resumability through the producer path.** A validator-only 315-row fixture can miss producer bugs. Add an end-to-end regression over one candidate contract: run batch A for one model, validate the checkpoint while other models remain pending; run batch B for another model, verify batch A is retained, full candidate count/summary totals stay stable, and validate again. Assert no duplicates/missing rows and fail-closed enablement throughout.
11. **Verify in an isolated exact-head worktree.** Clean-install dependencies, install the browser engine, run at least one representative forced destination × viewport replay, inspect the resulting evidence, and remove the scratch worktree. For final merge-readiness, require current-head Reviewer A and B after any evidence/classifier fix.
12. **Sweep every repo-visible status statement before re-review.** When canonical state moves from `pending` to a terminal state such as `complete-disabled`, search the whole branch for the old status token, superseded failure reason, earlier capture method, and stale future-tense handoff language—not only the primary spec/evidence files. Include source packets, build plans, friction logs, and current-result sections. Historical observations may remain when explicitly labeled as superseded, but their present-tense result/handoff lines must match the authoritative artifact. Verify the final PR body and signed comments describe the current canonical run. This prevents serial one-line documentation blockers across repeated A/B reviews.

## Reviewer checklist

- Does the runner actually execute from a clean checkout?
- Were all scoped slots observed, not merely preallocated?
- Can a wrong rendered title be copied into evidence and pass?
- Are repeated titles distinguished by stable ID and exact tuple?
- Can a non-browser method produce an accepted failure?
- Do runner and validator accept the same candidate source/schema?
- Does `--models` select work without shrinking the declared candidate universe/count or dropping prior batch evidence?
- Does a two-batch producer→validator regression pass after each checkpoint?
- Does a full-scale offline fixture pass while malformed/partial enablement fails closed?
- Does the PR body describe current canonical evidence rather than an earlier scrape/session result?
