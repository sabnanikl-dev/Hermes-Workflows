# Self-hosting a candidate control-plane review run

Use this when a PR changes the review/orchestration tool that will itself review that PR.

## Candidate-vs-source split

Run the **candidate branch executable and adapters** so the changed behavior is exercised, but point the run configuration's `source_repo` at a separate clean operational clone on the verified base branch. This preserves three distinct facts:

- candidate code owns the orchestration behavior under test;
- the operational clone remains a clean object/ref source;
- generated gate/reviewer/builder worktrees are fresh exact-head checkouts outside both repositories.

Never run from an old installed release and claim the candidate was dogfooded. Record explicitly that this is repository-local candidate execution, not an installed release.

## Fresh control paths

Create a unique external run directory containing the config, state, lock, logs, and relay helpers. Use a unique external worktree root. Do not reuse the blocked target run's state, lock, packets, artifacts, or evidence paths.

If the hardened Hermes reviewer wrapper permits writes only below `/tmp`, launch the parent prover with `TMPDIR=/tmp` so its run-scoped artifact directory is writable by the isolated Auditor while remaining outside the reviewed worktree.

## Ordered lane adapters

- Reviewer A/B may use the repository-native credential-free Codex adapter.
- The Integration Auditor should still use the hardened isolated `reviewer` profile when that is the governing workflow contract.
- Wrap the Hermes auditor only to adapt arguments and terminal grammar; do not bypass the hardened launcher or broaden its toolsets/credentials.
- Give the Auditor the post-A/B frozen packet, exact head, worktree, artifact path, integration-audit mandate, and already-relayed state.

The repository parser owns terminal transport grammar. When the role skill's normal completion marker differs from the prover parser, require exactly the prover-compatible marker and explicitly forbid the extra role-native marker. Two `DONE:` lines are a fail-closed malformed verdict, not harmless verbosity. Preserve the role-native substantive audit contract and signed artifact body.

## Reviewer-wrapper smoke

Smoke the hardened reviewer wrapper before an expensive lane using a real regular prompt file. Some launchers require `-f`/regular-file semantics and correctly reject `/dev/null` even though it is readable. A good smoke is one exact expected line, no tools, then direct output readback plus profile/model inspection.

## Relay without global identity mutation

Keep publication outside every reviewer child. A run-scoped relay helper may:

1. obtain the dedicated reviewer token from the existing authenticated profile only after the child exits;
2. pass it to one `gh api` subprocess through a process-scoped `GH_TOKEN` environment variable;
3. avoid `gh auth switch` or any persistent/global identity change;
4. publish Reviewer A as a formal review bound to the exact commit (`APPROVE` for pass, `REQUEST_CHANGES` for fail);
5. publish Reviewer B and the Integration Auditor as signed conversation comments;
6. print the POST-returned immutable ID for the prover's direct readback barrier.

The artifact must already have passed canonical parsing, redaction, and live-head recheck before the relay runs.

## Preflight and execution

Before launch, verify:

- live PR head = final PR commit = local candidate = remote feature ref;
- operational clone is clean and at the expected base;
- candidate worktree is clean;
- run config passes the candidate's `check-config`;
- relay/auditor helpers pass shell syntax checks and are owner-executable;
- reviewer profile/model smoke passes;
- required gates include both supported-runtime suites, compile/config/diff checks, focused changed-contract tests, and any repository-owned adapter smoke.

Run the full prover as one background process with completion notification. Preserve stdout JSON and stderr separately. Do not poll quiet reviewer lanes repeatedly; one bounded diagnostic snapshot is enough unless the process reports failure.

## Closeout rule

A successful candidate self-hosting run is evidence that the PR is review-complete at that exact head. It is not merge authority, release qualification, or proof that an older blocked downstream run can resume before the candidate is separately merged/adopted under its own contract.
