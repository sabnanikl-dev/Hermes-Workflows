---
name: notebooklm-to-obsidian-synthesis
description: Query a specific NotebookLM notebook, distill durable insights, ingest them into Obsidian Hermes Brain, then return action items.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [notebooklm, obsidian, research, synthesis, knowledge-management, action-items]
    related_skills: [knowledge-memory-workflows, hermes-brain-wiki]
---

# NotebookLM to Obsidian Synthesis

## When to Use

Use this skill when Karan asks to:
- query a specific NotebookLM notebook;
- use NotebookLM as a research brain/source-grounded synthesis tool;
- extract strategic or operational lessons from NotebookLM;
- turn NotebookLM research into Obsidian Hermes Brain knowledge;
- identify action items from notebook research;
- evaluate whether a NotebookLM-derived workflow should become memory, a wiki page, or a skill.

Do **not** create a generic NotebookLM “Hermes Research Brain” notebook by default. Karan prefers querying specific notebooks, then promoting only durable distilled knowledge into Obsidian Hermes Brain.

## Mental Model

```text
Specific NotebookLM notebook
  -> source-grounded NotebookLM synthesis
  -> Hermes judgment/filtering
  -> Obsidian Hermes Brain durable note
  -> concise user-facing action items
```

NotebookLM is the research/synthesis substrate. Obsidian Hermes Brain is the durable memory/wiki layer. Hindsight/standard memory are only for compact facts or preferences that should be recalled conversationally.

## Workflow

### 1. Load supporting skills

Load these first if not already loaded:

- `knowledge-memory-workflows`
- `hermes-brain-wiki`

If the task's primary output is GitHub issues, PR follow-ups, or repo backlog items, stop and use `notebooklm-to-github-issues` instead.

If the task only needs repo state as context for durable Obsidian synthesis, load `github-operations` as needed for read-only grounding.

If the task touches a specific domain, load the relevant domain skill too.

### 2. Verify NotebookLM CLI/auth

Use the NotebookLM CLI path if available:

```bash
/Users/creator/.local/bin/notebooklm --version
/Users/creator/.local/bin/notebooklm auth check --test --json
```

If auth is expired, refresh from the Chrome profile Karan uses for NotebookLM:

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

### 3. Identify the exact notebook

Use the notebook title/id from the user's request. If ambiguous, inspect the list and pick the obvious match. Ask only if multiple notebooks plausibly match and the choice changes the research.

List sources for context:

```bash
/Users/creator/.local/bin/notebooklm source list -n <notebook_id> --json --no-truncate
```

### 4. Query NotebookLM with an action-oriented prompt

Use a focused prompt that asks for:

1. durable principles;
2. workflow/product opportunities;
3. current-state implications;
4. small next experiments;
5. citations/references.

Example:

```bash
cat > /tmp/notebooklm-query.md <<'EOF'
We are using Hermes as an orchestrator and Obsidian Hermes Brain as durable memory. Using only this notebook's sources, synthesize:
1. The durable principles that matter for our setup.
2. Concrete workflow/product opportunities.
3. The smallest high-leverage next experiments.
4. What should be promoted into Obsidian versus left as temporary research.
Prefer actionable patterns over generic theory. Include citations.
EOF

/Users/creator/.local/bin/notebooklm ask \
  -n <notebook_id> \
  --json \
  --prompt-file /tmp/notebooklm-query.md \
  --request-timeout 180
```

### 5. Ground against current local/source-of-truth state

Before recommending actions, inspect the relevant durable source of truth:

- Obsidian index and related pages;
- GitHub issues/PRs if product/workflow action items touch a repo;
- Linear if the work belongs there;
- repo docs/specs if implementation is involved.

Do not treat NotebookLM as the only authority. NotebookLM gives research synthesis; current systems give live state. If the desired deliverable is GitHub issues rather than Obsidian/Hermes Brain knowledge, switch to `notebooklm-to-github-issues`.

If Karan asks to query a specific NotebookLM notebook for ideas that should become repo-local artifacts, automation loops, product surfaces, or market-facing assets, do not force an Obsidian promotion. Use `references/notebooklm-to-repo-artifact-synthesis.md`: query the notebook with explicit repo and release boundaries, ground against live repo state, distill a concise research note if useful, land one small forkable artifact, and verify the repo/push like normal GitHub work.

For strategic workflow/opportunity questions, use a **two-pass refinement** pattern:

1. Query NotebookLM broadly for principles, opportunities, risks, gates, and small experiments.
2. Inspect current state outside NotebookLM.
3. Feed a concise current-state digest back into NotebookLM and ask what is redundant, what is missing, which opportunities rank highest, and what should *not* be built yet.

See `references/loop-opportunity-synthesis-pattern.md` for the loop-opportunity prompt pattern.

For NotebookLM research about Hermes startup token costs, context optimization, tool-schema bloat, skill loading, or prompt bloat, use `references/hermes-context-optimization-notebook-pattern.md`. The key extra requirement is to measure/cross-check the current local Hermes tool/config state before recommending changes, because NotebookLM may surface generic router advice while the installed Hermes already has progressive disclosure (`tool_search`) or platform MCP gates (`no_mcp`, allowlists).

