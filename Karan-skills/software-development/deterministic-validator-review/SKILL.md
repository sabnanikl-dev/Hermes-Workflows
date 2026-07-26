---
name: deterministic-validator-review
description: "Adversarially review deterministic validators, static checkers, policy scanners, and regression guards by separating current-artifact correctness from guard soundness and documentation honesty."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [code-review, validators, static-analysis, regression-testing, adversarial-testing]
    related_skills: [autonomous-pr-prover, code-review, integration-audit-review]
---

# Deterministic Validator Review

## Purpose

Use this skill when a PR adds or hardens a deterministic validator, static checker, policy scanner, contract test, migration verifier, content safety gate, or custom parser.

The central rule is:

> A green suite proves the committed fixtures pass. It does not prove the checker rejects contract-violating mutations or accepts valid boundary cases.

This skill complements PR workflow skills. `autonomous-pr-prover` governs agents, exact-head review, relay, and fix cycles; this skill governs how to test the checker itself.

## Trigger

Load this skill when:

- a PR claims `fail-closed`, `active document only`, `all variants`, `no false positives`, or similar completeness;
- a checker approximates HTML, regex, route, schema, or policy semantics;
- reviewers are fixing a checker rather than the product artifact;
- the full suite is green but a reviewer suspects a missing mutation class;
- documentation or success diagnostics make stronger claims than the implementation proves;
- a script is about to become the **completion gate for an autonomous run** (its `exit 0` decides whether a mission passed) — see §4.6 on oracle provenance before that run launches.

## Required state separation

Always assess and report these independently:

1. **Current artifact correctness** — committed page/config/data is valid.
2. **Guard soundness** — representative bad mutations fail and valid controls pass.
3. **Claim honesty** — code comments, diagnostics, tests, specs, PR body, and handoff prose claim no more than the guard proves.

A PR may pass the first while remaining blocked on the second or third. Never dismiss a false-pass or false-positive merely because the current artifact is safe.

## Procedure

### 1. Inventory the public contract

Read every relevant claim surface:

- issue acceptance criteria;
- PR body;
- checker comments and success messages;
- test names and fixture descriptions;
- specs, AGENTS guidance, friction/decision logs;
- prior reviewer findings.

Extract strong phrases into a claim table, especially:

- “cannot” / “always” / “all”;
- “active only”;
- “full morphology”;
- “no false positives”;
- “supports” a parser or regex feature;
- “fail-closed.”

### 2. Build external claim-derived mutations

For each claim, create at least one violating mutation and one valid control. Do not derive the entire matrix from implementation branches; that only re-tests assumptions already encoded by the author.

Run mutations against the public checker entry point from an isolated `/tmp` copy. Keep the repository worktree clean and preserve an exact-head identity check.

See `references/adversarial-claim-matrix.md` for boundary classes and reproduction patterns.

### 3. Test both directions

A sound gate needs:

- **false-pass probes:** invalid input must fail;
- **false-positive probes:** valid input must pass;
- **positive controls:** the committed artifact and representative valid fixtures pass;
- **scope controls:** unrelated files/config remain unchanged for guard-only fixes.

A large self-test count is not evidence of completeness. Independent reviewers should add at least one mutation not already named by builder fixtures.

### 4. Choose parser semantics or explicit policy

When a lightweight checker approximates a real parser or routing engine, accept one of two honest designs:

1. Implement the claimed semantic domain robustly and test its boundaries; or
2. Narrow the accepted policy/domain and explicitly document conservative rejection/manual review.

Do not retain heuristic behavior while claiming universal semantics or zero false positives. If scope is narrowed, update all contract surfaces in the same commit: comments, diagnostics, test labels, specs, AGENTS guidance, decision logs, and PR body.

### 4.5 Detect validator scope inversion

If the committed artifact remains correct but the checker keeps accumulating parser, routing-language, morphology, or other open-ended semantics, stop treating each adjacent counterexample as a normal fix. Warning signs include a guard that dwarfs the feature, rapidly growing fixture counts, stronger universal claims after every patch, and exceptions that keep discovering new blocker classes.

At that point choose a real semantic engine, narrow to an explicit finite repository policy, or replace/split the overbuilt PR. Do not continue example-by-example patching merely because another local self-test can be added. Freeze the replacement envelope before work begins, and treat reviewer ideas outside that envelope as follow-up proposals unless they prove the original issue acceptance criteria are unmet.

