# Stale deployment alias vs. UI regression

Use this when a user reports that a recently merged UI fix is still absent on a preview/non-production URL.

## Diagnostic pattern

1. **Reproduce the exact visible state.** Open the reported URL and inspect the rendered DOM/accessibility tree. Distinguish absent elements from clipped/off-screen elements. Fallback copy where actions should be is strong evidence of state/data gating rather than CSS clipping.
2. **Inspect the live browser-facing artifact.** Fetch the exact JS/JSON/CSS asset loaded by the page and check whether it contains the expected state. Do not infer live state from the repository alone.
3. **Refresh git state before comparing.** `git ls-remote` can show a newer remote SHA while the local `origin/main` ref remains stale. Run `git fetch origin main`, then inspect `origin/main:<path>`.
4. **Compare three states explicitly:** merged/default-branch artifact, deployment/commit status, and public-alias artifact.
5. If merged code is correct but the alias still serves the old artifact, classify this as **deployment propagation/alias lag**, not a code regression. Do not create a compensating code change.
6. Monitor deployment status and poll the public artifact until both update. A green deployment status alone is insufficient; verify the public alias content.
7. Re-open the exact public route and confirm the expected elements in the live DOM.
8. For responsive action pairs, run a real mobile-width geometry check against the public alias: count, labels, same-row alignment, non-overlap, container bounds, tap-target size, horizontal overflow, and link attributes. Capture a fresh screenshot.

## Evidence checklist

- Exact reported URL and state/model identifier.
- Live artifact before propagation (for example, an empty `enabled` map).
- Fetched default-branch SHA and expected artifact contents.
- Deployment status transition (`pending` to `success` or failure).
- Live artifact after propagation.
- Live DOM showing expected controls.
- Mobile geometry output and screenshot.

## Pitfalls

- Do not call missing controls “clipped” merely because a screenshot has blank space. Check whether controls exist in the DOM and whether fallback copy is rendered.
- Do not trust a stale remote-tracking ref; fetch before reading `origin/main`.
- Do not trust a PR preview URL to represent the public alias. Preview deployments may also be access-protected while a stable alias is public.
- Do not redeploy, promote, or change aliases without approval. First determine whether an already-running deployment will finish normally.
- Do not report success when only repository tests pass. The user’s complaint concerns the public URL, so verification must end there.
