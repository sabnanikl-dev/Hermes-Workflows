# Project-local Google Search Console wiring

Use this when a repo/workspace should let future agents use Google Search Console without copying raw OAuth secrets into the repo.

## Pattern

1. Keep canonical credential files outside the project, usually under `~/.hermes/`.
2. Create a project-local ignored credential directory, for example `.credentials/`, with symlinks back to the canonical files:
   - `.credentials/google-search-console-readonly-token.json` -> `~/.hermes/google_search_console_jmd_gbp_agent_token.json`
   - `.credentials/google-search-console-write-token.json` -> `~/.hermes/google_search_console_write_token.json` when an approved write token exists
   - `.credentials/google-gbp-client-secret.json` -> `~/.hermes/google_gbp_client_secret.json`
3. Add or verify ignore rules in both tracked `.gitignore` and local `.git/info/exclude` where practical:
   - `.credentials/`
   - `.env`
   - `.env.*`
   - `!.env.example`
4. Add a project-local env file containing path/config values only, not secret values:
   - `GOOGLE_SEARCH_CONSOLE_ACCOUNT=karanagent20@gmail.com`
   - `GOOGLE_SEARCH_CONSOLE_READONLY_TOKEN_FILE=<project>/.credentials/google-search-console-readonly-token.json`
   - `GOOGLE_SEARCH_CONSOLE_WRITE_TOKEN_FILE=<project>/.credentials/google-search-console-write-token.json`
   - `GOOGLE_SEARCH_CONSOLE_CLIENT_SECRET_FILE=<project>/.credentials/google-gbp-client-secret.json`
   - `GOOGLE_SEARCH_CONSOLE_DEFAULT_SITE=<property>`
5. Provide a small helper CLI/script that:
   - loads the project env file automatically,
   - refreshes the OAuth token,
   - calls tokeninfo for email/scope verification,
   - calls `webmasters/v3/sites`,
   - runs a tiny `searchAnalytics.query` smoke test.
6. Document usage in the repo’s agent instructions and a docs page. Future agents should run the smoke command before claiming connected GSC access works.

## Safety checks

- Do not copy token/client-secret JSON contents into the repo.
- Do not print access tokens, refresh tokens, or client secrets.
- Confirm ignored secret paths with `git check-ignore -v` and confirm they are not tracked with `git ls-files <paths>`; for non-git workspaces, still add `.gitignore`/agent docs because the workspace may become a repo later.
- `git ls-files -o --exclude-standard` should not show `.credentials/` or `.env.google-search-console` as addable untracked files.
- Ensure project-local env files contain only paths/config, not raw secret values. Variable names like `GOOGLE_SEARCH_CONSOLE_CLIENT_SECRET_FILE` are okay if the value is a path.
- Commit only safe guardrails (`.gitignore`, agent instructions, helper scripts/docs). Never commit `.credentials/`, `.env.*`, OAuth token JSON, client-secret JSON, or copied credential contents.

## Verification

If no canonical test/lint/build command exists for the workspace, create a temporary ad-hoc verifier under the OS temp directory using a `hermes-verify-` filename prefix. Have it check:

- changed files exist,
- symlinks point to the intended canonical credential files,
- canonical credential files exist and are mode `0600`,
- `.credentials/` is mode `0700`,
- ignore rules cover secret paths,
- `git check-ignore -v` confirms the credential/env files are ignored,
- `git ls-files` confirms those paths are not tracked,
- docs/agent instructions mention the smoke command and safety boundary,
- helper script compiles/parses,
- helper `smoke` reaches live GSC as the expected account,
- helper query returns live Search Analytics JSON,
- tracked guardrail files do not contain obvious raw-secret markers.

Clean up the temporary script and report the result explicitly as ad-hoc verification, not “suite green.”
