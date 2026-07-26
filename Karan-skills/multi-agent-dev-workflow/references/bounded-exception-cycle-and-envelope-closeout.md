# Bounded exception cycles and fail-closed contract closeout

Use this reference when a PR has exhausted its normal review/fix budget but objective blockers remain.

## Exception authorization is a finite contract

Record every human-approved exception as a small ledger before launching the builder:

- approved blocker class(es);
- allowed files/surfaces;
- maximum extra fix cycles;
- required verification commands/probes;
- required current-head reviewer lanes;
- explicit non-goals;
- merge authority remains with Karan.

One exceptional cycle means **fix + independent verification + exact-head re-review**. A pushed commit is not the end of the authorized cycle.

If re-review finds a blocker outside the approved class or surface, relay the current-head artifacts, stop, and request a new explicit decision. Do not reinterpret “approved” as an unlimited loop. A same-class correction can continue only when the original exception explicitly allowed another attempt.

## Deduplicate before asking

Before escalation, group reviewer findings into objective blocker classes rather than counting comments. For each class report:

- reproducer;
- affected contract/AC;
- whether code, tests, docs, or PR metadata must change;
- which reviewers confirmed it;
- recommended narrow fix.

This keeps the decision human-sized and prevents one root cause from looking like several unrelated blockers.

## Run a closure matrix before spending the exception

Do not fix only the exact examples named by the first review and immediately launch all reviewer lanes. For duplicated/compiled safety artifacts (SQLite exports, caches, generated manifests, normalized tables plus embedded JSON), first enumerate every value the runtime consumes and every parallel representation that claims to authenticate it.

Build a producer/consumer matrix covering at least:

- artifact/table presence and non-empty requirements;
- manifest-declared membership versus actual rows;
- SQL/normalized row identity and ownership versus embedded identity and ownership;
- normalized content versus embedded content for every consumed field, not just ID sets;
- projection/include lists and other denormalized routing data;
- client-declared scopes/workstreams versus modules that can actually enforce them;
- correlated deletion, same-ID mutation, duplicate/rogue rows, and cross-owner reassignment;
- genuine canonical artifact as the positive control.

For each duplicated field, decide one source of truth and either compare the other representation by full canonical content or remove it from the enforcement path. If a scope is accepted only because a client declares it, require that the scope resolves to at least one owned enforcing module; otherwise fail closed rather than returning a clean result.

Run these probes in memory or against disposable copies before the exception builder exits. This avoids a whack-a-mole sequence where each final re-review discovers the next unauthenticated field.

## Use an A-first convergence gate for narrow exception closeout

After an exception fix, do not automatically spend three parallel reviewer runs if Reviewer A is the lane actively discovering adversarial correctness bypasses.

1. Default Hermes independently runs the named regressions and full gate.
2. Launch Reviewer A alone for an exploratory exact-head adversarial pass across the whole approved blocker class, not only the named examples.
3. If A finds a reproducible blocker, relay it, classify whether it is inside the authorized class/surfaces, and stop for a new human decision when the ledger does not permit another attempt.
4. Launch Reviewer B and the Integration Auditor only after A returns zero blockers, unless their independent specialties are needed to adjudicate the finding.
5. A single reproducible P0/P1 blocks merge readiness even when B and the Auditor pass. Passing lanes are evidence about their inspected surfaces, not votes that cancel a concrete bypass.

The exception ledger should distinguish **blocker class** from **enumerated reproductions**. If approval covers only exact reproductions, same-class variants still require a new decision. If Karan intentionally authorizes one class-wide closure attempt, say so explicitly and cap it to one builder attempt plus the A-first gate.

## Reviewer provider refusal is a non-verdict

A reviewer process can exit without a signed artifact because the model provider rejects an otherwise legitimate consistency probe, the launcher loses its session, or another reviewer-infrastructure boundary interrupts generation. Do **not** convert that into PASS, FAIL, or a blocker count.

1. Confirm that no complete `BEGIN_ARTIFACT` / `END_ARTIFACT` body and terminal `DONE:` marker were produced.
2. Record the run as infrastructure/no-verdict; do not relay truncated reasoning or partial findings.
3. Keep the same exact head, detached worktree, packet, role, model, and review scope.
4. Retry once with equivalent **correctness/data-integrity/regression** language, avoiding unnecessary adversarial or security terminology while preserving every required reproduction and acceptance check.
5. If the retry also fails without an artifact, escalate the reviewer infrastructure problem instead of substituting another lane or claiming review completion.

