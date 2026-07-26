# Sovereign Rig Portable Control-Plane Pattern

Use this reference when an AIOS, filesystem, or recovery plan must preserve owner control across model and computer changes.

## Class-level decision

AIOS is an **additive control plane and project-creation system**, not a monolithic storage root. It owns contracts, registries, templates, recovery instructions, authority envelopes, and verification. Existing canonical systems remain authoritative and may stay in their established locations.

## Portable body

Version these owner-controlled artifacts:

- system map and source-of-truth boundaries;
- stable project/knowledge/tool registries;
- project templates and agent-agnostic harnesses;
- normalized work-packet schema;
- removable model adapters;
- bootstrap, doctor, restore, and rollback contracts;
- verification fixtures and acceptance criteria.

Do not version secrets, machine caches, dependency directories, or active worktree directories.

## Registry and path pattern

Tracked registry entries use logical IDs and `path_ref` values. Absolute machine paths resolve through a tracked example plus an ignored local configuration file. Registries record stable identity, authority, remote, restore method, and durable lifecycle—not copied issue/PR status or active queues.

## Replaceable brains

One normalized work packet should identify:

- project and canonical workdir;
- source-of-truth issue;
- harness/spec paths;
- tools and authority envelope;
- acceptance criteria and verification commands;
- artifact destinations;
- completion schema.

Each model adapter adds only runtime-specific launch syntax. It must not rewrite intent or widen authority. Prove portability by executing the same fixture through at least two adapters and comparing real artifacts and verification evidence.

## Existing repositories and worktrees

Before relocation or consolidation:

1. identify every clone sharing the remote;
2. inspect branches, commits, stashes, untracked/ignored files, linked worktrees, and active processes;
3. label a canonical **candidate**, not a final winner, until evidence closes;
4. push or deliberately archive all durable unique work;
5. produce dry-run and rollback manifests;
6. obtain approval before move/delete/prune/repair/archive actions.

Worktrees are disposable execution environments. On a new machine, clone the repository and recreate worktrees from pushed branches instead of copying path-bound worktree metadata.

## Recovery proof

A recovery claim requires a disposable drill:

1. clone the private control-plane repository;
2. create machine-local path configuration;
3. restore credentials separately through the approved provider;
4. restore knowledge and non-Git assets through their own backup contracts;
5. clone a representative project;
6. recreate one disposable worktree;
7. run a read-only doctor;
8. execute one adapter fixture;
9. report verified, degraded, missing, and approval-gated systems.

AIOS orchestrates recovery; it is not itself the backup for every canonical system.

## Wiki plan capture

For proposal-only capture, include current observed state, target architecture, residency rules, non-goals, phases, approval gates, recovery drill, risks, acceptance criteria, and an implementation `/goal`. Add a visible no-implementation warning; update the existing index/activity/daily logs; verify readback and formatting budgets; do not mutate the proposed target systems.
