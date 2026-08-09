---
name: deterministic-validator-review
description: "Adversarially review deterministic validators, static checkers, policy scanners, and regression guards by separating current-artifact correctness from guard soundness and documentation honesty."
version: 1.4.8
author: Hermes Agent
metadata:
  hermes:
    tags: [code-review, validators, static-analysis, regression-testing, adversarial-testing]
    related_skills: [autonomous-pr-prover, code-review, integration-audit-review]
---

# Deterministic Validator Review

## Purpose

Use this skill when a PR adds or hardens a deterministic validator, static checker, policy scanner, contract test, migration verifier, content safety gate, custom parser, or evidence/report generator whose rendered output can claim success or owner-safe status.

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

### 3.0.1 Prove parity across every transport boundary

When a validator governs agent verdicts, review artifacts, generated reports, or any staged publish/readback flow, validate the **same semantic records at every boundary**:

1. lane/process output;
2. prepared local artifact;
3. relayed or published remote body;
4. direct remote readback used for the terminal decision.

Checking status and count at readback is not equivalent to checking records. Add mutations that remove, add, rename, re-sever, rewrite, duplicate, truncate, or reorder finding records while preserving the declaration block, author, signature, head, and blocker count. If the remote readback predicate still passes, transport self-report has replaced proof of what landed.

Where the prompt, parser, artifact, and documentation claim one grammar, make one canonical parser drive all stages and compare records one-to-one. The prepared artifact and the published body both need this proof; pre-relay validation alone cannot detect relay-side truncation or substitution.

### 3.0.2 Probe exact length and regex boundaries

For every documented bound `N`, execute `N-1`, `N`, and `N+1` cases (plus empty/zero where applicable). Regexes with one mandatory token followed by `{0,N}` commonly accept `N+1` total characters. Verify the boundary before redaction or clipping and again after any canonicalization, because accepting then truncating changes the record while leaving the parse green.

Do not settle for a prompt-round-trip test that merely asserts the prose says “1 to N.” The production parser must reject `N+1`, and artifact/readback paths must preserve the exact accepted record.

### 3.0.3 Probe report truth, redaction, and source attribution

When a generator turns workflow/run evidence into owner-safe or operator-facing HTML/JSON/Markdown, test more than curated fixtures. Cross-check declared counts against detail rows, reject success when any failure evidence exists, prove every required issue-contract field survives the real producer→adapter boundary, and never attach a real execution ID to synthetic counts. Redaction needs independent families beyond the builder's examples (assignment-form secrets, Basic/Bearer credentials, opaque IDs at path boundaries, and person-bearing filenames).

Also separate **configured scope** from **executed evidence**: a skipped or not-yet-reached gate must never render as “checked,” “passed,” or “observed” merely because its configuration declares an endpoint or evidence mode. For strict producer-owned JSON envelopes, reject duplicate object keys before mapping validation, parse timestamps as real canonical UTC instants rather than regex-shaped strings, and reject/escape control-bearing values before Markdown rendering. A separate executed-results list does not cure a contradictory sentence elsewhere in the same report. Enforce byte limits before an unbounded read, and define any summarized adapter/topology identity precisely enough that interpreter wrappers and path aliases cannot silently change the answer.

Use `references/evidence-report-truth-and-redaction-matrix.md` for the general report matrix and stop rules. Use `references/evidence-envelope-report-integrity.md` for configured-vs-executed claims, duplicate-key JSON, semantic timestamps, Markdown structural injection, pre-allocation size limits, and topology identity probes.

### 3.0.4 Probe semantic privacy and real interaction state, not only test doubles

For analytics/policy guards over browser URLs, test the semantic privacy promise after browser decoding. A character-shape regex can reject obvious email and phone values yet still pass a literal or percent-encoded name/free-text value (for example, `JaneDoe` and `Jane%44oe`). If the contract forbids names or free text, require a finite approved-value policy or another demonstrably non-free-text boundary; a broad token grammar is not proof. Pair each reject case with a normal shipped route and approved acquisition-token control so hardening does not silently destroy required attribution.

