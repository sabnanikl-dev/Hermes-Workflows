---
name: sanity-studio-deploy
description: Deploy the Femme Events Sanity studio after merging PRs that add or change schemas.
triggers:
  - PR merges that modify files under studio/schemas/
  - "redeploy studio"
  - "deploy sanity"
---

# Sanity Studio Deploy

Deploy the Femme Events Sanity studio after merging PRs that add or change schemas.

## When to use

Any time a PR merges that modifies files under `studio/schemas/`. The studio must be redeployed for new content types to appear at femmeevents.sanity.studio.

## Steps

1. **Verify merge** — confirm PR state is MERGED before proceeding:
   ```bash
   gh pr view <NUMBER> --repo sabnanikl-dev/Femme-Events-Website --json state,mergedAt --jq '"\(.state) | merged at \(.mergedAt)"'
   ```

2. **Sync local repo** — fetch + hard reset (local branches often diverge):
   ```bash
   cd ~/projects/femme-events/website/"Femme Events Website Build"/Femme-Events-Website
   git fetch origin main && git reset --hard origin/main
   ```
   Note: `git reset --hard` requires user approval via Hermes security gate.

3. **Deploy studio**:
   ```bash
   cd studio && npx sanity deploy
   ```
   Timeout: 120s. Expect ~10s build + deploy. Success message: `Success! Studio deployed to https://femmeevents.sanity.studio/`

4. **Comment on linked issue** — confirm studio is live and list the new content types:
   ```bash
   gh issue comment <ISSUE> --repo sabnanikl-dev/Femme-Events-Website --body "PR #<N> merged and Sanity studio redeployed. <Content type names> now live at https://femmeevents.sanity.studio/"
   ```

## Populate CMS from branch/static data

When Karan asks to populate the CMS from data currently in a website branch, use the `references/vendor-import-from-static-data.md` playbook. The key pattern is: inspect static data and schemas, query existing Sanity content first, ask before destructive cleanup, prefer non-destructive placeholder cleanup if proceeding without a response, import with deterministic IDs through `sanity exec`, verify counts/names from Sanity, then remove any temporary import script and confirm `git status --short` is clean.

## Sanity CORS for Local and Production QA

When local previews or deployed frontends show browser console errors like `Access to XMLHttpRequest ... has been blocked by CORS policy`, check and update the Sanity project allowlist from the `studio/` directory. CORS changes are Sanity project settings, not website code changes.

For production/public frontend origins, keep public reads anonymous and add them with `--no-credentials`:

```bash
cd ~/projects/femme-events/website/"Femme Events Website Build"/Femme-Events-Website/studio
npx sanity cors list
npx sanity cors add https://femme-events-website.vercel.app --no-credentials
npx sanity cors add https://femmeevents.com --no-credentials
npx sanity cors add https://www.femmeevents.com --no-credentials
```

Verify by re-running `npx sanity cors list`, then load the exact deployed URL in browser automation and check console output for CORS/JS errors. If a custom domain returns a platform-level error like `400 Bad Request`, state that separately and do not conflate it with Sanity CORS.

For local QA origins:

```bash
cd ~/projects/femme-events/website/"Femme Events Website Build"/Femme-Events-Website/studio
npx sanity cors list
npx sanity cors add http://127.0.0.1:3000 --no-credentials
npx sanity cors add http://localhost:5173 --no-credentials
npx sanity cors add http://127.0.0.1:5173 --no-credentials
npx sanity cors add http://localhost:4173 --no-credentials
npx sanity cors add http://127.0.0.1:4173 --no-credentials
```

Keep credentials disabled for these public frontend local origins unless a future authenticated workflow explicitly needs cookies/tokens. Avoid wildcard CORS origins. Verify with `npx sanity cors list`, then smoke-test the exact local preview origin in the browser console.

For production CORS issues on the Femme Events frontend, the production origins should also be allow-listed with `--no-credentials` because the frontend uses anonymous public reads:

