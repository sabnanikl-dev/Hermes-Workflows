# Deterministic Validator False-Pass Probes

Use this reference when proving a PR that adds or changes a read-only checker, validator, health report, evidence verifier, or similar CLI. The highest-risk bugs are often **empty-success paths**: invalid input causes the tool to inspect nothing, emit a clean-looking report, and exit 0.

## Boundary matrix

Before approving, exercise the CLI contract at each boundary:

| Boundary | Required probe | Fail-closed expectation |
|---|---|---|
| Missing root | nonexistent path | usage error, normally exit 2 |
| Wrong root type | regular file passed as root | usage error, not an empty report |
| Unreadable root | existing directory that cannot be enumerated | usage error; do not rely on `exists()`/`is_dir()` alone |
| Unknown filter | nonexistent client/module/namespace | usage error when the CLI documents the filter as validated |
| Valid empty scope | readable directory with intentionally no records | only exit 0 if the contract explicitly permits an empty report |
| Missing repo-relative source | declared path absent inside repo | strict failure |
| Unavailable external source | owner-machine path absent in CI | advisory/unresolvable, never `verified_match` |
| Available external source | external absolute path exists locally | label as environment-local, not portable/CI proof |

For unreadable directories, **force enumeration** (`next(iter(root.iterdir()), None)` or an equivalent `os.scandir` probe) and catch `OSError`. Calling `root.iterdir()` without advancing it is insufficient because the iterator is lazy. Regression tests should restore permissions in `finally` and skip only when the runtime genuinely bypasses permission bits (for example root).

## Logical-line and span hashing probes

When a checker hashes line ranges, test the normalization contract directly:

- LF, CRLF, and CR forms of the same text must hash identically when normalization says they are equivalent.
- A terminal newline is a terminator, not a synthetic one-past-end logical line, unless the published contract explicitly says otherwise.
- Preserve genuine empty lines: interior empty lines and an actual trailing empty line must remain addressable.
- Test the real last line, one-past-end, malformed/descending ranges, insertion before the cited range, and edits inside the cited range.
- Use the same canonical hash helper for authoring anchors and verifying them.

A strong regression set includes:

```text
"one\ntwo\n"      -> logical lines ["one", "two"]; line 3 invalid
"one\r\ntwo\r\n" -> same result
"one\ntwo\n\n"    -> logical lines ["one", "two", ""]; line 3 valid, line 4 invalid
```

## Report-shape checks

If the tool reports both source existence and citation health, keep them as separate streams/summaries. Verify that:

- every path-bearing source is reported even if no citation references it;
- citation counts are not inflated by source-existence rows;
- strict failures are explicit and advisory categories never silently become passes;
- human and JSON output use the same category and scope semantics;
- unknown filters and invalid roots cannot produce an empty green report.

## PR-prover procedure

1. Reproduce any suspected false pass independently before accepting it as a blocker.
2. Put the finding on the PR bus with exact command, exit code, and affected contract.
3. Send Claude Code a pointer-first fix prompt; do not patch directly.
4. After the push, verify local HEAD, PR `headRefOid`, commit list, CI, and signed fix comment.
5. Re-run the entire boundary matrix—not only the cited failing case—then run fresh current-head Reviewer A/B lanes.
6. Treat small prose mismatches as non-blocking only when behavior, machine output, acceptance criteria, and safety semantics remain unambiguous; record them as follow-up rather than opening another code cycle.