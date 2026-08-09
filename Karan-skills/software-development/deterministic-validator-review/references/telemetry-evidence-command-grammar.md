# Telemetry evidence: closed command grammar probes

Use this when a deterministic checker validates committed browser evidence containing loader requests and modeled provider calls.

## Threat model

A clean committed artifact can coexist with an unsound guard. Treat the evidence JSON as untrusted input: it may gain extra config fields, extra command tuples, or query parameters while preserving the expected status, run count, runtime hash, and all known event rows.

## Required validator shape

Validate provider traffic as one closed grammar:

- exact command allowlist (for example `consent`, `js`, `config`, `event`);
- exact tuple length and argument types per command;
- exact config-key allowlist and value domains;
- exact event-name/key/value allowlists;
- rejection of unknown commands such as `set` or `user_properties` unless explicitly contracted;
- exact loader URL, or parsed equality against a finite approved query schema;
- payload-only privacy scan, separate from input URL/referrer/provenance fields.

Do not use a condition like `forbidden appears in record unless it also appears in record.url`: a value appearing in both input and payload is the leak case, not an exemption.

## Independent mutation matrix

Run these against the public checker entry point from an isolated temporary copy while keeping the exact-head worktree clean. Capture the source worktree's full SHA and explicitly check out that SHA in every copy: a plain local clone of a detached worktree can select another advertised/default ref, producing convincing green/red output against the wrong base. Print and assert each copy's `git rev-parse HEAD` before crediting the probe.

1. Add an unseen semantic name/free-text config field, e.g. `user_name: "JaneDoe"`.
2. Append an unknown provider call, e.g. `["set", "user_properties", {"full_name":"Jane Doe"}]`.
3. Append a sensitive query parameter to an otherwise approved loader URL.
4. Add the same sensitive value to both the hostile source URL and a provider payload.
5. Add an extra argument to each known command tuple.
6. Add one unknown config key with a benign scalar to prove structural closure independently of PII detection.
7. Duplicate a once-only approved event while leaving interaction counters unchanged.
8. Append an extra repeated event while preserving valid tuple shape and all aggregate/counter fields.
9. Delete one occurrence of a legitimately repeated event, then reorder causally significant event rows after initialization.
10. Swap one approved placement for another approved placement (for example `hero` → `footer`) while preserving the exact payload schema.
11. Replace an exercised position with a different valid in-range integer (for example `2` → `12`).
12. Flip an interaction-outcome field (for example a rejected drag claiming the viewer opened) while leaving event rows and numeric counters unchanged.
13. Positive controls: the exact approved loader, every permitted command/value, and every scenario's exact event sequence with interaction-owned values still pass.

For cardinality and value probes, compare more than event-name membership. A predicate such as `requiredEvents.every(name => emittedNames.includes(name))` proves presence but not exactness; a global placement enum or bounded integer proves schema validity but not interaction truth. Pin an expected event contract per scenario, including event name, placement/position when present, exact repeated-event cardinality, and explicit outcomes for rejected interactions. Reconcile it with recorded counters (for example one section view, tap + keyboard opens, no drag open, and `lightboxOpenAfterDrag === false`) and enforce sequence when the harness drives a deterministic order. Otherwise an artifact can remain structurally valid while overcounting conversions or contradicting its own interaction evidence.

### Repair pattern for deterministic browser scenarios

Make the scenario definition—not the evidence artifact—the authority for expected events. Give every eligible scenario an explicit expected multiset or ordered list, including scenarios expected to emit nothing and scenarios with legitimate repeated events. Compare the recorded event list exactly; do not derive expectations from the artifact under review.

Use exact order only when the producer drives a deterministic interaction sequence. If browser scheduling can legitimately vary, compare multisets and separately reconcile causal counters rather than freezing incidental order. Keep initialization command order (`consent` → bootstrap → `config`) separate from interaction-event order.

After replacing presence checks with exact comparison:

- update older self-tests whose expected diagnostic named the superseded presence predicate;
- add named duplicate, deletion, reorder, approved-value-swap, and contradictory-outcome regressions;
- run one unchanged external verifier before and after the repair;
- keep product runtime and committed evidence byte-identical for checker-only fixes;
- reconcile pinned mutation counts and proof claims in operator docs, specs, success diagnostics, and the live PR body; and
- read the PR body back remotely after editing it, verifying the new totals are present and stale totals are absent before restarting exact-head review.

Every invalid mutation must make the checker exit nonzero for the intended reason. A self-test count is not evidence unless at least one external mutation outside the builder's named corpus is rejected.

### Self-restoring external verifier pattern

Prefer one unchanged verifier that:

1. reads and retains the evidence file's original bytes;
2. deep-clones the clean parsed artifact for each mutation;
3. writes one mutant, invokes the public checker in a subprocess, and records the real exit code;
4. restores the original bytes in `finally` even when a mutation or checker crashes;
5. runs the clean control after restoration; and
6. exits nonzero if any invalid mutant passed or the clean control failed.

Run the same verifier before and after the repair. The useful proof is `FALSE_PASS` on the old head becoming `REJECTED` on the new head without changing the verifier. Finish by checking the exact-head worktree is clean; restoration claims are not enough.

For a checker-only repair, prove scope as well as behavior: the served runtime bytes and committed browser-evidence artifact must remain byte-identical. Run the full suite, focused public checker, checker self-test, and fresh direct red/green copies of the reviewer mutations before exact-head re-review.

## Reporting

Separate:

- current evidence correctness;
- evidence-validator soundness;
- honesty of success messages such as “all payloads are PII-safe.”

Recommended blocker wording: **“Current evidence clean; committed browser-evidence gate accepts privacy-invalid provider grammar.”** Include the validator `file:line`, the exact mutation, and the public checker’s real exit code/output.
