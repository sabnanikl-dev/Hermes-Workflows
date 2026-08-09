# Successor issue and parent-train reconciliation

Use this during closeout when a merged/completed hardening child produces a new pilot, re-pilot, qualification, or follow-up while an earlier terminal pilot and a separate target execution tracker already exist.

## Keep the four roles distinct

1. **Completed predecessor** — owns the shipped fix/merge evidence and becomes immutable after closeout.
2. **Earlier terminal pilot** — remains Done as historical evidence; do not reopen it merely because the defect was fixed.
3. **Target execution tracker** — owns the real target’s implementation/evidence state. Do not duplicate its checklist into the new control-plane issue.
4. **New successor** — owns the new qualification/re-pilot contract. Create it in Backlog/Triage unless execution is separately authorized.

## Ordered mutation

1. Re-read the parent, predecessor, earlier pilot, target tracker, live target source, and duplicate/adjacent issues.
2. Draft the successor from current live coordinates. Mark observed SHAs/states as evidence that must be re-read at execution time.
3. Create and verify the successor’s team, project, parent, state, priority, title, body markers, and acceptance count.
4. Wire relations before terminal closure:
   - predecessor **blocks** successor: `issueId = predecessor`, `relatedIssueId = successor`, `type = blocks`;
   - successor is **related** to the earlier terminal pilot;
   - successor is **related** to the target execution tracker.
5. Amend the open parent in the same bounded reconciliation:
   - update the active sequence/train;
   - check the predecessor row with exact merge/outcome evidence;
   - add the successor row unchecked;
   - leave the parent workflow state unchanged unless the full parent contract is complete.
6. While the predecessor is still open/in-review, append its final merge/closeout evidence and successor link. Only then move it to Done. Do not later amend a Done child merely to backfill sequencing.
7. Add a concise pointer to the target tracker: successor exists, target tracker remains canonical, and execution has not started. Do not mirror the successor’s full acceptance list there.
8. Directly read back the predecessor state/body, successor state/body, both ends of every relation, parent sequence/criteria, and target-tracker pointer comment by ID.

## Authority boundary

Creating and wiring a successor authorizes specification/tracker mutation only. It does not authorize claiming or executing the successor, target-branch mutation, reviewer publication, merge, deploy, tag/install/release, credential/account changes, or client-facing action.

## Verification notes

- Linear may normalize Markdown links, ordered-list indentation, bullets, and trailing newlines. Verify unique headings, identifiers, checkbox transitions, SHAs, URLs, state/project/parent IDs, and relation direction rather than requiring byte-identical descriptions.
- A helper can print a successful ID and still exit nonzero. Treat that as ambiguous and read the exact object back before retrying any mutation.
- Verify the successor acceptance checklist begins unchecked; a freshly created specification is not completed work.

## Failure modes

- Reopening the terminal pilot instead of creating a new bounded successor.
- Marking the predecessor Done before successor relations and parent sequencing are wired.
- Leaving the parent train stale even though the child hierarchy changed.
- Making the target tracker a duplicate second copy of the control-plane specification.
- Treating issue creation as implicit approval to execute the re-pilot.
