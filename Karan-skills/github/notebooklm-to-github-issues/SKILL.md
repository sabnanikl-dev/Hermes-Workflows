---
name: notebooklm-to-github-issues
description: Query one or more specific NotebookLM notebooks, provide a detailed repo/system digest because NotebookLM cannot see live state, synthesize source-grounded recommendations, then draft or create verified GitHub issues. Use when the user asks to turn NotebookLM findings into GitHub issues, backlog items, repo enhancements, or implementation tickets. For durable wiki synthesis instead, use notebooklm-to-obsidian-synthesis.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [notebooklm, github, issues, repo-grounding, research-to-backlog]
    related_skills: [github-issue-specs, github-operations, notebooklm-to-obsidian-synthesis]
---

# NotebookLM to GitHub Issues

## When to Use

Use this skill when Karan asks to:

- query one or more NotebookLM notebooks and open/create/file GitHub issues;
- turn NotebookLM research into implementation tickets;
- compare NotebookLM recommendations against a repo and create backlog items;
- use NotebookLM to critique a project/control center/repo and convert the findings into agent-ready issues;
- create issues from NotebookLM feedback on a plan, report, workflow, product, or codebase.

Do **not** use this skill for ordinary NotebookLM research that should become Obsidian knowledge. For that, use `notebooklm-to-obsidian-synthesis`.

## Core Principle

NotebookLM can reason over its notebook sources, but it **cannot see the repo, GitHub, Linear, local files, credentials, current issues, or live connector state** unless Hermes explicitly provides that context.

Therefore, every NotebookLM → GitHub issue run has two grounding layers:

1. **NotebookLM source grounding** — what the notebook says.
2. **Repo/live-state grounding** — what the target repo/system currently contains.

Never ask NotebookLM for repo recommendations with only a repo name. Provide a detailed current-state digest in the prompt.

## Required Supporting Skills

Load these when using this workflow:

- `github-issue-specs` — issue body quality bar.
- `github-operations` — GitHub auth, labels, duplicate search, create/verify mechanics.
- `notebooklm-to-obsidian-synthesis` only if you also need NotebookLM auth/query mechanics or want durable wiki promotion.

If the target repo has domain-specific rules, load the relevant domain/project skill too.

## Authority Rules

- If the user says **draft/spec/write issues**, draft only.
- If the user says **open/create/file issues**, that is approval to create GitHub issues after grounding and duplicate checks.
- Never guess the target repository. Verify it with `gh repo view <owner/repo> --json nameWithOwner,url,defaultBranchRef,isPrivate`.
- Use only existing labels unless the user explicitly asks to create labels.
- Search existing open issues before creating; if a recommendation overlaps an existing issue, comment/extend or report the overlap instead of creating a duplicate.
- Re-read every created issue with `gh issue view --json number,title,body,labels,state,url` before claiming success.
- Preserve project-specific sign-off rules. In the SEO control center, every GitHub artifact ends with `— seo-control-center-agent`.
- Do not let a GitHub issue authorize live side effects. Keep deploys, DNS, account changes, Search Console/GBP/Merchant Center, robots/noindex/canonical migrations, security reconsideration, purchases, and client-facing messages explicitly gated.

## Repo-Local Skill Packaging Pattern

When Karan wants this workflow available **inside a specific repo/project** rather than as a global Hermes skill, create a repo-local class-level skill under that repository, for example:

```text
skills/notebooklm-to-github-issues/SKILL.md
skills/manifest.md
```

Then wire it into the local harness rather than relying on global memory:

- update the repo's `skills/manifest.md` loading rule;
- add the local skill to the repo map/README;
- add validator/audit coverage so future agents cannot miss it;
- add the local skill to any cron prompt that turns NotebookLM findings into issues/backlog;
- keep it scoped to that repo and preserve external/live-action gates.

For the Hermes-personal autonomy lab specifically, proposal-scout runs should ground issue/backlog suggestions in both strategic notebooks before creating or drafting issues:

```text
AI OS — 7442a0ae-5a2d-4863-ac9b-b0a8bccea6f3
Strategic Engineering: Harnessing AI as a Force Multiplier — 95758f68-a24f-442b-8973-bf542052b267
```

See `references/hermes-personal-repo-local-notebooklm-issue-skill.md` for the concrete issue/backlog pattern.

For Hermes Personal passive-revenue product scouting, use `references/hermes-personal-three-notebook-product-scout.md`: query AI OS + Strategic Engineering every run for loop/harness/work-system improvements and Ai money every run for product/revenue opportunities, then synthesize exactly one repo-local move.

### Hermes Personal passive-revenue scout pattern

When the cron task is a focused passive-revenue product scout rather than an issue-creation run, treat the three NotebookLM answers as decision inputs, not as issue candidates:

1. Build a compact digest from live repo state, active product workspace, readiness gaps, experiment ledger, and open issues/PRs if checked. NotebookLM cannot see these.
2. Query AI OS and Strategic Engineering for loop/harness/work-system improvements, and Ai money for buyer/revenue/product-artifact improvements.
3. Synthesize outside NotebookLM and choose exactly one allowed move. If the active product has a human value-clarity blocker, prefer a concrete buyer-facing product artifact or product experiment over more harness polish unless the harness is the bottleneck.
   - When the strategic notebooks recommend an adversarial harness/evaluator but the AI-money notebook identifies a missing buyer-facing “hero” artifact, treat the harness idea as next-loop backlog and build the product artifact first if it directly resolves the current buyer-usefulness blocker.
   - Good tie-breaker: if all repo/harness audits are already green and the readiness tracker names product gaps, pick the product/revenue lane; if product artifacts are blocked by missing verification/scoring, pick the loop/harness lane.
   - If NotebookLM auth passes but every required notebook query is rate-limited/rejected after a compact retry, mark each notebook as blocked in the final report and continue with bounded public/repo-local evidence work. Do not stall the run or fabricate NotebookLM grounding. The durable lesson is: preserve the mandatory query attempt, record the blocker, then make the smallest evidence-backed repo-local move that the current state already supports.
4. Do not commit raw NotebookLM output. Distill it into a repo-local artifact, experiment file, validator/checklist, or issue body.
5. If running a product experiment, change one surface only, append one TSV row to the product ledger, and verify the metric with a deterministic check when possible (for example, a small internal-term scan for self-referential buyer copy, a targeted objection-coverage scan that checks the new artifact handles each named objection and contains no internal/leaky terms, or a product evidence-fidelity checker that proves buyer-voice rows have accessible URLs, quote-level language, buyer-segment signals, and no proxy/snippet/vendor disqualifiers).
6. For value-clarity blockers, a strong one-run move is a **self-reference removal experiment**: rewrite only the buyer-facing surface under test (brief/listing/hero/etc.) so it leads with the buyer's job, concrete artifact, and next action; scan the changed buyer-facing files for internal terms such as `Hermes`, `Product 001`, `repo-local`, `experiment`, launch-deadline language, approval-packet language, and generic `researched PDF`/`AI automation offer` framing; record baseline hits, result hits, and a promote/hold/discard ledger decision.
7. If an adversarial reviewer or human feedback says the **entry point** (README, listing lead, landing hero, sample post opening, or exported buyer-facing first page) still carries rejected framing, fix that entry point before building more harness, dist exports, or approval packets. Treat stale entry points as intent debt: future agents and buyers start there, so they can silently undo clarified positioning even when deeper files are improved. Change only one surface, log the before/after scan, and keep title/price/buyer-demand research as separate experiments unless the prompt explicitly authorizes a broader pass.
8. Preserve public-live gates: NotebookLM recommendations never authorize posting, checkout/listing activation, outreach, paid setup, credential changes, or revenue/ROI/legal/compliance claims.