When committed browser evidence records telemetry/provider calls, validate the **entire provider-command grammar**, not only known event rows. Require an exact allowlist of command types, tuple arities, config keys, event keys, value domains, and loader URLs. Reject unknown commands and unknown config fields: a checker that validates event parameters but ignores extra config parameters or `set`/`user_properties` commands can accept PII-bearing evidence while truthfully reporting that every inspected event is safe. Compare loader URLs by exact identity or an explicitly parsed finite query schema, never `startsWith`; otherwise a reviewed loader prefix can carry an appended email, token, or campaign value.

Close the **browser-evidence envelope** as well as provider calls. Bind every scenario label to its exact URL or finite parsed URL schema, hostile query/referrer inputs, status, and route facts; compare origins as parsed origins, never string prefixes. Validate interception/no-egress arrays by exact element shape and expected counts/multisets rather than merely requiring arrays. Validate the recorded public surface against an exact allowlist or baseline delta: regex rejection of names containing `analytics` still accepts forbidden generic APIs such as `track` and `emit`. Bind related `dataLayer`/`gtag` types on disabled and eligible paths, and reject unknown run/envelope fields when they can carry provider diagnostics, public state, request data, or PII. See `references/browser-evidence-envelope-closure.md`.

Also validate **event cardinality, sequence, interaction-owned values, and reconciliation with recorded interaction outcomes**. Requiring each expected event name to appear at least once is not a closed grammar: duplicated approved events can overcount conversions while every tuple remains individually valid. Likewise, checking that a placement belongs to a global enum or a position falls inside a numeric range does not prove the event describes the exercised interaction—a hero click relabelled `footer`, or photo 2 relabelled position 12, can remain schema-valid but evidentially false.

Derive an exact per-scenario event contract: ordered event names when the harness controls order, exact expected placements/positions and other interaction-owned values, and explicit outcome fields for rejected interactions. Cross-check provider calls against section-view counts, accepted tap/keyboard opens, rejected drag clicks, and before/after wake-up counters. A rejected-drag record must assert the viewer remained closed, not merely keep the event count unchanged. Mutate evidence by duplicating a once-only event, appending an extra event while counters remain unchanged, deleting one of repeated legitimate events, reordering causally significant rows, swapping one approved placement for another, substituting a different in-range position, and flipping a rejected-interaction outcome boolean; each contradictory artifact must fail while the clean control passes.

Scan provider payloads independently from hostile input/provenance fields. Never exempt a forbidden value merely because the same value appears in the run URL—the duplication may be evidence of leakage. Add unseen semantic-name/free-text probes rather than relying only on the builder's finite known-PII corpus. See `references/telemetry-evidence-command-grammar.md` for a compact mutation matrix and reproduction pattern.

For tracking that represents a successful UI transition, test the event at the component's committed state seam. Exercise click, Enter, standard Space, legacy `Spacebar`, an already-open dialog, and a real pointer drag followed by its synthesized click. Do not accept a fixture that simply writes a private suppression flag: ensure the fixture has enough data to enable the real gesture binding, since many carousels skip pointer/swipe setup for single-item fixtures.

When a client-side configuration value authorizes a loader, provider initialization, or telemetry, inject placeholder, empty, malformed, and syntactically valid-but-unreviewed values through the same config seam. Assert effects—not just a guard boolean: no script insertion, provider command, initial page event, queue, or network request. A syntax regex is not an authorization boundary; use an explicit reviewed allowlist for values capable of creating external effects, while retaining a positive controlled-debug control.

See `references/url-privacy-and-lightbox-state-probes.md` and `references/configured-activation-negative-space.md` for compact claim-derived matrices and exact reproduction patterns. When a third-party loader requires a window-named queue but page code must not gain payload authority, use `references/private-provider-queue-authority.md` for the conditional-loader accessor, QA-only defensive observation seam, mutation probes, compatibility boundary, and exact-head evidence lifecycle.

### 3.0.5 Separate semantic location from evidence polarity

Before reusing one parsed-tree helper across checks, classify whether finding a node is **negative evidence that fails** or **positive evidence that passes**. A broad walk can be conservative for forbidden markup such as `noindex`, yet unsound for required markup such as a canonical: body-only or inert-template declarations can manufacture a false pass.

