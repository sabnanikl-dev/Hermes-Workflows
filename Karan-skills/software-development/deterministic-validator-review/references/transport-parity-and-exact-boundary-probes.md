# Transport parity and exact-boundary mutation probes

## Why this exists

A staged reviewer pipeline can validate the local artifact perfectly and still trust a weaker predicate after publication. Likewise, prompt/docs may advertise an exact field limit while a compact regex accepts one extra character. Both failures survive broad green suites because honest fixtures preserve the intended shape.

## Four-stage record matrix

For each finding or verdict record, compare these stages semantically:

| Stage | Required proof |
|---|---|
| Lane output | Exact grammar parses; status/count derive from parsed records. |
| Prepared artifact | Same IDs, severities, messages, head, role, status, and count one-to-one. |
| Published body | Remote author/signature/commit/head plus the same complete record set. |
| Direct readback | Re-read remote bytes; do not accept a declaration-only surrogate. |

Mutation matrix for prepared **and** published bodies:

- zero findings while `BLOCKING=1`;
- one finding removed;
- extra finding added;
- duplicate ID;
- ID renamed;
- severity changed;
- message changed;
- malformed separator/prefix;
- status/count preserved while records change;
- truncation immediately after declarations;
- reordering if order is contractual, or explicit order-insensitive comparison if not.

The remote readback predicate must receive or reconstruct the expected finding records. If its API only accepts `status` and `blocking`, that narrow signature is itself a review clue.

## Exact-length probes

For a field documented as 1–`N` characters:

- empty: reject;
- 1: accept;
- `N-1`: accept;
- `N`: accept;
- `N+1`: reject;
- much larger: reject.

Common off-by-one:

```regex
\S.{0,N}
```

This accepts one required non-space character plus up to `N` more: `N+1` total. The usual bounded form is equivalent to one required character plus at most `N-1` additional characters, while still enforcing the intended whitespace/newline policy.

Run the probes through the public parser, then through artifact serialization, redaction/canonicalization, relay validation, and readback. “Accepted then clipped” is not preservation: it silently changes the record that reviewers and operators reconcile.

## Review conclusion language

Use precise status:

- “Prepared artifact parity is fixed; published readback remains declaration-only.”
- “The prompt documents 300 characters; the parser accepts 301.”
- “Current honest artifacts pass, but relay-side mutation still false-passes.”

These are contract/evidence blockers when the issue promises one-to-one prompt/parser/artifact/readback parity; otherwise classify them against the narrower documented policy rather than inventing a stronger one.
