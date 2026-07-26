# Static copy PR current-head closeout pattern

Use this for static-site copy/content PRs where earlier review comments flagged copy-risk items and the PR later pushed a wording-only fix.

## Pattern

1. **Anchor every judgment to the current head.** Old content/SEO reviews can be useful context, but do not carry their blockers forward unless the current head still contains the risky wording.
2. **Verify the builder's follow-up comment against the diff.** If the author says they softened owner-gated claims, inspect the changed HTML/text directly and confirm the current wording now stays inside the approved ledger.
3. **Run deterministic copy probes in addition to repo tests.** For JMD-like static pages, probe changed pages for:
   - required approved facts/phrases from the issue acceptance criteria;
   - residual disclaimer language that the issue intended to remove;
   - forbidden claim classes: live inventory, stock counts, size runs, guaranteed availability, online ordering, hard pricing beyond the approved ledger.
4. **Handle approved negative facts carefully.** A raw forbidden-word search can produce false positives for approved brand positioning such as "when it is gone, it is gone" / "does not reorder fashion garments" when the repo source document explicitly approves that limited-floor concept. Classify by claim meaning, not token presence.
5. **Do not carry an old head's closeout forward.** A wording-only fix is still a new exact head, and `pr-prover` re-proves it; earlier artifacts posted from another account or against an older commit are history.
6. **Separate merge-readiness from public approval.** For draft/customer-facing copy, report technical/prover merge-readiness while preserving any brand, commerce, owner, client, or deploy approval gates as load-bearing.

## The copy half of the closeout

Repository gates and GitHub readback are owned elsewhere. What this reference adds is the copy-specific probe set:

- read the changed customer-visible pages themselves, not only the cited line;
- assert the required approved facts are present and the disclaimers the issue removed are actually gone;
- assert each forbidden claim class is absent **by meaning**, keeping the approved-negative-fact exceptions from step 4;
- keep brand, commerce, owner, client, and deploy approval gates outside the technical result.