Useful support notes:
- `references/hermes-personal-three-notebook-product-scout.md` contains the full three-notebook scout framing.
- `references/hermes-personal-readme-entrypoint-experiment.md` captures the 2026-07-04 Product 001 README entry-point framing pattern.
- `references/hermes-personal-pack-buyer-demand-evidence.md` captures the pattern for separating market-adjacent product-pack demand signals from true buyer-voice proof during Product 001 scout runs.
- `references/hermes-personal-direct-buyer-voice-leads.md` captures the follow-on pattern for mapping direct pack-buyer research leads when source pages are blocked or only snippets are available: treat them as leads, keep the gate unchecked, and log `hold` rather than overclaiming proof.
- `references/hermes-personal-buyer-demand-proof-map.md` captures the follow-on pattern for adding a proof-map artifact when packaging is clearer but direct buyer-demand proof is still missing; map objections to artifacts, keep confidence labels honest, and log `hold` unless the buyer-voice gate actually passes.
- `references/hermes-personal-freelancer-sales-objection-map.md` captures the pattern for mapping accessible sales-friction/vendor/expert/end-buyer sources to kit objections while keeping the direct freelancer/agency buyer-voice gate blocked; use `source-map support count` and log `hold` when the map improves but quote-level buyer proof is still missing.
- `references/hermes-personal-competitor-wtp-proxy-map.md` captures the pattern for mapping paid/proxy competitor products, prices, ratings, and review snippets to Product 001 artifacts while preserving the distinction between willingness-to-pay proxy evidence and direct buyer voice; use `source-map support count` and log `hold` unless exact buyer-segment quote proof passes.
- `references/hermes-personal-pricing-hypothesis.md` captures the pattern for revisiting Product 001 price after buyer/usefulness clarity improves: treat price as the single experiment surface, build a private `pricing-hypothesis.md`, use bounded public-source anchors, keep public price/listing/checkout approval closed, and usually log `hold` until real market exposure is approved.
- `references/hermes-personal-observed-wtp-evidence-pass.md` captures the pattern for mapping paid/reviewed comparable marketplace assets when exact buyer willingness-to-pay is the blocker: classify exact target WTP vs comparable service-seller WTP vs price/category-only signals, update the proof map, and log `hold` unless the exact gate truly passes.
- `references/hermes-personal-target-buyer-wtp-scan.md` captures the follow-on pattern for Product 001 when proxy/comparable WTP evidence exists but the exact buyer class is still unproven: run a bounded target-buyer-category scan, classify listed prices/sales/reviews/search snippets separately, update the proof map, and log `hold` unless clean observed WTP clears the gate.
- `references/hermes-personal-notebooklm-rate-limit-product-scout.md` captures the fallback pattern when all required NotebookLM product-scout queries are rate-limited/rejected after compact retries: mark notebooks blocked, do not fabricate grounding, continue with one repo-local evidence-backed move, and prefer adversarial P0/P1 blocker gates over more proxy polish.
- `references/hermes-personal-direction-traffic-light-gate.md` captures the pattern for stopping proxy-polish drift when a product has clear artifacts but unresolved buyer/WTP/pivot direction: add a product-direction traffic-light gate, append exactly one `hold` ledger row, and keep public-live approval closed.
- `references/hermes-personal-local-owner-pivot-scorecard.md` captures the pattern for testing a local-service owner/operator pivot without confusing stronger underlying pain/budget with low-fulfillment demand for a self-serve paid kit; use one audience-segment experiment, update the governor/ledger, and usually log `hold` unless support burden and owner WTP are solved.
- `references/hermes-personal-observed-wtp-governor.md` captures the pattern for converting an unresolved observed-WTP blocker into a deterministic repo-local governor: report mode for safe cron visibility, `--require-pass` for public-live approval gates, explicit `WTP-VERIFIED:` markers, and ad-hoc red/green fixture verification.
- `references/hermes-personal-observed-target-buyer-wtp-ledger.md` captures the follow-on pattern for Product 001 when the WTP governor is installed but still 0/3: run one bounded transaction-proxy pass, separate exact priced sources from comparable reviewed sources, add no `WTP-VERIFIED:` markers unless the five-part contract truly passes, and log `hold` rather than proxy-polishing.
- `references/hermes-personal-free-lead-magnet-path.md` captures the pattern for Product 001 when useful private artifacts exist but observed WTP remains blocked: stop paid-listing polish, draft an approval-required free-sample/lead-magnet interest path as a distribution-channel experiment, log exactly one `hold` ledger row, and preserve all public-live gates.
- `references/hermes-personal-launch-claim-verification.md` captures the pattern for Product 001 after WTP/source evidence improves or passes: do not jump straight to public approval; first build a claim-to-evidence launch handoff, map each buyer-facing promise to evidence/artifact anchors plus excluded wording, log exactly one `promote` ledger row when complete, and keep all public-live gates closed.
- `references/hermes-personal-launch-thesis-handoff.md` captures the follow-on pattern when WTP/claim gates are passing but the decision state is scattered or stale: create a single approval-required launch thesis memo, refresh the approval packet, sync stale setup/protocol price/readiness fields, log exactly one `approval-needed` ledger row, and ask only for a narrow private setup decision unless Karan separately approves public-live action.
- `references/hermes-personal-private-setup-provenance.md` captures the follow-on pattern when a private setup protocol is the bottleneck: pin the current dist artifacts by commit, byte count, and SHA-256; treat setup-protocol integrity as the single product-format experiment; log one `promote` row; and do not open/login to external platforms or imply public-live approval.
- `references/hermes-personal-path-decision-packet.md` captures the convergence handoff pattern when Product 001 has enough repo-local artifacts/evidence and the next bottleneck is Karan choosing a path; create one `path-decision-packet.md`, log `product direction` / `approval-needed`, and avoid more autonomous polish or bundled launch/setup requests.
- `references/hermes-personal-path-decision-gate.md` captures the follow-on pattern when a path packet exists but needs deterministic enforcement: add an adversarial stress-test section, wire the one-reply options into a strategic alignment gate, log exactly one `product direction / approval gate` row, and verify with a red/green temp-fixture script.
- `references/hermes-personal-simulated-boring-business-output.md` captures the pattern for resolving abstract value-clarity drift with a finished fictional local-service example output: use `preview/sample` as the one surface, measure objection coverage, frame calculations as exposure hypotheses, and avoid changing price/platform/public setup.
- `references/hermes-personal-owner-self-audit-proof-pass.md` captures the pattern for testing a local-service owner/operator self-audit pivot when the current buyer is too far from the pain-holder: use `audience segment` as the one surface, collect owner worksheet/calculator signals, preserve support-burden caveats, and usually log `hold` unless owner self-serve demand and low-fulfillment fit are both strong.
- `references/hermes-personal-mua-control-room-handoff.md` captures the pattern for turning a vague AI/prompt/info product into a minimal-useful-agent control-room deliverable: use `product format` as the one surface, add trigger/context/approval/escalation/log/do-not-automate rules, measure objection coverage, and avoid dist rebuilds or public/setup posture changes in the same run.

