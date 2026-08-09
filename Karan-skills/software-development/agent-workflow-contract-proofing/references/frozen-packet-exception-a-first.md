# Frozen Reviewer Packets and Bounded Exception Closeout

Use this reference when a PR repair cycle depends on a credential-free reviewer packet or Karan authorizes a finite exception after the normal repair budget is exhausted.

## Freeze the exception

Before launching the builder, record the exact starting head, consumed normal-cycle budget, approved blocker classes, explicitly accepted/retired findings, allowed surfaces, forbidden adjacent scope, maximum builder attempts, required verification/review sequence, and unchanged authority boundaries.

If Karan accepts broad trusted-builder shell access for one exception, preserve that scoped decision and do not let a later reviewer revive it as a blocker. This is not a permanent default and grants no merge/deploy/account authority.

## Validate the landed packet at both levels

A correct producer is insufficient; serialization can discard the proof. The final public packet reader must validate:

### Envelope

- exact schema and positive sequence integers, rejecting booleans;
- canonical repo/PR/base/head plus reviewer/role binding;
- exact required surface set;
- boolean `complete`, non-empty string `read_as`, non-boolean non-negative integer `count`, list `items`, and `count == len(items)`.

### Inner contract records

- exactly one PR-body item bound to the expected PR;
- a present string PR body (empty may be valid when explicitly allowed);
- governing issue records whose ordered unique numbers exactly equal trusted configuration;
- present string bodies for every governing issue;
- clipping/completeness consistency.

Never infer governing authority from `Refs`, `Closes`, or arbitrary PR prose. Pass the trusted configured issue tuple into packet readback and compare it to the landed file.

## Mutation matrix

Test the public reader and loop seam for missing/wrong envelope fields, boolean numeric fields, wrong lane binding, missing/null PR or governing bodies, substituted/duplicate governing numbers, governing sets differing from config, clipped contract marked complete, and absent/null closing references versus explicit `[]`.

Every invalid case must assert zero reviewer lanes, zero transport, and no `merge-ready`. Keep positive controls for valid round-trip, explicit present-empty closing references, and honestly incomplete non-contract surfaces.

## A-first exception re-review

After an exception repair changes the head:

1. verify local/upstream/remote/PR/commit-list SHA agreement;
2. rerun full gates and focused former-red probes;
3. refresh stale PR contract/evidence;
4. run Reviewer A first;
5. run Reviewer B only if A has zero P0/P1 blockers;
6. run the Integration Auditor only if B also clears.

A residual approved-class blocker means the finite builder attempt was incomplete; it does not authorize another attempt. A new blocker class requires a new Karan decision.

## Reviewer runtime versus verdict

Live logs can contain historical artifacts copied from the packet. Count a verdict only after process completion with exact-head role/runtime declarations, final machine marker, and complete prepared artifact body.

If the process exits without those, record no verdict. A same-lane retry on the unchanged head is a reviewer transport retry, not a builder cycle. If the complete exact body is returned in final output but scratch writing is unavailable, Hermes may relay it unchanged after live-head revalidation, disclose transport-only provenance, and read it back. Never reconstruct missing substance from partial logs.

## Blocked closeout

If A-first stops, keep the PR draft/unmerged and tracker active/blocked; relay A when possible; state that B/Auditor were intentionally not run; report the exact reproduction, consumed exception budget, and smallest repair; obtain fresh approval before another builder attempt.