A provider refusal does not consume a code-fix cycle because repository state did not change. It may consume a reviewer-attempt budget, so use the retry only after verifying the head and packet are still current.

After an A-first approval is relayed, later B/Auditor packets may still predate that public artifact. Either refresh a small immutable review supplement containing the current-head A approval, or name its verified URL/head explicitly in the downstream prompts.

### Stage review-state reconciliation instead of manufacturing packet-timing blockers

For exceptional/surgical closeout, use a strict stage barrier when the Integration Auditor is expected to certify review state:

1. Run Reviewer A alone; wait for exit, inspect the terminal marker, relay/read back the exact-head artifact.
2. Run Reviewer B; wait for exit, relay/read back its exact-head artifact.
3. Freeze a small review-state supplement containing the verified current head, A review URL/state, B artifact URL/verdict, checks, and threads.
4. Launch the Integration Auditor last with the original immutable implementation packet plus that supplement.

Do **not** launch A/B/Auditor concurrently and then ask the Auditor to block on absent current-head A/B artifacts that could not have existed when its packet was frozen. That converts orchestration timing into an artificial review blocker and wastes expensive reviewer runs.

If B and the Auditor must run concurrently for latency, split the Auditor contract explicitly: it may issue an implementation/AC verdict while marking review-state synthesis as `pending-relay`, not a code blocker. Default Hermes must then reconcile B, live checks, threads, and head after both lanes exit. Rerun the Auditor only if B exposes a material implementation seam the Auditor did not test—not merely because its packet predated B's comment.

## Disposable reviewer-worktree hygiene

A nominally read-only reviewer may invoke packaging/test tooling that leaves untracked metadata such as `*.egg-info` in its disposable worktree. Treat reviewer worktrees as contaminated scratch after execution:

- never use their final `git status` as evidence about the builder branch;
- verify artifact hygiene from the builder/exact-head source worktree and PR diff;
- capture the reviewer artifact, then remove/recreate the disposable worktree before another lane if generated files could affect inspection;
- do not ask a read-only reviewer to clean files it cannot delete.

## Fail-closed registry and DSL closeout

For safety-sensitive test registries, validate the complete envelope before evaluation:

- identity/path fields are non-empty strings;
- human-readable `question`/`rationale` fields required by the contract are non-empty strings;
- gating fields such as `required` are real booleans;
- unknown top-level keys fail closed except documented extension namespaces such as `x_*`;
- misspelled safety keys such as `gaurds` cannot silently remove assertions;
- query, expected-result, and guard fields are relationally compatible.

Require direct negative probes for missing, wrong-type, misspelled, unknown, and gating-suppression cases. Also prove the documented extension path still works.

### Close the column-type contract across every consumer

When a registry declares per-column types, do not harden only filters or expected rows. Build a value-flow census for every place the column can be consumed:

| Consumer | Scalar form | Collection form | Required proof |
|---|---|---|---|
| Query filters | `field: value` | any supported `in`/list form | wrong-type rejection + valid control |
| Expected rows | selected key/value | row collections | JSON/type-sensitive equality |
| Field guards | `require_field_equals` | `require_field_in`, `forbid_field_in` | operand type validation before evaluation + strict comparison |
| Controlled guards | status/confidence/severity/predicate | allowed/forbidden lists | schema vocabulary and element-type validation |
| Export/runtime projection | normalized SQLite scalar | embedded/JSON representation | normalize once at the boundary and preserve the declared JSON type |

The durable pitfall is Python's loose scalar equality: `False == 0` and `True == 1`. A row comparison may be hardened while a guard evaluator still fails open through ordinary `==` or `in`. Therefore:

1. Validate scalar and every list element against the selected column's declared type before evaluation.
2. Use one JSON/type-sensitive comparator for row matching and all guard equality/membership paths; do not let Python boolean/integer coercion define contract truth.
3. Add both negative and positive controls for every affected consumer: `false` versus `0`, `true` versus `1`, valid booleans, wrong-type values on string columns, and mixed-type list operands.
4. Run the adversarial closure census **before** spending an exceptional builder cycle, then use Reviewer A as the A-first convergence gate before launching B/Auditor.
5. Derive probe counts after these cases land; a green suite that does not exercise one consumer path is not evidence that the class is closed.

