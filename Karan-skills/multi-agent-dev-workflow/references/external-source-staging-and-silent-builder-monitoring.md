# Staging External Owner-Supplied Inputs for Builder Agents

Use this pattern when an issue depends on a local source file outside the repository, while the builder lane is prohibited from reading outside its isolated worktree.

## Safe staging pattern

1. Create the isolated task worktree from current `origin/main` first.
2. Confirm the source exists and record only non-secret integrity facts needed for provenance (for example size/hash); never print source contents or credentials into chat/logs.
3. Copy the source into an already-ignored repo-local agent path such as:

   `.claude/inputs/<descriptive-source-name>`

   Prefer an existing ignored agent directory. Do not modify tracked `.gitignore` solely to stage a one-run input unless the repo genuinely needs that convention.
4. Verify `git status --short --branch` remains clean before launching the builder.
5. In the builder prompt:
   - name the exact repo-local staged path;
   - explicitly prohibit reading outside the worktree;
   - prohibit committing the raw source when it contains prices, private fields, secrets, or unrelated source data;
   - require a deterministic sanitized projection plus validator/check mode;
   - require the builder to prove the staged input remains ignored/uncommitted before push.
6. After the builder finishes, inspect `git status`, the commit file list, and the PR diff to verify the staged raw input did not enter Git history.
7. Remove the staged input during worktree cleanup after the PR is merged/closed or the run is abandoned.

## CI/source-of-truth warning

An ignored local source can drive generation, but CI cannot assume an absolute user path exists. The implementation must choose and document a deliberate contract, such as:

- commit only the sanitized deterministic artifact and let `--check` validate its schema/counts/provenance invariants offline;
- accept an explicit source argument for manual regeneration while keeping CI artifact validation self-contained; or
- vendor an approved sanitized source snapshot when the product contract requires full regeneration in CI.

Block any design that silently hardcodes a user-specific absolute path or makes CI depend on an unavailable local file.

## Monitoring large silent builders

Large issue-to-PR runs may spend several minutes reading a long issue and reconstructing contracts before the first file appears. Empty stdout and an initially clean worktree are not enough to classify a hang. Check, in order:

1. process is still alive;
2. elapsed time and CPU activity;
3. child process tree (especially long-lived MCP servers);
4. worktree status/diff/new files;
5. active test/build subprocesses.

If the builder is alive, using CPU, has no stuck MCP child, and later begins writing files, preserve the intended builder lane. Do not downgrade merely because output is buffered.

## Separate reviewer identity fallback

If a dedicated Keychain PAT entry is stale, a separately configured `gh` account may be used without changing the global active account:

1. obtain its token per process with `gh auth token --user <reviewer-login>`;
2. inject it only as `GH_TOKEN` for reviewer commands;
3. verify `gh api user --jq .login` and target-repo access before launching reviewers;
4. never export it globally into the persistent Hermes terminal environment;
5. preserve the required reviewer signatures and verify the resulting GitHub review surfaces at current PR head.

Treat this as an identity-preserving credential route, not permission to collapse builder and reviewer into the same account.