# Validator Scope Inversion and Clean-Replacement Recovery

Use this when a feature PR's regression checker has become larger or more complex than the product change and repeated adversarial review keeps finding adjacent semantic gaps.

## Scope-inversion signals

Stop treating the next counterexample as an ordinary fix when several signals appear together:

- the committed product artifact is repeatedly verified correct while only the speculative future guard fails;
- the checker implements partial semantics for a real parser, routing engine, natural language, schema language, or other open-ended domain;
- each fix adds stronger claims such as “HTML-faithful,” “all morphology,” “exact semantics,” or “fail-closed,” which generate another review universe;
- fixture counts grow rapidly but independent reviewers still find claim-derived case N+1;
- the checker/docs diff dwarfs the feature;
- the normal review/fix-cycle cap has been exceeded or exceptions keep discovering new blocker classes.

This is **validator scope inversion**: the guard has become the product, but the issue did not authorize or justify that product.

## Required decision

Do not continue whack-a-mole patching. Choose one:

1. **Use the real semantic engine** (for example, a real HTML parser or schema validator) when exact semantic parity is truly required and dependency/architecture expansion is approved.
2. **Narrow to an explicit finite repository policy** and update every claim surface accordingly.
3. **Remove/split the speculative guard** and keep the original feature PR issue-scoped.

Green self-tests do not override this decision; they prove only the enumerated fixtures.

## Clean-replacement recovery

When a PR is already polluted by the overbuilt checker:

1. Freeze a replacement contract before editing. Name both required checks and prohibited architecture.
2. Create a fresh branch/worktree from the current default branch; do not revert the polluted branch in place.
3. Reuse independently verified product artifacts by exact commit/hash when safe.
4. Add only finite committed-artifact checks for facts not already covered by existing validators.
5. Prefer conservative repository policy over partial interpretation. Example: reject any future routing configuration for human review instead of partially interpreting arbitrary route regexes.
6. Describe vocabulary as an explicit finite policy list; never claim exhaustive English morphology unless a real language system and bounded contract justify it.
7. Keep docs honest and proportional. Remove parser-equivalence, universal fail-closed, and zero-false-positive claims.
8. Run the full baseline, focused checks, diff checks, artifact hash comparisons, and remote-head verification.
9. Open and verify the clean replacement PR before closing the polluted PR as superseded.
10. Re-review the frozen contract. A new reviewer idea outside that envelope is a follow-up proposal, not an automatic blocker, unless it proves the original issue acceptance criteria are unmet.
11. Reconcile issue-closing metadata with deferred/manual acceptance criteria. If a live or post-deploy check cannot be proven on an exact-head preview, use `Refs #N` and keep the issue open. Use `Closes #N` only when every issue acceptance criterion is already evidenced or validly completes on merge.
12. For a PR-body-only correction with unchanged code head, refresh the immutable review packet and rerun the reviewer lane that raised the metadata blocker plus the integration auditor. Do not rerun unrelated code review solely for ceremony.

## Preview-proof pitfall

A green deployment status is not proof that an unknown path returns the intended branded 404. Preview protection may redirect to an authentication/login surface and return HTTP 200. Bind any live probe to the exact deployment SHA, inspect final headers/body (including matched-path/auth markers), and accept it only when the response is the actual product page with the required HTTP status. Otherwise keep the manual gate open and avoid automatic issue closure.

## Reporting

Separate these statements explicitly:

- **Artifact correctness:** whether the committed feature is valid now.
- **Guard soundness:** what finite regressions the replacement checker detects.
- **Claim honesty:** what the docs and diagnostics promise.
- **Deferred architecture:** broader semantic validation intentionally moved out of scope.

A useful closeout sentence is: “The replacement preserves the verified product artifact and finite issue contract; generalized parser/policy hardening is not part of this PR.”
