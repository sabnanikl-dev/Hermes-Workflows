# GodMode worktree-isolation review pitfalls

Session-derived notes from running the GodMode issue-to-PR loop for per-run builder worktrees.

## Durable lessons

1. **Validate persisted worktree paths on every reuse, not only creation.**
   - It is not enough for `createWorktree()` to reject stale/foreign/wrong-branch directories.
   - Any `ensureRunWorktree()` or "reuse `run.worktree.path`" branch must revalidate that the recorded path is:
     - inside a git work tree;
     - registered in `git -C <projectRoot> worktree list --porcelain` for the operated repo;
     - checked out on the expected run branch.
   - Otherwise a path that was valid when recorded can later be manually removed/recreated, converted to a foreign repo, or moved to the wrong branch and still be launched as the builder cwd.

2. **Commit verification in isolated-worktree mode must use the run branch/worktree tip, not primary checkout HEAD.**
   - The primary checkout is intentionally left untouched and may remain on `main` or another branch.
   - If the run has no recorded expected commit, resolve from the run branch tip (`git rev-parse refs/heads/<branch>` or the worktree HEAD) before falling back to the project root HEAD.
   - Add a regression test where primary HEAD differs from the run branch.

3. **"Clear run" must not erase cleanup authority.**
   - If a run owns a worktree or has a live builder PTY, unconditional clear drops the state needed to protect cleanup.
   - Guard clear as terminal-only, or refuse clear while the run is active, owns a worktree, or has live PTYs. Preserve the run record until cleanup/cancel has happened.

4. **Re-review the exact reuse/fix path after blocker fixes.**
   - A fix can close the obvious helper-level vulnerability while leaving a higher-level cached/reuse path unpatched.
   - Ask reviewers to check both creation and already-recorded reuse paths explicitly.

5. **Long autonomous loops need a checkpoint before starting another fix cycle near tool limits.**
   - Before spawning another builder/fix agent, verify whether enough interaction budget remains to observe completion, verify remote head, rerun tests, and rerun at least the blocking reviewer.
   - If not, stop at a verified checkpoint and report the remaining exact next steps rather than launching work that may finish after the operator loses tool access.