For positive evidence, select the active semantic container before matching and counting. Probe body-only, template-only, one active declaration plus inert copies, and two active declarations through the public evaluator. A finite repository policy such as “direct child of the parser-built document head” is valid when every governed artifact follows it and all claim surfaces say so; do not dress it up as universal HTML semantics.

Use `references/semantic-location-and-evidence-polarity.md` for the operation order, minimum external mutation matrix, polarity comparison, and review wording.

### 3.0.6 Keep active-document semantics consistent across extraction seams

Do not stop after proving one HTML extraction path handles inert content correctly. Validators often parse metadata with active-node semantics while a separate regex-based `visibleText` helper still flattens `<template>` content. That split creates both a false pass for required positive evidence and a false positive for prohibited negative evidence.

For every reader-visible rule, inventory which extractor supplies its input: metadata, body copy, required disclosures, allowlists, duplicate signatures, and prohibited phrases. Run a template-only mutation through the **public evaluator** for each polarity:

- a required phrase only inside `<template>` must be reported missing;
- a prohibited phrase only inside `<template>` must be ignored;
- active required text plus an inert duplicate must still pass based on the active instance;
- nested templates must stay inert.

Prefer one parser-derived active text representation shared by all visible-copy checks. Attributes and comments should be unreachable by construction rather than removed by a tag regex. Probe quoted attribute values containing delimiter characters such as `>` plus template-looking literals and prohibited entities: the attribute must stay invisible while active text immediately after the element remains governed. Deliberately choose and test the parser's scripting mode so reader-visible `<noscript>` markup does not become undecoded raw text. If a finite checker retains regex anywhere in the extraction chain, its claims must stay within that accepted grammar and the matrix must include both false-green and false-positive controls. Reconcile success diagnostics and self-tests across every seam; “inert templates are ignored” or “attributes are exempt” is a whole-validator claim, not a metadata-only claim.

Use `references/active-visible-copy-and-required-evidence.md` for the minimum matrix, reproduction shape, and repair checklist.

### 3.1 Cross product valid and invalid control syntax

When one text body can contain both prose and a line-oriented control protocol, do not test valid and invalid lines only in separate posts. Build mixed-validity combinations in the **same** body.

The load-bearing rule is line-specific: only an exact line that passed syntax, target, chronology, authority, and self-reference checks may be removed as bookkeeping. A later residual-prose phase must not strip every line sharing the protocol prefix merely because one sibling line was valid. That pattern can erase malformed control-prefixed substantive text and produce false success.

Require valid-only controls, valid-plus-plain-prose cases, valid-plus-each-invalid-class cases, and a mutation test that restores broad prefix stripping. Test the cleared target and the source post's remaining findings independently. See `references/mixed-control-lines-negative-space.md` for the matrix and exact-head reviewer-reconciliation pattern.

### 3.2 Match binary-evidence claim depth to parser depth

For screenshots, archives, media, envelopes, or other container formats, separately prove recognition, complete container integrity, payload decode completion, decoded-shape semantics, and evidence binding. A signature/dimension check is not a decode; CRC/bounds checks do not prove legal chunk order; decompression does not prove row or manifest semantics.

Build independent malformed-container probes beyond the builder's named cases. Include honest controls at the same layer—for example a normal generated stream and consecutive split payload chunks—then attack duplicate headers, interleaved payload chunks, unknown critical elements, malformed terminators, trailing data, and decoded-shape mismatches. When identifier bytes encode semantics such as critical/ancillary status, validate the complete lexical envelope (width, allowed bytes, reserved positions/bits) before classification; otherwise malformed identifiers can fall through as optional extensions. After each repair, sweep the entire claim class rather than only the cited bytes. Keep the repair proportionate to the exact generated grammar instead of demanding a general-purpose parser.

See `references/binary-evidence-claim-depth-and-container-grammar.md` for the layered matrix, review sequence, deduplication rule, and bounded-cycle closeout.

### 4. Choose parser semantics or explicit policy

When a lightweight checker approximates a real parser or routing engine, accept one of two honest designs:

1. Implement the claimed semantic domain robustly and test its boundaries; or
2. Narrow the accepted policy/domain and explicitly document conservative rejection/manual review.

