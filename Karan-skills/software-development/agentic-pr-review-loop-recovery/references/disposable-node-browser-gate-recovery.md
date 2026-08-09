# Disposable Node/Playwright gate recovery

When an exact-head prover copies a repository into fresh per-gate worktrees, a local browser test can pass while its detached equivalent fails with `ERR_MODULE_NOT_FOUND` for a declared dependency such as Playwright. Treat this as an environment-gate failure, not source evidence.

For a lockfile-backed Node repository with an already available package cache, make restoration explicit in the disposable browser-gate command:

```json
["sh", "-lc", "npm ci --offline --ignore-scripts && npm run validate:browser"]
```

`npm ci` preserves lockfile exactness; `--offline` prevents review-time package fetching; `--ignore-scripts` avoids lifecycle hooks. The install touches only the throwaway gate worktree.

Before rerun: confirm local/remote/PR head equality; retain the failed report; change only the run config; validate it; reset the terminal local run journal; rerun all gates and lanes at the same head. Do not revise the PR source solely to make a detached dependency installation work.

## Automated status comments before a run or rerun

A bot preview-status comment remains unresolved feedback because `pr-prover` intentionally does not interpret prose. Read it first. If it is only a status notification, publish one **pure canonical ACK bridge** containing only exact lines:

```text
PR-PROVER: ACKNOWLEDGED <immutable-comment-id>
```

Do not add explanatory prose such as deployment/activation disclaimers beside those lines: residual text becomes another unresolved feedback item. Preserve authority boundaries in the run config/report instead.

If the ACK author is a configured publishing login, REST-read the new comment back, verify its exact body/author/URL, hash the API body using the repository's canonical `[body, review_state]` evidence rule, and pin that exact numeric ID plus digest in `operator_acknowledgements`. On a reset/rerun, the prior journal's reviewer artifacts are no longer run-owned; after reading them, include their immutable IDs in the same cumulative ACK bridge or the fresh run will stop on them as historical feedback. This reconciles transport history only—it does not declare those blockers fixed or waive a fresh exact-head triad. Never ACK substantive human feedback, a native `CHANGES_REQUESTED` review, or an unresolved inline thread through this mechanism.

Before spending reviewer lanes, simulate or run the shipped reconciliation against the final pin set and require zero unresolved historical items. `check-config` proves pin shape/evidence, not that every target is actually cleared.

## Browser producers that write tracked evidence

A real browser producer may intentionally overwrite tracked JSON/screenshots under a known evidence directory. Running it directly as a disposable prover gate can then fail the post-lane cleanliness check—or a byte-for-byte `git diff --exit-code` can fail on harmless screenshot encoding variance—even though the semantic run passed.

For a producer whose exit status and narrow binder are authoritative, run both first and restore **only the declared generated-output directory** in an `EXIT` trap:

```json
["bash", "-lc", "set -e; trap 'git checkout -- docs/evidence/issue-N' EXIT; npm ci --silent; npm run qa:browser; npm run check:browser-evidence"]
```

This keeps the exact-head product checkout clean after the gate without treating generated PNG bytes as a deterministic product surface. The trap must be narrower than the producer's source inputs. Never use `git reset --hard`, `git clean`, or a broad checkout that could erase an unexpected source mutation; an undeclared changed path must still trigger scope contamination. If the producer or binder fails, the trap may restore only the known generated outputs and the gate must preserve the non-zero result.

The clean-worktree pattern is not permission for a weak archive. Bind the report to the exact checkout head **and every behavior-controlling surface** needed by the claim: controller/runtime JavaScript, stylesheet, committed page/template wiring, producer/binder version or hash, and screenshot/report manifest as applicable. A file-history commit for only one script is not exact-head UI proof when later CSS or markup can hide or disconnect the control.

Require former-red visual mutants appropriate to the acceptance contract:

- append CSS that hides the changed component; the archive binder/full gate must fail;
- change a recorded focus outline to `0px`; both producer verdict and binder must fail;
- for visible focus, require `:focus-visible`, non-`none` style, and a parsed width greater than zero (plus any contract-required contrast/color evidence), not merely a solid style token;
- mutate page/template wiring so a runtime-enabled page omits the control; exact-head binding or scenario coverage must fail.

A fresh real-browser pass and a durable archived-report binder serve different purposes. The producer proves current rendered behavior; the binder proves that the committed report is successful and bound to the claimed product bytes/head. Keep both finite and product-centered rather than widening the archive into a hostile-input framework.
