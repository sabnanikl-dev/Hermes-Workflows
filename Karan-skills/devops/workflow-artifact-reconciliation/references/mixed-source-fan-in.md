# Mixed-source fan-in pattern

## Failure shape

A source root emits direct records and nested containers. The partition's two branches independently target a run-once normalization/planning node. The first arriving branch triggers reconciliation against an incomplete source universe. A mass-mutation guard may correctly abort, but the workflow cannot converge.

## Deterministic repair

```text
partition folders -> nested listing -> Merge input 1
partition direct -------------------> Merge input 0
Merge (append; exactly two inputs) -> normalization
```

Required graph assertions:

- exactly one Merge node at the exercised node version;
- append mode with exactly two inputs;
- direct branch targets input 0;
- nested-list output targets input 1;
- Merge output targets normalization;
- no residual direct or nested edge bypasses Merge;
- Merge is normalization's only upstream edge.

## Behavioral matrix

Use credential-free fixtures and execute the committed normalization code when practical:

| Case | Expected result |
|---|---|
| Direct only | All direct records normalize once; no collection provenance. |
| Nested only | All nested records normalize once; collection provenance retained. |
| Mixed | One pass receives the complete direct+nested union exactly once. |
| Reversed append order | Deterministic normalized/planning order is unchanged. |

Include a former-red mutation that removes Merge and reconnects both branches directly to normalization. The validator must reject it in a named category.

## Source-of-truth conflict

If the build template is older than the reviewed repository export:

- compare the targeted connection seam first;
- apply only the proven graph transform to both copies;
- do not regenerate the reviewed artifact from stale node code;
- run each lane's native tests;
- sanitize the repository copy and prove a sanitizer fixed point;
- document broader node-code drift separately.

## Downstream boundary

After the automation updates its CMS destination, inspect the actual website consumer. A dynamic endpoint may expose the change immediately. Rebuild or deploy a generated feed only when that feed is authoritative and the user has approved the live action.
