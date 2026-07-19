# Pre-PR architecture and acceptance audit

Use when the builder has not opened a PR yet and the deliverable is a compact, evidence-backed verifier checklist rather than code changes.

## Read-only grounding

1. Read the live issue and linked/adjacent issues, including current state and comments. Treat issue prose that names an old commit or open/closed state as potentially stale.
2. Identify the live default-branch SHA with `git ls-remote origin refs/heads/main`; compare it with local `origin/main` and inspect only the exact matching tree. Avoid fetching or checking out when the user requires strict read-only operation.
3. Read repository instructions, baseline commands, recent merged work, and the exact implementation/docs/tests named by the issue.
4. Run the existing baseline when it is side-effect-free, then verify the worktree is still clean.
5. When an external source artifact drives generation, inspect its real schema, hash, edge-case distribution, and representative rows rather than trusting issue counts alone.

## Trace contracts across seams

Map each acceptance criterion across four layers:

- **Source/generator:** inclusion rule, identity, provenance, deterministic ordering, missing/duplicate handling, sanitization, and CI source availability.
- **Stored/browser projection:** distinguish repo-visible candidate/provenance data from browser-facing data. Sensitive or unapproved URLs can be unsafe even when the UI merely chooses not to render them.
- **Runtime/UI:** bounded DOM/network work, progressive enhancement, failure isolation, accessibility, history state, and cleanup ownership.
- **Validators/docs:** ensure old validators are replaced or materially updated instead of remaining green over obsolete behavior; keep package scripts, specs, build plans, and source contracts synchronized.

## High-risk checks for generated catalogs

- Validate the actual source field names and nested shapes.
- Reject duplicate IDs before map/object insertion can overwrite them.
- Preserve IDs as strings; avoid permissive numeric parsing for query/deep-link identity.
- Inspect all asset URL path variants. Do not reuse a narrow primary-image regex for alternate-image paths unless the source proves that invariant.
- Require deterministic sort/key order/newline and avoid generated timestamps in byte-stable artifacts.
- Test long text, missing labels, one/many assets, repeated titles, malformed rows, and injection-like text; render untrusted text via text nodes.
- Resolve how `--check` works in CI when the owner source lives outside the repository. Block absolute-local-path designs without a committed sanitized contract, fixture/provenance strategy, or another explicit reproducible source.

## Runtime and state-machine probes

- Count real DOM nodes and network requests; `loading="lazy"` alone does not prove bounded loading.
- Keep a no-JS/static fallback visible until validated enhanced content has mounted. Test script failure, fetch failure, malformed data, and broken/hung individual assets.
- For dialogs, verify accessible naming, focus entry/trap/return, background `inert` or equivalent, scroll-lock ownership, Escape/backdrop/visible-close paths, and listener/DOM cleanup across repeated cycles.
- For shareable query state, distinguish initial deep links from page-pushed history entries. `popstate` must reconcile without pushing; closing removes only owned state; asynchronous completion must re-read current URL/state so stale work cannot reopen a closed dialog.
- Test positive authorization with deterministic fixtures when live authority is disabled; never flip committed production authority merely to make a happy-path button appear.

## Output shape

Lead with audit basis: live issue URL, exact default-branch SHA, baseline result, and read-only/clean status. Then provide a concise checkbox list grouped by P0 contract boundaries and likely regression surfaces, with file/line references. State any issue/default-branch drift explicitly. Do not pretend to approve a PR that does not yet exist.
