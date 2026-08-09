# Background review budget and flaky-gate triage

Use this reference when exact-head Reviewer A/B jobs are long-running or when a reviewer reports a gate failure that the parent verification did not reproduce.

## Preserve the parent control-plane budget

The expensive work is not finished when A/B start or exit. Default Hermes still needs enough tool/runtime budget to:

1. validate both markers and prepared bodies;
2. re-query the live head;
3. relay A/B under the verified reviewer identity;
4. read back immutable artifact IDs;
5. refresh every review surface into the post-A/B packet;
6. launch and collect the Integration Auditor;
7. relay/read back the Auditor artifact;
8. perform the stable feedback-state re-read and final synthesis.

Launch bounded reviewer jobs with completion notification. Do not spend one tool iteration per minute on repeated `wait`/`poll` calls while the jobs are healthy and quiet. Use at most one diagnostic poll after a meaningful quiet threshold or when completion notification appears missing. Prefer a single parallel status check over serial polling.

Before launching A/B, estimate whether the remaining execution budget can cover the entire ordered chain. If not, stop at a stable exact-head checkpoint before launch. If a platform limit arrives after launch, preserve the exact head, process handles, worktree paths, packet hash, and unrelayed status; never infer verdicts from partial stdout or artifact existence.

## Triage a reviewer-only gate failure

One failing run in a reviewer sandbox is evidence to investigate, not automatically a product blocker and not something to waive because the parent suite passed.

Use this order:

1. Verify the reviewer stayed on the frozen full SHA and left the detached worktree clean.
2. Capture the exact test name, command, exit status, runtime, and failure output.
3. Re-run the focused test multiple times in the same reviewer launcher mode when the lane is still available.
4. Re-run the identical focused test from an independently verified exact-head parent or disposable worktree.
5. Compare process/sandbox details relevant to the test: temp/cache roots, process-group/session ownership, signal behavior, timeouts, concurrency, and inherited environment policy. Do not compare credentials or dump environment values.
6. Classify the result explicitly:
   - **product blocker** — deterministic or credibly reproducible on the shipped supported path;
   - **reviewer-infrastructure blocker** — caused by the bounded launcher/sandbox rather than product behavior;
   - **flaky/pending evidence** — intermittent and not yet localized.
7. Do not relay a pass while a load-bearing failure remains pending. Do not publish a formal code blocker from a single irreproducible sandbox failure without the concrete reproduction and boundary analysis.

For process-management tests, prefer repeated focused execution plus a real child/process-tree probe over increasing sleeps. Timing-only repairs and blanket retries can hide ownership defects.

### When the same unchanged timing test flakes across runtimes

Do not keep restarting the entire proof chain as gate roulette. If the same test alternates between Python/runtime lanes while:

- the test and implementation have no base-to-head diff;
- one complete exact-head run already passed every required gate;
- focused repetitions pass on the same clean head; and
- the head, branch, PR body, and operator authorization inputs remain unchanged,

preserve the successful run's gate evidence and frozen packet. Continue only through the repository's lower-level governed reviewer lifecycle: fresh isolated worktree, credential-free repository-owned launcher, canonical final-message/prepared-artifact validation, sanitized configured relay, immutable-ID readback, and a newly frozen packet after each upstream publication. This is reuse of complete exact-head evidence, not a waiver or invented pass.

Hard stops:

- do not alter the gate command, exclude the test, increase a threshold, or patch unrelated code;
- do not reuse a packet after the head or any required contract surface changes;
- do not hand-author reviewer output or publish directly from the reviewer lane;
- do not infer success from a watchdog exit;
- if canonical validation/readback fails again or no complete all-gates run exists, stop fail-closed.

## Checkpoint output

When work must pause mid-chain, record only verified facts:

- exact PR head and packet hash;
- reviewer process status/handles;
- whether complete signed bodies exist;
- whether anything was relayed and, if so, immutable IDs;
- unresolved failure classification;
- the next ordered barrier.

Never call the PR merge-ready until A/B and the post-A/B Auditor are all durable on the same live head and the final feedback-state gate is stable.
