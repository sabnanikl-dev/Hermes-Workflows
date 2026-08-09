# Immutable Proportionality Audit Reference

## Exact-object inspection with dirty WIP

Use committed Git objects, not working-tree files:

```bash
BASE=<base-sha>
HEAD=<reviewed-head-sha>

git rev-parse HEAD
git status --short
git diff --numstat "$BASE...$HEAD"
git diff --dirstat=lines,0 "$BASE...$HEAD"
git diff --name-status "$BASE...$HEAD"
git show "$HEAD:path/to/file"
git blame --line-porcelain "$HEAD" -- path/to/file
```

`git show HEAD:path` and `git blame HEAD -- path` exclude uncommitted changes. Record status again before finishing. Do not run repository imports in the dirty tree because they may create bytecode or caches.

## LOC decomposition

Classify every changed path into:

- production source;
- tests and test support;
- docs;
- examples and launch scripts;
- generated or binary assets.

For each category report files, additions, and deletions. Useful derived values include:

- source share of total additions;
- test share and test/source ratio;
- boundary/security cluster share of source;
- current-line attribution by commit or contract slice using porcelain blame.

For Python, AST and tokenization can derive:

- module/class/function line spans;
- explicit `test_*` function count;
- test-function average length and tiny-test count;
- blank, comment-only, docstring, and remaining code lines.

Physical LOC is the primary reproducible metric. “Code-only” LOC is supplementary and should state its classification method.

## Test-shape analysis

To detect obvious repetitive tests without mislabeling a thorough suite:

1. Parse every test function with `ast`.
2. Compare exact body dumps after removing the function name/docstring.
3. Run a second comparison after replacing literal constants with one placeholder.
4. Report the number of duplicate groups and tests in those groups.

A low duplicate count means the suite is not simple copy-paste inflation. The more important question becomes why the production contract requires so many distinct cases and whether they prove real boundaries.

Count tests that exercise real:

- Git repositories/worktrees;
- child processes and descendants;
- sockets and shutdown;
- sandbox/client behavior;
- provider/GitHub readback.

Contrast them with deterministic doubles. A modeled function that predicts an external sandbox and tests settings against that same prediction is a shadow model, not external qualification.

## Architecture hotspot interpretation

Large files are evidence, not automatic findings. Escalate when size aligns with mixed responsibilities:

- coordinator class owns inspection, gates, reviewers, builder, Git verification, artifact readback, cleanup, and reporting;
- launcher owns identity resolution, policy, filesystem material, transport, sandbox generation, executable attestation, and process execution;
- capability module implements custom framing, authentication, threading, operation execution, process cancellation, and teardown for a three-operation vocabulary;
- policy generator is paired with a large independent validator/interpreter maintained in the same package.

Measure class spans and list the responsibilities before recommending simplification.

## Contract-drift checks

Search exact-head source and docs for concepts the parent removed, including synonyms:

- journal, digest chain, nonce, packet root, manifest;
- approval grammar or parallel authority plane;
- source/launcher byte attestation, fingerprint, integrity proof;
- proof-of-death or process takeover;
- broad broker or credential machinery.

Do not decide by substring alone. For example, constant-time comparison of a per-lane bearer secret is not a MAC'd reviewer envelope. Judge data flow and authority semantics.

When the child explicitly requires a mechanism the parent explicitly removes, report both citations and mark it `NEEDS HUMAN CONTRACT RESOLUTION` unless hierarchy rules say otherwise.

## Verdict rubric

### Necessary

- Each major subsystem maps directly to a requirement.
- One implementation exists per invariant.
- Configuration and public API are no broader than approved deployment needs.
- Real boundary tests qualify the load-bearing claims.

### Defensible but too large

- Threat model and mechanisms are required.
- Excess lies mainly in module shape, repetition, prose, packaging, or reviewability.
- Simplification can preserve every approved concept.

### Overengineered

- Optional modes create different assurance levels.
- New protocols or concurrency exist where a simpler closed path works.
- Shadow validators replicate external semantics.
- Attestation/packet layers contradict a narrow parent contract.
- Supporting boundary machinery dominates the core workflow.

Use one primary verdict. “Defensible intent, overengineered implementation” is appropriate when security concerns are real but the implementation is disproportionate.

## High-value simplifications

Prefer removals with clear architectural effect:

1. One production lane type; keep test doubles behind internal interfaces.
2. One immutable lane/role policy generating environment, capabilities, tools, and sandbox settings.
3. One serial authenticated broker when operations are already mutually exclusive.
4. One source of repo/login/SHA/path/capability validation.
5. Exact Git commit/tree/readback checks without redundant executable or source-byte attestation when the parent excludes it.
6. External live qualification for sandbox/provider semantics; local checks remain structural.
7. Table-driven literal permutations while preserving real boundary probes.
8. Minimal public exports matching the actual CLI/router surface.

Tie each recommendation to files and name the subsystem or branch it eliminates.