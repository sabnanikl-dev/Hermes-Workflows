# Phase 0 Step 1 Execution-Lane Breakdown

Use this when a user has a master local SEO / Google visibility plan and asks to break the first Phase 0 step into smaller kick-offable chunks before choosing an execution lane.

## Goal

Turn “create/validate the local SEO source of truth and guardrails” into bite-sized work packets that can be assigned to humans, Hermes, Codex/Claude, or a tracker issue without mutating public profiles.

## Micro-steps

1. **Locate and freeze the plan source**
   - Identify the master plan file/path and the exact Phase 0/Step 1 wording.
   - Do not edit the plan until asked; first produce a breakdown.

2. **Extract the required source-of-truth fields**
   - NAP, website, inquiry URL, service areas, address/privacy posture, categories, services, description, hours, socials, UTM standards, approved assets, approved claims, disallowed claims.
   - Mark each field as observed, API-derived, legacy/wiki-derived, missing, or approval-needed.

3. **Run read-only public-source/API discovery where available**
   - Website: homepage, contact/about/inquiry routes, visible package names, CTAs, metadata, JSON-LD basics.
   - GBP/API: account/location IDs, primary category, service area, service items, description, open status, metadata, hours gaps.
   - Never infer blocked GBP page fields from anti-bot/share-link output.

4. **Reconcile terminology conflicts**
   - Compare website, wiki/business-plan, GBP, and user-supplied terms.
   - Surface conflicts explicitly, e.g. package name drift such as “Just Show Up” vs “In Your Corner.”

5. **Create the approval ledger**
   - Convert unresolved decisions into checkbox-style items.
   - Separate public-edit approvals from internal documentation approvals.

6. **Package artifacts by lane**
   - Wiki lane: private canonical source-of-truth and claims guardrails.
   - Repo/docs lane: markdown copy, approval ledger, read-only baseline JSON.
   - Tracker lane: Linear/GitHub issue with links, owner notes, AC, and blockers.
   - Public GBP/directory lane: only after explicit approval.

7. **Verify before reporting**
   - Verify files/links/issues exist and contain the expected fields.
   - If a branch is pushed, verify the remote commit before reporting success.
   - If GBP/dashboard state is claimed, verify via API/dashboard read.

## Execution lane picker

When the user asks which lane to use, offer a compact menu:

- **Lane A — Human decision prep:** Produce only the missing-decision checklist and approval ledger. Best when Amanda/Karan need to answer business questions first.
- **Lane B — Hermes/wiki documentation:** Fill the private canonical source-of-truth from read-only sources. Best when facts are scattered.
- **Lane C — Repo/docs package:** Create versioned docs and branch, but do not push until approved. Best when work needs PR/review trail.
- **Lane D — Tracker ops:** Create/update Linear/GitHub issues and acceptance criteria. Best when multiple work items need ownership.
- **Lane E — Public profile execution:** GBP/directory edits/submissions. Requires explicit approval and exact field-level changes.

## Output format

Keep the first response ADHD-friendly:

- “Here’s Step 1 broken down”
- 5–8 micro-steps, each with outcome + owner/lane
- A lane recommendation
- A clear approval boundary: what is read-only/internal vs what mutates public accounts

Avoid long prose or executing the lane before the user picks one, unless the user explicitly asked you to proceed.