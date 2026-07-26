# Hybrid Linear routing reference

This reference adapts profile-isolated execution to a Linear-native non-coding work-order loop.

## Authority split

```text
Karan revision-bound approval
  → Default Hermes: inspect, select, record approval/claim
  → Default Hermes: create frozen packet + optional one-time capability grant
  → role-native profile OR linear-worker: execute exact approved work
  → fresh independent reviewer: acceptance/security/evidence gate
  → Default Hermes: adjudicate and control review/final tracker status
```

A one-time grant may enable the executor to perform live operational work. It does not delegate human approval, claim creation, self-advancement, merge/deploy, outreach, purchases, or unrestricted account authority.

## Example role matrix

| Work class | Preferred profile | Typical permanent capability | Operational boundary |
|---|---|---|---|
| Issue contract, AC/DoD, implementation plan | `pm-spec` | planning/spec skills | Returns a proposed contract unless exact issue mutation is task-granted |
| External/domain research | `researcher` | research + web extraction | Uses role-native research credentials; tracker update remains control-plane work unless granted |
| Durable wiki/Obsidian output | `wiki-ops` | wiki/note maintenance | Writes approved vault paths and returns readback |
| Multi-part coordination | `orchestrator` | orchestration/harness skills | Produces bounded routes; does not absorb implementation |
| Repository work | `builder` | GitHub PR/testing/debugging | Branch/push/PR authority as assigned; merge/deploy separately gated |
| Bounded non-coding execution without a role-native fit | `linear-worker` | worker protocol, execution harness, planning | Exact temporary skills/credentials and mutations are packet-granted |

## `linear-worker` permanent boundary

Permanent skills:

- `linear-worker-execution`;
- `ops-execution-harness`;
- `writing-plans`.

Recommended CLI toolsets:

```text
file, terminal, web, skills, todo
```

Standing capabilities omitted:

```text
messaging, memory, session_search, cronjob, delegation,
browser automation, tracker/GitHub/client credentials
```

The hardened wrapper permits only one-shot `chat -q` runs. Direct `hermes -p linear-worker`, profile/model/toolset overrides, and yolo mode are rejected.

## One-time grant format

Grant files contain metadata and names, never secret values. Store them under:

```text
~/.hermes/task-grants/linear-worker/
```

Owner must match the current user; permissions must be `0600` or stricter; lifetime is at most eight hours.

```json
{
  "version": 1,
  "grant_id": "<unique-id>",
  "root": "PAPI-3",
  "issue": "PAPI-76",
  "body_sha256": "<64 lowercase hex characters>",
  "run_id": "<packet-run-id>",
  "created_at": "<ISO-8601 timezone-aware>",
  "expires_at": "<ISO-8601 timezone-aware, <=8h>",
  "credential_env": ["LINEAR_API_KEY"],
  "skills": ["linear"]
}
```

Launch:

```bash
linear-worker --grant /absolute/path/to/grant.json chat -q \
  'Execute the frozen packet at /absolute/path/to/packet.md exactly.' --quiet
```

The launcher:

1. validates path, owner, mode, single-link identity, schema, root/issue/body-digest/run binding, expiry, credential-name allowlist, and skill names;
2. atomically marks the grant consumed under an exclusive single-worker lock before exposing capabilities;
3. reads only named credential values from Default Hermes' parent environment;
4. builds a clean runtime environment;
5. copies only named task skills from Default Hermes, including approved symlinked skill roots;
6. injects grant metadata for worker attestation;
7. runs the fixed `linear-worker` profile;
8. removes the consumed grant and temporary skills on every normal/handled exit, while fail-closing on crash residue.

## Frozen execution packet template

```markdown
# Linear execution packet

Root: <ROOT-ID>
Issue: <ISSUE-ID>
Body-SHA256: <normalized source issue body digest; not the packet file hash>
Packet-SHA256: <optional packet file hash only when separately required>
Run-ID: <uuid>
Execution profile: <profile>
Grant-ID: <grant-id or none>

## Goal
<exact outcome>

## In scope
- <exact actions>

## Authorized external mutations
- <system, object, mutation class, and limit; or none>

## Hard stops
- no approval/claim impersonation
- no self-advancement to review/final status
- no merge/deploy/outreach/purchase/account change without separate exact human gate

## Inputs
<verified snapshot or exact live-read authority>

## Allowed outputs
<absolute paths, object IDs, and returned artifacts>

## Required temporary skills
- <exact names>

## Required credential environment names
- <exact names only; never values>

## Acceptance criteria
- [ ] ...

## Verification and readback
- <exact commands/queries>

## Return format
- summary
- artifacts and mutation IDs
- commands/readbacks and real results
- grant/skill/credential names
- blockers
- proposed control-plane status update
```

## Verification

After each run verify:

1. grant metadata matched packet root/issue/run/revision;
2. only requested credential names appeared;
3. permanent and temporary skill sets were exact;
4. every authorized mutation has ID/path/state readback;
5. no unapproved mutation occurred;
6. the consumed grant file is gone;
7. temporary task skills are gone and permanent count is restored;
8. a fresh ungranted launch cannot load the temporary skill or see the task credential;
9. independent review is green before source status advancement.

A Hermes profile is not a filesystem sandbox. Use a stronger terminal sandbox when actual filesystem enforcement is required.
