# Human Copy/Goal Corrections: Contract-Cascade Closeout

Use this when a human changes the purpose or conversion goal of a page after a PR is otherwise green.

## Core lesson

A customer-facing correction is rarely limited to one sentence. Treat it as a contract cascade across every surface that can restore or certify the rejected behavior:

1. visible page copy and CTA hierarchy;
2. metadata and social descriptions;
3. visible FAQ and structured-data parity;
4. repo spec/source packets;
5. mutable PR title/body and closeout comments;
6. machine-readable allowlists or consumption contracts;
7. validators, invariant comments, error messages, fixtures, and negative self-tests.

A green suite is not sufficient when its validator still enforces the old requirement. Read the invariant itself and prove the guard fails on reintroduction of the rejected behavior.

## Procedure

1. Treat the human direction as a blocking current-head contract. Quote the new page goal and name examples of prohibited implications/actions, so the contract is explicit rather than inferred.
2. Inspect the whole page before any fix is scoped. Search visible copy, metadata, JSON-LD, CTA destinations, FAQ, and lower-page conversion sections.
3. Translate absolute intent literally. If the human says the page's only purpose is destination X, merely demoting Call/Directions/visit actions is a partial fix; page-specific competing actions must be removed unless the human allows them. Distinguish global site chrome from page-specific conversion actions.
4. State the acceptance bar with the blocker: visible FAQ/JSON-LD parity, and no regression to unrelated commerce/accessibility boundaries.
5. Compare the implementation against **every** clause of the human blocker. An omitted clause means the blocker is not closed, and a quietly shrunken contract judged as closed is the failure this cascade produces most often.
6. Re-read the PR body and committed docs. Then sweep structured contracts and executable validators—not just prose.
7. For each changed invariant, require both:
   - positive proof that the final contract passes; and
   - negative proof that the rejected old behavior fails (including likely alias fields or alternate encodings).
8. Run browser QA on the changed site tree. A later docs/contract-only head may prove the rendered site tree is unchanged, but if the human asks for screenshot proof, recapture fresh screenshots from the exact final PR head anyway. Pair them with geometry, console, interaction, reduced-motion, and no-JS/degraded checks as relevant, and store proof outside disposable worktrees.
9. The cascade, not the code diff alone, is what the next head has to satisfy. PR-body, docs, allowlist, and validator consistency are all part of the contract under judgment.
10. Cycle budget, corrective reruns, and escalation belong to `pr-prover/MISSION.md`; this reference decides none of them.

## Entry vs rendered-instance terminology

When one approved collection URL is intentionally repeated on the page, keep authority and presentation separate:

- **one allowlist entry / one approved destination** describes what is authorized;
- **N rendered anchors / placements** describes how often that destination appears.

Record both dimensions explicitly wherever the contract is stated: specs, validators, and PR evidence. Avoid “exactly one CTA” when it could mean either one approved destination or one rendered anchor. If placement count is contractual, add positive and negative validator cases for it.

## Common failure pattern

- Human says: the page should only hand off to an external builder and must not imply products are in-store.
- Builder fixes visible copy but retains secondary Call/Directions actions.
- Corrective pass fixes the UI, but source docs still prescribe showroom-first behavior.
- Docs pass is green, but an allowlist and validator still require Call/Directions/showroom alternatives.

The correct closeout is not complete until the UI, prose contract, machine-readable contract, validator behavior, negative self-tests, and PR description all agree.