Do not retain heuristic behavior while claiming universal semantics or zero false positives. If scope is narrowed, update all contract surfaces in the same commit: comments, diagnostics, test labels, specs, AGENTS guidance, decision logs, and PR body.

For open token namespaces, scoped directive lists, or HTML metadata where arbitrary names can mean either crawler identity or ordinary document metadata, use `references/open-grammar-and-metadata-scope-probes.md`. Before freezing a builder path allowlist, search every authoritative contract and regression inventory; a narrow repair packet is valid only when its allowed paths are contract-complete. If syntax cannot resolve the policy ambiguity without a growing heuristic, stop and require an explicit finite-scope or fail-closed policy instead of opening another example-by-example repair.

### 4.5 Detect validator scope inversion

If the committed artifact remains correct but the checker keeps accumulating parser, routing-language, morphology, or other open-ended semantics, stop treating each adjacent counterexample as a normal fix. Warning signs include a guard that dwarfs the feature, rapidly growing fixture counts, stronger universal claims after every patch, and exceptions that keep discovering new blocker classes.

At that point choose a real semantic engine, narrow to an explicit finite repository policy, or replace/split the overbuilt PR. Do not continue example-by-example patching merely because another local self-test can be added. Freeze the replacement envelope before work begins, and treat reviewer ideas outside that envelope as follow-up proposals unless they prove the original issue acceptance criteria are unmet.

When the product artifact is already correct and can be proved directly without changing repository bytes, a human-approved **finite exact-head contract reset** may close the existing PR instead of opening another checker cycle. Bind trusted parser/browser probes (including reversible negative oracle controls) to the exact head and product hashes, amend and digest-verify the canonical governing issue/spec, reconcile prior review artifacts substantively, and run one mechanically read-only final triad. The reset narrows proof mechanics; it never waives actual product, privacy, accessibility, security, no-egress, or authority failures. See `references/finite-exact-head-contract-reset.md`.

For the fresh-branch recovery sequence, artifact-hash reuse, conservative-policy examples, and reviewer-envelope rules, see `references/validator-scope-inversion-clean-replacement.md`.

### 4.5.1 Bound semantic-lint claims before adding synonyms

For prose-policy scanners, distinguish **current committed-surface cleanliness**, **bounded mutation-corpus coverage**, and **general semantic recognition**. A finite regex/vocabulary matcher can prove the first two; it normally cannot justify the third. Do not treat a larger same-commit corpus, provenance labels, or rule-coverage counts as proof of open-ended English semantics.

If ordinary unseen lifecycle imperatives still bypass the guard after the second bounded cycle—or valid domain instructions are being rejected—stop synonym-by-synonym repair. Narrow the claim, replace free prose with structured metadata, split semantic hardening into a follow-up, or ask for a scope-bound exception. At cycle closeout, count only reviewer artifacts whose head, role, model, and reasoning runtime validate. Wrong-runtime outputs are diagnostic-only. One valid exact-head P1 is enough to withhold readiness; three valid passes are required to grant it.

See `references/semantic-lint-claim-boundaries.md` for the proof-level split, independent-corpus standard, runtime-integrity gate, blocked/needs-human closeout sequence, and the bounded recovery when Karan chooses contract narrowing. That recovery requires amending the issue before code, splitting broader semantics into a non-blocking follow-up, deleting rather than renaming the overclaim, directly auditing every committed target, retracting stale PR evidence, and verifying both GitHub and tracker closeouts separately.

### 5. Gate each fix cycle

#### Run one class-wide envelope sweep before Reviewer A

Do not use sequential exact-head reviewers as a mutation fuzzer. Before the first Reviewer A—or before restarting A after a validator repair—build one external, unchanged mutation batch from the complete claim table and sweep every load-bearing surface together:

- scenario identity: exact URL, hostile inputs, origin, status, and route facts;
- network outcome: aborted/fulfilled/placeholder/not-found shapes, counts or multisets, and unknown egress;
- public surface: exact keys, arity, `gtag`, `dataLayer`, debug/config registries;
- provider grammar: command types, order, arity, exact keys and values, exact loader;
- interaction evidence: event order/cardinality, approved-but-wrong values, counters, and rejected-action outcomes;
- envelope identity: viewport/scenario matrix, runtime binding, screenshots, result/problems, and contract-relevant unknown fields.

