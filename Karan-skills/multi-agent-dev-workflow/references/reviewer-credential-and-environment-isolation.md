# Reviewer credential and environment isolation

Use this for Codex Reviewer A/B and the Hermes Integration Auditor.

## Security decision

Reviewer model processes receive **no GitHub token and no unrelated parent-shell credentials**. They inspect an exact-head disposable worktree plus an immutable review packet prepared by default Hermes, then return a signed artifact body. Default Hermes performs a disclosed transport-only GitHub relay after independently rechecking live state.

This is stricter than passing `GH_TOKEN` to the child. A reviewer credential can have broader access on other repositories even when the target repository reports `push: false`; environment scoping alone does not reduce the token's GitHub authorization.

## Separate auth paths

1. **Model authentication** — Codex/Hermes uses its approved filesystem OAuth store. OAuth material is never prompt content.
2. **GitHub artifact transport** — only default Hermes resolves the dedicated reviewer token, after the reviewer child exits. The reviewer prompt and child environment contain no GitHub token.

Never paste tokens, OAuth material, credential paths, secret values, or environment dumps into prompts, packets, artifacts, repositories, or logs.

## Default-Hermes review packet

Before launching any lane, default Hermes prepares a temporary packet bound to one exact `headRefOid`. Include only the data needed to audit:

- repository, PR number, packet timestamp, base, head branch, and full expected head SHA;
- PR title/body, linked issue contract, labels, draft/mergeability state;
- current-head reviews, inline comments, conversation comments, GraphQL review threads, and checks;
- base-to-head diff or local exact-head worktree path;
- baseline verification output and visual-evidence manifest when applicable.

Do not include credentials or broad environment state. The packet is a handoff snapshot, not proof that GitHub remained unchanged. Default Hermes must re-query `headRefOid` immediately before relaying each artifact.

## Hardened launchers

### Codex Reviewer A/B

Use `~/.local/bin/codex-reviewer`:

```bash
codex-reviewer \
  --role A \
  --workdir /absolute/path/to/disposable-review-worktree \
  --prompt-file /tmp/review-a.md \
  --read-only
```

The launcher:

- builds a clean `env -i` allowlist;
- supplies no `GH_TOKEN`, Linear key, messaging token, deployment credential, or unrelated secret;
- pins `gpt-5.6-sol`, medium reasoning, and ephemeral context;
- rejects model/config/dangerous-sandbox overrides;
- defaults to Codex's read-only sandbox.

Use `--workspace-write` only when default Hermes explicitly decides a disposable review worktree needs test-generated files. It still receives no remote credential, and default Hermes discards or verifies the worktree afterward.

### Hermes Integration Auditor

Use `~/.local/bin/reviewer`:

```bash
reviewer \
  --workdir /absolute/path/to/disposable-review-worktree \
  --prompt-file /tmp/integration-audit.md
```

Add `--ui` only for UI-affecting PRs. The launcher:

- starts only profile `reviewer` on `gpt-5.6-sol`/medium;
- pins base toolsets, adding only browser/vision for `--ui`;
- rejects `--yolo`, profile/model/provider/toolset/skill overrides;
- launches from a clean environment;
- sets file-tool writes to `/tmp` only.

The profile additionally uses `terminal.home_mode: profile`, no shell startup files, no persistent shell, no env passthrough, and unconditional deny rules for git/GitHub/tracker/deployment mutation and credential discovery.

## Artifact relay

Each child returns the exact artifact body and:

```text
ARTIFACT=relay-required
```

When launch output is captured with `tee`, reviewer CLIs may echo the prompt (which itself mentions `BEGIN_ARTIFACT`) and may repeat the final artifact after token-usage output. Extract only between lines whose entire content equals the delimiter—never with a raw substring search. Choose the first complete exact-line `BEGIN_ARTIFACT` → `END_ARTIFACT` pair after the reviewer starts producing its final answer, then validate the role signature, full head SHA, runtime line, and completion marker before any transport. If extraction or validation fails, post nothing. This prevents relaying prompt text or a partial artifact.

Then default Hermes, outside the reviewer process:

1. verifies the live PR head still equals the reviewed SHA;
2. validates the artifact's role signature, runtime line, blocker count, and expected head;
3. resolves the reviewer credential without printing it;
4. verifies identity and target-repository permissions;
5. submits the intended artifact under the reviewer identity;
6. reads the GitHub artifact back and verifies its body/head association;
7. unsets the scoped shell variable.

Example operator-only transport shape:

```bash
set +x
REVIEWER_TOKEN="$(gh auth token -u karanagent1)"
GH_TOKEN="$REVIEWER_TOKEN" gh api user --jq .login
GH_TOKEN="$REVIEWER_TOKEN" gh api repos/<owner>/<repo> --jq .permissions
GH_TOKEN="$REVIEWER_TOKEN" gh pr comment <N> --repo <owner>/<repo> --body-file /tmp/prepared-review.md
unset REVIEWER_TOKEN
```

For Reviewer A's formal review state, use the corresponding `gh pr review` command. Reviewer B and the Integration Auditor use signed conversation comments when all lanes share one account. Always disclose that default Hermes performed transport only; never describe a relay as a direct reviewer post.

## Verification checklist

- [ ] Child environment lacks `GH_TOKEN` and unrelated secret-variable names.
- [ ] Child `HOME`/XDG paths are reviewer-scoped where applicable.
- [ ] Exact runtime is `gpt-5.6-sol` with medium reasoning.
- [ ] Fresh profile snapshot contains only role-native skills.
- [ ] Removed skills cannot load.
- [ ] File-tool writes outside `/tmp` are blocked.
- [ ] Git push/commit/merge/auth/deploy commands hit unconditional deny rules.
- [ ] The child returns `relay-required`, not an unverified artifact URL.
- [ ] Default Hermes rechecks the head, relays, and reads the artifact back.
