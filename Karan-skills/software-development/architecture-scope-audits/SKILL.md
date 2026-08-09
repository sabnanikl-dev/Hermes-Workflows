---
name: architecture-scope-audits
description: "Audit large code changes for architectural proportionality, contract drift, source-versus-test scope, duplicated mechanisms, and concrete simplification opportunities without mutating the worktree or trackers."
version: 1.3.0
metadata:
  hermes:
    tags: [architecture, scope, code-review, pull-requests, maintainability, verification]
    related_skills: [integration-audit-review, code-review, adversarial-technical-artifact-review]
---

# Architecture and Scope Audits

## Purpose

Use this skill when the decision is not merely “does the code work?” but “is this much architecture necessary for the governing mission?” It is especially useful for large PRs, security/control-plane work, autonomous-agent launchers, validators, workflow engines, and changes whose test volume may conceal a broad production surface.

The output is a proportionality verdict backed by immutable diff evidence:

- **necessary**;
- **defensible but too large**; or
- **overengineered**.

A sound security motive does not automatically make every supporting protocol, policy replica, configuration mode, or attestation layer proportionate.

## Authority Boundary

Default to read-only inspection.

- Do not edit source, tests, docs, GitHub, or trackers.
- Bind the audit to one exact base and full head SHA.
- If the named worktree contains WIP, inspect committed objects with `git show <sha>:<path>`, `git diff <base>...<head>`, and `git blame <head> -- <path>` rather than reading working-tree files.
- Record initial and final worktree status. Never reset, clean, checkout, stash, format, or import repository modules that may emit bytecode into the dirty tree.
- Use a disposable `/tmp` extraction only when execution is required and separately allowed.

## Workflow

### 1. Freeze the review target

Record repository, PR/change identifier, base SHA, exact head SHA, branch, and current worktree status. Confirm the local commit and live review target agree when live metadata is in scope.

### 2. Reconstruct the contract hierarchy

Read the governing parent mission and each implementation child relevant to the diff. Extract:

- required mechanisms;
- explicit non-goals and removed mechanisms;
- threat model and authority boundary;
- acceptance criteria;
- downstream qualification work;
- any child requirement that broadens or contradicts the parent.

A detailed child does not silently override an explicit parent removal. Treat an unresolved parent/child conflict as a human authority decision.

For agent launchers and PR control planes, reconstruct the **human trust statement** explicitly: what may Claude/Codex do directly, what does Hermes verify, and who alone may merge/deploy/change accounts? Do not infer a hostile same-UID tenant model when the mission describes trusted scoped coworkers. Code can be well-tested and faithfully implement its child issue while still being the wrong architecture because the child’s threat model drifted beyond the parent product goal.

### 3. Quantify the change

Split net LOC into source, tests/test support, docs/examples/bin, and generated assets. Report additions and deletions separately. Then identify:

- top files by LOC;
- largest classes and functions;
- architectural clusters and their share of source;
- source:test ratio;
- current-line ownership by commit or mission slice when the PR combines several contracts;
- physical source lines versus nonblank/non-comment/non-docstring code where useful.

Do not call the headline additions count “production code” when half is tests.

### 4. Identify essential mechanisms

Map every significant subsystem to a concrete acceptance criterion or threat. Typical essentials include exact-head binding, bounded attempts, fresh worktrees, narrow credentials/capabilities, readback, stale-verdict invalidation, and fail-closed behavior.

Verify that explicitly removed apparatus was not reintroduced under cosmetic renaming.

### 5. Audit avoidable complexity

Look for:

- multiple production execution modes with different assurance levels;
- a producer plus a separately maintained shadow interpreter/validator of the same policy;
- concurrency around operations another lock already serializes;
- custom RPC, lifecycle, packet, journal, or attestation machinery for a tiny closed vocabulary;
- repeated regexes, capability sets, role rules, SHA/path validators, and slug logic;
- giant coordinator classes that combine orchestration, transport, lifecycle, validation, and evidence;
- broad public APIs where the mission calls for one CLI/router;
- configuration flexibility that serves no approved deployment;
- code-owned replicas of external sandbox/provider semantics tested only against themselves;
- a security/launcher boundary larger than the useful workflow it protects, especially when the user already trusts the scoped agents and retains final merge authority.

For browser providers that require a mutable realm-global queue, do not accept a same-realm getter, symbol, proxy, frozen wrapper, or `document.currentScript` condition as private authority. Prefer an opaque sandboxed child realm when the product genuinely requires isolation, but keep the threat boundary finite: qualify provider-bound behavior through intercepted network attempts rather than publishing a top-page debug queue, and do not expand ordinary page-code protection into an impossible hostile-preinitialization/XSS sandbox unless the contract requires it. See `references/browser-provider-authority-realm-split.md`.

### 6. Evaluate test inflation honestly

Separate:

1. test share of the diff;
2. mechanical repetition or table-driven opportunities;
3. whether tests prove the load-bearing boundary.

Use AST/body-shape analysis when helpful to distinguish obvious copy-paste tests from distinct cases. A large suite with little mechanical duplication is **complexity-driven**, not padded. Still ask how many tests exercise real Git, processes, sockets, sandbox/client behavior, or provider readback rather than deterministic doubles.

Green tests that validate a local model of an external policy are circular evidence. Repeated live-probe failures after green modeled tests are a reason to shrink the replica and move semantic qualification to a real-client gate.

### 6.5 Require semantic closure for stateful classifiers

When a PR changes a classifier, validator, parser, evidence filter, ownership rule, or workflow state machine, test count and local branch coverage are not enough. Reconstruct the finite state/transition table before judging proportionality or approving another same-class repair.

