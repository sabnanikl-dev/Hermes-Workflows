# Electron renderer preview visual QA for GodMode PRs

Use this reference when a GodMode/Electron PR changes operator-facing renderer UI, disabled/enabled control honesty, layout, or labels.

## Pattern

1. Run the repo's real verification first when possible:
   - `npm run typecheck`
   - `npm test`
   - `npm run build`
   - `npm run smoke` for preload/main/IPC/renderer wiring changes.
2. For a quick visual check of static renderer state, start Vite from the PR worktree as a tracked background process:
   - `npm run dev -- --host 127.0.0.1 --port <free-port>`
3. Open `http://127.0.0.1:<port>/` with browser tools.
4. Capture a screenshot/visual inspection and check browser console output.
5. Verify the specific operator-facing claim, for example:
   - Global command/chat controls that are not wired are visibly disabled/unavailable.
   - Enabled role message controls are not visually masquerading as global/team chat.
   - Layout remains readable at the default dashboard viewport.
6. Stop the tracked Vite background process after inspection.

## Important boundary

Renderer-only Vite preview is useful for visual/layout sanity and disabled-state honesty, but it does **not** prove Electron preload/main IPC behavior. For changes touching `src/main`, `src/preload`, PTY, or IPC channels, `npm run smoke` remains the stronger gate because it launches real Electron against the production renderer and checks the preload bridge / PTY path.

Report visual QA as a separate evidence line from smoke/CI, not as a replacement for them.