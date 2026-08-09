# Manual lower-level triad recovery after terminal prover transport failure

Use this only when the full prover has already stopped terminally **after all gates passed on the exact current head**, and the stop is confined to reviewer artifact grammar, relay, or readback. This is governed evidence recovery, not a second prover implementation and not permission to reopen a repair cycle.

## Eligibility gate

All must be true:

1. Local retained worktree HEAD, remote branch HEAD, and live PR `headRefOid` are the same full SHA.
2. One retained run completed every configured gate on that SHA.
3. No code, PR body, governing issue, gate command, or acknowledgement evidence changed after those gates.
4. The failure was transport/control-plane only: malformed or incomplete reviewer artifact, final-message/artifact parity drift, relay failure, or immutable-ID readback failure.
5. No builder, push, force-push, merge, deploy, or client/live mutation occurred after the gate evidence.
6. The repair-attempt count is preserved. Manual review recovery consumes no builder cycle, but it must never reset or edit a terminal journal to manufacture a resumable state.

If any condition fails, stop. Start a normal fresh head-bound run or ask Karan; do not preserve stale gates.

## 1. Prove the reviewer really exited

A Hermes background handle can report `exit code None` while the real wrapper and model child remain alive. Before relaunching:

- inspect the process tree for the exact worktree/artifact arguments;
- inspect stdout, stderr, and the prepared artifact separately;
- verify the worktree is still clean and at the bound head;
- if the real PID remains alive, attach a one-shot watchdog to that PID and do not duplicate the lane.

A reliable watcher is:

```sh
pid=<real-wrapper-pid>
while kill -0 "$pid" 2>/dev/null; do sleep 30; done
printf 'reviewer wrapper %s exited; inspect authoritative artifacts\n' "$pid"
```

The watcher proves termination only. The authoritative verdict remains the final-message file, prepared artifact, stderr diagnostics, worktree state, and live PR state.

## 2. Rerun only the malformed role

Create a fresh detached clean worktree at the unchanged exact head, a fresh empty `GH_CONFIG_DIR`, and unique absent stdout/stderr/artifact paths. Use the repository-owned reviewer launcher and the same frozen packet.

The focus/prompt must say explicitly:

```text
Write every FINDING: line into the prepared artifact.
Make every FINDING: line in the final message byte-for-byte identical to the corresponding line in the prepared artifact.
```

Do not assume a prompt that says only “state every blocker in the artifact” is enough. The canonical parser needs the exact `FINDING:` grammar in both surfaces.

A same-head correction is still a fresh substantive audit. Its finding count may differ from the malformed attempt because the model can deduplicate, reproduce, or refute findings differently. Do not hand-preserve the old count. The latest complete parser-valid same-head audit governs; record the earlier malformed audit as transport evidence, not as an additional blocker ledger.

## 3. Validate with shipped parser/publication code

Never hand-edit reviewer output. Parse the exact final message with `parse_reviewer_verdict`, then validate and sanitize the exact prepared artifact through:

```python
verdict = parse_reviewer_verdict(name, stdout_text, expected_head=head)
prepared = read_prepared(
    artifact_path,
    reviewer=name,
    role=role,
    signature=signature,
    head=head,
    status=verdict.status,
    blocking=len(verdict.blocking),
    findings=verdict.findings,
)
published = publication_copy(
    prepared,
    reviewer=name,
    signature=signature,
    findings=verdict.findings,
)
relay_path = relay_source(published, reviewer=name)
```

Require:

- exact role/runtime/head/status/blocking declarations;
- required signature and `KILL-SWITCH:` declarations;
- one-to-one finding ID/severity/summary parity;
- sanitized publication copy created outside the repository;
- reviewed worktree clean after exit.

When piping validator output through `tee`, use `set -o pipefail`; otherwise a Python validation crash can be masked by `tee` returning zero.

## 4. Relay and prove immutable readback

Immediately before POST:

1. re-read live PR head and stop on drift;
2. snapshot existing review/comment immutable IDs;
3. smoke-test the configured reviewer identity in a process-scoped credential context;
4. invoke the configured relay with the **sanitized** path only;
5. capture the POST-returned immutable ID and URL.

Then fetch that exact ID and verify:

- expected author and artifact surface;
- formal-review `commit_id` equals the exact head where applicable;
- remote body equals the sanitized local body byte-for-byte;
- UTF-8 SHA-256 values match;
- the fetched body passes `artifact_matches(...)` with the lane verdict findings.

Do not retry a POST after it returned an ID merely because later local verification failed. Read that ID back first.

## 5. Freeze the next ordered packet with shipped APIs

After upstream immutable readback, use the repository GitHub boundary and packet writer/reader rather than manually splicing JSON:

```python
boundary = GhCliGitHub(SubprocessRunner(default_timeout=120.0), timeout=120.0)
pull = boundary.pull_request(repo, pr)
comments = boundary.comments(repo, pr)
reviews = boundary.reviews(repo, pr)
evidence = boundary.review_evidence(repo, pr, head, governing_issues)
payload = build_packet(
    pull=pull,
    repo=repo,
    head=head,
    sequence=sequence,
    reviewer=next_name,
    role=next_role,
    comments=comments,
    reviews=reviews,
    evidence=evidence,
    governing_issues=governing_issues,
)
packet = write_packet(unique_path, payload)
read_packet(
    unique_path,
    repo=repo,
    pr=pr,
    base=pull.base_ref_name,
    head=head,
    sequence=sequence,
    reviewer=next_name,
    role=next_role,
    governing_issues=governing_issues,
)
```

Confirm the packet contains the exact immutable ID just relayed and that `generated_at` is later than that publication. Then continue strictly:

```text
Reviewer A readback
→ freeze Reviewer B packet
→ Reviewer B parser/relay/readback
→ freeze Integration Auditor packet
→ Integration Auditor parser/relay/readback
→ stable two-read feedback reconciliation
```

## 6. After the triad

If reviewers report blockers, deduplicate their exact-head records into one frozen cycle ledger before using any remaining builder cycle. Preserve provenance from all three lanes. If zero blockers remain, perform the normal stable feedback, local/remote/PR equality, checks, tracker, and human merge-authority barriers.

Never call a partial manually recovered chain merge-ready. Never use manual recovery to bypass a failed gate, altered contract, stale head, hidden third builder cycle, or missing reviewer artifact.
