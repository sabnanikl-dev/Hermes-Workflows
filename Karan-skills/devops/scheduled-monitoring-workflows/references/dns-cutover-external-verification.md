# DNS Cutover Watchdogs with External HTTPS Verification

Use this pattern for a read-only watchdog after an approved website DNS mutation, especially when email must remain on the old host or the operator's local network is not a trustworthy HTTPS vantage point.

## Evidence contract per tick

1. Record the exact local decision-zone timestamp (for example `TZ=America/New_York date ...`).
2. Re-read the live tracker issue and the exact execution-evidence comments. Treat superseding comments and human smoke-test evidence as current state; never infer it from an older execution comment alone.
3. Query both authoritative nameservers and at least three named public recursive resolvers for:
   - apex web record;
   - `www` record;
   - MX;
   - mail-host A/AAAA as applicable;
   - apex TXT policy/verification records;
   - DKIM selector TXT.
4. Create fresh external HTTPS measurements for the apex and canonical redirect host. Do not reuse a prior tick's measurement IDs.
5. Verify any separately gated production feature remains in its approved state from the deployed artifact when possible (for example, a committed `PRODUCTION_ENABLED=false` flag in the live analytics asset), not only from the local checkout.
6. Emit the exact alert payload or silence according to the job contract. Include timestamp, authoritative/public counts, external measurement IDs, HTTPS verdict, protected mail-state verdict, gated-feature state, tracker state, and `PID:none` when no process exists.

### Tracker and deployed-feature readback details

- Read named execution-evidence comments directly by comment ID **and** inspect a bounded issue-comment collection for newer superseding evidence. Do not trust `comments(last: N)` as chronological truth: tracker ordering can omit the newest-created comment from that slice. Fetch a sufficiently bounded collection, sort by `createdAt`, and report the latest state for each issue.
- Keep the issue workflow state separate from the evidence verdict. An issue may remain `In Progress` while its latest comment legitimately records a healthy cutover checkpoint.
- If the tracker records human cellular or mailbox checks as passed, report them as passed; do not keep calling them pending from an older execution comment.
- When production activation is separately gated, create a fresh external GET measurement for the deployed authority asset or config path in addition to the apex and redirect-host measurements. Require the disabled marker, reject an enabled marker, and fail closed when the relevant bytes are absent. A truncated response is usable only when the required marker is actually present in the captured body.
- Redact certificate material and DNS verification payloads from notifications. Report only safe certificate facts (authorization and subject hostname), HTTP status/server, resolver or probe counts, measurement IDs, and presence/match verdicts for SPF, DKIM, and verification TXT records.

## DNS classification

- **HEALTHY:** authoritative records are exact; the configured public-resolver quorum is on the approved values; external apex content and canonical redirect checks pass; protected mail/TXT records match; no gated feature was activated.
- **PROPAGATING:** authoritative values are exact, but a public resolver or external probe still reaches the recorded old web target within the prior TTL. This is not alone a rollback trigger.
- **ALERT:** authoritative drift, protected mail/TXT drift, an unexplained third target, externally reproduced TLS/canonical/content failure on the new host, forbidden feature activation, or contradictory tracker evidence.

Normalize trailing dots and harmless answer ordering before comparison. Keep an explicit allowlist containing only the approved new target and recorded rollback target; any third target fails closed. A timeout on one record is missing evidence, not drift: retry that exact read using the same server and, when appropriate, TCP before classifying.

## External HTTPS checks with Globalping

A working API shape for an apex GET is:

```json
{
  "type": "http",
  "target": "example.com",
  "locations": [{"magic": "world", "limit": 3}],
  "measurementOptions": {
    "request": {"method": "GET", "path": "/"}
  }
}
```

POST it to `https://api.globalping.io/v1/measurements`, capture the returned `id`, then poll `GET /v1/measurements/{id}` until `status == "finished"`. Require the requested probe count to produce completed results; a created-but-unfinished measurement proves nothing.

For each apex result, inspect at minimum:

- `result.statusCode`;
- `result.resolvedAddress`;
- `result.headers.server`;
- `result.tls.authorized`;
- `result.tls.subject.CN`;
- a high-signal expected marker in `result.rawBody`/`result.body`.

For a canonical host such as `www`, a HEAD request is sufficient when the contract is status/location/TLS only. Require the exact redirect status and exact `Location` value, plus authorized TLS for the requested hostname. Report only authorization, subject hostname, status, server, resolver/probe counts, and measurement IDs—never certificate blobs or credentials.

Keep DNS-target classification separate from HTTP connection addressing. Named DNS queries decide whether the apex A/CNAME is the approved new value, the recorded rollback value, or an unexplained third target. A Globalping HTTP result's `resolvedAddress` is the final connection address and may legitimately be a different CDN/edge IP after following an approved CNAME; do not compare it directly to the dashboard A/CNAME and call it drift. For that HTTP probe, require the provider/server identity, authorized TLS for the requested hostname, exact status/redirect, and content marker. Escalate an unfamiliar connection IP only when those identity checks fail or the DNS queries themselves expose an unapproved target.

Globalping may cap the captured response body. Choose a marker expected early in the document, and fail closed if the marker cannot be observed rather than treating response size as content proof.

## Local-network limitations

When a previously documented local resolver, ISP, security layer, or transparent proxy makes the operator's machine an unreliable vantage point, do not use local curl/browser TLS as a rollback trigger. This exception must be narrow and evidence-backed: authoritative DNS plus fresh completed external probes decide public health. Do not generalize it into “local checks never matter.”

A claimed second-network result requires a completed external measurement or a directly recorded human check. Never upgrade “scheduled” or “requested” into “passed.”

## Deadline behavior

Before the decision deadline, report HEALTHY/PROPAGATING/ALERT according to current evidence. At or after the configured deadline, include an explicit final continue/rollback recommendation and list any still-pending manual gates such as cellular smoke or bidirectional mailbox testing. Do not claim those manual checks are pending if the latest tracker evidence says they passed.