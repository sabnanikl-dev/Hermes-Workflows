# Operator-pinned acknowledgement recovery

Use this when a bounded autonomous PR run stops at `human-feedback` because every authenticated GitHub identity is also a configured builder/reviewer publisher.

## Core rule

A publisher-authored acknowledgement can participate only when the run config pins both the exact immutable GitHub post ID and the `body_evidence` digest for the post exactly as GitHub serves it. This is per-post authority, never a login-wide exemption. The post must exist before launch, remain unedited, and must not be a run-owned lane artifact.

## Body-evidence digest: do not hash the raw body

`body_evidence` is **not** `sha256(body)`. It is the digest over the same canonical payload PR Prover stores for its own artifacts:

```python
payload = json.dumps([post["body"], ""], ensure_ascii=False)
digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

For a formal review, replace the empty string with `post["state"].strip().upper()`. A raw-body SHA can look plausible and pass JSON/config shape validation, yet the terminal feedback barrier will classify the pin under `operator_pinned_acknowledgements_changed` after all three reviewer lanes have already run. Derive the digest from a direct GitHub readback using the exact recipe below, then confirm `check-config` prints the intended post ID.

## Mixed-post trap

A reconciliation comment containing ACK lines plus explanation is a **mixed post**:

- valid ACK lines may clear earlier prose;
- the remaining explanatory prose becomes one new unresolved feedback item;
- pinning the mixed post does not exempt its residual prose.

Recovery requires a later **pure bookkeeping post**:

```text
PR-PROVER: ACKNOWLEDGED <mixed-post-id>
```

Pin both the mixed post and the later pure post in a fresh run config **before** launch. Do not edit the original post to remove prose: IDs survive edits while the body-evidence authorization correctly lapses.

## Terminal green-triad feedback stops

A run can complete Reviewer A, Reviewer B, and Integration Auditor with `STATUS=pass`, `BLOCKING=0`, complete relay/readback, and green gates, then still return `needs-karan / human-feedback`. Keep these conclusions separate:

- the exact-head technical triad is valid evidence;
- the run is not formally `merge-ready` until the feedback barrier clears.

For recovery:

1. Preserve the green-but-stopped report under a new immutable path.
2. Read `fail_closed.evidence.unresolved` from that exact report. Build a pure ACK post from **only those unresolved IDs**.
3. Do not ACK run-owned or state-owned reviewer artifacts merely because they are visible on the PR. An ACK line whose target is already resolved performs no transition and remains residual acknowledgement-looking prose, creating another feedback item.
4. If an earlier publisher-authored ACK had an invalid/lapsed pin, it may appear separately as `operator_pinned_acknowledgements_changed` rather than in `unresolved`. A later pure ACK may need to acknowledge that post itself; determine this from the next resolver read rather than guessing extra IDs.
5. Derive the canonical `[body, state]` digest, pin the new post, preserve the exhausted attempt count and verified artifacts, and return the finished state to an idle continuation shape without restoring builder budget.
6. Treat the replay as control-plane reconciliation, not a new repair cycle. No code mutation is authorized.

Do not report the PR as formally merge-ready from the green lane markers alone when the tool's terminal feedback barrier has not cleared.

## Recovery sequence

1. Read the fail-closed report and confirm the unresolved item is exactly the mixed ACK post, commonly classified `acknowledged-and-raised-more`.
2. Verify the earlier ACK lines were consumed; do not post another blanket reconciliation record.
3. Publish one later pure ACK line for the mixed post under the authorized operator identity.
4. Read the new GitHub post back directly by immutable ID and verify author, exact body, timestamps, and unchanged PR head.
5. Derive `body_evidence` from the body GitHub currently serves:

```bash
gh api repos/OWNER/REPO/issues/comments/POST_ID > /tmp/pr-prover-ack.json
python3 -c 'import hashlib,json; p=json.load(open("/tmp/pr-prover-ack.json")); payload=json.dumps([p["body"], ""], ensure_ascii=False); print(hashlib.sha256(payload.encode("utf-8")).hexdigest())'
```

For a formal review, use identifier `review:<id>` and uppercase review state as the second array value.
6. Create collision-free run/state/lock/worktree/evidence paths. Preserve the stopped run as immutable evidence; do not overwrite it merely to change authorization.
7. Pin both exact posts, run `check-config`, and require its advisory to print every intended ID.
8. Launch the fresh run. Confirm state advances beyond `human-feedback` before claiming recovery.
9. Persist run ID, pin IDs/digests, target head, and authority exclusions in the governing tracker; verify that tracker comment directly by ID.

## Stop conditions

Stop rather than improvising when:

- the pinned post changed after it was read;
- the unresolved item is a native `CHANGES_REQUESTED` review or live review thread;
- the pure ACK post was created after the run launched;
- the PR head or branch changed while preparing reconciliation;
- recovery would require a third standing identity, login allowlist, fabricated author, or weakened publisher-denial rule.

## Verification checklist

- [ ] Stopped run retained and lock absent.
- [ ] Exact unresolved artifact/reason read from the report.
- [ ] Pure successor ACK contains one exact line and no residual prose.
- [ ] Both post IDs and body digests read back from GitHub.
- [ ] Fresh paths are collision-free.
- [ ] `check-config` prints every pin.
- [ ] Fresh run advances beyond `human-feedback`.
- [ ] No merge, force-push, deploy, install/release, or live/client mutation was implied by ACK authority.
