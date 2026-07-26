# Ontology competency relationship/path review

Use this when an ontology PR extends a deterministic competency-question corpus from entity/rule lookups to relationship rows or bounded graph paths.

## Contract reconstruction

Treat the live issue as authoritative. Separate three independent maturity dimensions:

1. **Model representation** — the schema can express the concept.
2. **Client coverage** — canonical, source-backed client resources actually contain the needed facts.
3. **Runtime queryability** — a supported consumer can retrieve the answer safely.

A test-owned query DSL can satisfy competency coverage without automatically expanding a public CLI/service. Verify that docs do not blur those boundaries.

## Relationship query gate

A relationship may surface only when all of these are true:

- the relationship belongs to an in-scope module;
- subject and object belong to the named client;
- both endpoints are included by the selected projection;
- predicate/filter/select operands are valid and deterministic;
- status/confidence guards bind to selected output fields rather than silently no-op.

Test excluded-module endpoints and foreign-client endpoints directly. Module membership alone is not sufficient isolation.

## Bounded path gate

Require a deliberately small path contract:

- explicit start and end constraints;
- explicit allowed predicates;
- integer minimum and maximum hop counts;
- a hard maximum-hop cap;
- deterministic ordering;
- simple-path/cycle handling stated and tested;
- every traversed edge and node projection-scoped and client-scoped;
- explicit path identity semantics when parallel relationship rows share subject, predicate, object, and confidence.

For parallel edges, either include relationship IDs in the public path representation or deduplicate by the complete public representation before comparison. If duplicate counts differ, diagnostics must remain useful; set-only missing/unexpected diagnostics are insufficient.

Probe disallowed predicates, below/above hop bounds, cycles, parallel edges, branching, duplicate routes, stable ordering, unreachable endpoints, malformed constraints, and foreign/excluded intermediary nodes. A path result that filters only its final output after traversing a wider graph is a blocker.

## Registry envelope and guard compatibility

Validate the full discriminated envelope before evaluating answers:

- required identity/human-readable fields are non-empty strings;
- `required` is a real boolean;
- unknown top-level/query/`expect`/guard keys fail closed except documented extension namespaces;
- filters accept only documented scalar/list shapes **and each operand matches the selected column's real type** (for example, reject boolean/number values for string IDs); do not let a generic “scalar” check accept values SQL will merely fail to match;
- relationship filters and path allowlists validate predicates against the canonical vocabulary plus only the documented extension syntax;
- every schema-controlled column used by the DSL is covered by the same vocabulary source, including less-obvious fields such as rule severity; do not maintain a partial hand-written set;
- controlled entity/status/confidence operands are validated rather than accepted as arbitrary strings;
- select outputs are unique and recognized;
- expected row/path shapes exactly match selected outputs;
- expected path chains are relationally compatible with query start/end constraints, allowed predicates, hop bounds, per-edge metadata, and the traversal's node-identity semantics;
- when traversal is simple-path-only, reject repeated nodes in expected chains; when endpoint constraints include entity type, validate the expected endpoint against scoped canonical data before evaluation (a DB-aware validation pass may be required);
- guards are compatible with the operation and selected fields;
- malformed relationship/path definitions become usage errors before any answer is trusted.

Include typo probes for safety-bearing keys, relationship predicates, path predicates, unknown `expect` keys, contradictory expected chains, invalid controlled values, and incompatible guards. Explicitly test the dangerous vacuous-pass shape: a typo returns an empty answer, `expect: []` matches it, and universal status/confidence/ID guards pass because there are no rows. A registry intended to prove an existing answer must reject that definition before evaluation.

Required positive assertions should assert a non-empty expected result. Define `required` exactly once across the registry, runner, docs, and PR prose—prefer **gating positive assertion**, not an automatic synonym for evidence-backed client coverage. Coverage proof should be a separate, explicit mapping from a coverage claim to canonical evidence plus a competency that retrieves the claimed answer. If a repository instead defines every `required: true` question as coverage proof, then a planning-only/non-coverage safety check cannot remain required. If the product needs absence questions, introduce a separately named negative/absence assertion mode that cannot be cited as positive coverage; do not let `required: true` plus an empty expected list ambiguously mean both. Optional empty expectations may stay non-gating, but they must never back a `covered` matrix cell.

### Type-strict answer comparison

