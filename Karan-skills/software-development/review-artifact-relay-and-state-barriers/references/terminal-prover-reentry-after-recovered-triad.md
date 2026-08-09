# Terminal prover re-entry after a recovered review triad

Use this only after `manual-lower-level-triad-recovery.md` has restored a complete, parser-valid, immutable-ID-read-back Reviewer A → Reviewer B → Integration Auditor chain for an unchanged exact head, but the original prover process is terminal and the recovered triad found blockers while one bounded builder cycle remains.

This is a narrow bridge back into the shipped control plane. It is **not** permission to reset the repair budget, edit a terminal journal into a resumable state, or maintain a parallel hand-built prover.

## Eligibility

All must be true:

1. The original run stopped for transport/control-plane reasons after its gates passed.
2. The recovered triad is complete and ordered; each artifact passed canonical parsing, pre-publication sanitization, immutable-ID readback, exact-byte/digest comparison, and exact-head checks.
3. Local worktrees, remote branch, and live PR all still name the same reviewed SHA.
4. The repair cap proves one cycle remains. Do not infer this from memory; read the durable state journal.
5. The recovered blocker set contains only code/documentation findings on that reviewed head—no `needs-Karan`, live-system, credential, merge, deploy, or client-facing action.
6. No unresolved human `CHANGES_REQUESTED` review is being laundered through acknowledgement bookkeeping.

If any condition fails, stop for Karan or start a normal supported run as appropriate.

## 1. Freeze one deduplicated blocker ledger with shipped types

Parse every lane's exact final output with `parse_reviewer_verdict`, combine the resulting `Finding` objects, and deduplicate/classify them with the shipped `classify(...)`. Preserve every lane origin and classification lineage.

Build the builder file in the shipped blocker schema (`schema_version`, repo/PR/branch/base/head, attempt, mode, blocker records, contract). Apply the same recursive sanitizer used by the prover and round-trip the classified records through `Classification.from_dict(...)`.

Important boundaries:

- assert the expected blocker IDs explicitly;
- do not copy prose summaries into a hand-authored substitute finding;
- do not fabricate `next_instructions` records the terminal run never produced;
- do not include non-blocking, false-positive, or needs-Karan findings in builder scope;
- keep the ledger outside the repository and bind it to the exact old head and remaining attempt number.

## 2. Invoke the shipped builder adapter once

Create a fresh, absent, detached worktree at the reviewed SHA and unique stdout/stderr paths. Invoke the same configured builder adapter, signature, branch, mode, MCP config, credential-unset list, and realistic timeout the prover would use.

Use `set -o pipefail` around any pipeline. A notification or watcher proves only termination; after exit inspect:

- authoritative stdout and stderr;
- worktree cleanliness and new local HEAD;
- remote feature-branch HEAD;
- live PR `headRefOid` and PR commit list;
- the signed fix comment's immutable ID and direct API readback.

Parse stdout/stderr with `parse_builder_report(...)`. Require `STATUS=success`, the exact PR/branch/new full SHA, and an `ADDRESSED:` set equal to the frozen blocker IDs. Then verify the signed comment was posted after invocation by the configured builder identity and contains the exact new SHA/signature. A self-report, local commit, or remote branch alone is insufficient.

## 3. Reconcile recovered run-owned artifacts exactly

Before a fresh final verifier can inspect live feedback, acknowledge only the exact immutable IDs that the recovery proved were run-owned:

```text
PR-PROVER: ACKNOWLEDGED <immutable numeric id>
```

Post one pure machine-readable acknowledgement per recovered A/B/Auditor artifact and the verified builder comment, then read every acknowledgement back by its own immutable ID and require exact body/author equality.

Do **not** use this for human feedback or to clear a formal `CHANGES_REQUESTED` state. Resolve formal reviews through GitHub's native review semantics first; an ineffective ACK can itself become unresolved prose.

## 4. Start a final-verifier-only run without restoring fix budget

Create a fresh run root and fresh worktree/evidence/report namespaces. Copy only the validated config/helpers needed for the new run and rewrite every run-root/worktree-root path. Search for stale predecessor paths, run `check-config`, parse JSON, compile helper scripts, and verify the live new head.

Do not edit the terminal journal. Seed the fresh verifier journal through the shipped `RunState` API with:

- `attempt=MAX_ATTEMPTS`;
- `head=<verified new live PR head>`;
- `phase=idle` and `attempt_head=None`;
- `outcome=None` and `classification=None`;
- no invented run-owned artifact evidence.

Then save and reload it through `RunState.load(...)`. This preserves the exhausted repair budget structurally: the run can execute all gates and the ordered final triad, but it cannot open another builder cycle. If findings remain, it must report `blocked`; if none remain and feedback is reconciled, it may report `merge-ready` for Karan's decision.

Never seed `attempt=0` or `1` after consuming the final cycle. Never copy an `outcome` or stale classification into the verifier journal. Never mark an attempt in flight when the push/comment readback has already been independently completed.

## 5. Final acceptance

The fresh verifier must re-run every exact-head gate because the builder push invalidated all old gate and reviewer evidence. It must then run Reviewer A → readback → Reviewer B → readback → Integration Auditor → readback on the new SHA.

Before reporting:

- verify local source, remote branch, PR head, each packet, each reviewer artifact, and terminal report all bind to one SHA;
- inspect the final state/report rather than trusting process exit alone;
- perform stable feedback reads;
- update the tracker only with read-back evidence;
- preserve Karan as sole merge authority.

## Failure modes

- **Process handle becomes ambiguous:** inspect the real PID/process tree and attach one watcher; do not duplicate the lane.
- **Compound POST returns an ID then local validation fails:** read that exact ID back; do not retry the POST.
- **Fresh verifier asks for old feedback resolution:** confirm each recovered artifact's immutable ID was acknowledged exactly; never broaden login-based exemptions.
- **Head drifts before builder relay or verifier launch:** discard the old-head bridge and start a normal exact-head run.
- **Verifier finds blockers at the exhausted cap:** report blocked. A third manual builder invocation would violate the lifecycle.
