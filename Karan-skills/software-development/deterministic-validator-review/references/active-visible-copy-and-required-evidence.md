# Active visible copy and required-evidence probes

Use this when an HTML validator has separate seams for metadata, visible text, required disclosures, de-duplication signatures, or prohibited phrases.

## Failure pattern

A checker can correctly use parser semantics for metadata while still flattening visible text with regex tag stripping. If that path does not remove inert `<template>` content, the same bug has opposite effects:

- **false pass for positive evidence:** a required disclosure exists only inside `<template>` and is counted as present;
- **false positive for negative evidence:** a prohibited phrase or em dash exists only inside `<template>` and is reported as reader-visible.

Success diagnostics such as “inert template content is ignored” are therefore whole-validator claims. Proving one extraction seam is active-only does not prove the others are.

## Minimum external matrix

Run these through the public evaluator, not only a helper:

| Case | Expected |
|---|---|
| Required phrase in active rendered text | pass |
| Required phrase only inside `<template>` | fail as missing |
| Required phrase active plus inert duplicate | pass; active instance governs |
| Prohibited phrase in active text | fail in its named category |
| Prohibited phrase only inside `<template>` | pass |
| Prohibited phrase in comment, script, style, or head | follow the documented finite scope |
| Nested templates containing positive or negative evidence | remain inert |

Pair the public-evaluator probes with a direct extractor observation so the root cause is visible. Keep the external probe unchanged for post-fix verification.

## Browser-semantic boundary matrix

Do not stop at a single closed lowercase `<template>` fixture. Exercise the parser boundary directly:

| Boundary | Required result |
|---|---|
| Nested templates | all nested content remains inert |
| Unclosed template | every later source byte is inert, matching browser parsing |
| Uppercase tag / attributes containing `>` | template extent still comes from the parser, not tag regex |
| Properly closed template followed by active text | later active text remains visible |
| `<template` literal in comment, script text, or attribute | must not hide unrelated active content |
| Stray `</template>` without an opener | must not create an inert region |

When the checker needs to preserve an established finite normalization pipeline rather than replace it with a new text-node collector, a bounded parser-derived blanking seam is acceptable:

1. parse with source locations enabled;
2. locate actual template elements through the parse tree, traversing `template.content` **only to locate nested inert elements**, never to collect active text;
3. blank each element's exact source span with same-length, newline-preserving spaces;
4. when an element has no explicit end tag, blank from its start through end-of-input;
5. only then run the existing comment/head/script/style/tag/entity normalization.

Same-length blanking keeps source offsets stable even when nested spans overlap. A cheap case-insensitive `<template` literal check may skip parsing on ordinary pages, but it is only a performance gate: parser nodes—not the literal—must decide what is inert.

## Repair guidance

Prefer one active-document traversal shared by every reader-visible rule:

1. parse HTML with the repository's locked parser;
2. traverse active nodes only;
3. stop at `<template>` and other explicitly inert/excluded containers;
4. collect active text nodes;
5. normalize entities/whitespace once;
6. run required and prohibited rules over that same normalized active text.

If a finite checker deliberately uses regex, blank complete template blocks before stripping tags and document the accepted grammar. Parser traversal is safer when malformed-but-browser-valid HTML is in scope.

## Closeout

- Add both template-only required-evidence and inert-prohibited-copy regressions.
- Include at least one unclosed-template false-pass case and one nested-template valid control when the checker claims browser-semantic inertness.
- Prove the new cases are load-bearing: run an isolated `/tmp` copy with only the inert-template fix neutered and require the new cases to fail while pre-existing cases retain their prior outcomes. A higher self-test count alone is not sensitivity proof.
- Re-run the unchanged external mutation matrix after the fix.
- Reconcile comments, success output, self-test counts, AGENTS/spec text, and PR claims.
- For a checker/docs-only repair, prove governed product bytes are unchanged; do not regenerate browser evidence merely because the Git head moved.
- Keep product correctness separate from guard soundness: the committed page can be correct while the regression guard remains blocking.
