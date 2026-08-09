# Detached reviewer transport continuation

Use this when an exact-head PR proof has passed its gates, but a reviewer wrapper or relay lifecycle stops before a canonical artifact is published and read back.

## Preserve before retrying

- Preserve the passed gate evidence, exact head SHA, frozen packet, original stdout/stderr, prepared artifact, and retained worktree.
- Do **not** consume another builder cycle or rerun unrelated gates for a transport-only failure.
- Re-read the live PR head and prove local worktree HEAD, remote branch, and PR `headRefOid` still match before each continuation step.

## Distinguish a dead tool handle from a live process tree

A background-tool notification with `exit code None`, empty output, or a missing artifact is not proof that the reviewer exited.

1. Inspect the real process tree for the reviewer wrapper, model child, worktree path, and artifact path.
2. If the real wrapper/child is alive, do not launch a duplicate review.
3. Attach one low-frequency watchdog to the real wrapper PID. The watchdog's exit code proves only that the PID ended; it does not prove reviewer success.
4. After the PID ends, inspect authoritative stdout, stderr, prepared artifact, worktree cleanliness, and the live PR head.

## Substantive failure underneath a transport stop

Keep the lane's code verdict separate from its transport disposition. A run may correctly parse `STATUS=fail`, a blocking count, and concrete finding IDs, then stop because the prepared artifact omitted those same `FINDING:` lines. In that state:

- report that all passed gates remain passed for the unchanged head;
- report the substantive fail verdict and blocker IDs as provisional lane evidence;
- report the relay/artifact mismatch as the reason publication did not complete;
- run only the frozen-packet, unchanged-head transport retry described below;
- do not describe the stop as merely infrastructural or imply that the review was green.

If the repair cap is already exhausted, the retry cannot authorize another builder. Canonically publish and read back Reviewer A, then still complete Reviewer B and Integration Auditor in order so the terminal blocked ledger is independent and deduplicated. The cap determines that no more repair may start; it does not waive the remaining evidence lanes.

## Canonical artifact-shape retry

If the final message parsed but the prepared artifact omitted or changed its `FINDING:` records:

- Treat a mismatch as substantive only when the canonical machine verdict actually declares a blocking finding. A reviewer may write a `STATUS=pass`, `BLOCKING=0` artifact that discusses a non-blocking metadata concern in prose; the relay/parser must not synthesize a finding ID from that prose and then demand a matching `FINDING:` line.
- Preserve the artifact and report this as a control-plane parser defect. Before a fresh exact-head retry, correct any stale PR body/test-count/verification claim that caused the reviewer note, read the PR body back, and freeze a new packet. Do not fabricate a `FINDING:` record to satisfy transport.

- Keep the exact head and frozen evidence unchanged.
- Launch a fresh credential-free reviewer worktree and artifact path.
- Add an explicit focus requirement: every `FINDING:` line must appear in the prepared artifact and must be byte-for-byte identical to the corresponding final-message line.
- Never hand-edit, reconstruct, or summarize the reviewer artifact.
- Parse the final message with the shipped verdict parser, validate the prepared artifact against that verdict, create the shipped sanitized publication copy, and point the relay only at that sanitized copy.

## Relay and immutable readback

Before relay:

1. Confirm the PR head is unchanged.
2. Snapshot existing comment/review IDs.
3. Verify the configured publisher identity.

After relay:

1. Capture the immutable GitHub ID returned by the relay.
2. Fetch that exact ID directly.
3. Verify author, canonical role/head/status/blocking declarations, exact `FINDING:` parity, and byte equality with the sanitized publication copy.
4. For submitted reviews, require GitHub `commit_id` to equal the exact head. For issue comments, require the canonical `HEAD=` declaration because comments do not carry `commit_id`.
5. Freeze and read back a fresh evidence packet for the next ordered lane; prove the packet contains every earlier verified artifact ID before launching it.

Keep reviewer order strict: Reviewer A → Reviewer B → Integration Auditor. A later lane must not start from a packet that omits an earlier live artifact.

## Common false-success traps

- Treating the watchdog's zero exit as the reviewer's verdict.
- Republishing the reviewer's original bytes instead of the sanitized copy.
- Relaunching because the orchestration handle detached while the model child was still alive.
- Hand-editing malformed reviewer output to make the parser accept it.
- Running Reviewer B or the auditor before the preceding artifact has an immutable, parser-valid GitHub readback.
- Starting a builder repair from Reviewer A alone when the contract requires the full ordered triad and a deduplicated blocker ledger.
