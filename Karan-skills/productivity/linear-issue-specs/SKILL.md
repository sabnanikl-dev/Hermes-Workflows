---
name: linear-issue-specs
description: Draft, create, update, split, and verify agent-ready Linear issue contracts using live hierarchy, project, dependency, approval, and evidence state.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [linear, issues, specifications, planning, agent-ready, verification]
    related_skills: [linear, github-issue-specs, linear-work-order]
---

# Linear Issue Specs

## Purpose

Use this skill when the user asks to draft, create, file, groom, split, or update a Linear issue. It adapts the outcome-first, repo-grounded, verifiable contract style of `github-issue-specs` to Linear’s role as the tracker for non-coding initiatives, planning, research, coordination, readiness, approvals, and operational work.

A strong Linear issue must let:

- an executor act without guessing;
- a reviewer judge pass/fail from observable evidence;
- Default Hermes reconstruct live state in a fresh session;
- the human see scope, sequence, authority, and next decisions without inspecting hidden local state.

This is an issue-authoring procedure, not a replacement for Linear UI templates. Reuse the existing Agent Delegated Issue template where convenient, but prefer this contract standard for substantive agent work.

## Core standard

A strong Linear issue is:

1. **Outcome-first** — names the operator/business capability or risk retired.
2. **File over AI** — any material deliverable exists as a durable, inspectable artifact in its approved canonical destination; chat prose, agent memory, and temporary run files are transport/evidence, never substitutes for the deliverable.
3. **Live-state grounded** — based on the current issue, parent, children, relations, comments, project, state, labels, and source artifacts.
4. **Tracker-correct** — does not mirror GitHub coding status into Linear or turn comments into a hidden second tracker.
5. **Scoped and sequenced** — names dependencies, parent boundaries, out-of-scope work, and approval gates.
6. **Executable** — provides exact source paths/objects, required outputs, and bounded mutation classes.
7. **Verifiable** — acceptance criteria are observable; mutations require direct readback.
8. **Fresh-session reconstructable** — the issue body and linked live evidence are enough without chat history.
9. **Safe** — capability never implies authority; deploys, merges, publishing, outreach, purchases, accounts, credentials, and client-facing actions stay separately gated.

### GitHub coding handoff rule

When a Linear issue coordinates or gates repository coding, Linear must not become the implementation ticket or leave the execution method ambiguous:

- Link the one exact GitHub implementation issue and, when present, the exact PR with full direct URLs. A bare `#N`, an `A or B` choice, or a parent tracker is not an executable coding target.
- If no dedicated GitHub issue exists, keep the Linear issue non-executable (normally Triage/Backlog), use `github-issue-specs` to create or groom the repo contract after any artifact-placement decision, link it back, and only then permit coding.
- Exact GitHub issue with no PR → route the issue-to-PR work through `multi-agent-dev-workflow`.
- Open PR → route exact-head review/fix/re-review through `autonomous-pr-prover`; do not restart the issue-to-PR lane or substitute a generic/ad-hoc reviewer or builder.
- Closed, merged, or superseded PR → reconcile live issue/closing-reference state first. Never resume or repair a stale PR merely because old Linear prose says it is active.
- Parent GitHub trackers may be context links only unless they are genuinely the bounded executable contract.
- Encode these routes explicitly in the Linear body, preserve Karan's merge/live-action gates, and align Linear state with readiness: a missing implementation link or unresolved blocker should not remain `Ready`.

### File over AI

When a ticket produces findings, research, documents, images, spreadsheets, presentations, scripts, reports, datasets, media, plans, or other material outputs:

- create the real artifact in the format best suited to its intended user and purpose;
- write, commit, upload, or save it to the approved canonical system before closeout;
- link the exact path, object ID, or URL from Linear;
- exercise/render/read back the artifact using checks appropriate to its type;
- treat the final chat or Linear comment as a concise handoff and evidence pointer, not as the only copy of the work;
- do not force every artifact into Markdown, and do not promote temporary or ticket-specific material into durable knowledge without a reuse case.

### Durable-knowledge placement checkpoint

