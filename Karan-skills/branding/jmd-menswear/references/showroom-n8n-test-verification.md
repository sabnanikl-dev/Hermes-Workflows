# JMD Showroom n8n Test Verification Notes

Use this reference when verifying JMD showroom photo automation issues that involve the Drive → n8n → Sanity path, especially required Hermes verification before moving Linear items forward.

## Verification boundary

- Treat JMD showroom automation verification as a safety gate, not a launch step.
- Explicitly report what was **not** done: no production Drive usage, no production Sanity writes, no schedule activation, no website deploy, and no client-facing/public changes unless separately approved.
- Keep workflow exports importable and inactive by default; verify `active=false` before reporting safety.
- For deterministic review of exported n8n workflows, check:
  - export is an importable object, not an array;
  - no non-empty credential objects in committed exports;
  - no forbidden production IDs/URLs/secrets;
  - expected node and connection structure;
  - Drive/Sanity nodes are intentionally unbound or bound only to approved test credentials.

## Test credential handling

- Prefer a least-privilege service-account path when credentials and Google tooling already exist, but do not create broad production access just to satisfy a local test.
- If the installed n8n Google Drive credential type is OAuth2-only, an OAuth2 fallback can be acceptable **only inside the user-approved test scope**.
- When OAuth2 is used for JMD-35-style Drive tests, state the containment honestly: OAuth grants account-level Drive capability, so the practical boundary is operational/config based:
  - inactive workflow;
  - test folder ID only;
  - `DRY_RUN=true` where applicable;
  - credential bound only to the intended Drive nodes;
  - Sanity write credentials unbound until explicitly approved;
  - secrets stored locally only and never posted or committed.
- Store redacted evidence locally (for example under a local `.jmd35-secrets/`-style directory) and verify secret file permissions are restrictive when possible.

## Evidence to collect before commenting in Linear

- Local tests passed, e.g. `npm test` and workflow export validation script.
- Independent scan of public handoff/docs files shows no secret-like findings.
- n8n API or credential test returns a real success response, not inferred success.
- Workflow remains inactive and schedule/public side effects remain disabled.
- Linear comment is verified after posting, including the issue key and key evidence phrases.

## Reporting pattern

Use a compact closeout:

1. What was verified.
2. What credentials/resources were configured, with names/types only — never secret values.
3. Safety boundary / what was not changed.
4. Real test results.
5. Remaining approval-gated next steps.

Avoid implying that a successful credential test authorizes execution, Sanity writes, schedule activation, or deploys.