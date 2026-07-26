# Adversarial claim matrix

Use this as a starting bank. Select only classes relevant to the checker, then add domain-specific mutations derived from its strongest claims.

## HTML and inert-content scanners

False-pass probes:

- Closing-tag text inside an HTML comment nested in an inert container.
- Closing-tag text inside a quoted child attribute.
- Ordinary nested inert containers.
- Raw-text/RCDATA content containing tag-shaped text.
- Unclosed comment/container that should swallow to EOF.
- Required metadata, heading, or link present only inside inert content.

Valid controls:

- Active markup immediately after a genuinely closed inert container.
- Approved nested inert structures.
- Required markup active exactly once.

A scanner that balances opens/closes with independent regular expressions is not token-aware if it cannot distinguish real tags from comment or attribute text.

## Forbidden vocabulary and morphology

Probe the same semantic class across:

- singular/plural;
- base/gerund/participle/past tense;
- hyphenated/unhyphenated/space-separated forms;
- direct text and href values;
- punctuation and case boundaries.

Pair every broad stem with safe controls sharing substrings. Examples:

- `shop` vs `showroom` and an approved proper name containing `Shopping Center`;
- `sale` vs `wholesale`;
- `sell` vs `bestseller`.

Do not claim “full morphology” when patterns enumerate only selected forms.

## Regex and route-policy checkers

False-pass probes:

- catch-all in one top-level alternative;
- optional literal before a wildcard;
- negative lookaround followed by wildcard;
- missing or non-exact status on a catch-all route;
- anchored and unanchored equivalents.

False-positive probes:

- fixed literal prefix;
- every branch of a grouped alternation scoped;
- restrictive character class;
- restrictive positive lookahead;
- optional scoped group followed by a mandatory separator/literal;
- exact allowed status wiring.

If full regex semantics are unnecessary, define a repository policy that rejects unsupported/exotic patterns for manual review. Then test and describe it as a **policy gate**, not a semantic parser with “no false positives.”

## Structured validators

Probe:

- missing and empty fields;
- wrong scalar/container types;
- duplicated keys or records;
- unknown keys/filter values;
- reordered records;
- malformed-but-parseable values;
- one-past-end spans and terminal-newline boundaries;
- source-vs-citation/report separation;
- portable paths vs environment-local paths.

## External mutation harness pattern

1. Copy only the checker, its required libraries, fixture/product tree, and config into a fresh `/tmp` directory.
2. Apply one mutation per case from a small script.
3. Invoke the public checker command and capture exit code/stdout/stderr.
4. Delete the temporary copy.
5. Print a machine-readable summary.
6. Confirm the review worktree stayed clean and at the expected SHA.

Keep the harness outside the PR unless the fixtures represent durable repository requirements. External probes are valuable because they do not share the builder’s fixture assumptions.

## Claim-surface sweep after a fix

Search and reconcile:

- checker header comments;
- success/failure diagnostics;
- self-test labels and counts;
- package scripts;
- AGENTS guidance;
- specifications and decision/friction logs;
- PR body and fix comments;
- review artifacts referring to old guarantees.

A corrected implementation with stale universal prose is still misleading and may remain review-blocking.

## Exceptional-cycle checkpoint

Before launching a cycle beyond the normal cap, record:

- exact starting PR head;
- approved blocker classes;
- allowed file/surface scope;
- maximum extra cycles;
- required external mutations and controls;
- product artifacts that must remain unchanged;
- final exact-head reviewer lanes;
- continuation details if the current parent session may hit its tool/context limit.
