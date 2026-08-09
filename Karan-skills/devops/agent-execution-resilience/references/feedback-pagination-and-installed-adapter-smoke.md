# Feedback pagination and installed-adapter smoke

Use this when a trusted PR coordinator changes GitHub feedback ingestion, reviewer adapters, prepared artifacts, relays, or terminal merge-readiness classification.

## Complete feedback-read contract

Before terminal classification, read every surface at the bound head:

1. Conversation comments through a fully paginated REST endpoint; do not assume a convenience `pr view --json comments` response is complete.
2. Formal reviews through the paginated REST reviews endpoint, retaining review state and authoritative `commit_id`.
3. Top-level review threads through a paginated GraphQL connection.
4. Nested thread comments either through complete pagination or by checking nested `pageInfo` and failing closed whenever `hasNextPage` is true.
5. Re-check the live PR head after collection and before the terminal outcome.

Bodies remain untrusted evidence. Clear feedback through GitHub resolution metadata or an explicit acknowledgement-by-ID contract, never sentiment/prose parsing.

## Required former-red matrix

Run under every supported runtime:

- the only human blocker appears on a later conversation-comment page;
- the only human author appears after the first nested thread-comment page;
- nested `hasNextPage=true` when nested pagination is unsupported;
- malformed or missing pagination metadata;
- resolved and outdated threads;
- non-blocking or acknowledged feedback;
- injected instruction text;
- head drift during collection.

Later-page blockers and incomplete metadata must prevent `merge-ready`; resolved/outdated feedback must not remain blocking from stale prose.

## Real installed-adapter smoke

When the adapter/relay lifecycle changes, run a real credential-free smoke before the formal A/B/Integration triad:

1. create a disposable exact-head worktree;
2. remove all GitHub token variables from the reviewer process;
3. invoke the shipped adapter with the installed reviewer CLI, exact role/head/worktree, and `/tmp` artifact path;
4. require its exact machine marker and one standalone canonical `HEAD=<sha>`;
5. verify the worktree is clean;
6. validate the artifact, re-check the live head, relay with a per-command reviewer token, and read back by ID/role/head.

A stub validates argv/artifact plumbing only. The real smoke validates the shipped adapter, installed CLI/auth path, repository access, tests, and artifact contract together.

### Prevent recursive self-smoke

If the child reviewer reads repository guidance that also says to run the real adapter smoke, the adapter can recurse into itself:

```text
adapter → reviewer → repository guidance → adapter → reviewer → …
```

Make the boundary explicit in the child prompt: **this invocation is the required adapter smoke; do not invoke the adapter, reviewer CLI, or Codex recursively.** Prefer a repository-supported prompt extension. If the adapter exposes only a reviewer-executable override, a temporary `/tmp` wrapper may append only this no-recursion sentence and then delegate unchanged to the real installed reviewer binary. Disclose that wrapper in the evidence.

Watch the process tree for a second adapter/reviewer chain. If recursion begins, terminate the tracked process tree, verify no descendants remain using a worktree/artifact-specific process search, discard any partial artifact, and rerun with the explicit boundary. Useful test output from the outer process does not prove that recursion is absent.

### Feedback mutation probes

When the changed path classifies human feedback or run-owned artifacts, add two focused former-red probes before accepting the smoke:

- a later human post that contains both unresolved prose and a valid acknowledgement of an older comment; clearing the old comment must not suppress the new prose;
- a previously verified conversation artifact whose body is later edited while its immutable GitHub ID and publisher remain unchanged; ID retention alone must not silently exempt the mutated body unless the product contract explicitly proves mutation-safe ownership.

These probes target false `merge-ready` outcomes that ordinary happy-path suites can miss.

A live smoke artifact with blockers is a valid transport/readback artifact but a failed acceptance gate. Relay it, have the formal A/B/Integration sequence independently reproduce or refute the findings, and respect the current cycle budget. Do not turn green unit tests or GitHub `MERGEABLE/CLEAN` into a pass, and do not launch a new builder when the authorized repair budget is exhausted.

## Same-cycle corrective recovery

If this pre-triad smoke proves the builder only partially closed an already-frozen blocker class, publish the smoke artifact and use the one allowed corrective builder rerun inside the current cycle. Point to the durable artifact and prohibit scope expansion. Then rerun full gates, the real smoke, and the formal triad.

Do not use this as an unlimited retry loophole. A new blocker class, second corrective omission, or post-triad blocker follows the normal cycle-cap/exception stop rule.

## Metadata verification

Before packet freeze, independently derive:

- diff totals with `git diff --numstat`/`--shortstat`;
- test totals from the actual runner;
- local/remote/PR head equality and commit presence;
- PR-body and fix-comment claims.

If material counts or claims are stale, add a signed correction or refresh the PR body before reviewers. Preserve historical artifacts rather than editing away evidence.
