# Narrowing a Live Mission Hierarchy

Use this when a large tracker-root contract is intentionally replaced by a smaller contract while completed evidence and superseded work must remain reconstructable.

## Desired result

- Each replacement acceptance criterion maps to one active child.
- Historical evidence remains visible and non-executable.
- Removed apparatus is canceled/superseded, never deleted.
- Dependencies form a coherent DAG without circular gates.
- Linear coordinates acceptance/evidence without duplicating the one GitHub implementation issue/PR.
- A fresh session can prove what changed from live state and a pre-edit snapshot.

## 1. Ground the complete hierarchy

Read before mutation:

- parent title, full description, state, project, labels, priority, comments;
- every direct child with full description, state, parent, comments, and metadata;
- outgoing and inverse relations for parent and children;
- `pageInfo.hasNextPage` for children, comments, relations, and inverse relations;
- linked source systems: exact GitHub issue, PR, repository head, external execution tracker, or durable artifact.

Fail closed if any readiness-bearing collection is truncated. Do not infer dependency direction from prose when live relations exist.

## 2. Create a disposition matrix

Classify every existing child into one bucket:

1. **Active replacement child** — rewrite it to map one-to-one to a new parent acceptance criterion.
2. **Completed historical evidence** — keep it completed; prepend a prominent historical/non-executable marker while preserving its original body and comments.
3. **Superseded apparatus** — move it to Canceled; prepend `SUPERSEDED — DO NOT EXECUTE`, explain the replacement, and preserve the original body verbatim below the marker.
4. **External execution tracker** — keep it authoritative for its own workstream and link it rather than mirroring its status into the narrowed hierarchy.

Do not delete old issues or replace completed evidence with a summary-only body. Current issue state should make the disposition obvious without relying on activity history.

## 3. Preserve a pre-edit snapshot

Before the first mutation, save a JSON snapshot containing the parent, every child, relevant external tracker, comments, relations, inverse relations, state, labels, and descriptions.

Recommended properties:

- canonical project evidence path rather than `/tmp`;
- restrictive permissions such as `0600` for internal bodies;
- deterministic JSON plus SHA-256 readback;
- exact timestamp/revision in the filename;
- path recorded in the parent audit comment.

The snapshot is rollback/audit evidence, not a second active tracker.

## 4. Rewrite the parent contract

Include:

- why the old contract was narrowed;
- exact historical evidence retained;
- current verified source-system state;
- new goal and load-bearing invariants;
- explicit removed-apparatus list;
- one-to-one child map;
- intended dependency graph;
- parent acceptance criteria keyed to child identifiers;
- escalation rules;
- authority statement separating tracker grooming from execution.

If a supplied contract and graph are normative, embed the graph or a durable exact pointer in the parent so reconstruction does not depend on a chat attachment/cache path.

When wording appears contradictory, preserve the stronger invariant and state the operational interpretation. Example: “broker-only push” may mean the launcher is the sole credential broker while the builder still performs the direct branch-scoped push; do not silently switch to a parent commit relay when the governing invariant requires direct writes.

## 5. Preserve tracker boundaries

For repository implementation:

- use one exact GitHub implementation issue and one focused PR when required;
- treat Linear children as acceptance/evidence slices, not separate coding tickets;
- require the GitHub issue to be narrowed before coding if it still contains superseded scope;
- leave external workstream trackers authoritative for their execution evidence and link them from the acceptance child.

## 6. Rebuild dependencies as a DAG

Delete obsolete relations by live relation ID, then create only the desired graph.

A common narrowed shape:

```text
implementation slice A ─┐
implementation slice B ─┼─> deterministic proof -> qualification/install -> pilot
router/docs slice       ─┘
```

Check for circular gates. A frequent trap is `parent blocks pilot` while parent acceptance requires the pilot to complete. Replace that with `immediate prerequisite blocks pilot`—for example, qualification/install blocks the pilot. Remove broad blocks on unrelated work when the narrower mission no longer owns that gate.

Verify both ends of every `blocks` relation. In Linear relation creation, `issueId` is the blocker and `relatedIssueId` is the blocked issue.

## 7. State conventions

Unless the governing workflow says otherwise:

- parent mission: `In Progress` while the narrowed mission is active;
- active replacement children: `Backlog` until exact execution prerequisites are ready;
- completed historical evidence: remain `Done`;
- superseded apparatus: `Canceled`;
- external tracker: do not mutate its state merely to make the graph tidy.

A tracker rewrite is not authority to code, merge, install, deploy, or run a pilot.

## 8. Add an audit comment

Record on the parent:

- active child set;
- completed historical set;
- canceled/superseded set;
- old relations removed and new graph created;
- unrelated work unblocked;
- circular gate repaired;
- pre-edit snapshot path;
- explicit statement that no source-system mutation occurred outside authorized tracker grooming.

Capture the returned comment ID and verify it directly with `comment(id:)`.

## 9. Mandatory readback

Re-read and assert:

- parent title, state, required body markers, acceptance section, and normative graph/pointer;
- exact child count and every child's identifier, title, state, and parent;
- active bodies contain goal, scope, acceptance, verification, authority, and dependencies;
- historical/superseded bodies start with the correct non-executable marker and still contain the original body;
- outgoing and inverse relation collections are complete and match the intended DAG;
- removed broad/circular relations are absent;
- external tracker has the intended inverse relation without unauthorized state change;
- audit comment resolves directly by ID with its evidence markers;
- snapshot exists, parses, has restrictive mode, and matches the reported SHA-256;
- linked GitHub issue/PR state remains unchanged when only tracker grooming was authorized.

Report the live parent URL, active/superseded sets, graph, snapshot path/hash, verification, and the next prerequisite intentionally left untouched.
