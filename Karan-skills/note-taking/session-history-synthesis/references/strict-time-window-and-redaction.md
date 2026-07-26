# Strict Time-Window and Redaction Synthesis

Use this when a requested synthesis names exact session lineages, a timezone cutoff, and exclusions such as secrets, issue/PR numbers, or temporary tool noise.

## Deterministic boundary

1. Convert the requested local boundary with an IANA timezone such as `America/New_York`; do not assume a fixed UTC offset across dates.
2. Enumerate the named roots and all descendants from `state.db` before reading content.
3. Filter substantive evidence by `messages.timestamp >= start AND messages.timestamp < end`.
4. Treat the end as exclusive. State the cutoff in the final result when later continuation activity exists.

## Root-through-endpoint lineage bounds

When the request gives both a root session and an exact ending continuation:

1. Walk `parent_session_id` from the endpoint back to the root and reverse that chain.
2. Use only that continuation chain for the main chronology, even if the root has later descendants with the same title or topic.
3. Read subagents attached to chain sessions only to recover findings already integrated into the parent; do not count them as separate workstreams.
4. Exclude sibling continuations and descendants created after the named endpoint unless the user explicitly includes them.
5. Report the state as of the endpoint, not a later resolution discovered in another lineage.

This endpoint rule is independent of the calendar cutoff: both constraints must pass when the request supplies both.

## Compaction duplication caveat

A continuation created after the cutoff can contain compaction summaries, preserved task lists, or delayed notifications whose stored message timestamps copy earlier values. These are transport/context duplicates, not new pre-cutoff accomplishments.

Before including a message from a post-cutoff continuation:

- compare it with the parent lineage's earlier content;
- exclude duplicated compaction summaries, preserved task lists, and repeated background notifications;
- include only genuinely new evidence whose event and message both belong inside the requested window;
- never let a post-cutoff continuation's later resolution backfill the earlier historical state.

## Efficient extraction

- Query session metadata first, then non-empty `user`/`assistant` messages with IDs, timestamps, roles, lengths, and short snippets.
- Retrieve full content only for selected final resolutions, decision turns, compacted `Completed Actions`/`Active State`/`Blocked` sections, and verification outputs.
- For a large review artifact, read the durable local review file when available rather than expanding a huge session-search result.
- Prefer one compact SQLite query over dumping full tool transcripts.

## Redaction and naming

Build the synthesis using semantic labels when identifiers are excluded:

- `root initiative`, `hardening gate`, `controller-contract child`, `downstream selector`, `pilot`, or `visibility work`;
- `open pull request` rather than its number;
- artifact basenames/paths, counts, states, test totals, and verdicts when they are allowed and useful.

Do not expose:

- credentials or environment values;
- issue/PR numbers when explicitly excluded;
- comment IDs, run IDs, grant IDs, or temporary process IDs unless the user asks for trace-level evidence;
- temporary retries, parsing failures, polling noise, or resolved setup errors.

## Final-state discipline

Separate bullets into:

1. work completed;
2. decisions/discussions;
3. verified artifacts/findings;
4. hierarchy state at the cutoff;
5. pending next steps.

Use phrases such as `At 23:58 ET` or `By the cutoff` for historical state. Do not silently substitute current live state or post-cutoff outcomes.