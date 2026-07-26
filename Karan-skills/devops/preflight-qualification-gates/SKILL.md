---
name: preflight-qualification-gates
description: Enforce evidence-before-mutation trust roots for issue-to-workflow missions, distinguish artifact age from qualification chronology, and close terminal escalations without accidentally authorizing downstream work.
version: 0.1.0
metadata:
  hermes:
    tags: [preflight, trust-root, evidence, chronology, escalation, linear, github]
    related_skills: [multi-agent-dev-workflow, linear-work-order, profile-isolated-work-execution, github-operations]
---

# Preflight Qualification Gates

## Purpose

Use this skill when a project or issue requires launchers, reviewers, automation surfaces, credentials, brokers, baselines, or other trust-root evidence to be qualified **before** the first issue, branch, worktree, push, PR, deploy, or external mutation.

This is a class-level safety workflow. It prevents a common false pass: proving that a tool existed before mutation while failing to prove that the required qualification record existed before mutation.

## Trigger

Load this skill when a contract says things like:

- “mandatory before mutation”;
- “capture the trust root before creating the issue/branch/worktree”;
- “prove the reviewer/launcher predates the change”;
- “do not retroactively certify”;
- “stop at ESCALATE if preflight evidence is missing”;
- “qualify the bootstrap before implementation.”

It also applies when live discovery finds that a supposedly pre-mutation action already occurred and the task is to decide whether the mission may continue.

## Core Invariants

1. **Artifact chronology and qualification chronology are different facts.** Old launcher bytes do not prove that identity, runtime, auth, isolation, automation, and broker evidence were recorded in time.
2. **Clean mutation is still mutation.** An empty issue, baseline-only branch, or clean worktree can reduce recovery risk but cannot rewrite an ordering invariant.
3. **Current smokes cannot backdate qualification.** Post-mutation smokes may classify the trust root as healthy; they cannot satisfy a contract that required the smoke record beforehand.
4. **Positive evidence survives escalation.** Preserve valid launcher hashes, smokes, and baseline facts so a human can authorize a bounded revision without repeating discovery.
5. **No invented recovery authority.** Grandfathering, reset, abandonment, replacement, or contract amendment requires explicit human approval when the original contract provides no recovery path.
6. **Terminal escalation is a valid completion result.** Completing an `ESCALATE` gate does not authorize its successor.

## Procedure

### 1. Freeze the governing contract

- Read the live issue and authoritative source in full.
- Hash the exact contract/source bytes.
- Identify the first prohibited boundary crossing.
- Extract the exact `PASS`, `NARROW`, `ESCALATE`, and recovery clauses.
- Resolve conflicts in favor of the stricter authority exclusion. An output-plan request to “link from GitHub” does not override a direct “no GitHub mutation” rule.

### 2. Reconstruct live chronology

Use original sources first:

- remote API timestamps for issues, PRs, comments, branches, and other external objects;
- git refs, reflogs, worktree metadata, and current local/remote state;
- filesystem `lstat`/birth/modify/change timestamps for local artifacts;
- tracker state, dependencies, claims, and comments.

Use session history only as secondary context. Derive UTC from epoch values; never label local wall-clock output with `Z`.

### 3. Capture canonical identities

For each required launcher/tool, record:

- absolute input path;
- `lstat` and every symlink hop;
- final `realpath` and final-file stat;
- owner, group, mode, size, inode/device when useful;
- group/world writability;
- location relative to worktree, staging, and active-runtime roots;
- SHA-256 of invoked bytes;
- version output;
- policy/runtime override-denial probes.

### 4. Run bounded current smokes

Run only non-mutating pinned-runtime/auth smokes:

- explicit model/provider/reasoning/sandbox pins;
- explicit environment allowlist or clean environment;
- no GitHub, tracker, messaging, deploy, payment, client, or live-system mutation credentials;
- no cycle/attempt creation;
- exact expected output marker and exit code;
- hash stdout/stderr.

