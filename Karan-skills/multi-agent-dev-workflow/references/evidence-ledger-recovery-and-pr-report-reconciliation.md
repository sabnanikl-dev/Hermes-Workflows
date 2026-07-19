# Evidence-ledger recovery and PR-report reconciliation

Use this when a long-running browser/API rollout has checkpoints that became terminal outside the normal batch ledger, or when late review fixes leave PR metadata stale even though code/docs are correct.

## Recover missing audit records without inventing history

A completed evidence artifact is not automatically an auditable rollout. Reconcile three sources:

1. **Base evidence** at the PR base (`origin/main` or the PR base SHA).
2. **Current evidence** at the exact PR head.
3. **Run ledger** records for preflights, crashes, resumes, and clean batches.

Compute the set of models/slots that changed from pending/missing on base to terminal on head. Require that every newly terminal item appears exactly once in the union of ledger phases. Do not validate a recovery record only against its own declared IDs; that tautology cannot detect omitted evidence.

Recommended phase model:

- `recovered-preflight` — an observation completed before the normal driver/ledger began;
- `crashed` — a partially completed driver that exited through infrastructure failure;
- clean batch records — normal command/start/end/exit/model records;
- `skipped` — an explicit no-work resume after all requested IDs are already terminal.

Keep phases separate. Do not fold an earlier preflight into a later crash merely to make totals add up.

### Unknown fields stay unknown

If the original wrapper failed to preserve command or process timing:

- use explicit `null`/`unknown` fields;
- record the exact evidence-slot timestamps and outcomes that are still authoritative;
- add provenance explaining how the model was identified (for example base-vs-head delta plus the next driver’s already-complete count);
- label the record as recovered;
- never synthesize a plausible command, start time, end time, or exit code.

Before asking the builder to repair the ledger, post the recovered facts as a signed PR-bus comment and read it back. Keep the fix prompt pointer-first so the PR remains the coordination source of truth.

## Fail closed on explicit operator input

Validate explicit `--models`/item IDs against the candidate contract **before** deciding that there is no work:

- any unknown ID must exit nonzero;
- mixed valid + unknown selections must also fail;
- no `skipped`/success audit record may be written;
- evidence must remain byte-for-byte unchanged.

Regression coverage should drive the real wrapper against throwaway fixtures and assert exit status, unchanged evidence, and unchanged ledger.

## Reconcile present-tense reports after every fix

The PR description is a review surface and an operator handoff, not decorative prose. After each fix/re-review cycle, compare these present-tense surfaces against the exact current head:

- PR description counts, ledger phases, commands, timestamps, and verification claims;
- evidence `run.note` / summary notes;
- source packet, spec/build plan, and friction log;
- generated artifact counts and test output;
- reviewer/fix comments that claim current state.

Preserve clearly labeled historical notes, but update stale current-state claims. A final reviewer can correctly block an otherwise-good PR if its description still reports an earlier ledger count.

### Metadata-only blocker at the cycle limit

If the normal two builder fix cycles are exhausted and the only remaining blocker is stale PR metadata:

1. Verify code head is unchanged, tests/checks are green, and the committed artifact/docs already contain the correct state.
2. Hermes may perform the narrow PR-description correction as PR hygiene; do not start a third code cycle or modify the branch.
3. Read the edited PR body back from GitHub.
4. Rerun the reviewer lane that raised the metadata blocker on the unchanged head.
5. Keep the other reviewer’s current-head pass only when the code head is unchanged and its review area was unaffected.

This exception does not permit code fixes past the cycle limit and never permits merge without the human gate.

## Carrying visual proof across non-UI fixes

Exact-head visual evidence may remain valid across later audit/docs-only commits only after proving the rendered surface is unchanged, for example:

```bash
git diff --quiet <visual-proof-head>..HEAD -- site/
```

If the rendered surface changed, recapture. If it did not, state that the proof was captured earlier and that `site/` is byte-identical across the later commits.

## Final closeout

Before merge-ready:

- local HEAD = remote branch HEAD = PR `headRefOid`;
- checks and full tests are green;
- base-to-head evidence delta is fully covered by the ledger;
- PR description matches the  exact ledger/artifact state;
- Reviewer A and B have role-signed no-blocker outcomes bound to the current head;
- review threads are empty/resolved;
- temporary status watchdog and helper script are removed;
- PR stays open/unmerged until the human approves.