When Karan asks to send an existing plan/report/artifact back to NotebookLM for critique and then revise it, use `references/notebooklm-artifact-feedback-loop.md`: extract or summarize the artifact, query each notebook separately, patch the artifact with visible feedback sections, optionally run adversarial reviewer lanes, and honestly disclose any blocked reviewer/auth lane instead of simulating the review.

When Karan asks multiple NotebookLM notebooks to produce a Hermes `/goal` or orchestration plan, use `references/multi-notebook-goal-synthesis-and-live-cleanup.md`: query each notebook separately with the same state digest, use the compact/plain retry for long-prompt parser failures, synthesize outside NotebookLM, then remove invented roles, wrong stack/tool assumptions, unrelated project constraints, circular gates, and unauthorized authority by revalidating live Linear/GitHub/repo/profile state.

When Karan asks to create a new source in a specific NotebookLM notebook from current local/system state and then query that same notebook for optimization recommendations, use `references/notebooklm-profile-operating-model-audit.md`: inspect live state first, create a concise audit source, add it as a `--type text` source, wait until the source is `ready`, then query NotebookLM for an operator playbook rather than generic documentation.

When Karan asks to share current Hermes skills with a specific NotebookLM notebook for critique, leaning, or workflow improvement, use `references/notebooklm-current-skill-feedback-loop.md`: upload dated current local skill snapshots as text sources, wait for readiness, ask for operational critique, run a refinement pass against current Hermes constraints, then promote distilled findings to Hermes Brain rather than accepting generic recommendations blindly.

When Karan asks to make Hermes more autonomous/proactive around `sabnanikl-dev/Hermes-personal` or a similar personal-infrastructure repo, use `references/hermes-personal-autonomy-cron-planning.md`: query the strategic notebooks, ground against live repo/cron state, run a refinement pass, and recommend a phased deterministic-watchdog → proposal-scout → PR-producing loop. If Karan explicitly grants repo-local autonomy for Hermes-personal, promote the plan to autonomous-lab mode: direct commits or auto-merged PRs are allowed inside that repo after deterministic checks, while secrets, global Hermes config/profile authority, live/client systems, external messages, private data dumps, and costly unbounded research remain stop-the-line boundaries.

For Hermes-personal **proposal-scout** grounding specifically, query `Agent sdk` (`185f25cd-44e5-48ff-90a4-d319b71ffc31`) and `Strategic Engineering: Harnessing AI as a Force Multiplier` (`95758f68-a24f-442b-8973-bf542052b267`) every run before choosing changes. Use Agent sdk for concrete agent-loop/tool/handoff/tracing/guardrail/evaluation implementation patterns, and Strategic Engineering for prioritization, leverage, autonomy boundaries, stop conditions, and operating-model strategy. Feed both a compact current-state digest from the repo, use answers as principle input rather than live-state truth, and distill into repo-local artifacts/cron prompts/issue candidates instead of committing raw NotebookLM answers.

When Karan asks to query an AI-money/monetization notebook for Hermes-personal or another autonomy lab, treat the notebook as an idea source for marketed value, not as permission to chase side-hustle tactics. Apply `references/notebooklm-to-repo-artifact-synthesis.md`: extract durable monetization mechanisms, translate them into repo-local scripts/templates/rubrics/examples, preserve a human-release boundary for publishing/outreach/payments/promises, and update the live scheduled-agent prompt if future runs should use the artifact.

When a repo/harness should let agents query NotebookLM directly, use `references/repo-local-notebooklm-cli-wrapper.md`: add a read/query-only repo-local wrapper around the NotebookLM CLI, document grounding/approval boundaries, keep project/client prompts compact, avoid leaking raw `git status` noise into prompts, and verify wrapper behavior with an ad-hoc `hermes-verify-` script when no canonical test suite exists.

When Karan asks for a constructive + antagonistic review of the Hermes-personal harness or passive-revenue experiment, use `references/hermes-personal-adversarial-revenue-review.md`: spawn read-only Claude Code and Codex review lanes, query AI OS + Strategic Engineering + Ai money separately, treat audit scores as table stakes rather than revenue proof, and synthesize toward the smallest buyer-facing artifact / approval packet / market-test gate. For recurring adversarial review, prefer a script-only Claude Code/Opus cron that writes timestamped reports plus a stable `~/.hermes/reports/hermes-personal/adversarial/latest.md`, then patch the Product Scout / Value Clarity / approval crons to read that file before choosing changes. The reviewer cron should remain read-only; downstream crons distill P0/P1 findings into repo-local artifacts rather than copying raw reviewer prose.

When that review converges and Karan says to proceed with the revenue-moving next step, use `references/hermes-personal-product-pack-launch-assembly.md`: assemble the buyer-facing product pack under `dist/`, add a deterministic leak-checked build script, fill the single launch approval packet, validate all repo gates, commit/push within Hermes-personal autonomy, and keep publishing/checkout/outreach behind explicit Telegram approval.

