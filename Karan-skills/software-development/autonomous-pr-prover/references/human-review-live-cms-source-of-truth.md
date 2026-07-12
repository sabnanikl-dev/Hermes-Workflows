# Human review + live CMS source-of-truth blockers

Session-derived pattern from a PR prover loop where automated A/B reviews and CI were green, but Karan posted a human PR comment: “not mergeable” because About photos were committed as static repo assets instead of being uploaded/published in Sanity and fed through the CMS path.

## Lessons

1. **Human PR comments are merge blockers even when GitHub says APPROVED.**
   - `reviewDecision: APPROVED`, green checks, and `mergeable: MERGEABLE` are not sufficient if Karan/human leaves a PR comment saying not mergeable.
   - Re-read PR conversation comments in final closeout; do not rely only on `latestReviews`/`reviewDecision`.

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
   - Update contracts/docs/PR body/comments to reflect live mutation happened and preserve boundaries: no archive/delete, no deploy, no DNS/hosting/account changes, no client-facing message.

5. **No direct Hermes patching after user says to use builder.**
   - If Hermes already made uncommitted local edits and the user says “don’t fix yourself, use builder,” immediately revert Hermes edits and hand the blocker list to the builder/fix lane.
   - The final fix commit/comment should come from the builder lane, with provenance disclosed.

## Verification closeout checklist

- PR head matches local HEAD and remote branch.
- `gh pr view` shows current head, mergeability, checks, and review decision.
- Full reviews API filtered by current `commit_id` shows Reviewer A and B signed approvals/comments on the current head.
- PR conversation comments since the latest approval contain no human “not mergeable” blocker.
- Review threads are empty/resolved.
- Endpoint/CMS projection returns expected count/order/public-safe fields.
- Tests/build pass after the source-of-truth fix.
