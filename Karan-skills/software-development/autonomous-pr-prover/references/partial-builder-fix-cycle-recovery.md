# Partial builder fix inside a bounded PR-prover cycle

## Failure mode

A builder reads a durable change-request artifact containing multiple blockers, fixes one, and explicitly declines another as "out of scope" or "already satisfied." If that partial push is treated as the end of the cycle, the loop silently narrows the reviewer contract to whatever the builder was willing to do.

## The judgment that matters

1. Judge the omitted finding from the durable artifact itself: is it bound to the current head, and is it still blocking? A builder's summary is not that artifact.
2. Adjudicate it independently against the issue/PR contract. **A builder's scope opinion does not supersede a review gate**, and a builder's own summary is not evidence that the frozen ledger is closed.
3. If the finding is valid, the ledger is not closed, so the cycle is not finished. The corrective-rerun allowance and the cycle cap are defined in `pr-prover/MISSION.md`; this reference does not restate them.
4. The correction is the exact omitted artifact — its review URL/ID plus the adjudication — not a fresh wall of reviewer prose. This is the narrow exception to pointer-first prompting: the lane already read the PR and misclassified a durable artifact, so identifying that artifact is the whole correction.
5. A corrective attempt that still refuses or fails is a Karan judgment, not another attempt. Unlimited retries under the label "same cycle" is the failure mode this reference exists to prevent.

## Why it is a judgment call, not bookkeeping

The tempting shortcut is to accept the partial push because the diff looks reasonable and re-review is cheap. It is not cheap: re-review against a quietly shrunken blocker set produces a pass that means nothing, and the next reader cannot tell which findings were adjudicated and which were merely dropped.
