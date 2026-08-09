# Finite Exact-Head Contract Reset After Validator Scope Inversion

Use this when the committed product repeatedly proves correct, repair cycles are exhausted, and reviewers keep discovering adjacent hypothetical checker bypasses. This is an alternative to another mutant-expansion cycle or a clean replacement when the existing PR can be closed out without changing repository bytes.

## Preconditions

All must hold:

- The normal review/fix cap and any approved bounded exception are spent.
- The latest findings concern speculative guard completeness, not a demonstrated defect in the exact-head product.
- Product, privacy, security, accessibility, no-egress, and authority boundaries can be proved directly with trusted semantics.
- The human merge authority explicitly approves narrowing/resetting the verification contract.
- No merge, deployment, or live mutation is implied by the reset.

If a finding demonstrates an actual-head acceptance-criterion failure, this procedure does not apply.

## Required separation

Write the reset around four independent layers:

1. **Exact-head artifact correctness** — facts about the committed product now.
2. **Finite guard coverage** — the named regression corpus the checker actually promises.
3. **Claim honesty** — docs and diagnostics must not claim general parser or accessibility-tree completeness.
4. **Deferred hardening** — hypothetical checker bypasses outside the finite envelope become follow-up proposals, not automatic blockers.

Do not say “the checker is sound” merely because a direct product probe passes. Say which product facts were proved and which generalized guard work was deferred.

## Procedure

### 1. Freeze the exact head and product hashes

Verify local worktree, remote branch, PR head, and final PR commit agree. Hash every product/authority file that the reset promises not to change. Keep the PR open and unmerged.

### 2. Build direct semantic probes outside the repository

Use the real semantic engine for each disputed product fact instead of widening the committed checker.

For active HTML wiring:

- parse every committed runtime-enabled page with the repository's locked HTML parser;
- count only active script nodes in document order;
- do not traverse comment text or inert `template.content` as active evidence;
- execute and parse generated template surfaces, not only their source substrings;
- include an oracle control where an active script counts as one and the same script inside a comment counts as zero.

For browser accessibility:

- load the exact committed page bytes in the real browser harness;
- query by browser role and exact accessible name, not manually resolved DOM text;
- run every contract viewport;
- record an accessibility snapshot when supported;
- add a reversible negative control: temporarily set `aria-hidden=true`, require the role/name query to return zero, restore it, and require one again;
- keep all network interception/no-egress protections active.

A temporary Node ESM probe that lives outside the worktree should resolve project dependencies from the exact-head worktree (for example, `createRequire(path.join(ROOT, "package.json"))`) rather than from the temporary script's directory.

### 3. Bind the probe result

The result must record:

- repository, PR, and exact head;
- product-file hashes;
- parser/browser versions or oracle identity;
- governed committed and generated surfaces;
- positive and negative-control outcomes;
- viewport coverage and no-egress count;
- PASS/FAIL.

Hash both the probe script and result. Confirm the repository worktree remains clean.

### 4. Amend the governing contract, not just chat

Put the human-approved finite closeout amendment in the canonical issue/spec surface that reviewers consume. State:

- original product acceptance criteria remain binding;
- the finite exact-head facts that remain merge-blocking;
- the checker domain that is intentionally finite;
- named hypothetical bypasses reclassified as follow-up proposals after direct probes pass;
- new hypothetical mutations are follow-ups unless they demonstrate an actual-head acceptance failure;
- no further checker, mutant-count, evidence-schema, or product expansion is authorized in this PR.

Include the exact head, product hashes, direct-probe summary, and probe/result hashes. Read the canonical body back, verify one amendment marker pair, and verify its complete body digest before claiming the reset landed.

### 5. Reconcile prior review artifacts with two separate posts

Do **not** combine substantive reset evidence and control acknowledgements in one PR comment. PR Prover can correctly classify such a post as `acknowledged-and-raised-more`: the ACK lines resolve earlier artifacts, but the new contract/evidence prose is itself fresh feedback that no later artifact has resolved. Operator pinning proves the post's identity and bytes; it does not make substantive text self-resolving.

Use this sequence:

