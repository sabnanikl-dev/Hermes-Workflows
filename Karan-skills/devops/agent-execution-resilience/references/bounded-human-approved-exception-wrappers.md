# Bounded human-approved exception wrappers

Use this after a normal autonomous PR repair budget is exhausted and Karan explicitly authorizes one more narrowly scoped builder pass. It is a recovery/control-plane pattern, not a generic cycle-counter reset.

## Freeze authority outside the ordinary run config

Record a machine-readable contract bound to:

- repository, PR, base/head branches, and exact approved head SHA;
- exact approved blocker IDs;
- one additional substantive builder attempt;
- allowed repository paths or path patterns;
- required behavior and proof commands;
- forbidden live/external actions and unrelated changes;
- a stop condition requiring one final exact-head triad with no automatic follow-on repair.

Keep exception-only fields in the external contract. Do not add unknown policy keys to the ordinary prover config; generate the config, then require the shipped config checker to accept it before launch.

## Put a fail-closed guard around the normal builder

The guard should parse the normal builder arguments and refuse unless repo, PR, base, branch, incoming head, attempt, mode, and frozen blocker IDs match the external contract. Require `attempt == 1` and `mode == initial`. The guard may create an augmented copy of the blocker file containing the approved path boundary, proofs, forbidden actions, and stop condition, then delegate to the repository-owned builder adapter. Do not replace the adapter's push, marker, or signed-comment protocol.

### Empty instruction arrays are valid

A schema-v2 blocker file created directly from reviewer findings may contain a complete `blockers` ledger and an empty `next_instructions` array. Validate authority from the structured blocker IDs. If instructions are absent, derive exactly one narrow instruction per approved blocker from its frozen ID, summary, origins, and head. Fail closed on unknown or duplicate instruction IDs.

Do not reject an otherwise valid reviewer-finding ledger solely because `next_instructions` is empty. That creates a false cycle failure before the real builder starts.

## Disposable guard proof before launch

Exercise the exact guard with a stub builder and fixtures proving:

1. the approved ledger passes;
2. an empty-instruction ledger receives exactly one bounded instruction per approved ID;
3. any additional or unknown blocker is refused;
4. attempt 2 is refused before the real builder launches;
5. the augmented payload carries the contract and path/proof/stop bounds;
6. shell/JSON syntax and the shipped config checker pass.

A populated-instruction fixture alone is insufficient.

## Preserve prior state and reconcile feedback

Use fresh state, lock, worktree-root, output, and error paths for the exception run. Preserve the exhausted run as evidence instead of rewriting its finished state.

When old review/fix artifacts would trip the strict feedback barrier, read the exact comments, post a pure `PR-PROVER: ACKNOWLEDGED <id>` reconciliation record, read it back, derive its exact body evidence, and pin only that post ID. Never create a publisher-login-wide exemption.

## When a prelaunch error does not spend the approval

A guard/configuration refusal remains a control-plane prelaunch error—not a substantive builder attempt—only after proving all of these:

- the real builder adapter never launched;
- the worktree and repository files did not change;
- no commit, push, PR-body edit, or comment occurred;
- the PR head is unchanged.

Correct the guard, test the previously missed fixture, preserve the failed artifacts, and replay with fresh state paths. This is not available once Claude ran, mutated files, committed, or pushed.

## Close out after the one substantive pass

After a push:

1. verify the commit appears in the PR's remote commit list;
2. require retained-worktree head = remote branch head = PR head = final PR commit;
3. rerun canonical exact-head gates;
4. run the full Reviewer A → Reviewer B → Integration Auditor triad;
5. compare changed paths against the approved boundary;
6. verify the PR remains open/unmerged unless Karan separately approved merge.

If the final triad reports any blocker, including a new one introduced by the approved repair, the exception is spent. The attempt-2 guard must refuse mechanically. Report the exact head, passed gates, scoped diff, artifact links, and blocker. A further repair needs a new explicit contract bound to the new head and new blocker IDs.

GitHub's mechanical `mergeable` field never overrides a blocking exact-head triad.
