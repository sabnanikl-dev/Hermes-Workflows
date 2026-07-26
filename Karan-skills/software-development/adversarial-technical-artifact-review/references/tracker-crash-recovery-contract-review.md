# Tracker-Governed Crash-Recovery Contract Review

Use this reference when a Linear/GitHub work order governs a task-scoped worker, grant, temporary capability, or recovery loop.

## Why unit tests are insufficient

A fixture may write residue more securely than the production producer. A real dogfood run found exactly this class of mismatch: the diagnostic required a private manifest while the producer created the live manifest with a permissive default mode. Synthetic tests passed because their helper explicitly used the safe mode.

The durable rule is: **exercise the real producer, then inspect with the real consumer.**

## Minimal live dogfood sequence

1. Freeze the approved issue body and digest.
2. Record and directly read back one valid approval and one valid claim.
3. Launch a sanitized, no-credential worker with one harmless temporary skill.
4. At a named checkpoint, directly verify:
   - wrapper lock is active;
   - consumed grant exists;
   - task-skill directory and manifest exist;
   - manifest owner, mode, hard-link count, path type, run/root/issue/digest binding are valid.
5. Deliberately terminate both wrapper and child so no orphan worker remains.
6. From a fresh process/session with no chat-history dependency, independently reconstruct:
   - live tracker result (normally resume the active claim);
   - local residue classification;
   - exact safe next checkpoint.
7. If residue is unsafe or unknown, inspect it first. Do not coerce or delete it silently.
8. Recover only with exact grant/run/root/issue/digest confirmation and no active lock.
9. Read back global clean state, retry recovery, and retry the consumed grant. The latter two must not create work or delete anything new.
10. Complete with a new one-time grant, then prove automatic cleanup and an ungranted worker cannot recover grant metadata, credentials, or temporary skills.

## Reviewer packet

Freeze and hash:

- full current issue/work-order body;
- live approval, claim, state, relations, comments, pagination, and adjacent-issue boundaries;
- implementation and tests;
- test commands/results;
- interruption checkpoint and process IDs;
- fresh-session classifications;
- recovery command/readbacks;
- replay/no-op results;
- final cleanup and ungranted probe.

Require the independent reviewer to evaluate every clause and acceptance criterion as `PASS`, `FAIL`, `NOT YET`, or `NOT APPLICABLE`. A final evidence comment and status transition may be `NOT YET` while their prerequisites are under review; that is not a pass for Done.

## Gate

- P0/P1 findings block control-plane advancement.
- Any edit to reviewed implementation, tests, or contract bytes invalidates the prior pass.
- Never infer reviewer PASS from process exit alone; read the report and its exact final marker.