Validation-time operand types are not enough; normalize or compare runtime results type-strictly too. SQLite commonly serializes booleans as integer `0/1`, and Python equality makes `False == 0` and `True == 1`. A runner can therefore report `PASS` even when its JSON `expected` and `actual` values have different types. At the query/projection boundary, convert storage booleans back to real booleans, or use a JSON/type-sensitive comparator. Add true and false controls that assert both value **and** serialized type, including filters and expected rows.

## Loading and result isolation

Result filtering is not proof of projection-directed loading. Instrument the shared parser/loader at every actual read boundary, including manifest lookup, projection resolution, explicit-reference resolution, and export. Assert excluded modules and other clients are never parsed. Separately verify relationship endpoints and path intermediaries cannot leak through query results.

## Status/confidence and evidence safety

Competency questions must preserve uncertainty honestly. Add guards proving draft/proposed/inferred technical flows cannot appear as verified current architecture. Drift probes should mutate one status/confidence edge and fail only the competency question that depends on it.

A modeled draft relationship is not automatically a source-backed competency answer. For every required question, verify that the canonical resources actually returned carry evidence appropriate to the claim. If they do not, record a coverage gap or select another genuinely source-backed question; never fabricate evidence or promote draft/proposed data merely to satisfy the matrix.

## Coverage contract review

For each current client, check the documented matrix covers:

- business identity, offerings, audiences, constraints;
- people/roles and durable responsibilities;
- systems, repositories, domains, environments, systems of record;
- integrations and data flows;
- workflows, state transitions, actions, approvals;
- metric definitions, sources, cadence, planning vs observed;
- maintenance ownership, handoff, lifecycle posture.

Use a controlled status vocabulary such as `covered`, `known gap`, `not applicable`, and `deferred/trigger-gated`. Each `(family, client)` cell should carry exactly one controlled status unless the contract explicitly defines separately statusable subrows. Keep model-representation, coverage-evidence, and runtime-queryability notes in distinct columns or basis text; compound labels such as `covered / gap` blur the maturity dimensions.

A `covered` claim should identify exact proof. If the contract says competency retrieval establishes coverage, the cited competency must retrieve the specific resources **and fields/relationships named by that row**—retrieving an adjacent entity, a projection resource list, or an approval rule is not proof of a claimed website system, offering, state machine, or transition. Split broad rows when only part of the family is executable, or downgrade unsupported subclaims. A row with no exact competency closure cannot be labeled covered merely because the schema represents the concept. A coverage gap must remain explicit; do not invent canonical facts merely to turn the cell green.

After correcting a matrix cell, sweep the whole normative document, examples, registry comments, and PR prose for stale narrative claims. A later paragraph saying a client “covers” a represented-but-unevidenced family can silently undo an honest deferred matrix row. Treat the full chain as one contract: **canonical evidence → exact competency retrieval → matrix status → maturity examples → required/gating terminology → PR claim**. Any contradictory present-tense link is blocking when the PR claims proof-carrying coverage.

## Verification and metadata

Run the complete existing suite plus new positive/adversarial probes. Derive exact counts from executable output or source structures for total/new/required questions, operation distribution, malformed-vs-valid registry probes, drift cases, loading/resolver/scope cases, and runtime tests; compare them with the PR body and docs. Approximate counts are not merge-readiness evidence.

Keep optional-question behavior non-gating across the **entire** runner, not only the final exit calculation. Aggregate regressions such as drift isolation must compare the required-failure delta against a baseline or explicitly ignore pre-existing optional failures; otherwise one optional failure contaminates every drift case and indirectly forces exit 1. Add a full default-run regression where an optional question fails while drift checks remain enabled.

Keep reporting honest. The summary must say that required questions passed **and** name/count optional failures; never print “all questions passed” when an optional row failed, especially when PR evidence or CI uses the final output line. Likewise, disabling a regression (for example `--no-drift`) must produce an explicit `skipped` state in JSON/human output and remove that check from any “checks hold” summary. Never encode a skipped check as `passed: true` merely because it did not run.

Confirm generated SQLite/cache artifacts remain ignored and closing linkage is registered. Keep runtime-parity claims scoped precisely:

- runner-level deterministic query proof;
- parity for operations the public service actually serves;
- relationship/path operations that remain test-owned and runtime-deferred.

Do not say every competency question has YAML/SQLite service parity when the harness deliberately skips deferred operations.
