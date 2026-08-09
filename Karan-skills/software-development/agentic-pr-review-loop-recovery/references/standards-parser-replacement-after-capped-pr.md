# Standards-Parser Replacement After a Capped PR

Use this reference when an exact-head review/fix loop reaches its repair cap and the remaining blockers come from hand-written parsing, incomplete-observation handling, or a proof target that has grown out of proportion.

## Stop and preserve

- Keep the capped PR open, blocked, and unmerged as evidence when the owner requests preservation.
- Do not force-push, rewrite, retitle, or start a hidden extra patch cycle.
- Mechanical `MERGEABLE` / `CLEAN` state never overrides reproduced false passes.
- Publish a replacement plan and get owner approval before implementation.

## Fresh replacement contract

1. Start from the then-current default branch in a fresh isolated worktree; cherry-pick no implementation bytes from the blocked PR.
2. Carry forward only the governing acceptance criteria, evidence links, and named former-red regressions.
3. Freeze the finite product contract. Broader hardening ideas without a demonstrated contract violation become follow-ups.
4. Replace custom HTML/XML/robots grammars with mature libraries. Test the exact pinned versions against the former-red cases before adoption and run the package audit.
5. Write the known false-pass probes first as permanent, named tests.
6. Separate parser/planner/evaluator tests from the networked live gate.

## Fail-closed observation model

Keep transport and semantics distinct:

- stream/read/decoding failure, timeout, or overflow produces an explicit incomplete observation;
- incomplete evidence can never become an empty successful body;
- the fetch adapter should attempt the bounded read rather than skip based on `Content-Type`;
- missing or unsupported media type is an explicit evaluator failure for a route that requires HTML/text;
- whole URL identity retains `pathname + search`; reject silently discarded fragments and off-origin hops; and
- derive branded/error-page evidence from the repo-owned artifact using the same reliable parser used on the live response.

Pin every incomplete/media-type branch through the shipped fetch adapter, not evaluator-only fixtures.

## Exact-head live evidence

A green command against a mutable alias is insufficient. Require:

- local HEAD = remote branch = PR head;
- deployment metadata commit SHA = PR head;
- recorded deployment ID and immutable deployment URL;
- complete live matrix on that immutable deployment; and
- platform-injected indexability blockers treated as failures, not waived preview artifacts.

## Human trailer gate

Before the first commit, read the effective repo `git config user.name` and `git config user.email`, require the approved human identity rather than a bot/model identity, and use it for both trailers in this order:

```text
Co-authored-by: Human Name <human@email>
Signed-off-by: Human Name <human@email>
```

Audit every replacement commit before the first push and again before readiness. This avoids an approval-gated history rewrite later.

## Proportionality

Measure and report separately:

- production code;
- tests/fixtures;
- hand-written documentation; and
- generated lockfile churn.

Set stop-and-review triggers for production total, per-module size, any new parser/policy subsystem, and whole hand-written diff size. Do not let test/doc volume bypass the production guard, and do not compress code or weaken tests to meet a metric.

## Plan closeout

Post the plan in the originating thread with:

- blocked PR and exact head;
- frozen former-red IDs;
- proposed dependency pins;
- finite live matrix;
- incomplete-data/media-type semantics;
- exact-head deployment binding;
- commit trailer identity; and
- scope-review triggers.

Do not begin implementation until the owner approves or amends the plan.
