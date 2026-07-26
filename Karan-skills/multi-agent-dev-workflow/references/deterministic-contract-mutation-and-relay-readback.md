# Deterministic contract mutation probes and ambiguous relay readback

Use this when an issue or PR claims an installed CLI/placeholder is **deterministic**, **fail-closed**, or continuously enforced by CI.

## Why happy-path checks are insufficient

A helper that checks only:

- expected exit code;
- empty/non-empty stdout;
- parseable JSON; and
- presence of a generic key such as `error`

can still false-pass a nondeterministic or semantically wrong implementation. The current implementation may look correct while the CI gate fails to protect the contract.

## Minimum mutation matrix

Run the committed test helper against disposable fake installed entry points, not by editing repository source:

1. **Positive:** real installed entry point passes from the claimed consumer environment.
2. **Nondeterministic mutant:** same exit/stream shape but a fresh random value per invocation must fail.
3. **Deterministic-but-wrong mutant:** stable JSON with the wrong field/value must fail.
4. **Partial-success mutant:** non-empty stdout when the contract is stderr-only must fail.
5. **Exit mutant:** correct payload with the wrong exit status must fail.

For installed-console claims, keep the probe faithful to the issue:

- install from the exact PR head into a fresh virtualenv;
- invoke absolute installed executable paths, not source modules;
- use a foreign temporary cwd;
- restrict `PATH`/remove `PYTHONPATH` when isolation is part of the contract;
- generate required runtime artifacts before removing build-time tools;
- verify both the positive execution and the mutations.

## Strong deterministic assertion pattern

When the placeholder contract is intentionally stable:

1. Invoke it at least twice.
2. Require the expected exit code and stream placement on every invocation.
3. Require byte-identical output across invocations.
4. Parse the structured output.
5. Require the exact expected discriminator/value; when appropriate, require the exact key set or schema too.

A test is not complete merely because the real implementation currently behaves deterministically. The mutation probes must prove the test would fail if that behavior regressed.

## Review/fix loop

- Relay the concrete mutation reproduction as a signed blocker through the PR bus.
- Send Claude only the PR pointer/branch/issue; let it read live feedback.
- After the fix, independently rerun the old mutant plus a deterministic-wrong mutant and the real installed positive case.
- Re-run exact-head CI and all required reviewer lanes because test/CI code changed.
- Synchronize stale PR-body CI claims before creating the final immutable re-review packet.

## Ambiguous transport relay

A shell wrapper can return non-zero after one or more GitHub review/comment calls already succeeded. If individual calls printed success/status or comment URLs:

1. Treat the transport as **ambiguous**, not failed and not successful.
2. Do not immediately retry; that can duplicate reviews/comments.
3. Re-query the live PR head first.
4. Read back formal reviews, conversation comments, inline comments, and review threads.
5. Verify author identity, role signature, model/reasoning line, full head SHA, review state, and artifact URL/body.
6. Retry only the specific missing artifact.

GitHub readback, not the aggregate shell exit, is the success criterion for external review transport.
