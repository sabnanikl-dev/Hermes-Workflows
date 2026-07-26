# Versioned Line-Span Hash and Evidence-Health Review Pitfalls

Use this when a PR adds deterministic citation hashing, source-health reporting, or a strict evidence checker over line ranges.

## Line normalization must not invent a citable line

For a contract such as `sha256:utf8-lf-v1`:

1. Decode UTF-8.
2. Normalize CRLF and CR to LF.
3. Split into logical lines.
4. If the normalized text ends with LF, drop only the synthetic terminal split element.
5. Preserve genuine internal empty lines.
6. Select 1-based inclusive ranges, join selected lines with `\n`, append no synthetic trailing newline, then hash.

Regression cases must include:

- `one\ntwo\n` makes line 3 invalid, not an empty verified span;
- `one\n\ntwo\n` preserves line 2 as a real empty line;
- LF, CRLF, and CR forms are equivalent;
- an explicit decision/test for empty-file behavior;
- insertion before a range and edits inside a range both cause drift;
- out-of-bounds and malformed ranges fail under strict mode.

A common false pass is `normalized.split("\n")` without removing the terminal synthetic element: an anchor over the nonexistent one-past-end line can then return `verified_match`.

## Separate source health from citation health

If the issue requires “for each source with a path, report exists/missing,” walking citations alone is insufficient. Emit two deterministic streams:

- **Source level:** every path-bearing registry source, including uncited sources; classify present, missing repo-relative, or unavailable external.
- **Citation level:** every evidence reference; classify match, drift, missing source, missing anchor, invalid range, unsupported version, or environment-unresolvable.

Keep summaries and strict-failure sets separate so source rows do not inflate citation counts. Missing repo-relative sources may gate strict mode; unavailable external paths should remain advisory when CI cannot resolve owner-local paths.

## Verification scope must be explicit

An available external absolute path can be genuinely verified on the current machine, but that is not portable evidence. Report scope explicitly:

- `portable` for repo-relative sources;
- `environment_local` for available external paths;
- advisory/unresolvable for unavailable external paths.

Synchronize code, human output, JSON, docs, and PR metadata. Avoid saying “only repo-relative sources can be verified” if the implementation hashes an available external path; say only repo-relative verification is portable.

## CLI false-pass guards

A strict checker must reject invalid invocation surfaces before producing an empty success report:

- unknown `--client` -> usage error / exit 2 when that is the documented contract;
- missing `--root` -> exit 2;
- existing regular file passed as `--root` -> exit 2, not an empty exit-0 report;
- valid directory root -> normal reporting.

Test the actual CLI exit codes in addition to helper functions.

## Review-loop budget rule

An authorized exceptional cycle does not override the operator budget checkpoint. Before launching it, confirm enough tool/runtime budget remains to observe the builder, verify the pushed head, rerun the complete suite, and obtain fresh A+B current-head reviews. If not, stop at the verified checkpoint rather than creating unknown post-checkpoint state.
