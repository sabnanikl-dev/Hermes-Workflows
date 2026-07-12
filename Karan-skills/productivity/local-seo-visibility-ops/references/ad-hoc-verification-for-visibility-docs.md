# Ad-hoc verification for visibility docs with API exports

Use this when a visibility-ops repo has no canonical test/lint/build command, but the task changed Markdown report/index files and/or structured API export files.

## Pattern

1. Create a temporary verifier script with Python `tempfile` under the OS temp directory and a `hermes-verify-` filename prefix.
2. Run the verifier against the changed files and any supporting export files used by the report.
3. Clean up the temporary verifier in a `finally` block where possible.
4. Report the result explicitly as **ad-hoc verification**, not “suite green.”

## What to verify

For docs-first local SEO/Search Console/GBP artifacts, include checks that match the changed behavior:

- Expected changed files exist.
- Folder README/index files reference newly added artifacts.
- `git diff --check` passes.
- Markdown has final newlines and no trailing whitespace.
- JSON exports parse successfully.
- Secret marker scan passes for obvious sensitive strings such as `access_token`, `refresh_token`, `client_secret`, `Authorization`, and `Bearer`.
- Human-readable Markdown report facts match the structured API export it cites.
- Approval boundaries are preserved in both export/report text when no public/account mutation was approved.

## Search Console-specific checks

When the artifact summarizes Search Console state, cross-check export fields and report snippets for:

- Operation mode is read-only when no explicit mutation approval exists.
- OAuth identity and Search Console scope are recorded without tokens.
- Property and permission level match the intended property.
- Production `robots.txt`, sitemap, and redirect fetch statuses are reflected accurately.
- `sitemaps.list` / `sitemaps.get` state is correctly interpreted as submitted/known vs not submitted/known.
- URL Inspection coverage/canonical fields match the written interpretation.
- Search Analytics numbers in the report match the export after any rounding.

## Pitfalls

- Do not treat lack of a canonical test suite as permission to skip verification. Create a focused verifier for the artifact contract.
- Do not run only `git diff --check` when a Markdown report is derived from JSON/API evidence; also verify evidence consistency.
- Do not claim public/account actions happened unless the verifier/API evidence proves they did. Preserve “not submitted/no mutation” wording when approval was absent.
- Avoid piping helper output directly into Python interpreters in environments that flag that pattern. Prefer writing helper output to a temp file, then reading the temp file from Python.
