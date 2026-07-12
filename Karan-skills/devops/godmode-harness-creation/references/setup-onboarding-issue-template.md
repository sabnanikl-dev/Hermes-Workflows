# GodMode Setup/Onboarding Issue Template

Use this reference when drafting or creating issues for a first-run/settings/setup flow that lets operators configure GodMode without hand-authoring `.agentic/godmode.yaml`.

## Trigger

Use when the user asks for an onboarding/config/setup screen or overlay to:

- choose/open the operated project;
- choose which agents power `head`, `builder`, `reviewer_a`, and `reviewer_b`;
- validate local agent commands;
- connect/check GitHub access;
- save/apply `.agentic/godmode.yaml`.

## Grounding checks before drafting/creating

- Inspect current open issues to avoid duplicating multi-project/project-switcher work.
- Ground against `origin/main`, not a stale local branch, when citing current code state.
- Check current docs and seams:
  - `docs/spec.md`
  - `AGENTS.md`
  - `src/main/config.ts`
  - `src/main/github.ts`
  - `src/renderer/App.tsx`
  - `src/renderer/components/ProjectBar.tsx`
  - `src/preload/index.ts`
  - `src/shared/ipcChannels.ts`
  - `src/shared/types.ts`

## Essential scope points

- Settings rail/button opens a dismissible setup/settings overlay.
- Auto-suggest or prompt setup when project/config/GitHub state is missing or invalid, but do not block advanced default usage unless the action truly cannot proceed.
- Keep app repo vs operated project explicit. Config writes target the operated project root.
- Role slots stay generic: `head`, `builder`, `reviewer_a`, `reviewer_b`.
- Offer built-in presets as defaults/display labels only: Hermes, Claude Code, Codex, custom CLI.
- Validate agent definitions before save: slug ids, command non-empty, reviewer panes not duplicated, roles reference known agents.
- Check command availability against the same safe PATH/launch environment GodMode uses.
- GitHub remains `gh`-first for v1: show missing `gh`, unauthenticated, no repo, and connected/readable states.
- Never store GitHub tokens in GodMode config. Do not ask users to paste tokens into the app. Display account-only or redacted auth info.
- Preview generated YAML before writing, require explicit confirmation, create `.agentic/` if needed, and back up an existing config before overwrite.
- Reload through the same main-process config loader after save so renderer panes and registry update from canonical state.
- If live PTY sessions exist, require stopping them or state that changes apply only to new sessions.

## Out of scope defaults

- Embedded GitHub OAuth app flow.
- GitHub token storage.
- Installing agents automatically.
- Running agents during setup.
- Full multi-project rail switcher.
- SaaS/team onboarding.
- Auto-merge/deploy behavior.

## Verification

Issue acceptance should require:

```bash
npm run typecheck
npm run build
```

Manual smoke checks should cover:

1. repo with missing `.agentic/godmode.yaml`;
2. default role config preview/save;
3. saved config reloads and panes update;
4. custom missing command is flagged;
5. no GitHub remote shows `no_repo`;
6. unauthenticated or missing `gh` guidance is visible when practical;
7. no token/secret is written to config or logs.
