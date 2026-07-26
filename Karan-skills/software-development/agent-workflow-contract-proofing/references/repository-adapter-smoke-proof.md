# Repository Adapter Smoke Proof

This reference captures a reusable proof pattern for repository-owned agent workflow adapters. It is intentionally implementation-oriented; the parent skill holds the class-level policy.

## Why this gate exists

A control-plane change can pass hundreds of unit tests while the shipped path remains unusable or unsafe. The recurring failure modes are contract drift across boundaries:

- example prompt emits a comment format the parser rejects;
- shell adapter checks fewer credential names than the Python lifecycle defines;
- top-level API pagination hides an incomplete nested connection;
- a launcher exits successfully but its audit correctly reports blockers.

## Exact-head smoke recipe

1. Verify the implementation worktree is clean.
2. Confirm local HEAD, remote branch SHA, and live PR `headRefOid` are the same full SHA.
3. Create a disposable detached worktree named for the short SHA.
4. Invoke the repository-owned reviewer adapter with:
   - exact repo/PR/head/worktree arguments;
   - artifact output under `/tmp`;
   - all defined GitHub credential variables removed;
   - the real installed reviewer CLI, not a no-op stub.
5. Observe the process rather than assuming quiet output is a hang.
6. Validate the finished artifact:
   - expected role exactly once;
   - expected signature;
   - explicit verdict and blocker count;
   - exactly one standalone canonical `HEAD=<sha>` line;
   - worktree still clean.
7. Re-query the live PR head.
8. Relay under the reviewer identity and read back author/body/head/verdict.

## Credential-free invocation pattern

```bash
env \
  -u GH_TOKEN \
  -u GITHUB_TOKEN \
  -u GH_ENTERPRISE_TOKEN \
  -u GITHUB_ENTERPRISE_TOKEN \
  PR_PROVER_CODEX=/absolute/path/to/codex \
  ./scripts/reviewer-adapter.sh \
    --role adapter-smoke \
    --repo owner/name \
    --pr 123 \
    --head "$HEAD" \
    --worktree "$WORKTREE" \
    --artifact-file "/tmp/adapter-smoke-$HEAD.md"
```

Adapt flag names to the repository. The important properties are exact-head binding, real downstream execution, credential absence, disposable worktree, and `/tmp` artifact output.

## Producer/parser round-trip probe

Do not merely assert that the parser accepts a hand-built valid string. Extract or render the actual shipped builder prompt, follow its documented comment shape, and pass that output through the runtime readback predicate.

Required positive shape:

```text
HEAD=0123456789abcdef0123456789abcdef01234567
```

Required negative probes:

```text
HEAD: 0123456789abcdef0123456789abcdef01234567
Reviewed head was 0123456789abcdef0123456789abcdef01234567.
HEAD=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
HEAD=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
```

The final case represents duplicate/conflicting declarations. Also reject duplicate-but-equal declarations to preserve unambiguous binding.

## Credential parity probe

For each authoritative credential variable:

1. install a probe executable that records if invoked;
2. set exactly one credential variable to a non-empty sentinel;
3. invoke the shipped adapter;
4. require the adapter's credential-refusal exit;
5. prove the probe executable was never called.

Run once per credential name. This catches shell/Python drift that a general environment-scrubbing unit test can miss.

## Complete-surface probes

### Conversation comments

Return two REST pages where the only human blocker appears on page two. The classifier must see it and block readiness. Preserve deterministic page order because comment-ID snapshots may be compared across reads.

### Formal reviews

Return more than one page and ensure current-head review state is not hidden by page one.

### Review threads

Test both levels:

- more than one top-level thread page;
- one thread whose nested comments connection reports `hasNextPage: true` and places the only human author outside the returned slice.

If nested pagination is intentionally not implemented, the second case must raise a controlled fail-closed result. Also test missing `pageInfo`, missing connection, malformed nodes, and one incomplete thread among otherwise complete threads.

## Cycle decision table

| State | Action |
|---|---|
| Smoke passes | Launch fresh exact-head A/B/Integration triad |
| Smoke finds a false positive | Record adjudication with proof, then continue |
| Smoke finds omission in current frozen blocker class; corrective unused | One corrective rerun in the same cycle |
| Corrective already consumed or two cycles exhausted | Stop and request blocker-scoped exception |
| Exception approved | One named patch pass only, then restart smoke + triad |
| Exception pass still blocked | Stop; no implicit additional rerun |

A bounded exception record should state:

- exact current head;
- durable blocker artifact URL;
- exact blocker classes;
- permitted files/surfaces;
- prohibited scope expansion;
- verification commands;
- maximum extra builder passes;
- requirement for fresh adapter smoke and final triad.

## Evidence checklist

- [ ] local/remote/live SHA equality
- [ ] clean disposable worktree
- [ ] real adapter and installed reviewer CLI used
- [ ] all credential names removed/rejected
- [ ] full suite on every supported runtime
- [ ] producer/parser round-trip tests
- [ ] credential parity tests
- [ ] pagination/completeness tests
- [ ] artifact role/signature/verdict/head valid
- [ ] relayed under reviewer identity
- [ ] GitHub readback verified
- [ ] current head unchanged after relay
- [ ] cycle/exception ledger updated

## Durable lesson

For agent workflow control planes, the adapter smoke is not a ceremonial command check. It is an early independent audit of the shipped producer/consumer contract. Run it before the expensive reviewer triad, and treat its blockers with the same exact-head, durable-artifact, finite-cycle discipline as formal reviews.
