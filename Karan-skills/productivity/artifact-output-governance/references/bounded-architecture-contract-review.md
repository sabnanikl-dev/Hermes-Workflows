# Bounded Architecture-Contract Review

Use this reference when a specification, operating contract, policy, architecture note, or other non-code artifact risks expanding into an implementation-total document or entering repeated review/fix loops.

## Core principle

An architecture contract should remove unsafe ambiguity at its boundary. It should not eliminate every legitimate implementation choice.

Independent review verifies the governing issue's acceptance contract. It does not maximize criticism or silently strengthen the completion threshold.

## 1. Freeze a governing contract card

Before authoring or review, record:

```text
Governing issue/version:
Approved issue digest:
Named user and decision:
Canonical destination:
Blocking severities:
Accepted outcomes: Continue / Narrow / Stop
Maximum repair cycles:
Explicit implementation deferrals:
Prohibited authority/actions:
```

Rules:

- Copy the blocking threshold from the issue exactly.
- If the issue says P0/P1 block, P2 is advisory unless it directly breaks an acceptance criterion, safety boundary, or intended-user usability requirement.
- If `Narrow` is authorized, treat it as accepted completion with explicit operating boundaries—not as a failed attempt at `Continue`.
- Do not launch a reviewer until this card exists.

## 2. Set an abstraction and size budget

Separate decisions into two columns:

| Architecture contract fixes | Implementation issue chooses |
| --- | --- |
| authority and source-of-truth precedence | internal record grammar |
| public outcomes and ordering | exact reason-code representation |
| safety/fail-closed invariants | serialization and byte encoding |
| interface and handoff boundary | stable-ID and Git-OID representation |
| required fixtures and externally visible behavior | process/lock identity and adapter mechanics |

Move a detail into the architecture column only when leaving it open would permit unsafe authority, non-deterministic public behavior, incompatible handoff, or direct acceptance-criteria failure.

Set a soft size/complexity budget before drafting. Crossing it is a stop signal: inspect whether implementation details have leaked upstream instead of simply raising the cap.

## 3. Author one clean candidate

Prefer a clean rewrite when serial patches have made the artifact internally coupled or materially larger.

Required author self-check before hash freeze:

- every named scenario has one expected public outcome;
- normative precedence and scenario matrix agree;
- terms used in outcomes are defined;
- historical fixtures and captured-live evidence are clearly separated;
- delegated implementation choices include behavioral conformance constraints;
- authority and prohibited-action boundaries are explicit;
- lifecycle, provenance, destination, and fresh-session use are present.

This author self-check is not an independent repair cycle. It occurs before the accepted review hash is frozen.

## 4. Use structural validators honestly

Heading, token, regex, and substring checks are useful for:

- required-section presence;
- byte/line budgets;
- expected public outcome names;
- acceptance-criterion identifiers;
- accidental secret shapes;
- prohibited old verdict wording.

The validator output must label itself `structural_smoke_only` (or equivalent) and state that semantic acceptance is false. If the validator makes a brittle exact-phrase assumption, repair the validator to test the intended structure; do not distort correct prose merely to satisfy a token check.

## 5. Freeze an exact-hash review packet

The independent reviewer receives:

- exact candidate path, SHA-256, bytes, and lines;
- governing issue path/ID and approved digest;
- source-evidence paths and hashes;
- the exact blocking-severity rule;
- accepted `Continue / Narrow / Stop` semantics;
- explicit implementation deferrals;
- required reviewer output shape;
- read-only/no-mutation boundary.

Required verdict shape:

```markdown
# Verdict: PASS_CONTINUE | PASS_NARROW | BLOCKED

## Exact identity
## Acceptance criteria
## Frozen blocker ledger
- P0:
- P1:
## Advisory findings
- P2:
## Decision and operating boundary
## Reviewer read-only confirmation
```

A reviewer elevating an advisory concern to P1 must identify the exact acceptance criterion or safety invariant it breaks.

## 6. Repair a frozen ledger, not an expanding critique

After the first broad review:

1. freeze the complete P0/P1 ledger;
2. repair that ledger holistically;
3. re-review closure on the new exact hash;
4. allow new blockers only for direct acceptance/safety regressions introduced by the repair;
5. keep new P2 observations advisory.

Default maximum: two repair/re-review cycles. At the cap, present:

- current exact artifact/hash;
- remaining frozen blockers;
- size/complexity change;
- recommendation to accept `Narrow`, split downstream work, or authorize one explicitly bounded exception.

Never launch an unrestricted third review automatically.

## 7. Promote the accepted hash unchanged

After `PASS_CONTINUE` or `PASS_NARROW`:

- copy/promote the exact reviewed bytes to the canonical destination;
- verify candidate and canonical SHA-256 match;
- read back the canonical artifact;
- verify index/map discoverability;
- link exact path/hash and review evidence from the tracker;
- preserve advisory findings in the downstream implementation handoff;
- do not edit wording after review merely to make closeout prose current.

If lifecycle state changes after review, record promotion and acceptance in the tracker, index/log, or an authority marker rather than invalidating the reviewed artifact for non-material wording churn.

## 8. De-authorize superseded material

When several candidates exist, add a workspace authority marker such as `STATUS.md` containing:

- accepted canonical path/hash;
- accepted review path/hash;
- validator authority limits;
- superseded filename patterns;
- downstream advisory carry-forward.

Historical drafts may remain as evidence, but they must be explicitly non-canonical. Legacy validators must not imply semantic acceptance.

## 9. Close out only after the inventory is complete

Create continuity logs, lessons, indexes, and authority markers before posting the main tracker closeout when practical. Inventory every material output with:

- exact path/ID/URL;
- hash/version when material;
- provenance;
- readback/verification;
- lifecycle;
- approval/publication status.

If a required output is created after the main closeout, add a small tracker supplement and verify it rather than pretending the earlier inventory contained it.

## Worked pattern from PAPI-76

A repeated patch/review loop expanded an architecture candidate from 655 to 1,916 lines because P2 findings were silently treated as blockers and internal implementation choices were pulled into the contract. Recovery used:

- the original P0/P1 threshold;
- `Narrow` as an accepted issue-defined outcome;
- one clean 277-line behavioral rewrite;
- one exact-hash independent review;
- an empty frozen P0/P1 ledger;
- same-hash canonical promotion;
- advisory implementation fixtures carried to the downstream issue;
- an authority marker de-authorizing prior candidates.

The reusable lesson is not the project-specific numbers. It is that acceptance-threshold fidelity plus an explicit architecture/implementation boundary restored convergence.