```bash
npx sanity cors add https://femme-events-website.vercel.app --no-credentials
npx sanity cors add https://femmeevents.com --no-credentials
npx sanity cors add https://www.femmeevents.com --no-credentials
```

Known safe origins currently used by the project include:
- `https://femmeevents.sanity.studio`
- `https://femme-events-website.vercel.app`
- `https://femmeevents.com`
- `https://www.femmeevents.com`
- `http://localhost:3000`, `http://127.0.0.1:3000`
- `http://localhost:3000`, `http://127.0.0.1:3000`
- `http://localhost:5173`, `http://127.0.0.1:5173`
- `http://localhost:4173`, `http://127.0.0.1:4173`
- `http://localhost:3333`

## Pitfalls

- Deploy success must be verified by the exact success text (`Success! Studio deployed to https://femmeevents.sanity.studio/`) or an authenticated Studio/browser check — **do not trust exit code alone**. Sanity CLI can print `Forbidden - User is missing required grant sanity.project.read` while the shell reports exit code 0.
- If deploy fails with `Forbidden - User is missing required grant sanity.project.read`, check which projects the current Sanity CLI login can see before retrying: `SANITY_STUDIO_PROJECT_ID=<id> SANITY_STUDIO_DATASET=production npx -p node@22 node ./node_modules/.bin/sanity projects list`. If Femme project `tc3rpyl9` is absent, the machine is logged into a Sanity account/token without Femme access; log in with an account that has the Femme project grant or add that account to the project.
- If the working repo has unrelated dirty files or is behind, deploy from a clean temporary worktree at `origin/main` instead of resetting the user's working tree: `git worktree add --detach /tmp/femme-events-studio-deploy origin/main`, run `npm ci && sanity deploy` in `/tmp/.../studio`, then `git worktree remove --force /tmp/femme-events-studio-deploy && git worktree prune`.
- If the local Sanity CLI fails under a bleeding-edge Node version with an ESM/CJS error from `yargs`, run the Sanity command through a supported Node one-shot instead of treating the CLI as permanently broken: `npx -p node@22 node ./node_modules/.bin/sanity ...` (or `npx -p node@22 -p sanity@<studio package version> sanity ...` when local deps are unavailable). See `references/vendor-import-from-static-data.md` for the import case.
- When reviewing Sanity client fail-fast code, do not claim the browser client has “no timeout” unless verified against the installed package. In `@sanity/client@7.22.0`, undefined timeout defaults to a long 5-minute request ceiling; `timeout: 10000` lowers that ceiling, and `maxRetries: 0` disables retry backoff.
- Schema/frontend mismatch: when reviewing or merging a PR that projects a new Sanity field in GROQ (for example `"image": image.asset->url`) or adds it to frontend TypeScript types, verify the matching field exists in `studio/schemas/<type>.ts`. If Studio lacks the field, Amanda cannot enter the content even though the frontend builds. Request changes before merge, then redeploy Studio after merge.
- Local branch divergence: `git pull` fails with divergent branches error. Use `git fetch + git reset --hard origin/main` instead.
- The repo path has spaces: `~/projects/femme-events/website/"Femme Events Website Build"/Femme-Events-Website`. Always quote or cd with quotes.
- Sanity CLI may print `/bin/sh: /Users/creator/projects/femme-events/website/Femme: No such file or directory` because of the space in the path, even when the command succeeds. Treat it as benign only if the command continues and ends with the expected success output (for deploy: `Success! Studio deployed to https://femmeevents.sanity.studio/`; for CORS: `CORS origin added successfully` or the origin appears in `npx sanity cors list`).
- `npx sanity deploy` shows a styled-components version warning — benign, ignore it.
- **Deploy command can produce exact success text even when the terminal wrapper reports non-zero afterward.** Do not blindly retry and risk duplicate/confusing deploy attempts. If the output contains the exact `Success! Studio deployed to <studio-url>` line, immediately verify independently with the hosted URL headers and `npx sanity schema list` from the same clean deploy worktree. Report the wrapper exit mismatch honestly, but treat deploy as complete when the success text plus independent checks agree.
- The `--delete-branch` flag on merge cleans up the remote branch but local tracking refs may linger. Not harmful.