Label these smokes with their real execution time. Do not imply they predate an earlier mutation.

### 5. Decide chronology

Ask two independent questions:

1. Did the underlying artifacts predate mutation?
2. Did the contract-required qualification record and smokes predate mutation?

If question 2 is not positively proven and no recovery clause exists, return `ESCALATE` even when question 1 is true and all current smokes pass.

### 6. Build an evidence-preserving terminal bundle

Prefer an access-restricted, hash-addressed local bundle:

```text
<evidence-root>/<manifest-sha256>/
  inventory.json
  decision.md
  manifest.json
  smokes/
    <lane>.stdout.txt
    <lane>.stderr.txt
```

Requirements:

- `inventory.json` explicitly records `qualification_record_predates_mutation: false` when applicable;
- `decision.md` explains why artifact age does not cure late qualification;
- `manifest.json` is acyclic and hashes every payload file;
- the manifest SHA-256 is the directory name;
- directories are normally `0700`, files `0600`;
- run a bounded secret/PII scan;
- rehash the bundle before closeout;
- keep it outside product repositories unless the contract explicitly makes it repo-owned.

### 7. Obtain an independent exact-artifact verdict

Use a fresh credential-free read-only reviewer bound to:

- live issue snapshot hash;
- authoritative source hash;
- evidence-manifest hash;
- exact acceptance threshold.

A reviewer process that exits without the required verdict/marker is **no verdict**, even if it emitted useful reasoning. If it drowned in a large source, retry fresh against the same artifact hashes, the full live issue contract, and only the exact normative clauses needed for the decision. Do not count partial output as acceptance.

### 8. Close tracker state without opening the pipeline

When `PASS | ESCALATE` is the issue’s explicit terminal contract:

- a verified `ESCALATE` may complete the gate child;
- keep the parent started/pending human decision;
- keep successors blocked/backlogged;
- record the child closeout and parent escalation comments;
- directly read back comment IDs, states, dependency relation, and successor state;
- state explicitly: “Done by escalation does not authorize continuation.”

Do not post to GitHub when the issue itself excludes GitHub mutation. Store the evidence link in the authorized tracker and disclose the omission.

## Verification Checklist

- [ ] Exact live contract/source digest frozen.
- [ ] First prohibited boundary crossing identified.
- [ ] Remote and local chronology read from original sources.
- [ ] UTC timestamps are correctly derived.
- [ ] Complete launcher identity and symlink-chain records exist.
- [ ] Current smokes are credential-free, non-mutating, and time-labeled honestly.
- [ ] Artifact chronology is evaluated separately from qualification chronology.
- [ ] No retroactive certification or inferred grandfathering occurred.
- [ ] Evidence bundle is hash-addressed, access-restricted, secret-scanned, and rehashed.
- [ ] Independent reviewer returned the required exact-manifest verdict.
- [ ] Tracker closeout was directly read back.
- [ ] Parent and successor remain blocked as intended.
- [ ] Recovery awaits explicit human contract revision.

## Pitfalls

- Treating filesystem birth time as proof that a smoke or qualification record existed.
- Assuming a clean worktree erases the fact that it was created too early.
- Re-running smokes and describing them as pre-mutation evidence.
- Backdating, touching timestamps, or recreating a missing record under an older-looking path.
- Treating process exit as a reviewer verdict.
- Letting an independent reviewer dump an entire large contract until it exits without synthesis; use a bounded exact-clause retry instead.
- Marking a gate child Done and then automatically selecting its blocked successor.
- Following an output-plan request for a GitHub link when the same issue forbids GitHub mutation.
- Inventing a “reasonable” reset or grandfathering path without human-approved contract text.

## Reference

See `references/retroactive-qualification-escalation.md` for a compact worked pattern covering evidence chronology, hash-addressed terminal bundles, bounded reviewer retry, and tracker closeout.