For the fresh-branch recovery sequence, artifact-hash reuse, conservative-policy examples, and reviewer-envelope rules, see `references/validator-scope-inversion-clean-replacement.md`.

### 5. Gate each fix cycle

Before exact-head re-review, require:

- full repository suite passes;
- public checker passes on committed artifacts;
- every previously reproduced invalid mutation now fails;
- valid controls still pass;
- docs and diagnostics match the proved domain;
- product artifacts/config are unchanged when the cycle is checker-only;
- tested local commit equals the remote PR head.

A builder’s passing self-test is not enough. Re-run the external mutation harness independently after the push.

### 6. Report blocker semantics precisely

Use language such as:

- “Current artifact correct; regression guard unsound.”
- “False pass contradicts the documented active-only guarantee.”
- “Valid scoped input is conservatively rejected; either support it or state the repository policy explicitly.”
- “Green suite demonstrates the missing fixture because the reproduced mutation still passes.”

Do not collapse product correctness and validator correctness into one status.

### 4.6 Check oracle provenance when the validator gates its own producer

When a validator is the completion gate for an autonomous run (an `exit 0`
that decides whether a mission passes), authorship and mutability matter as
much as logic. A run that can edit its own oracle has no gate: an agent at its
final remediation attempt, one assertion away from escalating, has both motive
and write access, and softening one line is cheaper than stopping. Nothing
outside the run would ever see it.

Independence here is **not** about whether a human typed the verifier. It is
temporal ordering + immutability + review:

1. **Produced in a prior invocation** than the run it judges.
2. **Adversarially reviewed** before that run launches (this skill).
3. **Hash-pinned and read-only** for the run's whole duration, asserted at
   start and end. Modifying it must be an escalate condition, not a fix.

This is the same rule already applied to trusted reviewer launchers — extend
it to the verifier, which is easy to overlook because it feels like test code.

When reviewing such an oracle, additionally require:

- **No run-specific facts baked in.** The verifier stays generic; the run
  declares its results in a claim file (paths, SHAs, digests, artifact IDs)
  that the verifier consumes as an *index only*.
- **Every claim independently reproved.** The verifier must re-hash the
  binaries itself, re-read installed bytes, re-query remote state, recompute
  manifest digests from disk. A claim the run controls is worthless as
  evidence — the run says what it did; the verifier says what it can prove.
- **No unchecked claim fields.** A field in the claim file with no
  corresponding independent check is a bug, catchable at review time.
- **Small enough to audit.** Past a few hundred lines an oracle stops being
  reviewable and the trust problem has merely relocated into unread code.
  Flag that growth as a blocker, not a detail.

Name the tradeoff explicitly in the review: moving enforcement from prose onto
a script makes a *weak* oracle more dangerous than vague prose, because
`exit 0` looks authoritative.

## Long-running review hygiene

For autonomous builders/reviewers:

- launch with completion notification and a realistic timeout;
- avoid minute-by-minute polling that exhausts the parent tool budget;
- poll at meaningful 3–5 minute milestones or when state can change a decision;
- prepare packets/probes while agents run;
- ensure enough tool/context budget remains to verify the push and exact-head re-review;
- create a durable continuation checkpoint before starting an exceptional cycle if the parent session is near its execution limit.

Sibling launchers may intentionally expose different flags. Use the invocation documented by the governing workflow skill; do not assume a workspace-write option accepted by one reviewer wrapper is accepted by another.

## Stop conditions

Stop and ask for a bounded exception when:

- the governing PR workflow’s normal fix-cycle cap is reached;
- a new blocker class appears outside the approved exception envelope;
- supporting the claimed parser domain would materially broaden dependencies or architecture;
- policy narrowing changes repository governance or requires product judgment.

## References

- `references/adversarial-claim-matrix.md` — concrete HTML/inert parsing, morphology, regex/route, structured-data, claim-surface, and external mutation-harness patterns.
- `references/validator-scope-inversion-clean-replacement.md` — detect when a checker has overtaken its feature, rebuild an issue-scoped replacement from a fresh branch with finite claims, preserve artifact hashes, and keep issue-closing metadata honest when live preview proof is unavailable.
