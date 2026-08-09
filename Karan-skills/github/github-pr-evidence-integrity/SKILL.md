---
name: github-pr-evidence-integrity
description: "Protect GitHub PR workflows against hidden closing links, stale-head evidence, malformed reviewer relays, and unverified metadata. Use for staged PRs, exact-head reviews, and transport-only agent artifacts."
version: 1.0.0
author: Hermes Agent
---

# GitHub PR Evidence Integrity

## Trigger

Use this skill when a GitHub PR workflow depends on any of these claims being exactly true:

- an interim/staged PR references an umbrella issue but must not close it;
- reviewer or builder artifacts must be tied to one exact PR head;
- Default Hermes transports an artifact produced by a credential-free agent;
- a malformed review/comment must be repaired without losing audit history;
- a replacement branch/PR must preserve accepted bytes while removing bad metadata linkage.

Use `github-operations` for general GitHub actions and `multi-agent-dev-workflow` for full issue-to-PR orchestration. This skill is the integrity layer for PR metadata and evidence transport.

## Core rule

A successful command is not proof. Count only live readback that confirms the intended body, author, state, head association, and issue-closing behavior.

## Exact-head preflight

Before posting an artifact, launching a fix lane, or advising merge readiness:

1. Query the live PR state, draft state, base, head branch, and full `headRefOid`.
2. Require local HEAD, upstream, remote branch, live PR head, and final PR commit to agree when those views are applicable.
3. Read the complete current review/comment/thread/check surfaces with pagination accounted for.
4. Treat every artifact from an older head as historical evidence only.
5. Re-run this preflight immediately before each external artifact relay.

Any push invalidates current-head gates, reviews, and readiness claims.

## Interim PR closing-link gate

Plain `Refs #N` in the body does **not** prove that merging will leave issue `#N` open. A branch created through GitHub's issue-development flow can carry a separate development association that appears in `closingIssuesReferences`.

For an interim PR that must not close its umbrella issue:

1. Use an ordinary unlinked branch, not an issue-developed branch.
2. Put plain `Refs #N` in the PR body.
3. Query live PR metadata and require `closingIssuesReferences == []` before review.
4. Recheck after branch, issue, or PR-body changes.

If the PR is already incorrectly linked, preserve the accepted commit on a new unlinked branch, open a replacement PR at identical bytes, verify zero closing references, then close the old PR unmerged. See `references/github-pr-metadata-and-artifact-relay-integrity.md` for the recovery recipe.

## Credential-free reviewer relay

Reviewer processes should receive no GitHub credential. They return a signed artifact; Default Hermes performs transport only after independent validation.

Validate before transport:

- expected reviewer role;
- model/reasoning declaration;
- full head SHA;
- verdict and blocker count;
- completion marker;
- no credential or unrelated secret content.

Submit the intended artifact type:

- Reviewer A: formal review bound to the reviewed commit;
- Reviewer B: signed conversation comment;
- Integration Auditor: signed conversation comment.

For `gh api`, use `-F body=@/tmp/artifact.md` to submit file contents. Do **not** use `-f body=@/tmp/artifact.md`; that sends the literal path string. Prefer `gh pr comment --body-file` for conversation comments when practical.

## Mandatory relay readback

After every relay:

1. Fetch the artifact directly from GitHub.
2. Compare the complete live body with the local artifact.
3. Verify author login.
4. For formal reviews, verify state and `commit_id`.
5. Verify the expected head appears in the signed body.
6. Save the returned URL/ID as the durable handle.

Do not launch the builder/fix lane until all required artifacts pass readback.

## Recovery without rewriting history

If a conversation comment contains the literal file path or wrong body, patch that comment in place with a file-reading form field and verify it again.

A submitted formal review generally cannot be edited. Dismiss the malformed review with an explicit transport-correction explanation, then submit a replacement formal review at the same verified head. Preserve the dismissed review as audit history.

Never silently delete or ignore malformed evidence. The correction trail is part of the proof.

## Final verification checklist

- [ ] PR remains OPEN and on the expected base/head.
- [ ] Local/upstream/remote/live/final-commit heads agree.
- [ ] `closingIssuesReferences` matches the intended issue behavior.
- [ ] Every required reviewer artifact is current-head and read back.
- [ ] Formal review state and `commit_id` are correct.
- [ ] Conversation-comment bodies match their local artifacts.
- [ ] Old-head evidence is labeled historical.
- [ ] No merge, ready flip, deployment, installation, or live/account mutation occurred without separate approval.
