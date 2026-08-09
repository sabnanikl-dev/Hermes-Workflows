# Evidence-envelope and report-integrity probes

Use this matrix when a validator or coordinator turns a producer-owned JSON envelope into a JSON/Markdown success report, especially when the report claims an exact revision, execution result, or authority boundary.

## 1. Separate configuration from execution evidence

A configured gate is not an executed gate. If reports list every configured gate, track an explicit execution state such as `not-reached`, `skipped`, `passed`, or `failed`.

Negative probes:

- Configure an external gate that is skipped by a feature/visual flag.
- Put an external gate after an earlier failing gate so it is never reached.
- Stop the run before any gate launches.

In every case, reject or prevent wording such as “endpoint checked,” “test passed,” or “evidence obtained.” A separate executed-results list does not cure a contradictory per-gate sentence elsewhere in the same report.

## 2. Reject duplicate JSON object keys

Ordinary `json.loads()` silently keeps the last duplicate key. That permits a source artifact to contain conflicting `revision`, `head`, `repo`, `gate`, or timestamp claims while the parsed mapping appears consistent.

Probe both:

- duplicate keys with identical values;
- duplicate keys with conflicting values, placing the expected value last.

Strict envelopes should reject every duplicate before semantic validation, commonly via an `object_pairs_hook` that records seen names. “Exactly these keys” must mean exactly one occurrence of each key in the source artifact, not merely the final mapping’s key set.

## 3. Validate scalar semantics, not only shape

A timestamp regex such as `YYYY-MM-DDTHH:MM:SSZ` accepts impossible values (`2026-99-99T99:99:99Z`). Parse it as a real UTC datetime and require canonical round-trip formatting. Probe invalid month/day/hour/minute/second and leap-day boundaries.

For single-line URL, identifier, source, and summary fields:

- reject C0 controls, DEL, CR, LF, and other line separators where they have no contract meaning;
- test empty/whitespace-only, exact limit, and limit+1;
- decide whether URL semantics require a finite scheme/host policy or only a bounded identifier, and document that narrower claim.

## 4. Protect human renderings from structural injection

JSON string safety does not imply Markdown safety. A producer-controlled newline, backtick, heading, list item, or code fence can create a forged report section while the machine payload remains valid.

Probe each untrusted rendered scalar with:

- `\n### Forged section`;
- backticks and triple-backtick fences;
- list-item and blockquote prefixes;
- strings resembling status, approval, or merge-authority declarations.

Prefer rejecting controls for contractually single-line fields and also use a centralized Markdown inline/code escaping function. Confirm the JSON and Markdown renderings remain semantically equivalent after escaping and redaction.

## 5. Enforce size limits before allocation

If an envelope has a byte cap, do not call an unbounded `read_bytes()` and check length afterward. A large or sparse file can consume memory before the intended structured refusal. Use `stat` plus a bounded read, or read at most `limit + 1`, and test that the parser never allocates in proportion to producer-controlled file size.

## 6. Define topology identity honestly

If a report summarizes “shared adapter” topology, define the stable adapter identity. Using only `argv[0]` can collapse distinct interpreter-launched scripts into one adapter and split one adapter invoked through path aliases. Either:

- report a sanitized canonical invocation prefix sufficient to identify the adapter;
- add an explicit validated adapter identifier; or
- document that the field means executable identity only and avoid broader “same adapter” language.

## Minimum closeout matrix

A report/evidence change is not ready until tests show:

1. configured-but-unexecuted work cannot be described as executed;
2. duplicate-key and contradictory envelopes fail closed;
3. impossible timestamps and control-bearing scalars fail;
4. Markdown structure cannot be injected through evidence fields;
5. valid boundary controls still pass;
6. the full native suite remains green; and
7. external probes add at least one mutation absent from builder-authored fixtures.