Run a clean control after every destructive family and restore the artifact byte-for-byte. If one batch can still discover adjacent false-pass classes after two repair cycles, classify that as scope inversion rather than opening another ordinary fix loop: freeze a finite replacement envelope, narrow the claims, or seek an explicitly bounded human exception. Rising self-test counts are not a reason to continue.

Before exact-head re-review, require:

- full repository suite passes;
- public checker passes on committed artifacts;
- every previously reproduced invalid mutation now fails under an unchanged external harness;
- valid controls still pass and destructive evidence probes restore the artifact byte-for-byte;
- docs, checker diagnostics, pinned regression counts, and the **live PR body** match the proved domain;
- after editing the PR body, direct remote readback confirms the new counts/claims and absence of stale values;
- product artifacts/config are unchanged when the cycle is checker-only;
- browser/visual evidence is either recaptured or preserved honestly: prove every rendered input byte-identical between the capture head and reviewed head, name both heads in the packet, and never relabel preserved evidence as freshly captured; obey a stricter repository binder when it requires new commit binding despite unchanged bytes;
- tested local commit equals both the remote branch and the PR head/commit list.

A builder’s passing self-test is not enough. Re-run the external mutation harness independently after the push. Any new code commit invalidates the exact-head reviewer sequence; restart Reviewer A, then proceed to later reviewers only after A passes.

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

- `references/semantic-negative-space.md` — active-vs-inert parser traversal probes (including `<template>` metadata) and evidence-based resolution when independent reviewers disagree on an untested boundary.
- `references/open-grammar-and-metadata-scope-probes.md` — class-wide probes for real token grammar, scoped-vs-site-wide directive parsing, unknown sibling masking, crawler-name versus ordinary-metadata ambiguity, contract-complete repair paths, and the post-exception stop rule.
- `references/adversarial-claim-matrix.md` — concrete HTML/inert parsing, morphology, regex/route, structured-data, claim-surface, and external mutation-harness patterns.
- `references/mixed-control-lines-negative-space.md` — fail-closed review for bodies mixing valid control lines, malformed control-prefixed substantive prose, and ordinary prose; includes the mixed-validity mutation matrix, exact-head reviewer reconciliation, bounded-cycle stop rule, and supporting mission-audit fan-out.
- `references/validator-scope-inversion-clean-replacement.md` — detect when a checker has overtaken its feature, rebuild an issue-scoped replacement from a fresh branch with finite claims, preserve artifact hashes, and keep issue-closing metadata honest when live preview proof is unavailable.
- `references/finite-exact-head-contract-reset.md` — close an existing exact-head PR after validator scope inversion by binding direct parser/browser probes, digest-verifying a human-approved canonical contract amendment, reconciling prior findings, and running one mechanically read-only final triad.
- `references/semantic-lint-claim-boundaries.md` — separate committed-surface cleanliness, bounded mutation coverage, and general semantic recognition; avoid synonym-chase repairs; validate reviewer runtime identity; and close out correctly when one valid P1 survives the cycle cap.
- `references/fixture-isolation-and-harness-recovery.md` — prevent shared mutable fixtures from inflating mutation coverage; prove order-independent fresh sandboxes and split verifier integrity from feature recovery when the checker becomes the blocker.
- `references/binary-evidence-claim-depth-and-container-grammar.md` — layered false-pass review for binary/container evidence: recognition vs integrity vs decode vs semantic shape vs binding, with chunk-order/critical-element probes, honest controls, same-class deduplication, and bounded-cycle closeout.
- `references/transport-parity-and-exact-boundary-probes.md` — four-stage lane/prepared/published/readback record parity, relay-side mutation cases, and `N-1`/`N`/`N+1` regex boundary probes.
- `references/evidence-report-truth-and-redaction-matrix.md` — adversarial producer→adapter→renderer probes for failure/count coherence, required-detail gaps, owner-safe redaction families, real-vs-synthetic execution attribution, and live-instance vs sanitized-export documentation truth.
- `references/browser-evidence-envelope-closure.md` — exact scenario URL/origin binding, interception/no-egress reconciliation, public-surface closure, and contract-relevant extra-field mutations for committed browser evidence.
