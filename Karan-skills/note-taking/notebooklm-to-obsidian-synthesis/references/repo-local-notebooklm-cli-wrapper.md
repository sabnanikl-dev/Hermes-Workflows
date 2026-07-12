# Repo-local NotebookLM CLI wrapper pattern

Use when a project harness needs agents to query NotebookLM notebooks from inside the repo, especially when the global NotebookLM CLI exists but agents need safer defaults and project-specific grounding.

## Pattern

1. Add a repo-local wrapper script rather than teaching agents to hand-type raw NotebookLM commands.
   - Keep it read/query-only by default: auth check/refresh, list notebooks, list sources, ask, and project/client-scoped query.
   - Do not expose create/delete/share/source-mutation subcommands unless the user explicitly asks for that authority.
2. Default to the known local CLI path when stable, but allow an override such as `NOTEBOOKLM_BIN`.
3. Add `smoke` and `auth --refresh` commands.
   - `smoke` should verify CLI presence, version, auth status, and notebook listing.
   - `auth --refresh` can refresh from the user's browser-cookie profile when that is the established workflow.
4. For repo/client-scoped queries, inject a compact current-state digest from source-of-truth files.
   - NotebookLM cannot see the repo unless the wrapper provides context.
   - Keep prompts compact; long file dumps can trigger empty/parse-failed streaming responses.
   - Prefer selected key lines/headings over full files.
   - Do not include raw `git status --short` output in NotebookLM prompts; dirty/untracked files from the current implementation can confuse the model and leak irrelevant state.
5. Save query transcripts under the repo's reports/client reports area when useful, but do not commit raw NotebookLM output as strategy or issue text. Distill findings.
6. Document grounding and approval boundaries in repo docs and root agent guidance.

## Prompt hygiene

A good wrapper-generated prompt includes:

- notebook/source role: “use notebook sources for external/domain principles”;
- repo/client digest role: “use this only as current implementation context”;
- live-state caveat: do not invent GSC/GBP/rank/traffic/account data;
- authority gate: NotebookLM recommendations do not approve live changes or GitHub issue creation;
- compact task/focus;
- requested concise output shape.

## Verification

When adding or changing the wrapper, run an ad-hoc verifier if the repo has no canonical test suite:

- create a temporary script with a `hermes-verify-` prefix using `tempfile` under the requested OS temp directory;
- compile/import the wrapper;
- assert auth-status parsing behavior;
- assert client/repo prompt contains required grounding and approval-boundary text;
- include expected-red assertions for old bad behavior, such as prompt leakage of `git status --short` lines or untracked wrapper files;
- exercise path display/truncation helpers with external temp files, because repo-relative `Path.relative_to(ROOT)` calls fail outside the repo unless guarded;
- clean up the temp verifier and print `TEMP_SCRIPT_EXISTS_AFTER_CLEANUP=False`.

## Pitfalls

- Do not turn a NotebookLM wrapper into a live-action/account-mutation tool by accident.
- Do not treat NotebookLM source recommendations as current repo facts; verify live state separately.
- Do not dump full client memory/profile files into prompts if a compact digest will do.
- Do not persist transient auth-expired failures as “NotebookLM is broken”; the durable lesson is the auth refresh/smoke pattern.
