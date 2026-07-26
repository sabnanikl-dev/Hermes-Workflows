---
name: session-history-synthesis
description: Reconstruct a calendar day, project workstream, or operational closeout from Hermes session history using session_search, state.db, raw transcript fallbacks, lineage deduplication, and compact evidence-first synthesis.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [session-history, synthesis, sqlite, daily-log, project-status, closeout]
    related_skills: [daily-log, knowledge-memory-workflows]
---

# Session History Synthesis

## Purpose

Use this class-level workflow when the deliverable depends on reconstructing what happened across one or more Hermes sessions: daily logs, project-status refreshes, handoffs, operational closeouts, or “where did we leave this?” summaries.

The goal is an evidence-backed workstream narrative, not a dump of every session or tool call.

## When to Use

- A calendar day may contain multiple root sessions, continuations, subagents, and crons.
- `session_search` date recall is sparse or noisy.
- A long task spans compaction-generated child sessions.
- The final summary must distinguish completed, pending, blocked, and merely discussed work.
- A status/log artifact has a strict character budget.

Do not use this skill for a single small session whose final answer already contains everything required.

## Evidence Hierarchy

1. **Current source system** for live state: GitHub, Linear, files, deployments, or dashboards.
2. **Hermes `state.db` inventory** for complete target-window session discovery.
3. **`session_search`** for semantic context and readable decision windows.
4. **Raw session/request JSON** when SQLite is missing or incomplete.
5. Final assistant summaries as leads, not substitutes for live verification when current state matters.

## Workflow

### 1. Define the time or topic boundary

For calendar synthesis, compute start/end epochs in the requested timezone; use `America/New_York` for Karan’s daily operational logs unless the task says otherwise. Use an IANA timezone conversion rather than assuming a fixed UTC offset, make the end boundary exclusive, and include sessions that began earlier but contain messages inside the target window.

When the request names exact lineages, a strict cutoff, or redaction rules, follow `references/strict-time-window-and-redaction.md`. In particular, do not count duplicated compaction summaries, preserved task lists, or delayed notifications copied into a post-cutoff continuation as new pre-cutoff work, even if their stored timestamps retain earlier values.

### 2. Run lightweight semantic discovery

- Browse recent sessions.
- Run one or more low-limit targeted searches.
- Treat date-keyword search as a lead, never the full inventory.
- Prefer keywords from titles/previews over broad common dates found inside generated reports.

### 3. Enumerate the deterministic inventory

When available, query `~/.hermes/state.db` for sessions joined to messages inside the target window. Collect only compact metadata first: session ID, title, source, parent ID, message/tool counts, and first/last in-window timestamps.

See `references/sqlite-lineage-probe.md` for the query pattern.

### 4. Collapse sessions into lineages

Follow `parent_session_id` to the root. Compaction continuations are one workstream, not separate accomplishments. Exclude `subagent` and `bg_*` children when their result is already represented by the parent.

When the user specifies a lineage **from root through an exact endpoint**, reconstruct the endpoint’s ancestor chain back to the root and use that chain as the narrative boundary. Treat subagents branching from that chain as supporting evidence only; exclude later continuations or sibling branches beyond the named endpoint unless explicitly requested. This prevents same-topic work performed later that day from leaking into the requested historical state.

Include cron sessions only when they wrote a durable artifact, changed state, produced an actionable finding, or emitted a meaningful report. Omit `NO_ALERT`, `NO_CHANGE`, and empty monitoring runs.

### 4a. Optionally parallelize large inventories

When several large root lineages are independent, workers may extract them in parallel. Partition by non-overlapping root lineages and give every worker exact IDs, timezone, exclusive cutoff, redaction rules, and read-only scope. Require message-level cutoff handling for lineages that cross midnight.

Treat worker summaries as secondary synthesis rather than proof: the parent reconciles overlaps, independently verifies artifact writes or live state, combines the final narrative, and measures the complete output. Do not delegate one or two short lineages because orchestration overhead can exceed the value. See `references/parallel-lineage-synthesis.md`.

### 5. Extract compact evidence

For each lineage, begin with:

- first substantive user request;
- final substantive assistant resolution;
- selected intermediate user/assistant turns only when needed for decisions, corrections, or unresolved next steps.

Avoid full tool-call bodies by default. Large writes and persisted search payloads often dominate context without improving the synthesis.

### 6. Reconcile state

Classify each workstream as completed, in review, blocked, pending approval, or discussed only. If the output will update a current status source, verify that state in the authoritative system before writing “completed.”

### 7. Synthesize by workstream

Group related sessions into one project bullet. Preserve:

- what was done or decided;
- why the decision mattered;
- verification category;
- current pending state and next step.

Omit temporary branch names, commit hashes, exhaustive test lists, and every intermediate correction unless the target artifact specifically requires them.

### 8. Preflight constrained artifacts

Draft the complete response or artifact as one string and measure `len(text)` before delivery. Leave margin for Unicode, headings, and provenance notes. For a 3,000-character daily log, target 2,600–2,750 characters for the entire deliverable—not just the bullets.

Compress in this order:

1. merge related sessions;
2. remove temporary implementation detail while retaining verification category;
3. group file/wiki changes;
4. shorten lessons and next steps without deleting required sections.

### 9. Verify the result in the authorized delivery mode

- For a response-only or explicitly read-only request, verify scope, redactions, categories, and character budget without creating or modifying files merely for convenience.
- For an authorized artifact write, read it back and verify path, required sections/frontmatter, character limit, and referenced pages.
- State whether the synthesis itself was read-only. Report only verified success.

## Pitfalls

- Broad date searches with large limits can return enormous windows because the date appears inside generated reports.
- Recent browse rows are inventory hints, not scroll anchors; use discovery `match_message_id` values for scrolling.
- Counting continuation sessions separately inflates activity and duplicates outcomes.
- A final summary can be stale if a PR or issue closed later that day; verify live state for status/dashboard updates.
- Tool-call transcripts can contain secrets or noisy file bodies; extract only the evidence needed and redact sensitive material.
- Do not promote temporary task state into persistent memory. Logs/status pages hold chronology; skills hold reusable procedure.

## Verification Checklist

- [ ] Timezone/window defined with an exclusive end boundary.
- [ ] Named root-through-endpoint chains reconstructed exactly when supplied.
- [ ] Existing target artifact checked only when an artifact target exists and reads are authorized.
- [ ] Recent browse plus targeted discovery used.
- [ ] SQLite or raw-session inventory reconciled.
- [ ] Parent/child lineages deduplicated.
- [ ] Post-cutoff continuation copies, later sibling continuations, and compaction duplicates excluded.
- [ ] Non-meaningful monitor/subagent sessions excluded.
- [ ] Requested redactions applied to identifiers, secrets, and temporary tool noise.
- [ ] Live state verified where completion claims matter, or historical state explicitly labeled at the cutoff/endpoint.
- [ ] Character budget preflighted for the complete deliverable.
- [ ] Response-only/read-only constraints honored, or an authorized file write was read back.