### Direct-implementation variant (no issues)

When Karan says "send X to NotebookLM and refine/optimize it, then implement the findings," and X is a repo-internal system (eval suite, validator chain, harness, prompt set), skip issue creation entirely: digest → ranked refinement recommendations → implement each finding directly with red/green fixture verification → commit/push with remote SHA verification. The digest MUST name what the system does NOT do (empty dirs, uncomputed metrics, unenforced gates) — that meta-gap drives the best recommendations. Ask NotebookLM to flag already-covered recommendations so you skip them, and report infeasible findings as honest partials rather than faking them. See `references/hermes-personal-eval-suite-refinement.md` for the full pattern, including the prompt-drift guard (pin critical cron-prompt gate phrases as deterministic code_checks and red-test by deleting the phrase).

## Workflow

### 1. Verify NotebookLM CLI/auth

Use the NotebookLM CLI path if available:

```bash
/Users/creator/.local/bin/notebooklm --version
/Users/creator/.local/bin/notebooklm auth check --test --json
```

If auth is expired, refresh from Karan's Chrome profile:

```bash
printf 'y\n' | /Users/creator/.local/bin/notebooklm login \
  --browser-cookies 'chrome::Karan-PapiBot' \
  --account karanagent20@gmail.com \
  --include-domains=all

/Users/creator/.local/bin/notebooklm auth check --test --json
```