If Karan rejects or hesitates on a public-live approval because the product value, use case, buyer, or usefulness is unclear — especially if he says the product feels self-referential — use `references/hermes-personal-value-clarity-gate.md`: treat the feedback as a stop-the-line product clarity blocker, mark launch state as not ready, remove/avoid approval pressure, redirect cron/scout prompts toward buyer/use-case clarity, log an autoresearch-style blocked/retest row, and do not ask for publishing/listing/checkout approval again until the four-line clarity test passes.

When Karan asks for a recurring end-of-day status report for the Hermes-personal experiment, use `references/hermes-personal-daily-html-reporting.md`: build a repo-local deterministic HTML report generator, track revenue in a simple TSV ledger, generate self-contained reports outside the repo, and schedule a `no_agent` cron via a wrapper script under `~/.hermes/scripts/`.

### 6. Decide promotion target

Use this decision matrix:

| Output | Destination |
|---|---|
| Source-heavy synthesis, durable strategy, project lessons | Obsidian wiki page |
| Reusable procedure | Skill |
| Compact preference/environment fact | Standard memory |
| Conversational/session-specific context | Hindsight |
| Temporary answer or one-off analysis | Chat only |

Prefer Obsidian for rich, named, cross-linked knowledge. Prefer skills for repeatable workflows. Avoid dumping raw NotebookLM answers into memory.

### 7. Write the Obsidian note if durable

Create or update a focused page under the correct Hermes Brain path, usually one of:

```text
~/obsidian-vault/hermes-brain/wiki/shared/research/
~/obsidian-vault/hermes-brain/wiki/shared/lessons/
~/obsidian-vault/hermes-brain/wiki/consultancy/research/
~/obsidian-vault/hermes-brain/wiki/consultancy/playbooks/
~/obsidian-vault/hermes-brain/wiki/femme-events/processes/
```

Use Hermes Brain frontmatter conventions:

```yaml
---
title: "Page Name"
domain: "shared | consultancy | femme-events"
type: "research | lesson | playbook | process | workflow"
status: "active"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
sources:
  - "NotebookLM: Notebook Title"
---
```

Keep the note distilled and actionable:

- Overview
- Durable principles
- Opportunities / implications
- Small next experiments
- Related links

### 8. Update index/logs and verify

If a new wiki page was created:

1. Add it to `~/obsidian-vault/hermes-brain/index.md` if it is a durable top-level reference.
2. Update the daily log under `logs/YYYY/MM/YYYY-MM-DD.md` if the session changed durable wiki state.
3. Read the created/updated file back.
4. Verify Obsidian can find it:

```bash
obsidian search query="Page Title"
```

### 9. Return a concise action-oriented summary

Final response should include:

- Notebook queried;
- what durable artifact was created/updated;
- the key synthesis;
- recommended next actions, in priority order;
- verification performed.

Avoid over-reporting citations unless the user asks; keep the source path and wiki page link clear.

## Pitfalls

- Do not create a generic NotebookLM research notebook unless Karan explicitly asks.
- Do not ingest raw NotebookLM answers wholesale into Obsidian.
- Do not update standard memory with research content unless it is a compact durable preference/fact.
- Do not create GitHub/Linear issues from this Obsidian synthesis workflow. For NotebookLM-derived GitHub issues or backlog items, use `notebooklm-to-github-issues`.
- NotebookLM auth expires; refresh from `chrome::Karan-PapiBot` when needed, then re-run `auth check`.
- When feeding NotebookLM a long generated artifact (HTML report, full plan, transcript), first try a compact extracted summary rather than the whole artifact. If a long `ask --prompt-file` returns `No parseable chunks in streaming chat response` or an empty answer, retry with a 1–3KB digest containing the plan goal, key sections, current decisions, and the exact critique request. Capture the lesson as “summarize before feedback,” not “NotebookLM is broken.”
- NotebookLM CLI source operations have command-specific flags: `source wait` uses `--timeout` while `source add` accepts `--request-timeout`/`--timeout`. If uploading a local Markdown skill file with `source add --type file` produces an `unknown` source that enters `status: error`, delete it with `notebooklm source delete -n <notebook_id> <source_id> -y --json`, then re-add the content as inline text with `source add --type text --title ...`. Verify `source list` shows no non-ready sources.
- NotebookLM answers may cite sources awkwardly; preserve source list in the wiki note, but make Hermes's synthesis cleaner than the raw answer.

## Verification Checklist

- [ ] NotebookLM auth checked/refreshed.
- [ ] Exact notebook and source list inspected.
- [ ] NotebookLM queried with a focused prompt.
- [ ] Relevant current source-of-truth state checked before action recommendations.
- [ ] Durable findings promoted to the right layer, not dumped into memory.
- [ ] Obsidian page/index/log changes read back.
- [ ] Obsidian search verified the new/updated note.
- [ ] Final answer included concrete next actions.
