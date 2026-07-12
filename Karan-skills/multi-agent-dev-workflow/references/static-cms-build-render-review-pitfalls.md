# Static CMS Build-Render Review Pitfalls

Use this reference when reviewing or fixing static-site PRs that add a build-time CMS render path (Sanity/Portable Text -> generated `site/` HTML), especially when the PR intentionally avoids live browser queries.

## Lessons from JMD issue #141 / PR #165

A build-time render pipeline can pass offline fixture tests while still failing the real live path if the query shape and projector shape drift.

### 1. Verify live query shape matches the projector

Common bug:

- GROQ/query returns a flattened public projection (`slug`, `coverImageUrl`, `metaTitle`, `noIndex`, etc.).
- The projector still expects raw Studio documents (`_type`, `status`, `slug.current`, `coverImage.asset.url`, nested `seo`, etc.).
- The live build passes query results directly to the raw-document projector.
- Outcome: every real published post is dropped, even though fixture tests using raw documents pass.

Review/fix checklist:

- Add tests that feed the projector the **actual query-shaped live result**, not only raw fixture documents.
- Either make the query return the raw fields the projector expects, or make the projector accept/normalize the query projection explicitly.
- Include `_type`/`status` only if they are intentionally part of the normalized public-safe shape; do not leak them into emitted browser output.
- Verify SEO fallbacks, noindex, cover images, category/kicker, and body all survive the chosen shape.

### 2. Escape JSON-LD for script context, not just JSON context

`JSON.stringify()` is not enough when Sanity/user-authored strings are embedded inside `<script type="application/ld+json">`.

Blocking case to test:

- A title or breadcrumb name contains `</script><script>alert(1)</script>`.
- Plain JSON output can terminate the script element in HTML parsing.

Review/fix checklist:

- Use a helper that JSON-stringifies and then escapes `<`, `>`, `&`, U+2028, and U+2029 (for example replacing `<` with `\u003c`).
- Apply it to every JSON-LD block, not only visible markup/meta tags.
- Add a hostile JSON-LD self-test that asserts the generated page does **not** contain a literal `</script><script` breakout while still producing parseable JSON-LD content.

### 3. Remove stale generated routes when records leave the public set

A live static build that only writes current published pages can leave old generated pages on disk after a record becomes draft/archived/noindex.

Failure mode:

- Previous run generated `site/blog/old-slug/index.html`.
- Sanity record later becomes draft/archived or is removed.
- New build writes current pages but does not delete `old-slug`.
- Sitemap recomputation scans on-disk `site/blog/*/index.html`, so stale pages remain routable and may remain sitemap-included.

Review/fix checklist:

- Before writing generated article pages, clean only the generator-owned slug directories/artifacts, or maintain an explicit generated manifest and delete stale generated outputs.
- Preserve hand-authored/static fallback pages only if docs explicitly say they coexist; distinguish generator-owned routes from static/manual routes.
- Add a test that creates a stale generated page, runs the build with that slug absent/draft/archived, and verifies the stale page is removed or noindexed and omitted from sitemap.

### 4. Resolve Sanity inline image asset refs in body content

Sanity Portable Text/block-content image blocks often store an unresolved asset reference (`asset._ref`) rather than `asset.url`. If the live GROQ query passes `body` through raw and the renderer only accepts `block.asset.url`, approved inline body images are silently dropped while fixtures with pre-resolved URLs still pass.

Review/fix checklist:

- Prefer projecting inline image blocks in GROQ with `asset->url` so live query-shaped rows carry a resolved CDN URL.
- Also make the renderer robust to raw `asset._ref` by deriving the Sanity CDN URL from the ref using the active project/dataset, then reapplying the same CDN + non-empty-alt safety gates.
- Thread project/dataset through `renderPortableText` / projectors when deriving URLs.
- Add a non-vacuous self-test: raw `_ref` image + alt -> rendered `<img>`; pre-resolved `asset.url` still renders; bad host/unparseable ref/alt-less images stay dropped.

### 5. Plain-text source matters for reviewability

If a generated or hand-authored source file accidentally contains literal control bytes (especially NUL), Git can classify it as binary and hide the diff.

Review/fix checklist:

- Run `file <changed-source>` or a byte scan when a text file appears as binary in `git diff --stat`.
- Replace literal control bytes in regex source with escaped source text (for example `/[\\x00-\\x1f]/`) so the file remains UTF-8 text.
- Verify `git diff` shows a normal text diff, `file` reports text, and NUL count is zero.

### 6. Offline visual QA for deploy-gated generated pages

When generated public pages are intentionally not committed/deployed in the PR, visual QA can still exercise the render path without mutating production.

Review/fix checklist:

- Run the offline/fixture generator into a scratch preview output.
- Serve a copy that overlays the generated preview routes onto the static `site/` assets so CSS/images/nav resolve over HTTP, not `file://`.
- Label screenshot evidence as fixture/offline proof, not live deployed proof.
- Pair screenshots with DOM assertions: H1 count, cards/routes present, article CTA targets, JSON-LD types, horizontal overflow, and browser console errors.
- If fixture image URLs are synthetic and appear broken visually, do not overclaim visual image success; rely on targeted renderer tests for real Sanity asset-ref/URL behavior and disclose the fixture limitation.

## When near tool-call/budget limits

Do not start a builder fix lane for these blockers unless there is enough budget to verify the follow-up commit, run tests, and rerun A/B review. If forced to stop while the builder is still running, final status must say the fix result is unknown and list the exact last verified head/review state.
