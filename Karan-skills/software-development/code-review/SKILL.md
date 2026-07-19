---
name: code-review
description: Guidelines for performing thorough code reviews with security and quality focus
---

# Code Review Skill

Use this skill when reviewing code changes, pull requests, or auditing existing code.

## Review Checklist

### 1. Security First
- [ ] No hardcoded secrets, API keys, or credentials
- [ ] Input validation on all user-provided data
- [ ] SQL queries use parameterized statements (no string concatenation)
- [ ] File operations validate paths (no path traversal)
- [ ] Authentication/authorization checks present where needed
- [ ] For Electron/desktop shells, renderer-to-main IPC payloads are runtime-validated, untrusted URLs cannot receive privileged APIs, and process/PTY sessions have explicit stop/cleanup ownership

### 2. Error Handling
- [ ] All external calls (API, DB, file) have try/catch
- [ ] Errors are logged with context (but no sensitive data)
- [ ] User-facing errors are helpful but don't leak internals
- [ ] Resources are cleaned up in finally blocks or context managers

### 3. Code Quality
- [ ] Functions do one thing and are reasonably sized (<50 lines ideal)
- [ ] Variable names are descriptive (no single letters except loops)
- [ ] No commented-out code left behind
- [ ] Complex logic has explanatory comments
- [ ] No duplicate code (DRY principle)

### 4. Testing Considerations
- [ ] Edge cases handled (empty inputs, nulls, boundaries)
- [ ] Happy path and error paths both work
- [ ] New code has corresponding tests (if test suite exists)

## Multi-Agent Code Review Context

In a multi-agent workflow (Hermes + Claude Code), code reviews follow a cross-review pattern:
1. Agent A opens PR → Agent B reviews → Agent A fixes → Agent B or third agent re-reviews → merge
2. The human gives go/no-go approval only; they never review raw code diffs
3. Same-account GitHub PATs cannot approve PRs through the API (422: "Review Can not approve your own pull request"). Use manual review analysis instead.

When reviewing PRs from another agent, always:
- Check if the PR contains unrelated changes that should be split (e.g., color migration mixed with inquiry form code). If so, cherry-pick the relevant commit onto a clean branch instead.
- Verify the build passes: run `npm run build` on the PR branch
- Scan for `console.log` or debug code in modified files
- Check for hardcoded secrets or credentials
- Confirm the PR is linked to a GitHub Issue (`Closes #N`)

Before leaving a review comment, check existing comments with `gh pr view <N> --repo <repo> --json comments,reviews` to avoid repeating feedback from another reviewer.

### Iterative blocker review loop
When the user asks to send work to Codex/reviewer and proceed once the loop is good:
1. Ask the reviewer for **blocking findings only** with `file:line` references and a machine-readable final marker such as `DONE: STATUS=pass|fail BLOCKING=<count>`.
2. Treat `STATUS=fail` as actionable: patch the blockers, rerun the project's verification command, and re-review. Continue until `STATUS=pass BLOCKING=0` or a blocker requires user judgment.
3. Do not stop after one review if blockers remain. The deliverable is a clean review loop backed by verification output.
4. For Electron/PTY scaffolds, specifically probe: renderer-controlled command/cwd, inherited env/secrets, trusted dev-server origin, stop/kill-all paths, renderer teardown cleanup, stale session races, and safe parsing for fire-and-forget IPC.

For agent-harness reviewer flows, treat async lifecycle races as first-class blockers even when typecheck/build/tests pass: run/root drift across awaits, same-run relaunches under stable pane IDs, stale PTY `onData`/`onExit` callbacks, delayed `gh pr comment` results, and failure states that can collapse into green marker-comment states. Verify the state machine supports both initial review and fix-cycle re-review launch edges, and require regression tests for these paths.

See `references/electron-pty-review-loop.md` for a compact checklist from a GodMode scaffold review.
See `references/electron-reviewer-lifecycle-races.md` for reviewer-launch/capture/comment race patterns and regression tests from the GodMode PR #32 review loop.
See `references/pre-pr-architecture-acceptance-audit.md` for exact-default-branch, read-only audits that turn live issue contracts and current implementation seams into a post-PR verifier checklist.

## Safety-Critical Migration Plan Reviews

Use this extension when the artifact under review is an operational plan, migration runbook, cleanup goal, installer, data mover, or stateful automation—not only executable source code.

Review the plan as an executable state machine:
1. Enumerate every state the plan can create, including bootstrap, preflight, partial execution, rollback, post-processing, review-pending, and completion states.
2. Prove every produced nonterminal state has exactly one safe re-entry/finalization path. A state that can be written but cannot be resumed is a blocker even if the happy path is sound.
3. Separate new work from recovery. Expired approval may reconcile already-durable intent, but must never authorize a new side effect.
4. Bind approval to the safety machinery as well as the payload: rubric, schemas, validator, fixtures, executor, review package/projection algorithm, expected preimages, and exact control-plane paths.
5. Require kernel/process locks for live ownership and durable journals for recovery; never infer active ownership from a persistent lock-file body.
6. Define narrow compare-and-swap semantics for mutable control files. Bind expected preimages and deterministic revision/temp paths, preserve prior bytes, fsync, and specify interrupted-CAS reconciliation.
7. Check both source and destination trust boundaries immediately before mutation: path confinement, symlink ancestry, identity, volume, collision behavior, sync/File Provider status, and materialization state.
8. For privacy-redacted external review, require a deterministic locally validated projection with raw hashes, projection hashes, and one-to-one operation mapping. A prose summary is not cryptographic review binding.
9. Test bootstrap, preflight, operation, and post-execution crash points. Post-processing states such as pending map update or pending independent review need finalization-only re-entry lanes that cannot reopen data mutation.
10. Keep the reviewer loop blocker-only (P0/P1) after the first pass. Patch, verify, and re-review until PASS; do not let optional defense-in-depth create an endless hardening loop.

For plan documents that embed generated copies of standalone goals, verify decoded mirrors byte-for-byte. When no canonical test command exists, create a fresh temporary verifier that checks required invariants, forbidden stale wording, state closure, encoding/whitespace, and rendered-document structure; run it, report the real result, and remove it.

See `references/safety-critical-migration-plan-review.md` for the reusable checklist, adversarial-review prompt, and verification pattern distilled from a filesystem migration hardening review.

## Review Response Format

When providing review feedback in a multi-agent context, structure it as:

```
## PR #N Review: [Title]

**Verifier: APPROVED** or **NOT Approved** — [brief reason if blocked]

### Blocking (P0)
- Issue 1: [description + suggested fix or code snippet]

### Follow-up (P2)
- Issue 2: [description — not blocking but worth tracking]

### Looks Good
- Bullet points of things that are correct/well-done
```

For non-blocking reviews with no issues found:
```
## PR #N Review: [Title]

**Verifier: APPROVED** — no issues found.

## Looks Good
- [list what was verified]
```

### Questions
- [Any clarifying questions about intent]

## Common Patterns to Flag

### Python
```python
# Bad: SQL injection risk
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Good: Parameterized query
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

### JavaScript
```javascript
// Bad: XSS risk
element.innerHTML = userInput;

// Good: Safe text content
element.textContent = userInput;
```

## Tone Guidelines

- Be constructive, not critical
- Explain *why* something is an issue, not just *what*
- Offer solutions, not just problems
- Acknowledge good patterns you see