### Operator shape must precede column typing

Column-aware element checks are insufficient when the generic operand envelope has the wrong cardinality. Validate in this order:

1. guard/operator key envelope;
2. operator-specific container shape;
3. selected-column type for the scalar or every list element;
4. controlled vocabulary where applicable;
5. JSON/type-sensitive evaluation.

For existing field guards:

| Operator | Required shape | Essential controls |
|---|---|---|
| `require_field_equals` | exactly one scalar; reject lists and mappings | boolean `false` accepted for a boolean column; `0`, `[]`, `[false]`, and `{}` rejected; equivalent string-column controls |
| `require_field_in` | non-empty list of scalars | `[false]` accepted for a boolean column; bare `false`, `[]`, `[0]`, `["false"]`, and mixed `[false, 0]` rejected |
| `forbid_field_in` | non-empty list of scalars | same shape/type matrix as `require_field_in`, plus evaluation controls proving matching and non-matching behavior |

Do not encode membership operands as a generic `nonempty_str_list` when the selected column may be boolean or another scalar type. The generic layer should enforce “non-empty scalar list”; the column layer should decide which scalar type is valid.

Every positive and negative control must pass through the public registry-validation path (for example `validate_questions()`), then evaluation where relevant. Calling a private evaluator directly can prove strict comparison while completely bypassing a broken registry envelope. The exception is not converged until valid controls are expressible end to end and malformed scalar/list shapes fail early as usage errors.

### Accepted values must survive the complete failure path

A validator/evaluator contract is not closed merely because accepted values compare correctly on the success path. Trace every newly accepted value shape through:

1. registry validation;
2. match and non-match evaluation;
3. failure-message construction;
4. human and JSON rendering/serialization;
5. stable ordering/deduplication used by diagnostics.

This matters when a DSL intentionally permits heterogeneous JSON scalars for an untyped or extension field such as `fields.*`. Python cannot directly order mixed scalars: `sorted([False, "x"])` raises `TypeError`. Do not call raw `sorted()` on user-controlled heterogeneous collections in diagnostics. Preserve declaration order, or sort with one deterministic canonical key such as `(json_type_rank(value), canonical_json(value))` / compact canonical JSON text.

For every membership operator, add public-path probes that use an accepted heterogeneous list against both a matching and a non-matching actual value. Require a deterministic result/failure object and rendered message—never an exception. Include at least:

- `require_field_in` with heterogeneous accepted scalars on an intentionally untyped selected field;
- `forbid_field_in` with the same shape;
- a miss path that exercises diagnostic formatting;
- a hit path that exercises forbidden-value reporting;
- JSON output and human summary parity.

Whenever a fix broadens accepted input from a homogeneous type to “any scalar,” audit all downstream `sorted`, `min`/`max`, comparison, set/dict-key, string interpolation, and serializer assumptions before review. The durable lesson is **acceptance-domain expansion requires a downstream consumer census**, including error reporting—not just validator and happy-path evaluation tests.

This is a class-wide envelope check, not a request to expand the DSL. Keep the fix to existing declared consumers and preserve the issue's runtime/query boundaries.

## Machine-derived count parity

Never copy probe/test counts from builder prose or infer them manually. At the exact head:

1. parse the machine output;
2. assert the total case count;
3. derive valid/malformed or pass/fail splits programmatically;
4. compare those values with the live PR body, fix comments, docs, and immutable review packet;
5. make count drift a blocker when the PR uses those numbers as verification evidence.

Prefer executable assertions or generated summaries so adding cases cannot leave stale prose.

## Merge-readiness certificate

After the last pass, verify and report together:

- local head = remote branch head = PR `headRefOid`;
- required checks green;
- Reviewer A formal current-head state plus Reviewer B and Integration Auditor signed current-head artifacts;
- zero unresolved current-head threads;
- issue-closing linkage;
- clean worktree and no tracked generated artifacts;
- live PR metadata matches exact-head behavior and counts.

GitHub's aggregate `reviewDecision` can remain blank when no matching branch rule exists. In that case, use current-head reviews API records, checks, threads, and mergeability as evidence, and disclose the blank aggregate rather than treating it as a failed approval.