Then list notebooks:

```bash
/Users/creator/.local/bin/notebooklm list --json --no-truncate
```

### 2. Identify every notebook to query

If the user says “each of the four SEO notebooks,” inspect the list and resolve the exact notebooks. Do not silently collapse multiple notebooks into one query.

For each selected notebook, inspect sources:

```bash
/Users/creator/.local/bin/notebooklm source list -n <notebook_id> --json --no-truncate
```

Save notebook titles/ids and source-list summaries in your working notes so the final issue bodies can cite the notebooks queried.

### 3. Ground the target repo/system before asking NotebookLM

Minimum repo grounding before any NotebookLM prompt:

```bash
git status --short --branch
git remote -v
gh repo view <owner/repo> --json nameWithOwner,url,defaultBranchRef,isPrivate,description
gh issue list --repo <owner/repo> --state open --limit 100 --json number,title,labels,url
gh label list --repo <owner/repo> --limit 100
```

Also read relevant local files/docs before summarizing state:

- root guidance: `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `README*`;
- project maps/docs/templates/scripts likely to be affected;
- existing client/profile/task files if the repo is a control center;
- current open issues/PRs that may overlap.

For a repo-state digest, include:

- target repo and branch/ref verified;
- purpose of the repo/system;
- current file/architecture map;
- relevant scripts/tools/connectors and whether they were smoke-tested;
- current issue backlog and labels;
- observed gaps from direct repo inspection;
- explicit non-goals/authority boundaries;
- any project-specific signature/footer rules.

### 4. Query each NotebookLM with the repo digest

Use a prompt that makes NotebookLM treat the digest as current implementation context and its sources as SEO/domain authority.

Template:

```markdown
We are improving GitHub repo `<owner/repo>`. Use ONLY this notebook's sources for external/domain facts, and use the repo-state digest below only as current implementation context.

Current repo-state digest verified <date/ref>:
- Repo: ...
- Purpose: ...
- Current files/architecture: ...
- Existing open issues already cover: ...
- Labels available: ...
- Observed gaps from repo inspection: ...
- Authority/project rules: ...

Task: Identify actionable improvements for the repo that are directly implied by this notebook's sources and are not duplicates of the existing open issues. Favor enhancements that make the repo more reliable for agents: templates, checklists, small CLIs, validation scripts, docs, report artifacts, or issue workflows.

Return 3-5 issue candidates. For each candidate include:
1. title
2. why_from_sources, citing source titles when possible
3. current_gap from the repo-state digest
4. scope: concrete repo changes
5. acceptance_criteria: observable pass/fail
6. out_of_scope_or_approval_gates
7. recommended_label from the existing labels only

Also rank candidates by leverage and say if any overlap with existing issues enough that they should be a comment/extension instead of a new issue.
```

Run:

```bash
/Users/creator/.local/bin/notebooklm ask \
  -n <notebook_id> \
  --json \
  --prompt-file /tmp/notebooklm-to-github-issues.md \
  --request-timeout 180
```

If `--json` returns a streaming/parser error but auth check passes, do not treat the notebook as blocked yet. Retry once with a shorter digest and plain text output, preserving the notebook ID and prompt file separately:

```bash
/Users/creator/.local/bin/notebooklm ask \
  -n <notebook_id> \
  --prompt-file /tmp/notebooklm-short.md \
  --request-timeout 180
