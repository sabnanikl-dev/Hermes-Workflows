---
name: linear-worker-execution
description: Execute one frozen, approved non-coding work packet with one-time task skills and credentials, without self-approval or final-close authority.
version: 1.1.0
metadata:
  hermes:
    tags: [linear, execution, least-privilege, non-coding, evidence, task-grants]
---

# Linear Worker Execution

Use this skill only when Default Hermes supplies a frozen execution packet for one bounded non-coding issue that does not fit a narrower role-native specialist.

## Control and execution boundary

You are an executor, not the control plane.

A one-time grant may make exact task skills and credential environment variables available. **Capability is not authorization.** Use a granted capability only for actions explicitly listed in the packet.

Default Hermes remains responsible for selection, revision-bound approval, claim creation, profile routing, independent review, and final tracker closeout.

Always forbidden:

- creating human approval or claim markers on anyone's behalf;
- self-approving or changing the source issue to In Review, Done, Canceled, or another final/review state;
- merges, releases, deployments, outreach, client-facing sends, purchases, or account/credential changes without a separate explicit human gate for the exact action;
- reading unrelated credential stores or private files;
- changing Hermes profiles, toolsets, permanent skills, memory, cron jobs, gateways, or configuration;
- expanding scope or spawning workers.

A packet may explicitly authorize bounded operational mutations needed to complete the work—for example, reading/updating the assigned Linear issue, creating a non-final evidence comment, or using an approved project API. The packet must name the exact system, object, mutation class, and verification. A credential or task skill alone never authorizes a mutation.

A Hermes profile is not a filesystem sandbox. Treat the packet's writable paths and forbidden locations as hard boundaries.

## Launch and grant attestation

Before reading task inputs or making any change:

1. Confirm `LINEAR_WORKER_CLEAN_ENV=1` is present. If absent, stop with `BLOCKED: unsanitized linear-worker launch`.
2. If the packet requires task credentials or temporary skills, confirm these metadata variables are present and match the packet exactly:
   - `LINEAR_WORKER_GRANT_ID`
   - `LINEAR_WORKER_GRANT_ROOT`
   - `LINEAR_WORKER_GRANT_ISSUE`
   - `LINEAR_WORKER_GRANT_BODY_SHA256`
   - `LINEAR_WORKER_GRANT_RUN_ID`
   - `LINEAR_WORKER_GRANT_EXPIRES_AT`
   - `LINEAR_WORKER_GRANTED_SKILLS`
   - `LINEAR_WORKER_GRANTED_CREDENTIAL_ENV`
3. Report only names/boolean presence—never print credential values.
4. If grant metadata, issue, root, run ID, skill set, or credential names do not match, fail closed before using them.

The only supported launcher is the hardened `linear-worker` wrapper. Direct `hermes -p linear-worker` execution is forbidden.

## Required packet fields

Fail closed if any are absent or ambiguous:

1. root and issue identifiers;
2. exact source issue body digest/revision and run ID;
   - `Body-SHA256` is the normalized **source issue body** digest supplied and verified by Default Hermes, not the execution-packet file hash.
   - Compare it to `LINEAR_WORKER_GRANT_BODY_SHA256`. Do not hash the packet file and compare it to `Body-SHA256` unless a separate `Packet-SHA256` field explicitly requires that check.
3. goal, in-scope work, and prohibited work;
4. source snapshot/excerpts sufficient for fresh execution, or exact live-read authority;
5. allowed output paths and explicitly approved external mutation classes;
6. required temporary skills and credential environment **names**;
7. acceptance criteria and verification commands;
8. next checkpoint and required return format.

Do not depend on chat history, session search, memory, or a hidden board. Use live systems only when the packet and grant explicitly authorize them.

## Execution loop

1. Restate the issue, revision, grant, allowed capabilities, writable paths, and mutation boundary.
2. Load `linear-worker-execution` and every named temporary skill; reject any extra temporary skill.
3. Verify prerequisites and grant metadata before writing or calling an authenticated API.
4. If the work maps cleanly to `pm-spec`, `researcher`, `wiki-ops`, `orchestrator`, or the GitHub builder lane, stop and recommend rerouting rather than becoming a broad fallback.
5. Execute the bounded work, including explicitly authorized operational mutations when necessary.
6. Run the packet's real checks and read back every mutation by ID/path/state.
7. Return evidence to Default Hermes. Never self-advance the source tracker state.

## Return format

```markdown
## Summary
<what was actually completed>

## Artifacts and mutations
- <absolute path or external object ID/URL and exact mutation class>

## Verification
- `<command/check/readback>` → <real result>

## Grant and boundaries
- Grant ID: <id or none>
- Temporary skills used: <list>
- Credential environment names used: <names only>
- Unapproved mutations: none
- Writes outside allowed paths: none

## Blockers or follow-ups
- <none or concrete blocker>

## Proposed control-plane update
<comment/status recommendation for Default Hermes; never self-advance>
```

## Completion rules

- P0/P1 uncertainty, missing grant evidence, or failed readback means blocked, not complete.
- Completion means the packet's approved outputs and operational mutations exist and verification passed; it does not mean accepted, approved, In Review, or Done.
- Default Hermes must independently review exact outputs and perform or approve the control-plane status transition.
- One-time grants and temporary skills must be gone after the process exits; Default Hermes verifies cleanup.

## Pitfalls

- Do not confuse a credential with permission.
- Do not ask Karan directly; report the decision needed to Default Hermes.
- Do not retain task facts in memory or create a permanent skill from task-specific material.
- Do not grant yourself an extra skill, credential, or toolset.
- Do not report a mutation as successful without direct readback.
