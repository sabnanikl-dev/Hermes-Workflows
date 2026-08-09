# Open grammar and metadata-scope validator probes

Use this reference when a deterministic checker interprets an open token namespace, directive list, or HTML metadata scope.

## Contract inventory before a repair

Before freezing the builder's allowed paths, search every repository contract surface for the affected rule and regression inventory. Include authoritative specs (especially `docs/spec.md`), operational docs, `AGENTS.md`, test names/counts, checker diagnostics, and the live PR body. A narrow file allowlist is safe only when it includes every source of truth that must change.

## Grammar-boundary probes

Derive token syntax from the governing grammar rather than an ad hoc `[a-z0-9._-]` approximation. Test legal punctuation and separators, including at least one token that is valid under the real grammar but outside the implementation's first regex.

For scoped header/directive syntax, prove both:

- the scope is recognized rather than silently becoming an unscoped/site-wide directive;
- the same scope is handled consistently in parser helpers and the shipped stage evaluator.

A preview safeguard is especially sensitive: misparsing a crawler-scoped directive as site-wide can produce a false proof of deployment-wide protection.

## Unknown sibling directives must not mask blockers

If a directive list contains a recognized blocker such as `noindex` or `none`, an unfamiliar sibling directive must not cause the whole list to be discarded. Test:

- blocker alone;
- blocker plus a known sibling;
- blocker plus an unknown sibling before and after it;
- mixed separators and case;
- the shipped evaluator in every stage.

Unknown directives may be ignored or rejected according to policy, but they must not erase a recognized blocking directive.

## Open scope versus ordinary metadata

An arbitrary HTML `<meta name>` can be either a crawler user-agent name or unrelated document metadata. Syntax alone may not distinguish them. Test both directions:

- unfamiliar crawler name with `noindex`/`none` must fail when the contract promises open crawler coverage;
- ordinary namespaced metadata (for example Dublin Core-style names) with values such as `none` must not become robots directives when the contract promises valid-metadata acceptance;
- document-metadata prose containing the word `noindex` must remain a valid control.

If passing both directions requires an ever-growing heuristic or allowlist, stop the repair loop. Require an explicit policy choice: a finite supported crawler set, or a fail-closed approved document-metadata policy. Do not call heuristic expansion a standards-backed class-level repair.

## Post-exception stop rule

After an authorized exception repair:

1. rebind repository and deployment proof to the new exact head;
2. run the external class-wide probe batch before Reviewer A;
3. run Reviewer A, Reviewer B, and Integration Auditor with no builder budget restored;
4. if the triad discovers a new blocker class, report the PR blocked and stop rather than stretching one exception into another mutation cycle.

Separate functional false passes, false positives, stale spec/docs, and architectural proportionality in closeout. Preserve any post-merge production or cutover gate even when preview proof passes.