```

If the text-mode retry succeeds, count the notebook as queried, save only the distilled findings, and record the retry pattern in the final report. The durable lesson is “compact the prompt and retry without JSON,” not “NotebookLM is broken.”

If multiple notebooks are requested, query them separately and preserve each answer. Do not merge notebooks before NotebookLM sees the prompt; separate answers reveal consensus and contradictions.

### 5. Synthesize and de-duplicate outside NotebookLM

After all notebook answers return:

1. Group candidates by theme.
2. Remove duplicates and near-duplicates.
3. Mark candidates that should extend an existing issue rather than create a new issue.
4. Prefer fewer stronger issues over many overlapping tickets.
5. Ensure each final issue is implementable independently.
6. Ensure each final issue names what is out of scope and which authority gates remain closed.

Useful decision rules:

- If an idea is just a sub-scope of an existing issue, comment/extend instead of opening a new issue.
- If an idea changes a different artifact or risk surface, create a separate issue.
- If a recommendation depends on live account access that is not verified, make the issue a readiness/checklist issue, not an implementation/live-action issue.
- If NotebookLM recommends generic best practices that the repo already covers, skip or turn into an existing-issue comment.

### 6. Draft issue bodies using `github-issue-specs`

Each final issue should include:

- Goal
- NotebookLM source grounding (notebook names queried + source-backed principle)
- Current state verified (repo ref/date + files/issues checked)
- Scope
- Out of scope / approval gates
- Acceptance criteria
- Suggested implementation notes
- Verification
- Project-specific sign-off, if required

Do not paste raw NotebookLM output wholesale. Convert it into a repo-grounded, agent-ready contract.

### 7. Create issues only when authorized

When authorized to create:

```bash
gh issue create \
  --repo <owner/repo> \
  --title '<title>' \
  --body-file <body.md> \
  --label '<existing-label>'
```

Then verify:

```bash
gh issue view <number> \
  --repo <owner/repo> \
  --json number,title,body,labels,state,url
```

Check that:

- title matches;
- labels match;
- body contains required sign-off if project requires it;
- issue is open unless intentionally otherwise;
- URL is returned.

### 8. Optional durable knowledge promotion

If the NotebookLM run reveals a reusable playbook, long-term project strategy, or durable research synthesis, use `notebooklm-to-obsidian-synthesis` after issue creation to promote a distilled note into Hermes Brain.

Do not dump every raw NotebookLM answer into Obsidian. Preserve only durable, named, reusable knowledge.

## Pitfalls

- **Forgetting repo context in the NotebookLM prompt.** This is the big one. NotebookLM cannot see the repo unless you describe it.
- Creating duplicate issues because existing issues were not searched first.
- Treating NotebookLM recommendations as live-state facts. NotebookLM knows its sources, not current repo state.
- Letting NotebookLM invent file paths, labels, or scripts. Final issues must cite repo-inspected files and existing labels only.
- Over-opening issues. Prefer 3-6 focused tickets over a dozen overlapping ones.
- Allowing a repo issue to imply approval for account/deploy/client-facing mutations.
- Forgetting to verify created issues after `gh issue create`.
- Mixing this workflow into Obsidian synthesis. GitHub issue creation has different authority and verification requirements.

## Verification Checklist

- [ ] NotebookLM auth checked/refreshed.
- [ ] Exact notebook IDs and source lists inspected.
- [ ] Target GitHub repo verified.
- [ ] Existing issues and labels checked before issue creation.
- [ ] Relevant repo files/docs/scripts read before making the repo digest.
- [ ] NotebookLM prompt included a detailed current-state digest.
- [ ] Each requested notebook was queried separately.
- [ ] Findings were synthesized and de-duplicated outside NotebookLM.
- [ ] Issue bodies use `github-issue-specs` quality bar.
- [ ] Only existing labels were used.
- [ ] Created issues were re-read and verified.
- [ ] Final response reports issue URLs, labels, notebooks queried, and verification performed.
