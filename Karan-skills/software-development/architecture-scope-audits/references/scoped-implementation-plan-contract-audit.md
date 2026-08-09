# Scoped implementation-plan contract audit

Use this checklist when independently reviewing a proposed replacement plan, especially after a blocked or oversized PR. The review is read-only and should return only concrete edits.

## 1. Freeze the artifact, then detect drift

- Record the plan path, SHA-256, line count, governing base SHA, and clean/dirty worktree state before review.
- Recompute the plan hash before verdict.
- If it changed concurrently, re-read the complete final artifact and bind the verdict only to the final hash. Do not silently combine findings from two revisions.
- State that the review is superseded by any later edit.

## 2. Reconstruct the full authority packet

Compare the plan against:

- governing issue body and material comments/handoffs;
- current default-branch code, configuration, tests, and documentation;
- exact blocked implementation/reviewer evidence when it supplies regression cases;
- explicit human authority, merge, deploy, credential, and live-operation boundaries.

When direct tracker access is prohibited or unavailable, use locally preserved exact issue/review evidence if present and label that provenance. Do not contact external systems against instruction.

## 3. Build a producer-to-consumer input ledger

For every promised live assertion, identify the exact authoritative repo input and every task that must carry it into evaluation.

Example ledger columns:

| Assertion | Authority input | Parser/loader | Planned check | Live consumer |
| --- | --- | --- | --- | --- |
| Branded 404 identity | committed 404 page | parsed primary heading | missing/ambiguous/mismatch fixtures | gone-route evaluator |
| Redirect destination | redirect config | validated URL object | query/fragment/off-origin fixtures | manual-hop evaluator |

Flag any assertion named in architecture or acceptance criteria whose source input is absent from the implementation sequence. Adding a parser helper is insufficient if the planner never loads its authority file.

## 4. Make fail-closed states finite

Terms such as `unreadable`, `unsupported`, `incomplete`, and `invalid` need an enumerated protocol, not builder judgment. Require the plan to define:

- accepted media types and missing-content-type behavior;
- stream overflow, cancellation, timeout, network, read, and decode failures;
- whether each state retains status/header evidence while failing body-dependent evaluation;
- one shipped-adapter test per state, not evaluator-only synthetic objects.

The central rule: no missing or partial evidence may be converted into an empty clean body.

## 5. Validate command inputs, not just internal hops

If a CLI accepts a deployment base URL, require tests for:

- HTTPS only;
- no credentials;
- bare origin versus path/query/fragment;
- prohibited production/legacy hosts during pre-cutover use;
- normalization behavior that cannot redirect the test toward an unintended target.

An evaluator that rejects off-origin redirects does not compensate for accepting the wrong starting authority.

## 6. Bind live evidence to deployed bytes

Git branch/head equality alone does not prove that a mutable deployment URL serves those bytes. Require the proof workflow to:

1. read local, remote branch, and PR head SHAs;
2. wait for a ready deployment;
3. read deployment metadata and require its commit SHA to equal the reviewed PR head;
4. record immutable deployment URL and deployment ID;
5. only then run and attribute the live gate.

A mutable alias by itself is insufficient exact-head evidence.

Also distinguish an **ineligible environment** from a product failure. If a normal preview injects a platform `noindex`, authentication redirect, or other signal forbidden by the acceptance contract, do not waive that signal to make the gate pass. Use an exact-head release-candidate environment where the real contract can be exercised, or report that live proof is not yet available.

## 7. Prove workflow prerequisites are executable

A plan that says “stop if identity/config/credential is empty” has identified a blocker, not resolved it. For load-bearing prerequisites, require:

- the named human or authority who supplies/approves the value;
- the exact value or a bounded approval step;
- readback before the first irreversible action;
- rejection of bot/model identities when human attribution is required.

Do not infer that any non-empty local configuration satisfies a human-identity contract.

## 8. Measure the whole replacement

When the goal is a materially smaller replacement, production-only line caps are insufficient. Decompose and compare:

- production/runtime source;
- tests and fixtures;
- hand-written docs/process files;
- generated lockfile churn separately.

Set a whole-diff review trigger in addition to module caps. Otherwise an implementation can satisfy a production budget while recreating the oversized change in tests and documentation.

## Output contract

Return:

1. exact artifact hash and base SHA;
2. one verdict: approve, amend before approval, or reject;
3. only concrete scope, correctness, dependency, test-contract, or workflow gaps;
4. for each finding: plan lines/section, consequence, and exact replacement/addition text;
5. final read-only/no-mutation statement.

Avoid generic advice, speculative hardening, implementation, or unrelated style commentary.
