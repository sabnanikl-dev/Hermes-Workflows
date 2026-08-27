# Negative-Claim Provenance and Review-Byte Preservation

Use this matrix when a final report makes source-specific absence claims and when validation commands may regenerate tracked artifacts.

## 1. Source-specific negative claims

A negative claim needs evidence of the searched corpus, not only cautious wording.

| Report clause | Minimum reconstructable evidence | Invalid substitute |
|---|---|---|
| “The captured changelog documents no definition change” | Immutable changelog capture or query result, source locator, capture time/window, and hash | A current metric-definition page |
| “No incident was found” | Captured incident/status-history corpus and searched date window | Current healthy status |
| “No deployment change occurred” | Dated deployment ledger or immutable provider history | Current deployment identity |
| “No competitor recurred” | Complete frozen panel with stable row IDs and observation scope | A few current search screenshots |

Qualifiers such as “not ruled out” or “absence is not proof” do not cure invented provenance. If the corpus is missing, state only what available evidence directly supports. Example:

> Differentiated Search, Maps, and action series argue against a whole-pipeline loss. No captured evidence establishes a Search-specific reporting change, but such a change remains untested.

Fresh-session proof is bidirectional:

1. every cited artifact exists and hashes to its claimed identity;
2. every source-specific factual clause traces to a cited artifact of the right source type.

## 2. Distinguish binders from producers before execution

Before running a checker in a canonical review checkout:

1. independently hash the candidate;
2. inspect the command or its documented behavior;
3. classify it as:
   - **binder:** reads and verifies existing bytes without writing;
   - **producer:** rewrites reports, timestamps, sidecars, screenshots, manifests, or status readbacks;
4. run producers in a disposable copy or designated evidence worktree unless regeneration is explicitly in scope;
5. after every potentially mutating command, re-hash the candidate and inspect worktree changes.

An exit `0` is not proof of review integrity if the command changed the artifact under review.

## 3. Recover from incidental review churn without erasing user work

If a command unexpectedly rewrites tracked artifacts:

1. compare post-command status against the pre-command inventory;
2. identify only paths changed by the review command;
3. restore incidental sidecars/evidence paths only—never reset the whole worktree;
4. reconstruct any pre-existing candidate delta from the exact originally reviewed bytes or a captured patch;
5. independently re-hash the candidate and require the original digest;
6. verify accepted baseline sections changed only where the final synthesis intentionally differs.

For append-only final syntheses over an accepted baseline, compare the accepted artifact with the candidate across the entire old line range. Require only explicitly allowed edits (for example a status-line transition) and prove the new synthesis begins after the preserved baseline.

## 4. Verdict rule

Classify as a blocker when:

- a source-specific negative claim lacks a captured source of the claimed type;
- fresh-session reconstruction cannot locate the searched corpus;
- review-time mutation changed candidate bytes and the original digest was not restored;
- an accepted baseline was silently regenerated rather than preserved.

Report the unsupported clause exactly, explain why nearby evidence is not equivalent, and give a bounded replacement sentence or required artifact.