# Operator ACK feedback resume and process tracking

## Exact-ID bridge for shared publisher identities

When every available authenticated GitHub identity is also configured as a publisher, login-wide denial can leave no identity capable of submitting a usable acknowledgement. Preserve the denial and authorize exact posts instead.

1. Read each historical target comment from GitHub and verify immutable numeric ID, author, exact body, chronology, URL, and PR.
2. Publish one **pure bookkeeping** comment containing only canonical lines:

   ```text
   PR-PROVER: ACKNOWLEDGED <earlier-comment-id>
   PR-PROVER: ACKNOWLEDGED <another-earlier-comment-id>
   ```

3. Read the new comment back and verify exact body, author, ID, URL, and creation time.
4. Put only the new bookkeeping comment's immutable ID in `operator_acknowledgements` for the fresh run.
5. Run `check-config`; require it to name that exact ID and emit the post-specific authorization advisory.

Never pin a login, wildcard, pattern, or lane artifact created by the same run. Do not add explanatory prose to the bridge comment: residual prose becomes feedback.

### Substantive contract-post trap

Do not combine a contract reset, probe summary, classification rationale, or status update with canonical ACK lines. The reconciliation engine can correctly classify that post as `acknowledged-and-raised-more`: its ACK targets are cleared, but its added substance is new feedback. Evidence-pinning the exact post authorizes its ACK lines; it does **not** resolve the substantive text in the same body.

Use two chronological artifacts instead:

1. Publish the substantive contract/evidence comment with no ACK lines.
2. Publish a later ACK-only bridge containing exact canonical lines for the substantive post and all earlier artifacts already reviewed.
3. Read back and evidence-pin only the dedicated bridge.

If an exact-head run already completed green gates and a zero-blocker A/B/Auditor triad before stopping on this feedback condition, report those layers separately from the control-plane stop. Preserve its output/error/state, add the later pure bridge, and inspect the installed CLI's help before choosing recovery. When that version exposes reset-and-rerun rather than resume, confirm no run is active, use existing reset authority to remove only the terminal prover state, and rerun the unchanged exact-head config. Do not relaunch a builder or count a repair attempt.

A formal `CHANGES_REQUESTED` review cannot be cleared by an ACK. Require a later exact-head `APPROVED` or `DISMISSED` review from the same GitHub author.

## Fresh-run feedback boundary

Run-owned artifact retention is journal-scoped. When a terminal run cannot resume and a fresh state file is required, earlier Reviewer B/Auditor comments and builder summaries are ordinary live feedback to the new run.

Before launching fresh:

- inventory old conversation comments, formal reviews, and inline threads;
- map ordinary historical comments through the pure ACK bridge;
- leave formal review resolution to native GitHub review state;
- use a unique state file, lock file, and worktree root;
- never copy/edit the terminal journal into a new outcome;
- verify the PR head remains unchanged after bridge publication.

## Immutable publication identity vs mutable evidence ownership

These are different safety questions:

- `owns(item)`: does the artifact still match the content/state readback the run verified? It may become false after mutation so edited prose re-enters feedback classification.
- `published(item)`: did this run ever publish this immutable GitHub ID? It must stay true after mutation so the artifact can never gain ACK authority.

A dangerous guard is:

```python
if self.owns(item):
    return False
```

If content mutation makes `owns()` false, exact-ID pinning may then authorize a valid edited ACK. The acknowledgement guard must use immutable run-publication identity.

### Required mutation probe

1. Retain a verified lane artifact ID and its original publication evidence.
2. Edit the same ID into syntactically valid `PR-PROVER: ACKNOWLEDGED <human-id>` content.
3. Pin that immutable ID.
4. Prove:

   ```text
   owns(edited) == false
   published(edited) == true
   may_acknowledge(edited) == false
   ```

5. Reconcile and require zero clearance plus unresolved human feedback.
6. Exercise the real config → loop → publication readback → feedback path. A malformed-line edit is not sufficient proof.

## Additive tracker clarification

If an open issue AC narrowly contradicts the normative lifecycle:

1. Verify the contradiction against the issue, mission, tests, and live behavior.
2. Append a dated clarification to both GitHub issue and Linear child; do not erase historical wording.
3. State exactly which phrase is superseded and which safety invariants remain unchanged.
4. Read both trackers back directly before routing repair.
5. Keep contract clarification separate from implementation blockers.

Never use clarification to weaken run-owned denial, expand merge authority, or erase review evidence.

## Detached child watchdog

A background handle can report `exited` with a null exit code after `exec` while the real PR-Prover or Claude PID remains alive.

Before relaunching:

1. Inspect the process table for the exact command/config path.
2. Inspect output/error file sizes and state-file presence.
3. If the real child is alive, do not duplicate it.
4. Attach a bounded watchdog:

   ```sh
   while kill -0 "$pid" 2>/dev/null; do sleep 15; done
   printf 'PROCESS_%s_EXITED\n' "$pid"
   ```

5. After exit, validate the retained report, signed marker, local/remote/PR head equality, PR commit list, GitHub artifact readback, and tests.

Avoid wrappers that can mask the tool's return code. In zsh, `status` is read-only; use `rc` if an outer shell must capture a code, or invoke the tool directly.

## Repair-cycle accounting

Count a repair cycle only when a bounded builder produces a real repair commit/push attempt against the frozen ledger. CLI usage errors, unreadable config paths, detached-wrapper confusion, or launches that produced no commit do not consume the product's repair budget. Verify the absence of local/remote head change and PR comments before declaring the attempt non-consuming.
