# Trusted-Agent Control-Plane Proportionality

Use this reference when a PR adds security or launcher infrastructure around autonomous builders/reviewers.

## Start with the actual trust statement

Before judging implementation quality, write down:

- whether builders/reviewers are trusted to edit, commit, push, and publish scoped artifacts;
- whether Hermes independently verifies live exact-head evidence;
- who retains merge/deploy/account authority;
- whether agents are intended to be hostile same-UID tenants or trusted scoped coworkers.

If Claude/Codex are trusted for scoped repository work, Hermes verifies them, and Karan alone merges, the default architecture is a thin orchestration tool—not a zero-trust multi-tenant execution platform.

## Contract-drift smell

A child contract that simultaneously demands direct GitHub mutation, credential non-exposure to the process, same-UID lane isolation, filesystem/network/process escape prevention, runtime byte integrity, configurable generic lanes, and fail-closed behavior will naturally produce a custom capability/sandbox platform. The code may faithfully satisfy that child while violating the parent product goal.

Treat this as **contract/architecture failure**, not automatically poor implementation quality.

## Evidence decomposition

Report separately:

- production source;
- tests/test support;
- docs/examples/bin;
- nonblank/noncomment production code where useful;
- current-line attribution by mission slice;
- the launcher/security boundary’s share of production source.

A roughly 1:1 source:test ratio may indicate genuine coverage rather than padding. The key proportionality question is whether the boundary has become larger than the useful workflow it protects.

## Trusted-agent minimum

Usually retain:

- exact-head inspection and stale-verdict invalidation;
- isolated worktrees;
- bounded fix cycles;
- repository-native gates and UI proof;
- direct trusted builder/reviewer repository operations;
- live GitHub head, commit, identity, role, and artifact readback;
- deterministic markers, simple state/lock, and Karan’s final merge gate.

Question or remove absent an explicit hostile-tenant requirement:

- custom credential RPC/capability brokers;
- per-lane bearer secrets and socket authentication;
- synthetic HOME and same-UID credential-path proofs;
- shadow models of external sandbox semantics;
- cross-lane filesystem/process/socket isolation;
- runtime executable fingerprinting/byte attestation;
- future container/VM/cgroup/job-object qualification;
- generic script-lane compatibility without a real second use case.

## Verdict wording

Prefer: **“The code seriously and correctly implements an over-demanding contract.”** This separates engineering discipline from product proportionality and makes the fix clear: narrow the contract rather than merely refactor the same concepts.

## Recovery recommendation

When the approved core predates an overengineered slice:

1. preserve the draft PR, review history, remote branch, and dirty WIP;
2. stop scheduled workers following the obsolete contract;
3. save a checksum-backed patch without resetting;
4. create a clean replacement from the last independently approved head;
5. implement only the narrowed trusted-agent slice;
6. publish and verify the replacement before closing the old PR as superseded;
7. never force-rewrite or delete the evidence branch merely to make history look clean.

This produces a reviewable recovery without defending sunk cost or discarding already-approved core behavior.
