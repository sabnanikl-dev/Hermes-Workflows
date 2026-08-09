# Process-scoped relay identity and truthful run status

Use this when a reviewer lane finishes and the relay command exits zero, but GitHub readback finds no artifact—or when an operator update risks saying a review is “running” before launch.

## Identity failure pattern

A credential variable can be populated yet still name the wrong account. Variable names such as `REVIEWER_A_GITHUB_TOKEN` are labels, not proof. On hosts with several `gh` keyring accounts, an inherited token may resolve to the active operator/PR-author account. A `gh pr review --comment` attempt can then fail to create the expected reviewer artifact even when a wrapper obscures the semantic problem.

Before any POST:

1. Determine the expected reviewer login from the run config.
2. Resolve that account explicitly in the relay process. With `gh` keyring accounts, remove inherited token overrides before lookup:

   ```sh
   review_token=$(env -u GH_TOKEN -u GITHUB_TOKEN \
     gh auth token --hostname github.com --user "$EXPECTED_REVIEWER")
   ```

3. Smoke-test the exact token that will perform the POST:

   ```sh
   actual=$(GH_TOKEN="$review_token" gh api user --jq .login)
   test "$actual" = "$EXPECTED_REVIEWER"
   ```

4. Use that same process-scoped token for the relay. Do not switch the globally active `gh` account.
5. Capture the POST-returned immutable artifact ID when possible, then fetch that exact review/comment and verify author, type/state, exact head, role/signature, verdict, and body equality.
6. Clear the shell variable after use and never print token material.

A successful shell exit is not publication proof. If readback finds zero valid artifacts, classify `transport/readback failure`; inspect live reviews/comments and the relay identity before rerunning.

## Recovery classification

If gates and reviewer reasoning completed but no GitHub artifact was read back:

- do not call the lane complete;
- do not run the next ordered reviewer;
- do not consume a product repair cycle when no code/head changed;
- preserve the retained output as transport diagnostics;
- correct the identity path, reset only the terminal transport state, revalidate config/head/acknowledgements, then restart the required ordered sequence on the unchanged head.

If the unpublished output contains a candidate product defect, independently reproduce it against the exact shipped head. A successful reproduction establishes a product blocker but does not retroactively complete reviewer transport.

## Truthful operator status

Use explicit lifecycle verbs:

- **prepared** — config/relay exists but no process has launched;
- **validated** — config/head/ack checks passed;
- **launched / active** — a tracked process handle exists and live process state confirms execution;
- **exited, adjudication pending** — wrapper ended but report/readback has not been classified;
- **transport failed** — reviewer may have reasoned, but publication/readback did not complete;
- **complete** — authoritative report plus immutable GitHub readback has been verified.

Never tell the user “the reviewers are running” or “I’m at the review stage” when only preparation is complete. When interrupted mid-setup, state plainly that no process is active. Include the process ID only after launch, and verify it before later status claims.