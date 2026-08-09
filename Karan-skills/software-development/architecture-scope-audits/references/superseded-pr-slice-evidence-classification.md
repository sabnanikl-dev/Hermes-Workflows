# Superseded PR Slice-Evidence Classification

Use this when a historical mega-PR is preserved as implementation/review evidence but active work must land as a clean, child-owned PR from current `main`.

## Core rule

Treat the historical PR as **behavioral and review evidence**, never as an accepted merge unit. A historical test run, review, or useful implementation does not transfer to a new SHA. Prefer method/hunk-level reuse over file-level cherry-picks.

## Evidence order

1. Read current repository guidance and the normative mission contract.
2. Read the live child issue plus adjacent/dependent issue contracts; current ownership decides classification.
3. Read the historical PR body, commits, comments, reviews, and final unresolved blockers.
4. Compare historical base/head with current `main`; identify mixed commits and files before recommending extraction.
5. Classify behavior by current ownership, not by historical commit title.

## Required ledger

For each relevant path or method group, record:

- **Reusable in this slice** — behavior and focused tests satisfying the active issue.
- **Mixed; extract narrowly** — name reusable methods/hunks and excluded methods/hunks.
- **Deferred** — behavior explicitly assigned to another issue or final integration proof.
- **Forbidden/non-goal** — superseded architecture, authority, security-platform machinery, deployment, merge, or unrelated scope.
- **Already merged/current authority** — contracts, routers, or foundations that must not be recopied from the historical branch.

Include commit provenance when useful: initial implementation, necessary corrections, mixed corrections, and entirely deferred commits.

## Load-bearing separations

- **Transport versus proof:** relay success is not GitHub readback; report them distinctly when the contract requires it.
- **Publication readback versus feedback ownership:** a fresh artifact ID can belong to an execution slice, while durable shared-login ownership/edit reconciliation belongs to a later feedback slice.
- **Execution hygiene versus zero-trust:** process-group teardown, inherited-session overlays, temporary artifacts, and credential-free reviewer lanes do not imply brokers, synthetic HOME, attestation, containers, or detached-descendant qualification.
- **Focused fixture versus final matrix:** keep one end-to-end fixture required by the active slice; defer exhaustive cross-slice, visual, metadata, and anti-Goodhart proof to the integration slice.
- **Current suite versus historical churn:** do not import historical test deletions, reorganizations, exact module counts, or brittle prose/line-count assertions.

## Caveats

- A final historical head blocked in a deferred subsystem is not globally accepted. State which seams remain useful and which verdict cannot transfer.
- Later amendments to the live issue override historical prompts and tests. List acceptance gaps the old PR could not have proven.
- Exact-head reviews and test counts apply only to their recorded SHA.
- Mixed commits require chunk-level classification; never label a whole commit reusable solely from its title.

## Compact output

1. Historical/current base and head statement.
2. Path/method extraction table with rationale.
3. Deferred and forbidden groups by owning issue/class.
4. Commit provenance summary.
5. Current acceptance gaps absent from historical evidence.
6. Workspace mutation statement.

This gives a later verifier a bounded checklist for reviewing the clean builder diff without turning the old mega-PR into a de facto patch source.