# Pre-publication redaction and relay proof

Use this reference when a credential-free reviewer prepares a body that a trusted parent process will publish to GitHub or another external system.

## The failure mode

Parsing and redacting an in-memory finding is **not** the same as sanitizing what the relay publishes.

A dangerous implementation can:

1. read a raw reviewer artifact;
2. parse its findings through a scrubber;
3. compare the scrubbed findings successfully;
4. pass the original raw file path to `gh ... --body-file`;
5. read the raw published body back and normalize it through the same scrubber;
6. report parity even though credential-shaped text was published.

This is a false-success pattern: both sides compare equal only because both were normalized after the unsafe publication boundary.

## Safe relay sequence

Treat the child-produced artifact as **raw local evidence**, not as publication-eligible bytes.

```text
raw child artifact
→ sanitize the entire human-readable body for publication
→ write a unique run/head/role sanitized copy outside the worktree
→ parse and validate the sanitized copy
→ compare sanitized findings with the already-scrubbed lane verdict
→ relay only the sanitized copy
→ read back the POST-returned immutable artifact ID
→ compare the raw API body with the exact sanitized body/digest
→ parse the readback and recheck role/head/status/blocker/finding parity
```

Required properties:

- Preserve every non-secret character exactly where the redactor permits it.
- Preserve required declarations, signatures, headings, and finding grammar.
- If sanitization makes the body parser-invalid or changes role/head/status/blocker semantics, fail closed before publication.
- Keep the raw artifact local and permission-restricted; never pass its path to the relay command.
- Use a unique sanitized path bound to run, head, and role; prove it did not pre-exist.
- Compare GitHub readback to the exact sanitized publication bytes before any trimming or normalization. Parser parity is an additional check, not a substitute for raw-body equality.

## Deterministic regression

Exercise the normal application loop, not only helper functions.

1. Construct a synthetic credential-shaped sentinel at runtime from fragments; do not print it.
2. Make the reviewer stub place the sentinel inside a finding summary and signed artifact body.
3. Let the real prepared-artifact reader, publication sanitizer, configured relay, fake remote, and readback predicate run normally.
4. Assert the relay receives the redaction placeholder and never the sentinel.
5. Assert the raw child artifact still contains the sentinel locally, proving the test distinguishes raw input from sanitized publication.
6. Assert the sanitized artifact remains parser-valid and its findings match the lane verdict after the same redaction transformation.
7. Mutate the code to relay the raw artifact path; the regression must fail.
8. Mutate the readback to compare only normalized findings; a remote body different from the sanitized publication bytes must still fail.

## Source-level mutation protocol

A runtime mock that replaces the scrubber is useful, but it is not the same evidence as mutating the shipped source seam. When a PR claims the publication guard is load-bearing, prove that claim without touching the active or reviewer worktree:

1. Create a fresh disposable detached worktree at the exact reviewed head; verify the path did not already exist, `HEAD` is the full expected SHA, and the tree is clean.
2. Change exactly the publication substitution under test—for example, replace `body = scrub(prepared.body)` with `body = prepared.body`—and annotate it as a mutation probe. Do not weaken tests or alter any second guard.
3. Run the narrow relay/publication suite with stdout and stderr captured to a local file. The test command must exit nonzero, and the output should identify the expected publication-boundary failures and their count.
4. Construct the synthetic credential sentinel from fragments in test code. Search the complete captured mutation output for the fully assembled sentinel and require **zero occurrences**; a leak regression that prints the protected value while failing is itself unsafe evidence.
5. Record only safe observables: changed seam, suite/test count, failure count/names, command exit, and zero-sentinel result. Never include the suspect body in assertion messages or operator summaries.
6. Remove the disposable worktree only if this operator created it fresh for the probe. Then reverify the primary exact-head worktree is clean and unchanged. Never use force-removal on an inherited or unknown worktree.

Treat the mutation as non-vacuity evidence for the guard, not as a reviewer verdict or permission to skip the ordered exact-head triad.

## Audit probe

When reviewing a relay path, trace the concrete object/path used at each seam:

- raw child artifact path and body;
- parsed/redacted in-memory findings;
- path rendered into relay argv;
- bytes captured by the fake/real remote;
- immutable-ID API readback body;
- equality and parser checks applied afterward.

Do not accept claims such as “findings are redacted” or “readback parity passes” until the exact relay-eligible bytes are proven sanitized before the external POST.

## Pitfalls

- Redacting only structured findings while leaving surrounding prose raw.
- Comparing two scrubbed representations and mistaking equality for safe publication.
- Rewriting the raw artifact in place, which destroys forensic evidence and can blur the creation boundary.
- Applying asymmetric newline trimming between sanitized file and API readback, causing either false mismatches or duplicate posts.
- Logging the synthetic sentinel during tests or including real credential material in fixtures.
