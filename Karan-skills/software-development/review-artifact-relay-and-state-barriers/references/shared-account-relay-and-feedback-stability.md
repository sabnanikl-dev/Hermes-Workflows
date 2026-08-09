# Shared-Account Relay and Feedback Stability

## 1. Ordered exact-head packet refresh

Prepare a credential-free packet with repository/PR identity, generation timestamp, exact full head SHA, base/head branches, issue/PR contract, reviews, comments, threads, checks, baseline output, and evidence-file hashes.

The packet is a snapshot, not proof that GitHub stayed unchanged. Use one clean detached worktree per reviewer or one shared worktree only for strictly sequential read-only lanes.

When the Auditor certifies review state, use these barriers:

1. Launch Reviewer A and Reviewer B concurrently from the same frozen pre-A/B packet, each in its own clean detached exact-head worktree.
2. Wait for both to complete; independently validate each role, marker, head, runtime, blocker count, artifact body, and worktree cleanliness.
3. Recheck the live PR head. If it moved, relay neither artifact as current-head evidence.
4. Relay A as the formal review and directly read it back by immutable review ID.
5. Relay B as the signed conversation comment and directly read it back by immutable comment ID.
6. Refresh every GitHub review/comment/thread/check surface without changing the code head.
7. Launch the Integration Auditor with a new post-A/B packet containing both verified current-head artifacts.

A and B do not depend on each other's verdict and should normally run in parallel. The Auditor is the serialization barrier. A stale packet created while A/B are pending can establish implementation findings but cannot prove final review-state completeness.

## 2. Dedicated reviewer identity without global account switching

Resolve and verify the reviewer identity only in parent Hermes after the child exits. Prefer an already configured isolated `gh` profile because it keeps account selection per process and lets `gh` use its own current keyring credential:

```bash
REVIEWER_GH_CONFIG_DIR=/absolute/path/to/the/reviewer-gh-profile
EXPECTED_REVIEWER=karanagent1

actual=$(GH_CONFIG_DIR="$REVIEWER_GH_CONFIG_DIR" gh api user --jq .login)
test "$actual" = "$EXPECTED_REVIEWER"
GH_CONFIG_DIR="$REVIEWER_GH_CONFIG_DIR" gh api repos/OWNER/REPO \
  --jq '.permissions | select(.pull == true)'
```

If no isolated profile is configured, use a scoped token source such as `gh auth token -u "$EXPECTED_REVIEWER"` or the operator's configured Keychain item. Keep the token in one process environment only:

```bash
REVIEWER_TOKEN=$(gh auth token -u "$EXPECTED_REVIEWER")
actual=$(GH_TOKEN="$REVIEWER_TOKEN" gh api user --jq .login)
test "$actual" = "$EXPECTED_REVIEWER"
```

A remembered PAT/Keychain lookup is not identity proof. If that credential returns `401`, do not keep retrying it and do not fall back to the default account. Check whether the configured isolated reviewer `GH_CONFIG_DIR` is healthy, then use only a source whose live `gh api user` smoke test returns the expected reviewer. If none does, stop before POST and report the identity blocker.

Use the verified scoped execution context only for the exact relay command. Never print a token, pass it to the reviewer, export it globally, or switch global `gh` identity.

When roles share one account:

- Reviewer A owns formal `REQUEST_CHANGES`/`APPROVE` state and binds `commit_id` to the exact head.
- Reviewer B uses a signed conversation comment.
- Integration Auditor uses a separately signed conversation comment.

This prevents a later B/Auditor formal review from neutralizing A's live change request.

## 3. Relay validation and independent readback

Before relay, validate locally:

- expected artifact prefix;
- exactly one standalone `ROLE=<role>`;
- exactly one standalone `HEAD=<40 lowercase hex>`;
- one reviewer signature;
- pinned model/reasoning line;
- verdict and blocker count matching the final machine marker.

Re-query `headRefOid` immediately before POST. After POST, query by returned review/comment ID and verify:

- author is the configured reviewer login;
- correct artifact type/state;
- formal-review `commit_id` or canonical body head matches the exact head;
- role/signature/verdict/blocker count are present;
- URL is returned.

A shell can print the expected JSON and still exit non-zero because of a later command or wrapper behavior. In that case, run a separate direct GET by artifact ID. Do not infer success from output or failure from exit status alone; the independent readback decides.

## 4. Recovering an artifact from read-only stdout

A hardened `codex-reviewer --read-only` process may be unable to create `/tmp/<artifact>.md` even though the audit completes. If final stdout contains the complete signed artifact and machine marker:

1. Capture the final output.
2. Extract only the exact fenced body.
3. Remove opening/closing fences, token counters, duplicated terminal echoes, explanatory prose, and the outer `DONE:` marker unless the body contract requires it.
4. Write the body to a parent-owned `/tmp` file.
5. Run the local shape checks above.
6. Relay only after the live-head check.

This is normal transport recovery, not a degraded review. Disclose that parent Hermes performed transport-only relay.

## 5. Immutable identity for run-owned artifacts

These fields are public and copyable:

- author login;
- role line;
- signature;
- canonical head line;
- formal-review commit ID.

They prove shape and head binding, not provenance. A human using the shared reviewer login can copy them into decisive feedback.

The lifecycle should snapshot artifact IDs before lane launch, identify the new exact artifact during readback, and retain that immutable identifier in run state. Later feedback reconciliation excludes only those known IDs. Never exclude a whole shared login or reconstruct ownership solely from body shape.

Deterministic regressions should inject colliding human feedback across:

- formal `CHANGES_REQUESTED` review;
- PR conversation comment;
- builder-shaped comment;
- unresolved live review-thread comment.

Expected result: each remains human feedback and prevents terminal success unless its exact ID is recorded as run-owned.

## 6. Stable cross-surface feedback observation

A sequence such as comments → reviews → threads is not atomic. A human comment can arrive after the comments read but before later reads, while head/state/branches remain unchanged. A head-only freshness check can therefore permit false `merge-ready`.

Use a bounded stable-read gate:

1. read every feedback surface and record immutable IDs plus resolution/state fields;
2. classify;
3. re-read every surface immediately before terminal output;
4. compare the normalized ID/state snapshot;
5. retry once or fail closed on any difference.

Regression recipe: inject a human blocker immediately after the first surface returns, do not move the head, and assert the run retries or returns blocked/needs-human rather than merge-ready.

Do not generalize this into a workflow DSL or snapshot service; a direct deterministic comparison is enough.

## 7. Adapter smoke as a pre-triad gate

For changes to execution adapters, run the real installed credential-free adapter against the exact pushed head before the formal A/B/Auditor sequence. Unit tests with a stub CLI are necessary but can miss live reviewer reasoning and integration false-successes.

If the installed smoke reproduces a correctness or safety failure:

- publish/read back its signed exact-head evidence on the PR bus;
- include the finding in the refreshed packet;
- continue the full triad to bound the complete ledger;
- spend the next authorized builder cycle only after the triad freezes that ledger.
