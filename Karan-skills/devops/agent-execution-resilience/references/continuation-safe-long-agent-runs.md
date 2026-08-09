# Continuation-Safe Long Agent Runs

Use with `agent-execution-resilience` when a builder/reviewer chain may span a session or approach a tool/turn ceiling.

## Builder permission preflight

Before spending a frozen fix cycle:

- bind a clean isolated worktree to the reviewed full SHA;
- inspect the installed CLI's current permission modes;
- preserve host OAuth/keychain state and remove only explicit remote credentials not needed by the lane;
- use strict empty MCP plus task-scoped file tools and repo-native shell families;
- do not pair a mutating builder with a managed read-only/safe mode unless a disposable preflight proves edits and required commands work.

If the lane cleanly refuses permissions before any file/external mutation, verify the tree, PR, and blocker ledger are unchanged. Correct the launcher and retry inside the same cycle. This is launcher recovery, not another substantive builder attempt.

## Post-push continuation checkpoint

Write this before launching Reviewer A:

```markdown
- Repo / PR / branch:
- Cycle and maximum:
- Previous reviewed head:
- Current verified head:
- Local HEAD = remote branch = PR head = PR commit tail: yes/no
- Builder comment URL / author / signature readback:
- Changed paths and frozen-scope result:
- Baseline gates and exact counts:
- PR body / sole closing-linkage readback:
- Fresh packet and detached worktree paths:
- Completed current-head lanes and artifact URLs:
- Next required lane: A / B / Auditor / synthesis
- Remaining automatic cycle budget:
- No-merge/deploy/account-mutation boundary:
```

Keep this as temporary run state or a tracker handoff, not durable memory and normally not a committed product file.

## Budget gate

A final A → B → Auditor chain also requires packet refreshes, artifact extraction, exact-head checks, relay, ID readback, and synthesis. If the current execution budget cannot cover that, stop at the checkpoint before launching the next lane. On resume, inspect live PR/head and process state first.

If interruption occurs after launch:

- state the exact verified head and completed gates;
- name the running/completed lane and whether its artifact reached GitHub;
- mark all prior-head artifacts stale after a push;
- rerun a lost read-only lane on the same exact head with a fresh packet;
- never report merge-ready until all required current-head artifacts are live and read back.

## Read-only reviewer artifact recovery

When a hardened reviewer cannot write its requested `/tmp` body but prints a complete artifact:

1. Page the full process log; completion previews may omit the beginning.
2. Select one complete block from `ROLE=...` through the reviewer signature and matching `DONE:` marker; ignore duplicate partial echoes.
3. Materialize the returned body without changing verdict, blocker count, evidence, or recommendation.
4. Add only a clearly separated transport disclosure if the reviewer did not include one.
5. Recheck current PR head, role/runtime signature, and clean detached worktree.
6. Relay under the dedicated reviewer identity and read back by artifact ID.
7. Record the path as transport-only degradation.

Rerun instead of reconstructing when the body is incomplete, contradictory, stale, or unsigned.

## Final-cycle rule

After the configured final fix cycle, complete the current-head review triad. A remaining validated blocker escalates; no implicit extra cycle is opened. Green tests alone do not make an incomplete final chain merge-ready.
