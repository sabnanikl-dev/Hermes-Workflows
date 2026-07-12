# Hermes Personal Adversarial Revenue Review Pattern

Use this reference when Karan asks to review or critique `sabnanikl-dev/Hermes-personal` against its revenue-generating goal, especially when he wants both a constructive Claude Code lane and an antagonistic Codex lane with NotebookLM access.

## Trigger

Karan asks for a review of the Hermes-personal harness, passive-revenue experiment, Product 001, approval packet, or revenue-moving next steps, and wants agents to query appropriate NotebookLM notebooks and synthesize what will move the needle.

## Agent setup

Run this as a **read-only strategic review**, not a PR/build loop, unless Karan explicitly asks for repo mutations.

Recommended lanes:

- **Claude Code constructive reviewer** — use Claude Code with the full Fable 5 model name when Karan asks for Fable: `--model 'claude-fable-5'`. The alias `fable` also works, but `fable-5` may be rejected by Claude Code. Smoke-test before launch.
- **Codex antagonistic reviewer** — use `codex exec --cd /Users/creator/projects/Hermes-personal --dangerously-bypass-approvals-and-sandbox` with a strict read-only prompt.

Both prompts should explicitly forbid repo edits, commits, pushes, issue/PR creation, publishing, posting, outreach, payment setup, account mutations, and global Hermes/profile changes. Allow writing only to `/tmp/...review.md` report files.

## Required grounding

Before or inside each review lane, inspect the live repo state:

```bash
cd /Users/creator/projects/Hermes-personal
git status --short --branch
git remote -v
gh repo view sabnanikl-dev/Hermes-personal --json nameWithOwner,url,defaultBranchRef,isPrivate
python3 scripts/proposal_scout_context.py
python3 scripts/validate_repo.py
python3 scripts/local_skill_audit.py --min-score 80
python3 scripts/market_viability_audit.py --min-score 80
python3 scripts/product_experiment_audit.py --min-score 80
python3 scripts/loop_audit.py --min-score 80
python3 scripts/four_cs_audit.py --min-score 80
```

Read at minimum:

- `AGENTS.md`
- `README.md`
- `skills/manifest.md`
- `skills/ai-money-product-research/SKILL.md`
- `skills/product-experiment-loop/SKILL.md`
- `docs/autonomy-policy.md`
- `docs/marketed-value-lane.md`
- `docs/external-approval-and-agent-accounts.md`
- `docs/rubrics/market-viability-rubric.md`
- `prompts/passive-revenue-product-scout.md`
- active Product 001 files, especially `sunday-launch-readiness.md`, `experiment-ledger.tsv`, `launch-approval-packet.md`, and any `dist/`/deliverable files.

## NotebookLM grounding

Query these notebooks separately with a compact current-state digest. Treat NotebookLM as principle/input, not live state truth:

- `AI OS` — `7442a0ae-5a2d-4863-ac9b-b0a8bccea6f3`
- `Strategic Engineering: Harnessing AI as a Force Multiplier` — `95758f68-a24f-442b-8973-bf542052b267`
- `Ai money` — `c5c73a43-3ad5-489b-8f57-354ad6bfe7f2`

Constructive query shape:

```text
Using only this notebook's sources, and given this current Hermes-personal state digest: <digest>, what is the single highest-leverage next repo-local move toward passive/low-fulfillment revenue? Rank by direct revenue impact, speed to public-ready artifact, safety/approval boundaries, and evidence quality. Name what NOT to do yet.
```

Antagonistic query shape:

```text
Using only this notebook's sources, and given this current Hermes-personal state digest: <digest>, what would you challenge or cut if the goal is real passive/low-fulfillment revenue quickly? What is the highest-leverage next repo-local move, what is premature, what evidence is missing, and what approval-gated market test would matter most?
```

## Synthesis rule

Treat perfect audit/validator scores as table stakes. They prove safety and harness completeness; they do **not** prove buyer demand, purchase intent, channel fit, or product clarity.

When both reviewers converge, prioritize the revenue-moving bottleneck over more meta-harness work. In the 2026-07-04 Product 001 review, both lanes converged on:

1. stop adding validators/rubrics/NotebookLM loops/source-map research;
2. assemble one buyer-facing sellable deliverable/export;
3. fill `launch-approval-packet.md` as the single approval surface;
4. pick one price/platform/refund posture;
5. ask Karan to approve one low-risk public demand test.

## Report shape

Final synthesis should include:

- agents launched and model details;
- notebooks queried;
- verification/read-only evidence;
- what the reviewers agreed on;
- what was considered busywork/theater;
- the one next repo-local action most likely to move revenue;
- exact approval gate for any public/live action.

## Pitfalls

- Do not let reviewer agents mutate the repo unless the task explicitly changes from review to build.
- Do not confuse concurrent cron commits with reviewer side effects; verify final `git status`, HEAD, and remote SHA after agents finish.
- Do not report the harness as revenue-ready because audits are 100%; inspect whether there is an actual buyer-facing artifact and filled approval packet.
- Do not harden a transient model-name failure as “Fable does not work”; the durable fix is to use Claude Code’s full model name `claude-fable-5` when Karan says Fable 5.
