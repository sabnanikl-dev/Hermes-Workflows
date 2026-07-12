# Cloud-Agent Google Business Profile API Wiring

Use this when a project-level agent workspace needs read-only GBP API access without committing credentials.

## Goal

Make GBP access usable by local and cloud agents while preserving the dedicated OAuth boundary.

- Local agents use project-local symlinks into `~/.hermes`.
- Cloud agents use mounted secret files or base64 secret environment variables.
- Helpers never print access tokens, refresh tokens, client secrets, or raw credential JSON.
- Public/account mutations remain approval-gated even when API auth works.

## Local workspace pattern

Create project-local credential symlinks:

- `.credentials/google-business-profile-token.json` points to `$HOME/.hermes/google_gbp_token.json`.
- `.credentials/google-gbp-client-secret.json` points to `$HOME/.hermes/google_gbp_client_secret.json`.

Keep `.credentials/`, `.env`, `.env.*`, `__pycache__/`, and `*.pyc` ignored. Use `chmod 700 .credentials`. Prefer adding the ignore rules to both tracked `.gitignore` and local `.git/info/exclude` so the protection exists before and after the guardrail commit.

Use a project env file such as `.env.google-business-profile` with paths/config only:

- `GOOGLE_BUSINESS_PROFILE_ACCOUNT=karanagent20@gmail.com`
- `GOOGLE_BUSINESS_PROFILE_TOKEN_FILE=/secure/path/google_gbp_token.json`
- `GOOGLE_BUSINESS_PROFILE_CLIENT_SECRET_FILE=/secure/path/google_gbp_client_secret.json`
- `GOOGLE_BUSINESS_PROFILE_DEFAULT_ACCOUNT=accounts/...`
- `GOOGLE_BUSINESS_PROFILE_DEFAULT_LOCATION_MATCH='brand|domain'`

## Cloud-agent pattern

Prefer mounted secret files when the platform supports them:

- `GOOGLE_BUSINESS_PROFILE_TOKEN_FILE=/secure/path/google_gbp_token.json`
- `GOOGLE_BUSINESS_PROFILE_CLIENT_SECRET_FILE=/secure/path/google_gbp_client_secret.json`

For platforms that only support env secrets, accept base64 JSON:

- `GOOGLE_BUSINESS_PROFILE_TOKEN_JSON_B64`
- `GOOGLE_BUSINESS_PROFILE_CLIENT_SECRET_JSON_B64`

A helper should prefer sources in this order:

1. `GOOGLE_BUSINESS_PROFILE_TOKEN_JSON` / `GOOGLE_BUSINESS_PROFILE_TOKEN_JSON_B64`
2. `GOOGLE_BUSINESS_PROFILE_TOKEN_FILE`
3. project `.credentials/google-business-profile-token.json`
4. canonical `~/.hermes/google_gbp_token.json`

Do the same for the OAuth client secret if the token JSON does not include `client_secret`.

## Required smoke tests

Before telling the user a local or cloud agent can use GBP:

1. Compile helper scripts with the intended Python interpreter.
2. Verify local secret hygiene first: `git check-ignore -v .credentials .env.google-business-profile`, `git ls-files .credentials .env.google-business-profile`, and `git ls-files -o --exclude-standard` should prove local credential/env files are ignored and not tracked/addable.
3. Run the dedicated OAuth helper or token verifier and confirm:
   - account email is the intended account,
   - `business.manage` is present,
   - account discovery succeeds.
4. Run the project helper locally and confirm it finds the target location.
5. Run the project helper with the env-secret path, e.g. `GOOGLE_BUSINESS_PROFILE_TOKEN_JSON_B64`, and confirm it finds the target location.
6. Run a secret hygiene check over changed project files for raw access-token / refresh-token / private-key patterns.
7. Commit only safe guardrail files such as `.gitignore`, `AGENTS.md`, docs, and helper scripts; never commit `.credentials/`, `.env.*`, token JSON, client-secret JSON, or copied credential contents.

## Approval boundary

Read-only account/location discovery and Business Information reads are allowed under this pattern. Do not use the helper to edit profile fields, publish LocalPosts, upload media, reply to reviews, change ownership, or mutate public/account state without explicit approval.