# Real-agent adapter proof and detached reviewer supervision

Use this reference when a PR changes a Claude/Codex/Hermes launcher, verdict transport, prepared review artifact, or relay lifecycle. It captures failure modes that deterministic stubs and ordinary process tracking can miss.

## Prove the exact shipped CLI invocation

A green stub test does not prove an agent adapter is operational. Before final review, inspect and smoke the **exact adapter argv** against the installed CLI.

For a Codex review adapter that writes a prepared artifact outside its disposable worktree, verify every runtime property the contract claims, including as applicable:

- fresh/ephemeral context;
- pinned model and reasoning effort;
- explicit noninteractive approval mode;
- explicit sandbox mode;
- the artifact directory granted as an additional writable directory;
- final-message output file;
- ambient configuration handling consistent with the documented contract.

The smoke must prove two separate outputs:

1. narration/progress cannot become verdict input;
2. the agent can actually write the prompted prepared artifact at the external scratch path.

A test where a stub writes only the final-message file and the **test process** fabricates the prepared artifact after the adapter exits does not prove the artifact-writing contract.

## Keep final-message, parsed findings, and prepared artifact in parity

Do not validate only `STATUS` and `BLOCKING` declarations. When the prompt requires structured findings, prove one-to-one agreement among:

- final-message `FINDING:` records;
- parsed status and blocker count;
- finding records preserved in the prepared artifact;
- relay/readback content consumed by the Integration Auditor.

Required negative probe: a prepared artifact declaring `STATUS=fail` and `BLOCKING=1` with zero corresponding finding records must fail before relay.

## Exercise the lifecycle, not a helper-shaped approximation

An ordered `for` loop over adapter calls is not proof of the product lifecycle when the acceptance claim is:

`Reviewer A → Reviewer B → Integration Auditor → trusted relay → readback`.

The repository-owned integration proof must exercise the normal orchestration/relay seam and show that:

- each reviewer creates its own intended artifact;
- the trusted relay receives that exact validated artifact;
- readback binds author, role, head, status, blocker count, and finding details;
- Reviewer B sees the required state from A and the auditor sees both A/B artifacts;
- a defect in artifact creation, relay, ordering, or readback makes the proof fail.

Manual calls to a prepared-artifact parser after the test fabricates files are useful unit tests, but not end-to-end relay proof.

## Extract reviewer artifacts defensively

Reviewer CLIs may echo the prompt and repeat the final answer after token-usage output. Never select a block by raw substring or the first delimiter occurrence.

Scan exact-line `BEGIN_ARTIFACT`/`END_ARTIFACT` pairs and accept only a pair whose body contains the expected role, exact full head, pinned runtime/reasoning, one valid status, and one integer blocker count, followed immediately by the matching exact completion marker. If several valid pairs exist, require their bodies to be byte-identical before relaying one.

## Supervise wrappers that hand off to a native process

A launcher wrapper may `exec` into a native reviewer process such that the orchestration handle reports `exited` with no exit code while the native PID remains alive. Treat the process-manager event as a signal to verify, not proof of completion.

Recovery:

1. Inspect the reported PID directly.
2. Confirm the native model command, elapsed time, and expected output file are still active.
3. Do not restart or duplicate the review while that PID lives.
4. Attach a bounded replacement watchdog that waits on `kill -0 <pid>` and notifies when the real process exits.
5. Accept completion only after the expected artifact/marker validates and the disposable worktree remains clean.

The durable rule is to supervise the real child and validate its artifact—not to encode that a wrapper or process tool is permanently broken.
