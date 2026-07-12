# Project-local Google credential wiring for visibility repos

Use this when a docs-first visibility repo needs local agents to use GBP and Google Search Console credentials without ever committing credential material.

## Pattern

1. Keep canonical OAuth client secrets and tokens outside the repo, usually under `~/.hermes/`, with file mode `0600`.
2. Create a repo-local ignored `.credentials/` directory with mode `0700`.
3. Add symlinks, not copied JSON, from `.credentials/` to canonical credential files. Typical Femme/Papi names:
   - `.credentials/google-gbp-client-secret.json` -> `~/.hermes/google_gbp_client_secret.json`
   - `.credentials/google-business-profile-token.json` -> `~/.hermes/google_gbp_token.json`
   - `.credentials/google-search-console-readonly-token.json` -> `~/.hermes/google_search_console_jmd_gbp_agent_token.json`
   - `.credentials/google-search-console-write-token.json` -> `~/.hermes/google_search_console_write_token.json`
4. Add local env files with path/config values only:
   - `.env.google-business-profile`
   - `.env.google-search-console`
5. Protect the files in tracked `.gitignore` and local `.git/info/exclude`:
   - `.credentials/`
   - `.env`
   - `.env.*`
   - `!.env.example`
6. Add a short `AGENTS.md` section that tells future agents these are local-only credentials, not repo artifacts.
7. Commit only the guardrails (`.gitignore`, `AGENTS.md`, helper scripts/docs if any). Never commit `.credentials/`, `.env.*`, token JSON, client-secret JSON, or copied credential contents.

## Verification checklist

Run a focused ad-hoc verifier when no canonical test suite exists. It should check:

- `.credentials/` exists and is mode `0700`.
- Each credential path is a symlink to the expected `~/.hermes` canonical file.
- Canonical credential targets exist and are mode `0600`.
- Env files contain only path/config values, not inline JSON, tokens, PEM/private-key material, or raw secrets.
- `git check-ignore -v` confirms `.credentials/` and `.env.*` are ignored.
- `git ls-files` confirms local-only paths are not tracked.
- `git ls-files -o --exclude-standard` confirms they do not appear as addable untracked files.
- Tracked guardrail files scan clean for obvious secret markers.
- Live smoke tests verify only non-secret facts: expected account email, scope presence, account/property visibility, HTTP status, and row counts.

## Read-only smoke tests

For GBP, verify:

- OAuth identity is the expected account.
- `https://www.googleapis.com/auth/business.manage` scope is present.
- Account discovery returns HTTP 200 and shows the expected account/location.

For GSC, verify:

- Read-only token identity is the expected account.
- `https://www.googleapis.com/auth/webmasters.readonly` is present.
- `sites.list` returns HTTP 200 and shows the expected property.
- A tiny Search Analytics query returns HTTP 200.
- If a write token is wired, verify `https://www.googleapis.com/auth/webmasters` is present, but keep mutations approval-gated.

## Pitfalls

- Do not copy credential JSON into the repo to “make it easier” for other agents. Use symlinks or mounted secret files.
- Do not rely only on `.gitignore`; also verify with `git check-ignore` and `git ls-files` before reporting safety.
- Do not print tokens, refresh tokens, client secrets, or raw credential JSON in summaries. Report only account email, scope presence, target paths, HTTP statuses, and visible resource IDs.
- In docs-first visibility repos, commit the safe guardrail files locally after verification so future agents inherit the protection before any Linear issue is marked Done.
