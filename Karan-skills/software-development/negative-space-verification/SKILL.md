---
name: negative-space-verification
description: "Adversarial verification for safety-sensitive validators, projections, workflow summaries, generated artifacts, and final remediation cycles: test omitted stages, unknown attribution, contradictory states, hostile-but-plausible inputs, and objective accessibility properties that happy-path suites miss."
version: 1.1.0
author: Hermes Agent
metadata:
  hermes:
    tags: [verification, adversarial-testing, validators, workflows, privacy, accessibility]
    related_skills: [integration-audit-review, autonomous-pr-prover, deterministic-validator-review, web-application-qa]
---

# Negative-Space Verification

## Purpose

Use this skill when a system appears green on its known fixtures but correctness depends on what happens when input is **missing, contradictory, unattributed, oddly formatted, or omitted from the modeled path**.

This is a companion to `integration-audit-review`, `autonomous-pr-prover`, `deterministic-validator-review`, and `web-application-qa`. Those skills govern the review loop and authority boundary; this skill supplies the adversarial boundary matrix.

## Trigger

Load this skill when reviewing or proving:

- owner-safe/public-safe projections and redaction;
- validators or deterministic checkers;
- workflow producer → adapter → report pipelines;
- aggregate counts paired with row-level evidence;
- generated HTML/PDF/report artifacts;
- status machines, guards, protective stops, or tri-state semantics;
- the second/final remediation cycle of a bounded PR-prover loop;
- UI acceptance where geometry passes but accessibility/readability may still fail.

## Core Principle

A passing suite proves the cases encoded in the suite. It does not prove:

- every producer stage reaches the consumer;
- balanced totals are truthfully attributed;
- a fail-closed scanner recognizes formats its projector missed;
- a status is coherent in both directions;
- a clean screenshot meets measurable accessibility requirements.

Test the **negative space** before accepting the artifact.

**Do not confuse richer instructions with stronger controls.** If a recurring failure concerns model/runtime pinning, worktree concurrency, exact-head transitions, cycle limits, scope resets, or remote verification, move that guarantee into a versioned executable control plane. Keep the skill as a concise operator interface and put optional prompts, domain detail, and deterministic helpers in `templates/`, `references/`, and `scripts/`. Prompt prose is not runtime proof.

## Procedure

### 1. Map the full evidence path

Write the real path before probing:

```text
source → normalization/planning → fan-out/runtime stages → collectors → aggregate summary → adapter/model → rendered artifact → final leak/accessibility checks
```

List every stage that can produce a count, failure, warning, guard event, or owner-visible value. Inspect actual committed producer code; do not infer the path only from fixtures or docs.

### 2. Build a boundary matrix

For each safety-bearing field or relationship, include:

- valid value;
- missing value;
- explicit null/unknown;
- wrong type;
- invalid-but-plausible value;
- contradictory related values;
- value embedded in punctuation, JSON, path, URL, or human prose;
- reordered/permuted input when determinism matters.

Keep probes small and deterministic. Prefer direct execution of committed producer/consumer code over handwritten stand-ins.

### 3. Verify privacy as two independent layers

Owner-safe/public-safe handling requires:

1. field-level allowlisting/projection;
2. a fail-closed final scan with independently broader detectors.

Probe quoted JSON assignments, punctuation-bound identifiers, phone variants, email addresses, person-name prose, person-name filenames, raw upstream errors, URLs, credentials-in-URL, traversal/path values, and secret-like names.

If provenance is untrusted, prefer a safe stage/action label plus a withheld marker. Regex-only best effort is not a confidentiality guarantee.

### 4. Reconcile aggregates with rows

When an aggregate count and row-level evidence coexist, enumerate every producer stage—including discovery, normalization, planning, guards, and pre-fan-out failures.

Assert a contract such as:

```text
failed count == actionable file rows + explicitly classified non-file/global failures
```

Never allow `failed > 0` beside “no file-level failures” unless the difference is explicitly modeled and explained.

### 5. Reject invented attribution

Arithmetic consistency is not source truth. For category/reason totals, probe known, missing, and invalid attribution while at least two planned buckets are nonzero.

Do not decrement an arbitrary bucket merely to make sums reconcile. Unknown attribution must fail closed, remain explicitly incomplete, or use a contract-approved `unknown` bucket.

### 6. Enforce bidirectional state semantics

For each status, test both required evidence and forbidden combinations.

Example for a pre-mutation guard stop:

- `guard-aborted` requires `guard.fired === true`;
- unknown/false guard state is invalid;
- mutation counters must be zero or absent;
- rendered copy cannot claim “stopped before mutation” alongside positive mutations.

An allowlisted status string is not enough.

### 7. Measure visual properties

For generated UI/report artifacts, pair visual inspection with deterministic measurements:

- text/background contrast ratios;
- computed font size and weight;
- mobile pseudo-labels and muted/empty-state text;
- print CSS colors and visibility;
- geometry, clipping, overflow, and semantic labels.

A neat screenshot does not prove WCAG contrast.

### 8. Handle final-cycle failure honestly

When a bounded prover’s final normal cycle still has blockers:

1. stop automated code changes;
2. relay/read back all exact-head reviewer artifacts;
3. run the Integration Auditor after focused reviewer artifacts are durable;
4. deduplicate without erasing distinct evidence;
5. record `HUMAN_ESCALATION / NO-GO` in the project ledger;
6. keep the PR/tracker open unless the human chooses closure;
7. offer bounded choices: exceptional scoped cycle, defer, or close/replace.

Any exceptional cycle must be approved with named blocker classes, allowed surfaces, proof commands, and a finite extra-cycle cap.

## Verification Output

Report:

- exact source/head under test;
- matrix cases executed;
- real outputs and reproductions;
- which happy-path surfaces passed;
- blocker classes that remain;
- whether findings require normal remediation or human escalation.

Passing tests and clean visuals should remain in the report, but must not override reproduced safety or truthfulness blockers.

## Pitfalls

- Expanding the existing fixture set without executing the real producer path.
- Reusing the same incomplete detector for both projection and final leak scan.
- Treating balanced totals as proof of truthful attribution.
- Testing only `status → evidence`, not `evidence → valid status` and forbidden combinations.
- Omitting planning/normalization failures because runtime collectors are easier to exercise.
- Calling raw filenames “safe” solely because they lack obvious token syntax.
- Verifying visual geometry while skipping contrast and print styles.
- Quietly opening an extra remediation cycle after the configured cap.

## References

- `references/executable-control-plane-boundaries.md` — first-principles split between versioned enforcement and skill guidance; state machine, hardened builder, scope-reset, source/install, and real-PR pilot requirements.
- `references/final-cycle-boundary-matrix.md` — reusable probe checklist and closeout sequence for final-cycle safety/reporting reviews.
