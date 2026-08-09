# Completion notifications, relay parity, and human-visible milestones

## Completion is a state barrier

A background completion notification proves termination only. Immediately read the authoritative result, state journal, live PR head, worktree status, and immutable relay artifacts. Do this before unrelated work; a builder that pushed twenty minutes ago while the channel still says “active” is stale operational state.

## Channel-visible milestone contract

For Buzz-coordinated review loops, keep details in the originating thread but publish these milestones at channel root:

- builder/reviewer run started;
- blocker or fail-closed stop;
- repair pushed and new exact head;
- repository/protected-preview/browser gates complete;
- reviewer outcome;
- final merge-ready handoff.

Never describe reviewers as running unless a tracked reviewer process or live PID is active at the moment of the update. Say `prepared`, `gating`, `stopped`, or `awaiting launch` literally when that is the state.

## Artifact/final-verdict finding parity

The complete prepared artifact and final machine verdict must carry record-exact `FINDING:` entries: same ID, severity, and one-line summary. Numbered prose in the artifact plus machine-readable findings only in stdout is a transport failure. Fail closed, preserve the artifact, tighten the adapter prompt/preflight, reset only the invalid transport state, and rerun the affected role on the unchanged head. Never manually reconstruct or publish an informal formal verdict.

## Factual `needs-Karan` recovery

Reserve `needs-Karan` for real product, taste, legal-authority, or scope decisions. A timestamp, signed event, head, deployment ID, or source-comment date is a retrievable fact. Resolve it from the direct source and record conservative evidence.

When valid code blockers coexist with a factual item that stopped automatic builder routing:

1. resolve the fact from its direct source;
2. build a bounded packet containing only demonstrated code blockers;
3. invoke the configured trusted builder in the clean PR worktree within the remaining repair budget;
4. require commit/push/comment and local/remote/PR/final-commit identity;
5. freeze the new head and rerun every invalidated gate and ordered reviewer lane.

This recovery must not bypass a genuine human decision, regain an exhausted repair cycle, or weaken the stopping rule.
