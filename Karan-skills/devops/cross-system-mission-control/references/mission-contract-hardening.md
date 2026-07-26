# Mission Contract Hardening Checklist

Distilled from the JMD Visibility Mission Contract revision 2 hardening pass (2026-07-24), where a draft contract was reviewed against the Sovereign Rig AIOS invariants (owner-controlled files, replaceable brains, file-over-AI, canonical systems retain authority, independent verification survives brain swaps). Use when drafting or hardening any mission contract — especially when the environment has duplicate clones, a planned control plane, or multiple possible executors.

## Checklist

1. **Path indirection for the working repo.**
   - If more than one local clone of the remote exists, the contract names ONE operational clone as a recorded decision (path + date), forbids mission branches/worktrees/builds in the others, and classifies changing it as a material edit.
   - Workers receive `canonical_workdir` resolved from that decision, not from habit or cwd.
   - Example failure prevented: a supervisor building in a clone that a later canonicalization audit retires.

2. **Mutual exclusion with concurrent structural efforts.**
   - Any parallel effort that could move, prune, or consolidate the mission's paths (repo canonicalization, vault migration, AIOS-style control plane buildout) is explicitly blocked while the mission supervisor is active — stated in BOTH documents.
   - The mission grants that effort no authority over mission clones or tracker state.

3. **Claims as tracker comments, never local state.**
   Claim comment schema (posted on the claimed issue):
   ```text
   mission-claim v1
   contract_revision: <N>
   contract_digest: <sha256 of approved frozen contract file>
   issue: <tracker ID>
   packet_digest: <sha256 of normalized work packet>
   executor: <model/profile identity>
   claimed_at: <ISO-8601>
   ttl: <e.g. 4h>
   ```
   - Stale claim = past TTL with no heartbeat comment → reclaimable; comment the reclamation before proceeding.
   - Duplicate/ambiguous claims → CONFLICT, fail closed.
   - Mission lock is derivable from open claims; a local lockfile is a cache hint only.

4. **Normalized work packets + executor provenance.**
   Packet fields: `project_id, canonical_workdir, source_of_truth_issue, harness_paths, allowed_tools, authority_envelope, acceptance_criteria, verification_commands, artifact_destinations, completion_schema`.
   - Any capable executor (Hermes, Claude Code, Codex, future) consumes the same packet; adapters add launch syntax only, never rewrite intent or widen authority.
   - Provenance (which executor/model) is recorded in the claim, the PR body, and the closeout comment.
   - Completion is judged by commands/artifacts/readbacks, never executor self-report.

5. **Freeze/digest mechanics.**
   - Digest = SHA-256 of the exact bytes of the contract file, computed at freeze; recorded in frontmatter AND as a comment on the tracker mission-root issue.
   - Supervisor recomputes at every startup; mismatch = halt, do not execute.
   - Define up front which sections are material (definition of complete, operational clone, mappings/ordering, authority envelope, the freeze section itself → revision bump + fresh approval) vs non-material (typos, snapshot refresh annotations, link repairs → groomable).

6. **Explicit inspection state machine as a table.**
   Every read-only inspection terminates in exactly one named state: `RESUME_ACTIVE / SELECT_TRACKER_WORK / SELECT_CODE_WORK / WAITING_FOR_REVIEW / WAITING_FOR_MERGE / WAITING_FOR_HUMAN_DECISION / WAITING_FOR_LIVE_APPROVAL / MONITORING / CONFLICT / COMPLETE`. Prose stop-condition lists are not a substitute.

7. **Monitoring/delayed-completion states get a mechanism.**
   - Revision-bound cron (digest-checked), watchdog cadence (silent unless meaningful change; error alert on failure).
   - End date derived from a verified event (e.g. recorded verified-cutover date), not a calendar guess.
   - Findings land on the tracker issue; durable-knowledge system receives only source-backed knowledge, never metric mirrors.
   - Self-disable: pause cron + close issue with evidence + final report.

8. **Credential-gate wording.**
   Contracts and packets carry credential REFERENCES only (provider name / env var name), never values. Agents never enter credentials, passwords, OAuth codes, or CAPTCHAs. OAuth runs through the approved agent account with the human present.

9. **Independence clause.**
   The mission must not require an unapproved control plane (or any other unapproved draft) to exist. Anticipated future integrations (registry path refs, packet schemas) are self-contained in the contract; adopting them later is additive and separately approved.

10. **No local board systems in any role.**
    Karan's standing decision (2026-07-24): no Kanban/local-board tracker, lane mirror, or visibility layer anywhere in a mission. Authority stays in the real trackers; mission state must reconstruct with all local board state deleted. Rationale: local board DB has a corruption history and is single-machine; routing state through it also breaks replaceable-executor goals. Do not re-propose.

11. **Pre-activation normalization is a gated deliverable.**
    Tracker-structure fixes the recon surfaced (missing `blocks` relations, parent/child state ambiguity, two-way cross-system links) run as a readback-verified deliverable BEFORE supervisor activation — not as informal preamble — because they mutate structures the approval was bound to.

## Review heuristics that worked

- Read the contract and the control-plane/architecture plan side by side; most hardening gaps are cross-document conflicts (e.g. one doc's active worktrees vs the other's planned consolidation) that neither doc shows alone.
- Check the recon snapshot for implicit machine-local assumptions (paths, clone identity) — they are invisible until you ask "which clone does the supervisor build in?"
- Verify claims about local state before opining (e.g. integrity-check a local DB, count backup artifacts) — the evidence can flip the recommendation (Kanban: viable-as-cache in theory → excluded in practice once corruption history and dormancy were confirmed).
