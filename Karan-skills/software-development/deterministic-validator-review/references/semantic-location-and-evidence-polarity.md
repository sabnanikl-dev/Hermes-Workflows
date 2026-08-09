# Semantic location and evidence polarity

Use this reference when a deterministic HTML/XML/document checker treats the presence of markup as evidence of success or failure.

## The polarity rule

Before reusing a parser helper, classify what finding a node means:

- **Fail-closed negative evidence:** finding a forbidden declaration makes the artifact fail. Searching broadly can be conservative. Example: a page-owned `noindex` found anywhere in parsed markup should normally prevent an indexability pass.
- **Positive evidence:** finding a required declaration makes the artifact pass. Search only the semantic location where the declaration is active. Broad traversal can turn inert or misplaced markup into a false pass. Example: a canonical link in `<body>` or `<template>` does not prove an active canonical in the document head.

Never assume two checks can share a tree walk merely because they inspect similar tags or attributes. Opposite evidence polarity often requires opposite scope.

## Correct order of operations

For positive evidence, apply these operations in this order:

1. Parse with the real semantic parser used by the product or checker.
2. Select the active semantic container first (for example, the parser-built document `<head>`).
3. Exclude inert or misplaced containers before counting (`<template>`, body-only markup, or other repository-forbidden nesting).
4. Match the exact declaration grammar (`rel` token list, not substring matching).
5. Count and compare the remaining active declarations.
6. Resolve nothing unless the contract explicitly permits resolution; relative URLs must not become valid merely because a base URL exists.

Filtering location after cardinality is unsafe: inert copies can either manufacture a missing declaration or forge a duplicate.

## Minimum external mutation matrix

Run through the public evaluator, not only the parser helper:

| Probe | Expected |
| --- | --- |
| one valid declaration in the active location | pass |
| required declaration only in body/misplaced location | fail as missing |
| required declaration only inside inert template content | fail as missing |
| one active declaration plus identical inert copies | pass; inert copies do not forge duplicates |
| two active declarations | fail as duplicate |
| one active declaration with wrong value/origin/path | fail exact-value check |

Include both parser-level and end-to-end evaluator assertions. Reverting only the semantic-location repair should make the former-red cases fail while leaving valid controls green.

## Finite policy is acceptable

A repository checker does not need to solve all browser/parser semantics. It may require a declaration to be a direct child of the parser-built active container when every governed artifact already follows that form. State this as a deliberate finite repository policy in code comments, diagnostics, tests, specs, and PR prose. Do not claim universal HTML semantics.

## Review wording

Report the layers separately:

- “Committed artifacts are correct.”
- “The positive-evidence guard false-passes on inert/misplaced declarations.”
- “The repair narrows where evidence counts; it does not change product markup.”
