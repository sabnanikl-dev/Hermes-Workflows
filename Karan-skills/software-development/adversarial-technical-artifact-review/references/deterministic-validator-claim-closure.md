# Deterministic validator claim closure

Use this when a PR adds a validator, policy gate, static-site checker, or self-test and claims it is deterministic, fail-closed, structure-aware, or complete across a broad input class.

## Review the claim, not only the current artifact

A current page/config can be correct while its regression gate is materially unsound. Separate two verdicts:

1. **Current artifact correctness** — the committed page/config presently satisfies the issue.
2. **Enforcement-contract correctness** — the new checker actually rejects the future unsafe states claimed by tests, docs, and PR prose.

A green positive suite proves only the first unless mutation controls prove the second.

## Scope the guarantee to the parser and grammar actually implemented

Do not advertise an unbounded semantic guarantee when the checker uses bounded regex/string logic.

### HTML active-document claims

If docs say comments or inert containers “can never” satisfy structural assertions, either use a structure-aware parser or explicitly reject unsupported/malformed structures before evaluation. A sequence of non-balancing regex replacements is insufficient.

Required negative probes for `noindex`, heading count, and required-link checks:

- nested `<template>` elements;
- `<textarea>` raw-text content;
- balanced and unclosed HTML comments;
- balanced and unclosed `<script>`, `<style>`, `<template>`, and `<noscript>`;
- a real active positive control after each rejection fixture.

A matcher ending at the first closing tag can expose nodes still inside an outer inert container. A matcher requiring a closing tag leaves unclosed raw-text content visible even though the browser treats the remainder as inert.

### Hosting/routing configuration claims

Avoid claiming to classify every provider-supported catch-all regex unless the implementation uses the provider parser or a deliberately bounded grammar. Alternation, anchors, optional literal prefixes, and grouped scoped routes quickly defeat first-character heuristics.

Prefer the narrowest executable policy:

- If custom routing is unnecessary, reject `rewrites`, `redirects`, and legacy `routes` entirely.
- If one custom-404 shape is required, allowlist that exact shape and require `status === 404` plus the expected destination.
- If broader support is required, document the supported grammar rather than claiming arbitrary PCRE coverage.

Mutation examples should include `/api/(.*)|/(.*)`, `^/api/.*|/.*$`, `/a*(.*)`, `/(api|docs)/(.*)`, and catch-all statuses `404`, `410`, and `500`. Only the exact contractually intended 404 form should pass.

### Forbidden-language claims

A blacklist can enforce an enumerated policy, not an undefined “full vocabulary.” When an issue explicitly prohibits e-commerce language:

- include literal forms such as `e-commerce` and `ecommerce`;
- enumerate claimed word families and morphology (`purchase/purchasing/purchased`, `buy/buying`, `sale/sales`, `coupon/coupons`, etc.);
- pin legitimate brand-safe boundary controls;
- derive self-test counts from machine output;
- synchronize AGENTS/docs/PR claims with the exact executable list.

If broad linguistic interpretation is not required, narrow prose to “rejects these enumerated terms and patterns.”

## Closure workflow

1. Freeze the exact head/hash and read issue, implementation, tests, docs, and PR claims together.
2. Build a class-wide mutation matrix before spending a fix cycle; do not fix only examples named by the first reviewer.
3. Run mutations in disposable copies or `/tmp`, with a real positive control and restoration checks.
4. Deduplicate findings by root cause: parser scope, language policy, routing grammar, status semantics, or stale claims.
5. Let the builder either harden the implementation or narrow the contract—both are valid when they satisfy the actual issue.
6. After a push, verify the remote exact head, rerun the full gate, then run an exploratory correctness reviewer first. Launch additional review lanes only after that convergence gate passes or when their specialty is needed for adjudication.
7. Treat GitHub readback as the success criterion for relayed reviews/comments. A wrapper can exit nonzero after external posts succeeded; re-query before retrying to avoid duplicates.

## Anti-whack-a-mole rule

When a reviewer finds another example in the same semantic class, stop adding one regex at a time. Reassess the enforcement strategy and the breadth of the claim. The durable fix is often a parser, an exact allowlist/deny policy, or narrower honest documentation—not a longer heuristic.