The table must include both input-local and run-global/history state: same marker after an earlier transition, cross-input duplicates, mixed valid + invalid aggregates, restart/persistence, and exact cleared/retained/finding IDs. Distinguish **safety** from **transition correctness**: a fail-closed result can still violate the contract if it blocks a valid transition or retains the wrong findings.

Require three proof layers:

1. predicate tests for each individual state;
2. temporal sequence tests across multiple inputs/restarts;
3. shipped public-path probes asserting outcome, exact state transition, exact unresolved evidence, and supported-runtime parity.

If the same semantic blocker class recurs after a table-driven repair, recommend stopping the automated example-by-example patch loop for human-reviewed redesign or PR decomposition. See `references/stateful-classifier-semantic-closure.md` for the transition-table method, reviewer prompt capsule, and sensitivity requirements.

### 6.75 Classify superseded mega-PR evidence by current slice ownership

When a superseded historical PR is preserved as an extraction source for a clean child PR, do not treat its files, commits, tests, or reviews as one reusable unit. Reconstruct ownership from the current mission and live child/dependency issues, then produce a method/hunk-level ledger: reusable, mixed/extract narrowly, deferred, forbidden, and already merged/current authority. Distinguish transport from readback, publication identity from later human-feedback ownership, ordinary execution hygiene from zero-trust machinery, and one focused slice fixture from final cross-slice integration proof. Record which historical corrective commits contain useful seams, but never let a commit title override current issue ownership. See `references/superseded-pr-slice-evidence-classification.md` for the compact workflow and output contract.

### 6.9 Audit scoped plans as executable contracts

When the artifact is an implementation or replacement plan rather than code, audit the plan's producer-to-consumer chain, not only its stated architecture:

- hash the plan before and after review; if it drifts, re-read the final revision and bind the verdict only to its final hash;
- map every promised assertion to its authoritative repo input, parser/loader, fixture, and live evaluator;
- require finite definitions for incomplete/unreadable evidence and tests through the shipped adapter;
- validate CLI starting authority as well as redirect-hop containment;
- bind live deployment evidence to exact commit metadata, not merely a mutable alias or PR branch;
- treat platform-injected signals that violate acceptance as an ineligible test environment, never as a waived check;
- resolve human identity/config prerequisites before the first commit;
- measure the whole replacement—source, tests, and docs—not only production modules.

See `references/scoped-implementation-plan-contract-audit.md` for the compact ledger, exact-head deployment proof, drift handling, and output contract.

### 7. Decide and simplify

Return one primary verdict. Separate:

- essential mechanisms to retain;
- avoidable complexity to remove;
- contract conflicts requiring human resolution;
- concrete simplifications tied to paths.

Recommendations should remove concepts, not merely split large files. Prefer choosing one production mode, one policy source, one serialized broker, one shared validator vocabulary, and a narrow public surface. When the governing workflow trusts scoped builders/reviewers, prefer direct repository operations plus live readback over a custom capability platform.

If a narrow approved core exists beneath an overengineered later slice, recommend preserving the old draft/WIP and creating a clean replacement from the last independently approved head rather than force-rewriting history or discarding the useful core.

## Output Contract

Keep the report concise and evidence-first:

1. exact base/head and read-only status;
2. primary verdict;
3. source/test/docs LOC decomposition;
4. module/class hotspots;
5. essential mechanisms;
6. avoidable complexity and contract contradictions;
7. five to eight concrete simplification recommendations;
8. explicit statement that WIP and external systems were not modified.

Include file paths and line/range evidence for material claims. Do not bury the verdict beneath methodology.

## Pitfalls

- Treating all additions as source code.
- Equating a 1:1 test ratio with proportional architecture.
- Calling tests “inflated” without measuring repetition.
- Recommending only file splits; that moves complexity rather than removing it.
- Letting a child issue silently broaden an explicit parent non-goal.
- Reading dirty working-tree files while claiming an exact-commit audit.
- Treating a local sandbox/policy model as proof of the real client or OS.
- Treating a trusted scoped builder/reviewer workflow as a hostile multi-tenant platform without an explicit mission requirement.
- Blaming implementation discipline when the code faithfully implements an over-demanding child contract; state that distinction and recommend narrowing the contract.
- Confusing constant-time secret comparison with a forbidden MAC-envelope protocol; compare behavior, not vocabulary alone.
- Proposing an arbitrary target LOC without identifying which concepts disappear.
- Treating many isolated edge-case tests as semantic closure while omitting same-input/different-history and run-global state transitions.
- Accepting fail-closed output without checking whether the exact cleared/retained/finding sets satisfy the contract.
- Treating a same-realm provider queue accessor as private authority, or compensating by exposing a top-page QA/debug queue that recreates the production surface under review.
- Turning ordinary post-initialization page-code isolation into a hostile pre-runtime/XSS sandbox requirement without explicit contract authority.

## Reference

- `references/immutable-proportionality-audit.md` — exact-object inspection commands, metric recipes, test-shape analysis, and the verdict rubric.
- `references/stateful-classifier-semantic-closure.md` — finite state/transition tables, temporal and cross-input probes, safety-vs-correctness checks, and the stop rule for repeated same-class repair failures.
- `references/superseded-pr-slice-evidence-classification.md` — classify a historical mega-PR into current-slice reusable, mixed, deferred, forbidden, and already-merged evidence without turning it into a patch source.
- `references/browser-provider-authority-realm-split.md` — isolate provider-owned mutable queues in an opaque child realm, qualify behavior without a top-page debug surface, keep the threat model finite, and preserve narrow exact-head evidence layers.
