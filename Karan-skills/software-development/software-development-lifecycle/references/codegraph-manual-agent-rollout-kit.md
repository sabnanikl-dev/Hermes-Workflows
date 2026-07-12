# CodeGraph manual-agent rollout kit pattern

Use this reference when rolling out CodeGraph to manual external coding agents such as Claude Code as builder and Codex as reviewer.

## Durable pattern

1. **Separate host boundaries**
   - Claude Code config, Codex config, and Hermes profile config are separate adoption surfaces.
   - Do not treat CodeGraph working in one host as proof that another host can see it.

2. **Pin the package for evaluation**
   - Prefer pinned `npx` during Phase 0 instead of global install:
     - Claude/Codex server command: `npx -y @colbymchenry/codegraph@0.9.9 serve --mcp`
     - Repo indexing: `npx -y @colbymchenry/codegraph@0.9.9 init .`
     - Refresh: `npx -y @colbymchenry/codegraph@0.9.9 sync .`
   - Revisit global install only after repeated real use shows `npx` startup overhead is painful.

3. **Keep repo indexes local first, then track only the ignore rule**
   - For initial rollout, add `.codegraph/` to each repo's local `.git/info/exclude`, not tracked `.gitignore`:
     ```bash
     mkdir -p .git/info
     touch .git/info/exclude
     grep -qxF '.codegraph/' .git/info/exclude || printf '\n# Local CodeGraph index/cache\n.codegraph/\n' >> .git/info/exclude
     ```
   - The generated `.codegraph/` directory itself should not be committed to GitHub. It is a local index/cache like `node_modules/`, `dist/`, or `.vite/`: machine-specific, frequently changing, and not durable source.
   - After smoke tests prove value, add the tracked `.gitignore` rule `.codegraph/` plus repo harness docs by normal PR. The durable repo artifact is the ignore rule and workflow guidance, not the generated index.
   - Verify the boundary before reporting adoption:
     ```bash
     git check-ignore -v .codegraph
     git ls-files .codegraph | wc -l
     ```

4. **Audit fit by indexed source, not hope**
   - Run `status` and `files` after init:
     ```bash
     npx -y @colbymchenry/codegraph@0.9.9 status .
     npx -y @colbymchenry/codegraph@0.9.9 files -p . --format flat
     ```
   - Good fit: TS/TSX/JS/Python source with symbols/imports/calls.
   - Weak fit: static HTML/CSS/Markdown/image-heavy repos where CodeGraph sees only sitemap/XML or a tiny symbol graph. In weak-fit repos, make CodeGraph optional and prioritize existing validators/manual review.

5. **Package adoption artifacts**
   - Create reusable prompt blocks rather than one-off prose:
     - builder startup prompt
     - reviewer startup prompt
     - repo smoke tests
     - repo onboarding checklist
     - audit/index scripts
     - optional HTML dashboard for human governance

6. **Smoke-test both agent roles**
   - Builder smoke: read-only orientation question that should name key files and limitations.
   - Reviewer smoke: read-only impact/blast-radius question around a known function/API.
   - Require no tracked file changes and verify `git status` before reporting adoption.

7. **Post-merge adoption closeout**
   - When the user says a rollout PR was merged, verify the PR state with GitHub (`mergedAt != null` / `state == "MERGED"`) before updating any status artifacts.
   - Sync or inspect the target repo carefully: local checkouts may be on active feature branches. Do not claim a local checkout is clean `main` unless `git status --short --branch` proves it; otherwise recommend a separate clean worktree for smoke tests.
   - Update the rollout README/dashboard/plan from “create PR” to “observe real sessions,” with clear decision points: runtime access, usefulness, limitations, friction, and next repo.
   - Re-render/HTTP-preview HTML dashboards after status edits and check the browser console before final handoff.

## Prompt contract additions
   - If the repo requires every PR to link a GitHub Issue, create/search the issue before opening the PR and include `Closes #N` in the PR body.
   - For documentation-only adoption PRs, commit only the harness docs and tracked ignore rule; never include `.codegraph/` index files.
   - After pushing, verify the PR's remote head commit matches local `HEAD` before reporting success:
     ```bash
     LOCAL=$(git rev-parse HEAD)
     REMOTE=$(gh pr view <PR> --json commits --jq '.commits[-1].oid')
     test "$LOCAL" = "$REMOTE"
     ```

## Prompt contract additions

Builder PR descriptions should include:

```md
CodeGraph context used:
- Query/flow checked: ...
- Symbols/files inspected: ...
- Blast-radius notes: ...
- Limitations: ...
```

Reviewer summaries should include:

```md
CodeGraph review context:
- Changed symbols/files checked: ...
- Additional blast radius found: ...
- Known CodeGraph limitations: ...
- Tests/verification still required: ...
```

## Common limitations to name explicitly

- Electron IPC string channels may require manual `ipcRenderer` ↔ `ipcMain` pairing review.
- Sanity/GROQ strings and `VITE_*` environment wiring often require manual verification.
- Static site harnesses may have low graph value; do not force CodeGraph into workflows where the index shows little source coverage.