When an issue may produce reusable knowledge, the contract must distinguish durable knowledge from issue evidence, active task state, and ticket-specific deliverables.

- Search the existing project repository, approved client system, and Hermes Brain structure before proposing a new file.
- Name the intended user, repeated reuse case, canonical owner, proposed exact path/ID/URL, provenance, lifecycle, verification/readback, and discoverability/index update.
- If the issue or established mapping already specifies the canonical destination, use it and record the choice.
- If placement would create a new durable file, folder, index, ontology, or knowledge-system boundary and the canonical destination is not explicit, include a pre-execution human gate: **Default Hermes recommends the best location and asks Karan where it should live before creation.**
- Do not ask an executor to invent the information architecture mid-run.
- Do not create duplicate project trackers in Obsidian, put repository truth in Linear, or promote raw transcripts/transient metrics merely to satisfy a knowledge checkbox.
- If no reusable knowledge emerges, require closeout to say `Durable knowledge: none` with the reason.

## Authority rules

- “Draft/spec/write” means draft only.
- “Create/open/file” authorizes issue creation after grounding and duplicate checks.
- Do not guess the team, project, parent, state, labels, assignee, or dependency direction. Read adjacent live issues and reuse verified metadata.
- Use existing labels only unless the user explicitly asks to create labels.
- Re-read every created or edited issue before reporting success.
- Verify relation direction on both issues. For `blocks`, the blocker is `issueId` and the blocked issue is `relatedIssueId`.
- If adding a child to a work-order-controlled parent, update the parent’s explicit child-order section in the same bounded change or the queue may become invalid. Re-run the live inspector afterward.
- Creating an issue never authorizes its execution, approval marker, claim, final state, or external side effects.

## Required workflow

### 1. Identify the issue archetype

- Feature / implementation
- Bug / regression
- Refactor / architecture
- Test / reliability / hardening
- Research / decision
- Ops / readiness tracker
- Milestone / dogfood run
- Follow-up / split
- Issue grooming / correction

### 2. Ground against live Linear and source artifacts

At minimum:

1. Read the named issue and parent.
2. Read relevant children, relations, comments, state, project, labels, assignee, and priority.
3. Inspect the actual files/docs/scripts/live systems named by the work.
4. Search Linear for duplicate and adjacent issues.
5. If NotebookLM or other research is requested, provide it a verified implementation digest and synthesize outside the research tool.
6. Preserve tracker boundaries: Linear owns this issue’s contract/evidence; GitHub owns coding implementation/PR truth when applicable.

### 3. Choose create vs update vs split

- Update an existing issue when the recommendation is already inside its ownership boundary.
- Create a follow-up when the work is independently reviewable, has a different risk surface, or must gate another issue.
- Split live/external activation from readiness or artifact work.
- Do not silently widen a frozen or digest-approved issue; a material body edit invalidates revision-bound approval.

### 4. Write the issue contract

Default body:

```markdown
## Goal

<One short outcome-first paragraph.>

## Context

<Why now; parent/related issues; source-backed principle; operator impact.>

## Current state verified

Verified against <live issue/artifact/date or revision>.

- <issue/file/system> — <what exists and why it matters>.
- Existing/adjacent issues checked: <links or none>.

## AI OS output plan

- Intended user / decision supported: <who will use the output and why>.
- Expected material outputs: <artifact type and provisional lifecycle: ephemeral / ticket / reusable / durable>.
- Canonical destination: <exact path/system, or `Pending Karan placement decision`>.
- Durable knowledge: <existing canonical mapping, proposed location + rationale, or `none expected`>.
- Provenance and limitations: <sources/revision/known limits>.
- Verification/readback: <how each artifact will be exercised and found by a fresh session>.
- Approval/publication: <private, separately gated, or exact approved version>.

## Scope

### 1. <Slice>
- <bounded work>

### 2. <Slice>
- <bounded work>

### 3. Evidence / docs / handoff
- <required durable evidence and readback>

## Out of scope / authority gates

- <explicit non-goal>
- <external or sensitive action requiring separate approval>

## Acceptance criteria

- [ ] Happy path: <observable behavior>.
- [ ] File over AI: <every material deliverable exists in its canonical destination and is linked by exact path/ID/URL; chat-only output is insufficient unless the ticket is communication/decision-only>.
- [ ] AI OS output inventory: <intended user/purpose, artifact type, canonical location, provenance, real verification/readback, lifecycle, discoverability, and approval status for every material output>.
- [ ] Durable knowledge placement: <existing mapping used and verified, Karan approved the proposed location before new structure was created, or `none emerged` with reason>.
- [ ] Failure/recovery: <observable fail-closed behavior>.
- [ ] Regression/evals: <deterministic checks>.
- [ ] Evidence/readback: <IDs, paths, states, or command results>.
- [ ] Safety/authority: <what did not happen without approval>.
- [ ] Fresh-session reconstruction: <what a new session can prove from live state>.

## Suggested implementation notes

- Likely artifacts: `<path/object>`.
- Reuse: <existing seams/patterns>.
- Avoid: <known trap or tracker duplication>.

## Verification

```bash
<real project/tool-specific checks>
```

Live readback: <exact Linear/API checks>.

## Continue / narrow / stop decision

- **Continue:** <evidence threshold>.
- **Narrow:** <safe but limited result>.
- **Stop:** <authority, correctness, duplication, or recovery failure>.

## Dependencies and sequencing

- Parent: <identifier>
- Blocks / blocked by: <identifiers and rationale>
- Intended order: <where this belongs>
```

For a research/decision issue, replace implementation notes with evidence quality, options, recommendation, and owner decision. For a milestone/dogfood issue, emphasize prerequisites, run protocol, rules of engagement, deliverables, and closure evidence.

## Acceptance-criteria quality bar

For artifact/specification issues, define the review contract as well as the deliverable contract:

- state which finding severities block acceptance and do not silently strengthen that threshold during execution;
- define whether `Narrow` is an accepted outcome and what bounded decisions may pass to a downstream implementation issue;
- distinguish behavioral/interface requirements from implementation details so a planning issue does not become a line-by-line implementation surrogate;
- set a repair/re-review budget (default maximum two cycles) and require human escalation or a split follow-up at the cap;
- require the first review to produce a frozen blocker ledger, with later re-review focused on ledger closure plus new acceptance/safety regressions.

Every substantive issue should cover:

- primary happy path;
- relevant failure and recovery path;
- deterministic regression/eval coverage;
- direct mutation/artifact readback;
- fresh-session reconstructability;
- authority and non-action boundary;
- closeout or continue/narrow/stop decision when the issue is a pilot.

Avoid “works well,” “improve reliability,” “handle edge cases,” or “document findings” without naming observable outputs.

## Creating and verifying through Linear

1. Query team/project/state/label/parent IDs from live Linear.
2. Create in a non-executing state (normally Triage or Backlog) unless the user separately approved readiness/execution.
3. Set parent, project, labels, assignee, and priority to match the verified contract.
4. Create required dependency relations.
5. If the parent has an explicit child order, patch that body carefully and re-run its inspector.
6. Re-read the new issue and assert title, body markers, state, parent, project, labels, priority, and URL.
7. Re-read both ends of each relation.
8. For comments, capture `commentCreate.comment.id` and verify directly by ID.

## Output when created

Report:

- created and verified issue URL;
- state, parent, project, priority, and labels;
- duplicate/adjacent issues checked;
- relations and parent-order update verified;
- live inspector result after mutation;
- any assumptions, approval needed, or intentionally untouched issue.

## Pitfalls

- Treating a Linear issue as a generic task note rather than a versioned execution contract.
- Copying GitHub-specific sections blindly into non-coding work.
- Creating a child without updating a controlled parent’s explicit order.
- Guessing dependency direction.
- Moving an issue to Ready while its body is still unapproved or mutable.
- Letting an executor create human approval/claim authority or self-close.
- Using a local JSON/log as a second source of truth instead of attaching redacted evidence to Linear.
- Reporting a GraphQL HTTP 200 as success without checking `errors` and direct readback.
- Expanding PAPI-3 or another pilot root while a hardening gate says to remain narrow.
