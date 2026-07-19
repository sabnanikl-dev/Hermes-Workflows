# JMD Cross-Page Copy Regression Gate

Use this when adding or substantially rewriting any public JMD page.

## Durable rule

A new page must comply with previously approved **site-wide copy corrections**, not merely the current issue's local facts. The main recurring example is issue #132 / merged PR #154:

- When JMD-authored customer-facing copy names **Danny and Lucky together** as the team behind the store, include **Cornell** or use a neutral team-safe equivalent.
- Keep Danny and Lucky scoped as owners and keep their combined 70-plus-years claim scoped to them.
- Cornell may be described with the approved framing: visual merchandising and unexpected outfit combinations. Do not call Cornell an owner or invent another role.
- Verbatim customer testimonials are not rewritten to satisfy this rule.

## Pre-PR audit

1. Read the task issue and its approval source.
2. Search merged history/nearby approval issues for site-wide corrections affecting names, roles, commerce language, rental wording, testimonials, or imagery.
3. Search the new diff for `Danny and Lucky`, `Lucky and Danny`, ampersand variants, `owners`, and `Cornell`.
4. Confirm each new JMD-authored pairing follows the durable rule.
5. Keep the task PR narrow: fix newly introduced violations in the changed page. Do not silently pull older unrelated regressions into the same PR; record them separately when needed.

## Review-loop handling

If Hermes finds a durable-copy violation that builder/reviewers missed, post a signed blocking PR comment with the source issue/merged PR and exact file:line. The Claude fix lane should then read that live PR surface, make the narrow correction, push, and trigger current-head A/B re-review.
