# Reviewer Completion Idempotency and Relay Ledger

Use this when Reviewer A, Reviewer B, or the Integration Auditor runs in the background and completion can be observed through more than one path (`notify_on_complete`, `process.poll`, `process.wait`, or a delayed platform notification).

## Why this matters

A single reviewer process can generate duplicate-looking completion events. Reviewer wrappers may also echo the prompt, stream internal text, and print the prepared artifact more than once. Treating every event as new can:

- relay the same formal review/comment twice;
- parse `BEGIN_ARTIFACT` from the prompt rather than the actual output;
- count a stale or partial artifact as a final verdict;
- overwrite the lane state after readback verification.

## Idempotency key

Track each lane with a stable key:

```text
(repo, PR number, exact full head SHA, reviewer role)
```

Recommended state machine:

```text
running
  -> exited
  -> artifact_extracted
  -> relay_submitted
  -> relay_readback_verified
```

State transitions are monotonic. A delayed duplicate completion event must not move a lane backward or trigger another relay.

Record at minimum:

- process/session ID;
- exact expected full SHA;
- completion marker;
- verdict and blocking count;
- extracted artifact file path and SHA-256;
- GitHub review/comment URL or ID;
- readback verification result.

## Exact artifact extraction

Never use a raw substring search such as `text.index("BEGIN_ARTIFACT")`: the prompt itself may contain that token. Parse delimiter **lines** exactly.

```python
from pathlib import Path

lines = Path(output_path).read_text().splitlines()
start = next(i for i, line in enumerate(lines) if line == "BEGIN_ARTIFACT")
end = next(
    i for i, line in enumerate(lines[start + 1 :], start + 1)
    if line == "END_ARTIFACT"
)
body = "\n".join(lines[start + 1 : end]).strip() + "\n"
```

Then verify before relay:

- expected role signature;
- exact full `PR: #N | Head: <sha>` line;
- model/reasoning line;
- transport disclosure;
- completion marker outside the artifact with matching role, head, verdict, and blocker count.

Wrappers may print the final artifact twice. The first complete exact-line-delimited artifact is acceptable only when its signature/head/marker agree; otherwise stop and inspect rather than guessing.

## Relay deduplication gate

Before posting:

1. Re-query live `headRefOid`; reject the artifact if the head changed.
2. Query the intended GitHub surface:
   - Reviewer A: formal reviews filtered by exact `commit_id` and role signature.
   - Reviewer B / Integration Auditor: conversation comments filtered by exact head line and role signature.
3. If an exact matching artifact is already present, do **not** post again. Read it back, compare the signed body (or its normalized hash), save the existing URL/ID, and mark `relay_readback_verified`.
4. Otherwise relay once under the verified reviewer identity, then immediately read it back and verify head, signature, body, and intended review state.

Do not rely on `latestReviews`; same-account role reviews can collapse, comments are not included, and delayed process output can arrive after GitHub already contains the artifact.

## Handling delayed notifications

When a completion notification arrives after a lane is already `relay_readback_verified`:

- classify it as a duplicate transport event;
- optionally confirm the session ID and exit code agree;
- do not re-extract or re-post;
- report only if the delayed event conflicts with the stored marker/verdict.

A normal exit code proves only that the wrapper completed. The signed artifact and `DONE:` marker determine the lane verdict.

## Exception-cycle sequencing

For a human-approved exception cycle, preserve the umbrella skill’s A-first convergence rule:

1. verify the exception fix and build the immutable packet;
2. run Reviewer A alone as the adversarial convergence gate;
3. relay/read back A idempotently;
4. launch Reviewer B and the Integration Auditor only after A returns zero blockers, unless they are explicitly needed to adjudicate A.

This avoids spending the final reviewer budget on a head that Reviewer A can still break with an adjacent false-pass probe.
