# Risk router

Choose the lowest tier that can honestly support a merge recommendation. Record the choice before launching reviewers.

## Routine

Use when all material changes are low-risk and locally understandable, such as:

- copy, comments, docs, or metadata corrections;
- narrow CSS/presentation fixes without interaction or accessibility changes;
- test-only maintenance that does not weaken coverage or alter a validator contract;
- dependency-free cleanup with no runtime behavior change.

Default proof: repository-native gates, Hermes diff review, and one focused independent reviewer only when it adds useful coverage.

Escalate if the change touches generated artifacts, issue-closing semantics, CI, validators, or user-visible interaction.

## Standard

Use for ordinary product behavior:

- bounded bug fixes and features;
- API or CLI behavior with no sensitive authority;
- state or data transformations that are reversible and non-destructive;
- user-visible interactions, accessibility, or responsive behavior;
- repository configuration and CI changes with bounded blast radius.

Default proof: native gates, parallel Reviewer A/B, Hermes adjudication, and browser QA when the changed behavior is visual.

## High

Use when failure can create material harm, false readiness, difficult recovery, or authority expansion:

- authentication, authorization, credentials, secrets, privacy, PII, consent, or security;
- analytics activation or tracking lifecycle;
- payment, billing, destructive writes, schema/data migrations, or irreversible operations;
- production/deployment/runtime configuration and external-environment claims;
- release/cutover behavior or cross-system integrations;
- validators, evidence binders, review tooling, CI policy, or merge-readiness control planes;
- large mixed diffs or changes whose acceptance criteria are ambiguous.

Default proof: all relevant deterministic/integration/browser gates, parallel Reviewer A/B, then a dependent Integration Auditor, then Hermes live-state synthesis.

## Full Prover

Select only when one of these is true:

- Karan explicitly asks for the full PR Prover;
- the repository contract requires signed artifact transport/readback or its exact lifecycle;
- a high-risk PR needs the current tool's durable state, frozen packet, credential-free review adapter, and GitHub artifact provenance.

Do not select it merely because the PR is important. The current executable serializes Reviewer A, Reviewer B, and the Integration Auditor and carries significant ceremony. Record why its extra mechanics are necessary.

## Tie-breakers

- If two tiers plausibly apply, choose the higher tier only for a named risk, not a vague desire for confidence.
- A small diff can be High when it changes authority or proof semantics.
- A large generated diff can remain Standard when the generator and deterministic checks are trusted and the user-facing behavior is bounded.
- A reviewer suggesting generalized hardening does not retroactively raise the tier unless it demonstrates a current-head risk.
- If the selected tier's proof becomes larger or more complex than the feature, stop and ask whether the issue truly owns that proof machinery.