## Repo info

### Femme Events

- Repo: sabnanikl-dev/Femme-Events-Website
- Studio URL: https://femmeevents.sanity.studio/
- Studio path: `studio/` (within monorepo)
- Schema registry: `studio/schemas/index.ts`

### JMD Menswear

Use the same merge-then-deploy discipline for JMD Studio PRs that modify Sanity Studio desk structure, schemas, or operator-visible Studio configuration.

- Repo: `sabnanikl-dev/jmd-6-holding-page-harness`
- Studio URL: `https://jmd-studio.sanity.studio/`
- Studio path: `studio/`
- Sanity project/dataset: `yjaks0cn` / `production`
- Common verification before deploy: `npm test`, `npm run validate:testimonials-schema` when testimonial-related, `npm --prefix studio run validate`, `npm --prefix studio run build`, `npm run build`

JMD deploy sequence after the user explicitly approves merge/deploy:

Support references:
- `references/jmd-testimonial-native-publish-live-smoke.md` — use after JMD testimonial native-publish/schema PRs when the remaining live task is to deploy Studio, make/confirm a Sanity test testimonial visible on non-prod, verify the endpoint/homepage, then close the issue.
- `references/jmd-studio-closeout-after-pr-deploy.md` — use when a JMD Studio issue is still open but the repo-side PR and hosted deploy may already have happened; verify existing merge/deploy evidence from current `origin/main` before starting any new builder/reviewer loop.

0. For stale-looking open JMD Studio issues, first check whether a prior PR/deploy already completed the work. If so, use the closeout-after-deploy reference: re-query the merged PR, verify current `origin/main` in a clean worktree, rerun deterministic Studio gates, check hosted URL/schema evidence, and close with a signed evidence comment instead of duplicating implementation.
1. Verify PR review surfaces and merge safety first: latest review decision approved, review threads empty/resolved, checks green, `closingIssuesReferences` empty if the issue must remain open, and no PR-only commit message carries `Closes/Fixes/Resolves #<issue>` when the hosted deploy is still a separate approval-gated step.
2. Merge the PR only after verification, then re-query the PR through REST and confirm `merged: true` plus `merged_at`/`merge_commit_sha` before deploying.
3. Deploy from a clean detached worktree at `origin/main`, not from the user's active branch:
   ```bash
   git fetch origin main:refs/remotes/origin/main
   git worktree add --detach /tmp/jmd-studio-deploy-main origin/main
   cd /tmp/jmd-studio-deploy-main
   npm --prefix studio ci
   npm --prefix studio run build
   cd studio
   npx sanity deploy
   ```
4. Treat the Sanity CLI success text as required evidence: `Success! Studio deployed to https://jmd-studio.sanity.studio/`.
5. Post-deploy, verify at least:
   ```bash
   curl -I https://jmd-studio.sanity.studio/
   cd /tmp/jmd-studio-deploy-main/studio && npx sanity schema list
   ```
   An unauthenticated browser may redirect to Sanity login, so do not claim an authenticated Studio UI screenshot unless you actually captured one. CLI deploy success + hosted URL headers + schema list are acceptable deploy evidence; authenticated UI evidence can remain a follow-up if login is unavailable.
6. Comment on the linked GitHub issue with merge SHA, deploy source, pre-deploy build result, exact Sanity deploy success text, hosted URL check, and any screenshot/auth limitation. Leave the issue open when the acceptance criteria still require authenticated hosted UI evidence.
7. Clean temporary worktrees and verify remote branch deletion when merge used `--delete-branch`.
