# Evidence-Bundle Acceptance Preflight

Use this before dispatching independent review for reports or datasets backed by raw provider evidence, normalized rows, hashes, and tracker acceptance criteria.

## Why this exists

A bundle can be numerically correct yet still fail acceptance because required context exists only inside opaque provider payloads, narrative conclusions merely imply their evidence links, or temporary callback credentials are preserved in would-be committed evidence. Find these seams before freezing hashes; otherwise every repair invalidates in-flight review.

## Pre-freeze sequence

1. **Reconstruct the governing contract**
   - Read the live tracker body and authoritative upstream artifact.
   - Convert every acceptance criterion into a machine-checkable or manually inspectable gate.
   - Record blocking severities and `Continue / Narrow / Stop` semantics before review.

2. **Validate normalized rows against the consumer contract**
   - For every observation require explicit fields for evidence ID, raw-evidence path, query/input, geography or coordinates, method/provider, device/tool context, and normalized timestamp.
   - Do not count a field as satisfied merely because it can be recovered from the raw payload.
   - Verify every evidence path exists and representative normalized values equal their raw source values.
   - Assert expected row counts and key uniqueness across the whole packet.

3. **Bind conclusions explicitly**
   - Tables containing evidence IDs are not enough when the contract says conclusions must cite evidence.
   - Bind each material narrative finding, hypothesis, recommendation, limitation, and success measure to immutable IDs or a clearly defined ID range.
   - Avoid ambiguous wildcard references unless the packet itself defines the complete member set.

4. **Reconcile arithmetic and authority**
   - Independently sum component costs from provider evidence and balance/ledger readback.
   - Compare actual spend with the approved ceiling.
   - Record retries, failed requests, and whether they were billed.
   - Confirm the packet made no mutation outside the approved authority envelope.

5. **Sanitize operational callback material before Git staging**
   - Search requests, task-post responses, callback payloads, and summaries for `postback_url`, `pingback_url`, callback URLs, webhook tokens, signed URLs, request authorization, access tokens, and unnecessary PII.
   - Deleting or expiring an endpoint does not by itself make its token suitable for version control.
   - Preserve provider fidelity with a sanitized immutable derivative: replace only the sensitive value with a stable marker such as `[REDACTED CALLBACK URL]`, record the transformation and original file hash in a redaction manifest, and keep the unsanitized original outside Git in the approved private evidence store.
   - Never silently alter raw evidence while still calling it byte-identical provider output.

6. **Freeze once**
   - Run deterministic generation twice and compare hashes.
   - Run syntax/schema checks, source-link checks, secret/PII scans, and `git diff --check`.
   - Produce the exact candidate manifest and intended commit path list; explicitly exclude unrelated workspace files.
   - Only now dispatch independent review with exact hashes and superseded-hash warnings.

## Review and repair

- Any candidate-byte change invalidates every in-flight verdict for the prior hash.
- Mark prior hashes as superseded, rerun the full preflight, and dispatch a fresh exact-hash review.
- Do not create an acceptance sidecar until independent reviewers return a blocking-clean verdict for the final bytes.
- Bind the sidecar to report hash, normalized-data hash, manifest hash, reviewer verdict, blocking counts, and any accepted advisory findings.

## Commit and tracker closeout

1. Stage from the predeclared path list, not broad directory globs.
2. Inspect staged names and staged secret scan; confirm unrelated files remain unstaged.
3. Commit accepted artifacts and verify the commit tree contains the exact accepted hashes.
4. If pushed, verify the remote/PR commit directly; never infer remote state from local Git.
5. Post tracker closeout only after acceptance and repository verification.
6. Read back the exact comment/status/attachments and preserve the tracker-issued IDs.
7. Perform durable-knowledge promotion only after final synthesis; transient rankings and one-time provider observations usually remain ticket evidence.

## Common failure modes

- Dispatching review before a complete contract-to-artifact matrix exists.
- Treating raw-payload recoverability as normalized-schema compliance.
- Treating nearby table IDs as citations for uncited narrative conclusions.
- Keeping a dead callback URL in Git because the endpoint now returns 404.
- Repairing bytes while old reviewers are still running, then accepting their stale verdict.
- Hashing only headline outputs while failing to manifest supporting raw evidence.
- Broad staging in a dirty worktree.
