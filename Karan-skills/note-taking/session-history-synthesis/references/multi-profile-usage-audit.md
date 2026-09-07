# Multi-profile usage audit

Use this pattern before deciding which Hermes profiles to migrate, seed onto another machine, consolidate, or retire.

## Why raw session counts mislead

A profile can look active because of scheduled jobs, subagents, background tasks, or compaction continuations even when the user never interacts with it directly. Report at least these separate dimensions:

- active session records in the window;
- unique root lineages after following `parent_session_id`;
- direct human-facing, non-cron, non-subagent sessions;
- cron-generated sessions;
- subagent/background sessions.

Cron-only activity is operational use, not evidence of interactive adoption. Multiple continuation sessions in one lineage are one workstream, not multiple independent uses.

## Procedure

1. Define a bounded window in the requested timezone with an exclusive end timestamp.
2. Enumerate the default profile and every named profile from live profile metadata; do not infer the set from remembered names.
3. Inspect the appropriate session database for each profile. Filter inactive/rewound messages or sessions when the schema exposes an active flag.
4. Include long-running sessions that began before the window but contain messages within it.
5. Follow parent links to a root and count unique lineages separately from raw records.
6. Classify source and role from stored metadata rather than title text alone:
   - direct/human-facing;
   - cron/scheduled;
   - subagent/background;
   - other automation.
7. Sanity-check a sample of roots and deepest continuations so compaction summaries, copied task lists, and delayed notifications are not counted as fresh user activity.
8. Present the evidence by profile and state the decision rule. Typical selective-seeding guidance is to include profiles with sustained direct use, omit zero-use profiles, and review cron-only profiles separately based on whether their automations will exist on the destination.

## Decision guardrails

- Usage evidence informs scope; it does not authorize deletion or disabling.
- “Not used recently” is not equivalent to “safe to remove.” Preserve or archive until the user approves destructive cleanup.
- For a second independent instance, copy only the useful profiles while leaving the source host unchanged.
- Current profile count, schedules, and active services should come from live Hermes state, not a vault snapshot or old handoff.

## Output checklist

- [ ] Audit window and timezone stated.
- [ ] Every live profile enumerated.
- [ ] Direct, cron, subagent/background, raw-session, and lineage counts separated.
- [ ] Continuations deduplicated.
- [ ] Zero-use and cron-only profiles distinguished.
- [ ] Recommendation separated from authorization.
- [ ] No source profiles, schedules, or services changed during a read-only audit.