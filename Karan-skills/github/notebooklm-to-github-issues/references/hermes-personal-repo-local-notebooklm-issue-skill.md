# Hermes-personal repo-local NotebookLM issue skill pattern

Session learning: Karan wanted NotebookLM-to-GitHub issue behavior available as a **repo-local/project skill** for `sabnanikl-dev/Hermes-personal`, not only as a global Hermes skill.

## When to apply

Use this pattern when a repo is acting as an autonomy lab or project-specific operating system and Karan wants agents/crons to use NotebookLM findings to create issue candidates, backlog items, or implementation tickets inside that repo.

## Pattern

1. Keep the global skill class-level (`notebooklm-to-github-issues`).
2. Add a local class-level copy/adapter under the repo:

```text
skills/notebooklm-to-github-issues/SKILL.md
skills/manifest.md
```

3. Scope the local skill to the repo by name, e.g. `sabnanikl-dev/Hermes-personal`.
4. Wire the local skill into the repo harness:
   - README/repo map;
   - local skill manifest loading rules;
   - validation scripts/audits;
   - context packet script;
   - relevant cron prompt(s).
5. Preserve authority gates:
   - no issues in other repos without explicit approval;
   - no external/live actions implied by issue creation;
   - no raw NotebookLM answers or private exports in issues.

## Hermes-personal strategic notebooks

For the Hermes-personal proposal scout, every run should query both notebooks before deciding whether to draft/create an issue:

```text
AI OS — 7442a0ae-5a2d-4863-ac9b-b0a8bccea6f3
Strategic Engineering: Harnessing AI as a Force Multiplier — 95758f68-a24f-442b-8973-bf542052b267
```

Use NotebookLM output as principle input, not as live repo state. Feed NotebookLM a compact current-state digest from `scripts/proposal_scout_context.py`, then de-duplicate against live GitHub issues before creating anything.

## Verification

For repo-local skill/harness changes, use the repo's own validator/audits and a focused ad-hoc verifier if no canonical suite exists. Verify any created GitHub issue with:

```bash
gh issue view <number> --repo sabnanikl-dev/Hermes-personal --json number,title,body,labels,state,url
```
