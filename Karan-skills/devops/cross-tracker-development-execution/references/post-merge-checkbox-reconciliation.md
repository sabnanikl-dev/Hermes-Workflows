# Post-merge child/parent checkbox reconciliation

Use this when a verified GitHub merge completes a Linear child but the child acceptance checkboxes or the parent's corresponding roll-up box still lag behind live evidence.

## Evidence gate

Do not check boxes merely because Linear says `Done` or GitHub says the PR is closed. First verify the evidence each criterion claims, including as applicable:

- GitHub API reports `merged: true`, the reviewed head, and a merge commit;
- required tests and exact-head reviewer/auditor artifacts passed;
- branch deletion was separately verified when requested;
- the criterion is owned by this child, not a later child or non-blocking follow-up.

A user request to reconcile every checkbox authorizes the body correction, but it does not replace this evidence check.

## Procedure

1. Fetch the live child and parent issues with complete descriptions and states.
2. Extract each full description into a temporary Markdown file.
3. Identify every child acceptance checkbox and the parent's one roll-up line for this child.
4. Change only evidence-backed markers:
   - child: check every satisfied criterion;
   - parent: check only the exact completed-child line;
   - preserve sibling/future-child boxes unchanged.
5. Re-read each complete temporary description before mutation. Never overwrite a Linear body from a paginated or partial read.
6. Update each issue with its complete revised description in one mutation.
7. Fetch both issues again and assert:
   - child state remains correct (`Done` / `completed` when already complete);
   - expected checked-box count matches;
   - no unintended unchecked child acceptance boxes remain;
   - the exact parent roll-up line is checked;
   - unrelated parent boxes remain unchanged.
8. Add a closeout comment only if it supplies durable evidence not already present.

## Important distinctions

- **State and body drift independently.** A child can be `Done` while every acceptance box is unchecked; correct the body without toggling the state unnecessarily.
- **Parent roll-up is narrow.** Completing one child never authorizes checking sibling criteria or marking the parent complete.
- **Non-blocking follow-ups stay separate.** A research follow-up does not keep the completed implementation child unchecked and must not silently become a parent acceptance gate.
- **Linear requires full-description updates.** Preserve all surrounding prose exactly; then prove the mutation through direct readback rather than the update response alone.
