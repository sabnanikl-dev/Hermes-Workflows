# Stored GitHub Credentials and Relay Attribution

Use this reference when a reviewer must be credential-free while default Hermes publishes its prepared artifact.

## Why unsetting token variables is insufficient

`env -u GH_TOKEN` removes one credential path, not GitHub authority. GitHub CLI can also resolve authentication through:

- `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, and `GITHUB_ENTERPRISE_TOKEN`;
- `GH_CONFIG_DIR`;
- `XDG_CONFIG_HOME/gh`;
- `$HOME/.config/gh`;
- the operating-system credential store/keychain referenced by the selected `gh` profile.

A reviewer can therefore retain publication authority even when every token variable appears absent. Prompt text saying “do not post” is not a credential boundary.

## Credential-free launch contract

Preserve the model client's required OAuth/session environment, but make GitHub CLI remote-inert:

1. Unset all GitHub token variables named above.
2. Set `GH_CONFIG_DIR` to a fresh, run-owned, empty directory outside the repository.
3. Give the reviewer a frozen PR/issue/review/check packet. Do not require it to run authenticated `gh` to obtain evidence.
4. Before launching the model, run a negative launcher smoke proving `gh api user` fails in the exact child environment. Capture only success/failure—never credential output.
5. Keep relay credentials and the dedicated reviewer identity exclusively in the parent process after the child exits.

Do not use `env -i` or synthetic `HOME` when that would break the model client's legitimate OAuth session. Isolate the GitHub client specifically instead of rebuilding the whole environment.

## Frozen packet fail-closed contract

A credential-free reviewer needs enough immutable evidence to review without authenticated `gh`. Bind one direct, workflow-specific packet to:

- repository, PR, base SHA, and exact full head SHA;
- a generated timestamp and strictly increasing run/lane sequence;
- PR/issue contract text;
- conversation comments, formal reviews with `commit_id`, inline comments, review threads, check runs, and closing references;
- how each surface was read, whether pagination reached its end, and whether the surface is complete;
- baseline gate and installed-adapter evidence when relevant.

Validate the packet before model launch and again in the repository-owned adapter. Missing, empty, malformed, wrong-schema, truncated, wrong-repo/PR/base/head/sequence, or internally inconsistent binding data must stop before review or relay. An incomplete surface is unknown evidence, never an empty surface. Keep the packet implementation narrow; do not turn it into a generic snapshot framework.

## Real installed-adapter smoke

Unit doubles are not enough because host credential resolution lives in `gh`, the OS keychain, and the model client's own login path. On the actual operator machine, prove without printing credential material:

```text
operator `gh api user`                 -> succeeds
reviewer-lane `gh api user`            -> authentication failure
reviewer-lane publication attempt      -> authentication failure
reviewer-lane model login/status       -> succeeds
```

Also prove the adapter refuses a missing `GH_CONFIG_DIR` and a supposedly isolated directory containing `hosts.yml`. When practical, run the same smoke against the pre-fix environment to show the old lane could authenticate, then run it against the repaired environment to show the specific boundary—not a broken model session—caused the change.

## Relay attribution barrier

A snapshot taken before the reviewer starts cannot prove that a later artifact was published by the relay: a reviewer with residual credentials could post between that snapshot and relay execution.

Correct sequence:

1. reviewer exits and its local artifact validates;
2. parent rechecks the live PR head;
3. parent snapshots GitHub artifact IDs **immediately before relay**;
4. parent invokes the relay under the verified reviewer identity;
5. parent records the immutable artifact ID returned by the POST;
6. parent reads that exact ID back and verifies author, type, commit/head, role, runtime, verdict, blocker count, and body hash/shape;
7. if the transport cannot return an ID, require exactly one matching ID new since the immediate pre-relay snapshot—otherwise fail closed.

Never let a matching artifact that existed before the immediate pre-relay snapshot satisfy `published` or `read_back`. A no-op relay must not become successful transport merely because a reviewer-side copied body is already live.

## Deterministic regressions

Include tests for:

- reviewer environment retains HOME but `gh api user` fails through an empty `GH_CONFIG_DIR`;
- reviewer-side valid artifact appears before a no-op relay: transport fails;
- reviewer-side artifact appears, then real relay posts a copy: only the relay-returned ID is retained;
- copied body under wrong login, wrong artifact type, wrong commit/head, or old ID fails;
- concurrent extra matching artifact makes ID-diff fallback ambiguous and fail closed;
- formal review and conversation-comment transports both bind to their returned immutable IDs.

These are transport-integrity tests owned by the credential-free reviewer/relay contract. They are not acknowledgement chronology or general hostile same-UID containment.
