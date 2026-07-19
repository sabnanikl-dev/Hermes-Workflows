# Policy migrations: sweep every current contract, not only prose docs

Use this when a PR changes the meaning of an authority or gate—for example, separating source approval from destination-health evidence.

## Why this matters

A policy migration can pass runtime tests while stale instructions remain in machine-readable metadata or generator-owned fields. Those stale contracts can later regenerate the retired behavior or mislead another builder. Updating the main spec and visible runtime logic is not enough.

## Required sweep

After the first implementation and again after every fix cycle, inspect the full base-to-head state for both old terminology and old semantics across:

1. Human-facing current contracts: specs, build plans, source notes, runbooks, friction summaries.
2. Machine-readable contracts: JSON metadata, `authority`, `gate`, `consumptionContract`, `preserved`, `rule`, and similar instruction-bearing fields.
3. Generator sources: constants, copied/spread metadata, templates, defaults, and passthrough fields that can silently restore stale output.
4. Validators: positive assertions plus negative self-tests proving the retired policy is rejected.
5. Runtime/file headers and HTML comments: comments are durable implementation guidance even when they do not change rendering.
6. Generated artifacts and candidate/source contracts consumed by later generators.
7. PR body/current-state evidence when it repeats counts or gate language.

Search by **semantic family**, not one exact phrase. Include legacy field names and status words such as `enabled`, `disabled`, `pending`, `verified`, `gate`, `must not render`, and historical count pairs. Also search the **naming layer**: section headings, ownership labels, schema keys, top-level metadata notes (including JSON `"//"` fields), validator error strings, generated-file headers, and comments describing who “owns” or “enables” a state. A retired policy can survive entirely in names such as `evidenceEnablementOwner` even when the surrounding prose is correct.

Trace every current machine-readable hit back to its writer. Look specifically for object spreads and passthroughs such as `...committed`, `...existing`, preserved metadata shells, template defaults, and seed-when-absent logic. If the generator merely carries an instruction-bearing field forward, make that field generator-owned under the new policy; otherwise regeneration can preserve the contradiction forever.

Classify each hit:

- **Current contract:** rewrite to the new authority.
- **Current name/schema:** rename or explicitly deprecate it; update all consumers and validator messages so the old authority is not implied by the API itself.
- **Generator-owned current contract:** fix the generator first, regenerate, and validate byte stability.
- **Historical observation:** preserve only when explicitly labeled historical/superseded and impossible to mistake for current instructions. A supersession banner must precede or directly qualify stale headings and present-tense instructions—not appear many paragraphs later.
- **Negative regression fixture:** retain as an intentionally rejected example; make searches classify it as a fixture rather than repeatedly treating it as live policy.

## Pre-review closure matrix

Before launching A/B reviewers, build one exhaustive inventory instead of fixing the first grep hit and starting another micro-cycle. At minimum, account for:

| Surface | Closure question |
|---|---|
| Specs/build plans/source notes | Are headings, opening sentences, current summaries, and ownership statements aligned? |
| JSON/schema | Are key names, top-level notes, owner fields, rule/note/preserved fields, and counts aligned? |
| Generators | Does every instruction-bearing output field have an explicit current-policy writer rather than passthrough preservation? |
| Validators | Do positive guards require the new policy and negative fixtures reject the old semantic family and naming variants? |
| Runtime/generated files | Are file headers, comments, action maps, and generated artifacts aligned and reproducible? |
| Historical material | Is every retained old statement immediately and unmistakably labeled historical/superseded? |
| PR metadata | Does the body/comment evidence describe the exact current head rather than an earlier cycle? |

Do **not** launch reviewers while any search hit remains unclassified. A broad semantic census before review is cheaper than serial reviewer/fix cycles and avoids exhausting the tool budget on one-line contract remnants.

## Verification pattern

1. Regenerate artifacts from their real sources.
2. Run generation a second time and require no diff.
3. Add validator checks for instruction-bearing metadata and schema names, not only data rows.
4. Add negative fixtures that inject both the retired wording and plausible naming variants, then prove rejection.
5. Run a whole-branch semantic sweep after generation; classify every remaining hit as current, historical, or negative fixture.
6. Inspect the complete base-to-head diff and the final generated files before launching reviewers.
7. Have reviewers inspect the **full current-head diff**, not only the follow-up commit.
8. Do not call a reviewer cycle clean until both role-signed outcomes are on the exact current `headRefOid`.

## Whole-document rule

A correct #186/current-policy section later in a document does **not** neutralize an earlier present-tense instruction. Read every current contract from top to bottom, including provenance notes, headings, opening sentences, sidebars, ownership summaries, and handoff paragraphs. If an older sentence remains operational rather than immediately labeled historical/superseded, treat it as a blocker even when a later section states the new policy correctly. This prevents serial one-line reviewer discoveries in long source packets.

## Exact-head merge-readiness certificate

After the final fix and both reviewer processes exit, re-query live GitHub and require one coherent certificate before reporting merge-ready:

- PR `headRefOid` equals the independently verified local `HEAD` and remote branch SHA.
- Both role-signed Reviewer A and Reviewer B outcomes are `APPROVED` on that exact commit. When both roles share one GitHub account, read the full reviews API and filter by `commit_id` + signature; `latestReviews` can collapse one role.
- `reviewDecision == APPROVED`, `mergeable == MERGEABLE`, and `mergeStateStatus == CLEAN`.
- Required/status checks are successful.
- GraphQL review threads contain no unresolved nodes.
- `closingIssuesReferences` matches the intended issue-close policy.
- Worktree is clean and `git diff --check` passes.

Old `CHANGES_REQUESTED` reviews on prior commits are audit history, not current blockers, only when the exact-head approvals and aggregate `reviewDecision` above are both verified. Do not infer readiness from reviewer stdout or a fix-summary comment alone.

## Review-loop budgeting

A same-class stale-contract finding may expand from prose to nested metadata, generator passthroughs, runtime headers, and candidate contracts. Before starting a fix cycle, reserve enough execution budget for the complete chain: builder fix → regeneration → full verification → current-head A/B re-review → live GitHub readback. If that chain cannot be completed, stop at a verified checkpoint rather than launching an unverified final cycle.
