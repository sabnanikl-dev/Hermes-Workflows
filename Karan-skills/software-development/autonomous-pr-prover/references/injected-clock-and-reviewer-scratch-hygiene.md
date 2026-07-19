# Injected Clock Safety + Reviewer Scratch Hygiene

Use this during PR-prover loops when a fix introduces an optional evaluation clock for deterministic tests, or when external reviewer CLIs post GitHub comments via temporary body files.

## Injected evaluation clocks must fail closed

A common deterministic-test seam is an optional `now` epoch argument:

```js
function ageDays(timestamp, now) {
  const reference = now === undefined ? Date.now() : now;
  if (!Number.isFinite(reference)) return null;
  // parse timestamp, then compute age
}
```

Do **not** use only `typeof now === "number"`: JavaScript classifies `NaN`, `Infinity`, and `-Infinity` as numbers. Age comparisons against `NaN` are false, which can bypass both stale and future checks and turn a freshness gate fail-open.

Required contract:

- omitted clock → production `Date.now()`;
- finite supplied epoch → deterministic evaluation;
- explicitly supplied non-finite clock → invalid result / fail closed;
- malformed timestamp → invalid result / fail closed;
- production callers omit the clock unless they intentionally own the evaluation time.

Required regressions for **each gate layer** that consumes the clock:

1. Omitted clock accepts a genuinely fresh fixture.
2. Finite pinned clock accepts fresh and rejects stale/future fixtures.
3. `NaN`, `+Infinity`, and `-Infinity` never enable an action and never return a clean validation result for stale evidence.
4. Tests assert positive error/action counts, not vacuous predicates such as `array.every(...)` on an empty array.
5. Mutation-check the guard when practical: reverting `Number.isFinite` to a type-only check must make the regression fail.

Reviewer prompts should explicitly inspect clock injection/default behavior whenever a PR adds time-dependent test seams.

## Reviewer temporary-file hygiene

External reviewer CLIs may create a Markdown body file before running `gh pr comment`. If the prompt does not constrain the path, they may leave untracked `.reviewer-*` files inside the product worktree.

Reviewer prompt rule:

```text
Write any review/comment body file under /tmp (or the OS temp directory), never inside the repository.
```

After every reviewer exits:

1. Read back the signed GitHub artifact.
2. Run `git status --short --branch` in the bound worktree.
3. Remove only clearly reviewer-generated scratch files after confirming their provenance.
4. Do not begin the builder fix lane until the worktree is clean and current HEAD still equals the PR `headRefOid`.

This prevents reviewer bookkeeping from contaminating the builder diff or being accidentally committed under Claude provenance.
