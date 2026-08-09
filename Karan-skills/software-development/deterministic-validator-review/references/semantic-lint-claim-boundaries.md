# Semantic-Lint Claim Boundaries and Cycle-Cap Closeout

Use this reference when a deterministic checker attempts to keep lifecycle or procedural instructions out of prose, documentation, prompts, or skill references.

## Separate three proof levels

Do not collapse:

1. **Committed-surface cleanliness** — the currently indexed documents contain no prohibited mechanics.
2. **Bounded mutation coverage** — a declared adversarial corpus of prohibited and allowed sentences is classified correctly.
3. **General semantic recognition** — arbitrary ordinary-English paraphrases are recognized without false positives.

Finite regex or vocabulary matchers can establish levels 1 and 2. They normally cannot justify level 3. If code comments, test names, PR prose, or acceptance criteria claim semantic recognition broadly, a reviewer can legitimately disprove that claim with short unseen synonyms while every committed test remains green.

## Synonym-chase warning signs

- Every repair adds reviewer sentences or nearby synonyms to a verb/noun table.
- The matcher and its “independent” corpus are authored together from the same blocker list.
- Tests prove only that each declared rule hits one declared sample.
- Corpus growth or test count is presented as semantic completeness.
- Ordinary domain probes are false positives while ordinary lifecycle imperatives remain false negatives.
- The second fix cycle still yields easy unseen paraphrase bypasses.

At that point, do not start another automatic synonym patch. Choose a contract-level remedy:

1. Narrow the claim to committed-reference cleanliness plus a bounded, named mutation corpus.
2. Replace free prose with structure where the invariant matters: typed fields, explicit sections, schema-backed categories, or machine-readable route metadata.
3. Split broader semantic hardening into a follow-up with its own proportionality decision.
4. Use a real semantic engine only when the product actually justifies that dependency and domain.

The best fix is often to make the contract more deterministic, not to make regex imitate an NLP model.

## A defensible bounded prose validator

If the intended domain is levels 1–2:

- state that the detector is scoped pattern matching, not language understanding;
- scan every committed/indexed target and fail on actual prohibited content;
- keep positive directives and allowed descriptive/domain prose in data separate from rule definitions;
- remove rule-owned `sample` fields that let patterns vouch for themselves;
- require every rule to be exercised by an external corpus item;
- include negative cases with the same lifecycle nouns in descriptive prose;
- include domain-specific imperatives that must remain allowed;
- run independent `/tmp` mutations through the real public/focused gate;
- describe corpus size as bounded regression evidence, never completeness.

A same-commit corpus is useful regression coverage, but provenance labels do not make it independent. Strong independence comes from a frozen prior ledger, a separate reviewer/author, or post-implementation adversarial probes that were not used to tune the matcher.

## Runtime integrity before counting reviewer evidence

Before relaying or adjudicating a reviewer artifact, validate:

- expected full head SHA;
- expected role and machine marker;
- required model/reasoning runtime;
- fresh context/worktree identity;
- credential-free child execution;
- intended artifact type and transport disclosure.

A wrong-model or wrong-reasoning output is diagnostic-only. Do not count it toward a passing triad or relay it as a valid signed verdict. Rerun it when a valid triad is still necessary to decide readiness.

However, if the normal repair cap is already exhausted and one correctly pinned lane independently reproduces a concrete P1, the PR is already blocked. Do not spend another expensive run merely to manufacture a complete failing triad. One valid current-head P1 is sufficient to withhold readiness; three valid current-head passes are required to grant it.

## Approved contract-narrowing recovery

When the human chooses narrowing after the cycle-cap closeout, treat it as a bounded contract amendment rather than a disguised third synonym cycle:

1. **Amend the original issue before code changes.** Name the finite proof boundary (for example: exact committed inventory, manifest bytes, index/route/link invariants, named lessons, and pinned known forms) and state explicitly that arbitrary-English recognition is not claimed.
2. **Split semantic research out of the merge train.** Create a separate Backlog/evaluation issue when broader linting may still have value. Link it from the original and parent tracker, and state that it does not gate the current PR or reorder active implementation children.
3. **Freeze the correction envelope on the PR.** Record allowed surfaces, forbidden replacement mechanisms, exact verification, and the maximum corrective rerun before launching the builder.
4. **Delete the overclaim rather than rename it.** Remove the matcher/corpus/parser apparatus that implied general semantics. Retain honest structural guards that still prove finite repository invariants.
5. **Directly audit every committed target at the exact head.** Once generalized semantic proof is removed, exact-corpus inspection becomes load-bearing evidence. Rewrite concrete parallel procedures as declarative domain risks or pointers to the owning executable lifecycle; do not replace the removed detector with a hidden manual synonym checklist.
6. **Retract stale evidence.** If a PR body or signed builder comment claimed the audit was complete when it was not, edit or supersede that claim explicitly. A corrected diff with contradictory live evidence is not ready for review.
7. **Use one corrective rerun only for a missed item in the same approved class.** Point the builder to the durable review artifact, change only the missed target plus derived metadata, and then invalidate every prior verdict. A new blocker class requires fresh human approval.
8. **Run the complete exact-head triad.** All three current-head passes are required to move from `blocked / needs human` to merge-ready. Reviewers must inspect both the full base-to-head diff and the narrowing/corrective diffs.
9. **Close out GitHub and the tracker separately.** Post and read back the GitHub exact-head closeout first; then post and read back the tracker closeout that references it. Reserve execution budget for both mutations. If one surface was only drafted, disclose that and do not claim cross-system reconciliation is complete.

The merge-ready result may still remain draft and unmerged when the repository gives ready/merge authority to the human. Contract narrowing is permission to prove the smaller claim, not permission to expand authority.

## Cycle-cap closeout

When a valid P1 survives the final allowed cycle:

1. Verify local/upstream/remote/live head equality and a clean worktree.
2. Preserve green deterministic gates without implying they override the blocker.
3. Relay only runtime-valid current-head artifacts under the verified reviewer identity and read them back.
4. Post an operator reconciliation naming the blocker, cycle count, degraded/invalid lanes, and prohibited next action.
5. Keep the PR open/draft; do not mark ready.
6. Update the tracker as `blocked / needs human`, not done.
7. Offer contract-level choices: narrow, structure, split follow-up, approve a bounded exception, or stop.

Prefer reporting:

- “Current artifact correct; bounded corpus green; broad semantic claim disproved.”
- “Wrong-runtime reviewer output is diagnostic-only and was not counted.”
- “All deterministic gates are green, but one valid exact-head P1 remains.”
- “The normal cycle cap is exhausted; no additional automatic repair was started.”
