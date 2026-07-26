# JSON Schema Regex Portability in Build/Review Loops

Use this reference when a PR changes a JSON Schema `pattern`, especially when the repo has a custom validator implemented in Python, Ruby, Java, or another non-JavaScript engine.

## Core risk

JSON Schema patterns are expected to use the JavaScript/ECMA-262 regular-expression dialect for interoperability. A custom validator may silently accept engine-specific syntax that a conforming consumer rejects or interprets differently.

Example failure class:

- Python `re` treats `\Z` as an absolute-end anchor.
- ECMAScript without Unicode may treat `\Z` as a literal `Z` identity escape.
- ECMAScript with Unicode rejects it as an invalid escape.
- Local tests can therefore pass while external JSON Schema consumers reject valid values or accept the wrong value.

Do not treat “the repository's custom evaluator passes” as sufficient evidence for a published JSON Schema.

## Review checklist

1. Read the schema's declared draft and identify the expected regex dialect.
2. Inspect every added/changed `pattern` for engine-specific tokens, flags, groups, or anchors.
3. Test the same pattern and case matrix in:
   - the repository's real validation path; and
   - an ECMAScript engine such as Node (`new RegExp(pattern)` and, when appropriate, `new RegExp(pattern, "u")`).
4. Include positive and negative cases that expose anchoring differences:
   - valid token;
   - empty/bare prefix;
   - embedded whitespace;
   - trailing newline;
   - a literalized-escape canary (for a former `\Z` bug, a value ending in `Z`).
5. Add a deterministic regression test that reads the pattern from the schema rather than duplicating it in test code.
6. Keep docs synchronized with the exact schema pattern and explain any non-obvious absolute-end construction.
7. After a fix commit, verify the PR body still reports the final pattern, fixture count, commands, and head-specific evidence; correct metadata without changing the reviewed head, then rerun the reviewer lane affected by metadata/docs.

## Portable absolute-end pattern

When `$` is too permissive because it can match before a final newline, a cross-engine absolute-end construction that works in Python `re.search` and ECMAScript is:

```regex
^x_[a-z][a-z0-9_]*(?![\s\S])
```

`(?![\s\S])` succeeds only when no character remains, including a newline. Treat this as an example to verify, not a universal template: adapt the token body to the schema's contract and rerun both engines.

## Reviewer-loop handling

- Post interoperability findings as signed, exact-head PR-bus blockers with a small cross-engine reproduction.
- Keep the Claude fix prompt pointer-first; the live PR remains authoritative.
- A fix that replaces one local-engine bug with another portability bug consumes a review/fix cycle.
- Require final A/B reviews on the corrected head. Old-head approvals do not close the loop.
- If the only remaining issue is stale PR metadata and the code-cycle cap is reached, make the narrow metadata correction on the unchanged head and rerun only the metadata/docs reviewer lane.