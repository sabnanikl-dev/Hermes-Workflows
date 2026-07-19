# Partial builder fix inside a bounded PR-prover cycle

## Failure mode

A builder reads a durable `CHANGES_REQUESTED` review containing multiple blockers, fixes one, and explicitly declines another as “out of scope” or “already satisfied.” If Hermes accepts that partial push and starts re-review, the loop silently narrows the reviewer contract and wastes a cycle.

## Correct recovery

1. Read back the formal review object from GitHub and confirm the omitted finding is durable, current-head, and still blocking.
2. Adjudicate the finding independently against the issue/PR contract. A builder’s scope opinion does not supersede a formal review gate.
3. If valid, keep the current fix cycle open. Do not launch reviewers yet.
4. Re-run the original builder lane once with a compact correction that points to the exact review URL/ID and says the omitted finding remains the merge gate.
5. Require a focused commit, verification, remote commit-list readback, and signed PR comment.
6. Only after the complete blocker set is resolved should Hermes run full verification and current-head A/B re-review.
7. If the corrective builder run still refuses or fails, escalate. Do not add unlimited retries under the label “same cycle.”

## Cycle accounting

Count a new cycle when a new reviewer pass produces a new blocker set. A corrective builder rerun before re-review completes the already-open cycle; it is not a third cycle. Bound it to one corrective rerun.

## Prompt shape

```text
Your previous run fixed blocker A but declined blocker B.
Reviewer B's formal current-head review <URL/ID> remains the active merge gate.
Hermes has adjudicated blocker B as valid against issue/PR acceptance criteria.
Implement only that remaining blocker, verify it, commit/push, and comment back.
Do not merge or deploy.
```

This is a narrow exception to pointer-first prompting: the builder already read the PR and misclassified a durable artifact, so Hermes may identify the exact omitted artifact and adjudication without pasting a fresh wall of reviewer prose.
