# n8n Local Operations Notes

Use these notes when the user asks to run or access a local n8n server from Hermes.

## Starting n8n locally

1. Check whether n8n is already installed and whether the default port is occupied:
   ```bash
   command -v n8n || true
   command -v npm || true
   command -v node || true
   lsof -nP -iTCP:5678 -sTCP:LISTEN || true
   pgrep -fl 'n8n|node.*n8n' || true
   ```
2. If port `5678` is free, start n8n as a tracked Hermes background process, not with shell `&`:
   ```bash
   N8N_HOST=127.0.0.1 N8N_PORT=5678 N8N_SECURE_COOKIE=false npx --yes n8n start
   ```
   Use `background=true` and a readiness watch pattern such as `Editor is now accessible`, `n8n ready`, or `Server is listening`.
3. Verify readiness independently:
   ```bash
   lsof -nP -iTCP:5678 -sTCP:LISTEN || true
   curl -sS -I http://127.0.0.1:5678/ | sed -n '1,12p'
   ```
   Report the local URL only after an HTTP `200 OK` or equivalent reachable response.

## Password / account handling

- Do not claim to know a plaintext n8n password. n8n stores the user password hashed in the local SQLite DB.
- If the user asks “what is my password?”, first identify the owner account without exposing hashes:
  ```bash
  sqlite3 /Users/creator/.n8n/database.sqlite ".tables" | tr ' ' '\n' | grep -Ei 'user|auth|settings|credential'
  sqlite3 -header -column /Users/creator/.n8n/database.sqlite "SELECT id,email,firstName,lastName,roleSlug,disabled,mfaEnabled FROM user;"
  ```
- Summarize the account email/name/role/MFA state. Offer a reset only if needed.
- Resetting n8n user management or setting a new password is an account mutation; get explicit approval before doing it.

## Pitfalls

- `npx --yes n8n start` can take a while on first run and emit many npm peer/deprecation warnings. The durable signal is whether a `node ... n8n start` child process is listening on port `5678` and the HTTP endpoint responds.
- Avoid printing credential rows from `credentials_entity` or password hashes from `user.password` in the chat unless specifically needed for a safe diagnostic, and redact sensitive values.