1. Post one substantive PR comment that links the canonical amendment, summarizes the direct evidence, records the classification change, and preserves human-only merge authority.
2. Post a **later ACK-only control comment** with one `PR-PROVER: ACKNOWLEDGED <artifact-id>` line for the substantive reset comment and every superseded reviewer/builder artifact required by the workflow.
3. Read back both comments and pin their exact body evidence for the final run.
4. If the ACK-only comment is edited to add IDs, re-read it and replace its pinned body digest before running again.

The ACK-only post is a machine reconciliation artifact, not a social “thanks/agreed” reply; the general preference against bare acknowledgements does not apply to this exact control protocol.

### 6. Run one read-only final triad

Create a fresh exact-head review run that consumes the amended governing contract and reconciled feedback. Mechanically disable builder mutation with a tested refusal guard. The final triad may only:

- pass under the finite contract; or
- stop for human judgment if it demonstrates an actual-head failure or misapplies the amendment.

It must not silently reopen another repair cycle. A reviewer idea outside the finite envelope is classified as deferred hardening unless it proves the original issue is unmet.

### 7. Recover a feedback-only controlled stop without reopening the product loop

A run may have both gates passing and all three reviewers at `pass` with zero blockers, yet exit `2` / `needs-karan` because the feedback barrier reports one `acknowledged-and-raised-more` post. Read the report's exact `fail_closed.reason`, unresolved artifact ID, and `why` field before classifying the exit.

If the only failure is feedback reconciliation:

1. Preserve the successful output, error, and state artifacts before changing run state.
2. Add/update the later ACK-only post to acknowledge the unresolved substantive post and the just-published reviewer artifacts; read it back and refresh its pin digest.
3. Inspect the installed CLI's supported commands; do not assume a `resume` subcommand exists.
4. If continuation is unsupported, and the human-approved reset authority already covers a same-head read-only replay, reset **only** prover state and rerun the unchanged read-only config. Do not launch a builder or broaden the finite contract.
5. Require the replay to report stable feedback surfaces, `merge-ready`, zero blockers, zero builder attempts, exact-head currency, and complete artifact transport.

An unsupported continuation invocation is a local operator error and consumes no builder/review cycle when it changes no repository or remote state.

## Verification checklist

- [ ] Human approval for the reset is explicit.
- [ ] Exact head agrees across local, remote branch, PR head, and commit list.
- [ ] Product hashes are recorded and unchanged.
- [ ] Direct semantic probes use trusted parser/browser behavior.
- [ ] Positive and negative oracle controls pass.
- [ ] Full product gates and no-egress evidence still pass.
- [ ] Probe script/result hashes are recorded.
- [ ] Canonical issue/spec amendment is read back and digest-verified.
- [ ] Prior feedback is reconciled through a substantive reset post followed by a later ACK-only control post.
- [ ] Both posts are read back and pinned by current body evidence; edited ACK posts have refreshed digests.
- [ ] Final triad is read-only; builder mutation is mechanically refused.
- [ ] A feedback-only controlled stop is not misreported as a product/reviewer failure, and any replay preserves the successful first-run artifacts.
- [ ] Merge remains a separate human decision.

## Pitfalls

- **Contract reset without direct proof:** prose cannot reclassify a real defect.
- **PR comment only:** reviewers may still consume the unchanged governing issue body.
- **Substantive ACK post:** combining evidence prose and ACK lines leaves the new prose unresolved as `acknowledged-and-raised-more`; follow it with a later ACK-only control post.
- **Assumed continuation command:** inspect the installed PR Prover CLI before using `resume`; preserve artifacts and perform an approved same-head state reset/replay when continuation is unavailable.
- **Manual DOM-name reconstruction:** this repeats the accessibility false pass; use browser role/name semantics.
- **Parsing generated template source as HTML:** execute the renderer and parse its output.
- **Uncontrolled probe mutation:** negative controls must be reversible and leave repository bytes clean.
- **Another automatic builder:** a reset exists to terminate checker churn, not authorize one more hidden cycle.
- **Universal claims after narrowing:** describe finite repository policy honestly; do not replace one overclaim with another.
