# Candidate-path dogfood and durable reviewer completion

Use this when the PR changes the reviewer adapter, evidence packet, verdict grammar, relay, or readback predicate itself.

## Build packets through the shipped contract

Do not handcraft a reviewer packet that merely resembles the schema. Use the repository's canonical packet builder, writer, and reader so these executable fields are produced and validated together:

- canonical binding string;
- sequence number;
- reviewer name and role;
- exact repository/PR/base/head;
- governing issue identities and bodies;
- required surfaces, completeness flags, read methods, counts, and item arrays.

A custom packet can contain all substantive evidence yet be correctly rejected by the candidate adapter because its protocol binding is wrong. That rejection is a packet-construction failure, not a reviewer/product finding.

## Dogfood the candidate adapter

A direct installed-CLI smoke proves argument syntax and external-directory access, but not the changed lifecycle. Final proof must run the adapter from a clean detached worktree at the live PR head and require the child itself to create its prepared artifact before exit.

Then exercise:

```text
canonical packet
→ candidate adapter exact argv
→ isolated final-message parser
→ candidate prepared-artifact parser
→ normal application relay
→ immutable-ID GitHub readback
```

Run Reviewer A, relay/read back, refresh the packet, then Reviewer B, relay/read back, refresh again, then the Integration Auditor. A test or operator that writes the artifact after the child exits is not adapter proof.

## Prove prepared and published parity separately

Before relay, compare parsed lane findings with the prepared artifact one-to-one. After relay, parse the exact body read back from GitHub and compare the same records again. Status and blocker count alone cannot detect truncation or substitution.

Mutation cases must preserve declarations while removing, adding, duplicating, renaming, re-severing, or rewriting findings. Include malformed/near-miss markers and wrong author/head/role/commit controls.

## Probe grammar boundaries before normalization

For every documented bound `N`, test `0`, `1`, `N`, and `N+1`. A regex containing one mandatory character followed by `{0,N}` accepts `N+1` total characters.

Accepted records must be preserved exactly except for an actual secret-redaction match. Reject over-limit input before clipping, redaction, or canonicalization can collapse distinct raw records into one parity-equivalent value. Mutation-probe the boundary and preservation guard.

## Durable completion when wrapper tracking is lost

A launcher wrapper may lose its tracked exit status while its verified native child remains alive. Do not restart the lane or infer failure from the wrapper record.

- prove the native PID belongs to the launched lane;
- attach a wait-only watchdog rather than a second reviewer;
- after exit, require durable artifact delimiters, final marker, exact-head/role binding, and clean worktree;
- treat process termination as process evidence only, never as a pass/fail verdict.
