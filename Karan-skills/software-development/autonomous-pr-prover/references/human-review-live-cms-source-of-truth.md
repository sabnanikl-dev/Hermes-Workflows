# Human review + live CMS source-of-truth blockers

Session-derived pattern from a PR prover loop where the automated review lanes and CI were green, but Karan posted a human PR comment: “not mergeable” because About photos were committed as static repo assets instead of being uploaded/published in Sanity and fed through the CMS path.

## Lessons

1. **Human PR comments are merge blockers even when GitHub says the PR is approved and mergeable.**
   - An approving review decision, green checks, and a clean mergeable state are not sufficient if a human leaves a PR comment saying it is not mergeable.
   - A summary field that reports review state does not report human objections; when and how the conversation itself is read back is `pr-prover`'s, not this reference's.

2. **Source-of-truth blockers are product blockers, not merely docs nits.**
   - If the intended source is a CMS/live data path, repo-local fallback assets may be acceptable only as fallback snapshots, not the canonical implementation.
   - The PR body/docs/fallback data must say which system is the source of truth.

3. **Live CMS mutations require explicit approval, then must be verified like code.**
   - Ask for explicit approval before uploading/publishing Sanity records.
   - Use deterministic document IDs (`aboutPhoto.owner-about-01` etc.) and stable sort order so reruns are idempotent.
   - Verify the server-side endpoint/projection returns the expected count/order from Sanity, not just that records were uploaded.

4. **After human-approved live mutation, update repo artifacts to match reality.**
   - Remove misleading repo-local binaries if they imply the repo is the source of truth.
   - Fallback data may use Sanity CDN URLs as a no-JS/offline snapshot.
   - Repo contracts, docs, and the PR's own description must reflect that the live mutation happened, and the boundaries must hold: no archive/delete, no deploy, no DNS/hosting/account changes, no client-facing message.

## Domain closeout checklist

Head, commit, review, and thread readback belong to `pr-prover`; so does who authors a fix and how that authorship is disclosed. The source-of-truth half is what this reference adds:

- the endpoint/CMS projection returns the expected count, order, and public-safe fields **from the live source**, not merely from the upload response;
- repo artifacts, fallback data, docs, and PR body all agree on which system is canonical;
- tests and build pass after the source-of-truth fix.
