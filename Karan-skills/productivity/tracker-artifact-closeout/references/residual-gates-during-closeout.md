# Residual gates discovered during tracker closeout

Use this reference when a final evidence sweep proves the original acceptance criteria but also discovers a material risk that was not represented in the issue body.

## Decision rule

Do not mark the parent Done merely because its original boxes can be checked. First classify the newly discovered fact:

- **No material effect / outside mission:** record it as a non-blocking observation.
- **Real but independently shippable:** create a bounded successor, link it, and state why parent closure is still honest.
- **Directly contradicts the parent's claimed outcome or closeout contract:** add one explicit residual gate to the parent and keep it open until disposition and readback.

Examples of the third case include a supposedly retired deployment hostname still serving the complete production site, an unverified rollback path, or a knowledge-closeout claim whose canonical page remains stale.

## Required sequence

1. Re-read the live issue and comments; count checked and unchecked criteria from the persisted body rather than from memory.
2. Run the final read-only proof against current state.
3. Reconcile original criteria only where evidence exists.
4. If a material residual appears, add one narrowly worded unchecked gate with:
   - exact observed state;
   - why it blocks the parent outcome;
   - explicit statement that the gate itself grants no mutation authority;
   - the approved execution lane or successor issue once one exists.
5. Persist a closeout comment containing evidence, durable-knowledge paths, and residual status.
6. Directly read back body, state, and comment ID. Report the exact checked/unchecked count.
7. After remediation, verify the live result first, then check the last box and move the issue to Done; read back Done before reporting closure.

## Authority fallback

When the user approves a bounded live provider/account action but the authenticated provider lane is unavailable, do not improvise with credentials or silently turn approval into deploy/merge authority. Use the previously stated fallback: create a scoped repository or ops implementation issue, preserve human review/merge/deploy gates, link it to the parent, and keep the parent open until live readback passes.

## Avoid

- Closing first and opening an unlinked cleanup issue later.
- Expanding a frozen parent with unrelated improvements.
- Treating a correct HTML canonical as equivalent to retiring a duplicate HTTP 200 hostname.
- Checking a knowledge-closeout box from an agent self-report without file readback.
- Reporting success from mutation output without re-fetching the tracker state.