# Evidence inheritance across harmless head changes

Use this when a reviewed Git head changes but the new commit does not alter the bytes or environment that produced an expensive artifact such as browser screenshots, visual QA, a generated report, PDF, or runtime evidence.

## Principle

Reviewer verdicts are exact-head decisions and become historical after any code commit. Producer artifacts are different: their validity follows their complete controlling inputs. A docs/checker-only commit does not make rendered-site screenshots stale when every site/runtime/style/fixture byte remains identical and the evidence contract permits reuse.

## Required proof

1. Record the original evidence-producing head and the new candidate head.
2. Enumerate the artifact's complete controlling path set: product markup, CSS, browser/runtime code, producer/config, fixtures/data, viewport parameters, fonts/assets, and any other input the artifact claims to observe.
3. Require an exact old-head→new-head diff over that complete set to be empty.
4. Re-run any shipped binder/hash validator; it must accept the committed evidence unchanged.
5. Freeze a new review packet under the new head containing:
   - original evidence head;
   - exact empty controlling-path diff command/result;
   - current narrow repair delta;
   - fresh live PR/review/comment/check state;
   - a new packet manifest/digest.
6. Label the artifact precisely: **preserved from `<old-head>` and byte-valid at `<new-head>`**. Never call it newly captured or fresh exact-head evidence.
7. Require reviewers to verify the controlling-path inventory and confirm no changed input escaped it.

## Packet hygiene

- Use head-keyed packet, worktree, prompt, and result paths.
- Refuse to overwrite a prior frozen packet; preserve it for auditability.
- Treat stale hard-coded heads as a launch blocker and update the packet builder before proceeding.
- Finalize live surfaces and inheritance metadata before hashing the new packet.

## Regenerate instead when

Regenerate if any controlling byte changed, the environment materially differs, the original artifact is incomplete, its binder fails, or acceptance criteria explicitly require a new observation rather than byte-equivalent evidence.

Do not use this exception for reviewer verdicts. A/B/Auditor outputs must be rerun on the new head unless the governing workflow explicitly permits a metadata-only review exception.
