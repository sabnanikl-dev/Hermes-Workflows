# Direct GitHub Reviewer Relay with Immutable-ID Readback

Use this when a credential-free reviewer has produced a parser-valid exact-head artifact and the parent must publish it under a dedicated GitHub reviewer identity.

## Why this exists

A high-level GitHub CLI mutator can exit zero without leaving the expected review artifact. Treat command success as an attempted side effect, never as publication proof. Prefer the REST endpoint because its response carries the immutable artifact ID needed for exact readback.

## Identity preflight

Resolve the intended account explicitly from the keyring while ignoring inherited token overrides. Never print the token or switch the globally active account.

```sh
review_token=$(env -u GH_TOKEN -u GITHUB_TOKEN \
  gh auth token --hostname github.com --user "$EXPECTED_REVIEWER")
actual=$(GH_TOKEN="$review_token" gh api user --jq .login)
[ "$actual" = "$EXPECTED_REVIEWER" ] || exit 1
```

An environment variable named for the reviewer is not identity evidence. It may hold the operator or PR-author token.

## Formal Reviewer A publication

Create the payload from the complete relay-eligible artifact, bind it to the exact head, POST directly, and capture the returned review ID.

```sh
payload=$(mktemp)
jq -n \
  --rawfile body "$SANITIZED_ARTIFACT" \
  --arg commit_id "$EXACT_HEAD" \
  '{body:$body,event:"COMMENT",commit_id:$commit_id}' > "$payload"

review_id=$(GH_TOKEN="$review_token" gh api --method POST \
  "repos/$REPO/pulls/$PR/reviews" \
  --input "$payload" --jq .id)
```

Immediately read back that exact ID with the same token and verify:

- author login equals the configured reviewer;
- `commit_id` equals the exact reviewed head;
- state/type is the intended formal review state;
- raw UTF-8 body equals the sanitized artifact bytes;
- the canonical parser still returns the intended role, runtime, head, verdict, blocker count, and finding records.

## Reviewer B / Auditor comment publication

For signed conversation artifacts, POST to the issue-comments endpoint and capture the returned comment ID.

```sh
payload=$(mktemp)
jq -n --rawfile body "$SANITIZED_ARTIFACT" '{body:$body}' > "$payload"

comment_id=$(GH_TOKEN="$review_token" gh api --method POST \
  "repos/$REPO/issues/$PR/comments" \
  --input "$payload" --jq .id)
```

Read back `repos/$REPO/issues/comments/$comment_id` and apply the same author/body/parser checks plus canonical `HEAD=` equality.

## Zero-artifact recovery

If relay exits zero but the immediate post-relay review/comment inventory contains no new artifact:

1. classify it as transport failure, not reviewer pass/fail and not a consumed builder cycle;
2. inspect the actual relay identity under the exact process-scoped token;
3. confirm the head and repository were unchanged;
4. preserve the prepared reviewer artifact and any parser output;
5. correct only transport, then rerun/re-relay according to the governing tool's state model;
6. never publish a hand-reconstructed verdict from memory.

If the failed transport report exposes a canonical finding ID or complete prepared body, treat it as a lead. Independently reproduce and scope the finding before using a repair cycle; transport failure does not make a demonstrated product defect disappear.

## Instrument before rerunning an expensive reviewer

When an orchestrated reviewer finishes but relay/readback fails, do **not** immediately spend another five-minute reviewer run just to learn whether publication happened. First make the next relay diagnosable:

1. copy the exact prepared artifact to a run/head/role-bound retention path before the POST;
2. verify the process-scoped login immediately before mutation;
3. write the HTTP response body and status to run-scoped files, even on non-2xx responses;
4. record the target repo, PR, role, and head without recording the token;
5. query the exact review/comment collection after the relay, rather than trusting wrapper state such as `published=true`;
6. if the orchestrated invocation still leaves no response file, invoke the same relay manually with the retained **real** artifact and explicit repo/PR/head parameters. Do not create a synthetic “transport test” review that pollutes feedback state.

A parser-valid, exact-head artifact retained before a transport-only terminal stop may be relayed manually without rerunning the substantive reviewer. Capture the returned immutable ID and read it back. Then continue through the governing lower-level ordered recovery (`A readback → fresh B packet → B readback → Auditor`) or reset the prover only if its documented state model can consume that artifact. Never hand-reconstruct the artifact from the failure summary.

If a high-level `gh api` mutator behaves ambiguously inside a wrapper, a bounded `curl` POST is an acceptable transport fallback when it uses the same verified token, saves the complete response, checks HTTP 200/201 explicitly, extracts the immutable ID, and performs independent ID readback. The lesson is not that `gh` is broken; it is that every mutation path needs observable response and readback barriers in the exact execution context.

## Progress-state truth during transport recovery

“Prepared,” “reviewer finished,” “relay attempted,” “artifact published,” and “artifact read back” are distinct states. Likewise, a configured review stage is not an active run. Before telling the user a goal is running, verify a tracked process or live child PID exists. If configuration is merely being prepared—or an earlier run already stopped—say `paused at formal review` or `preparing the review run`, not `reviewers are running`.

## Cleanup and secret safety

Use traps to blank the shell variable and delete payload/body scratch copies. Do not log argv/environment containing the token. A concrete returned ID followed by a later shell failure means the side effect may already exist—read back that ID before retrying.
