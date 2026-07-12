# Static Contract Review Edge Cases

Use this reference when proving static-site / CMS contract PRs where docs, schemas, fixtures, and validators must agree exactly.

## Empty string vs null fallback parity

A common contract bug is treating “unset” differently in each layer:

- Schema permits `""` because a field only has `Rule.max(...)`.
- Validator treats blank/whitespace as unset via `trim()` and emits a fallback.
- GROQ uses `coalesce(field, fallback)`, which only falls back for null/missing and will emit `""` for an empty string.

This creates a false-green validator: the artifact can pass locally while the documented query renders a blank public label.

### Review probe

When a public projection uses fallback labels or values, check all three layers:

1. **Schema validation** — does it reject blank/whitespace when a value must not render blank?
2. **Validator / build script** — does it mirror the exact query semantics, not a friendlier JavaScript interpretation?
3. **Documented GROQ/query** — does it use `select(defined(field) && field != "" => field, fallback)` when empty strings should fall back, instead of `coalesce(field, fallback)`?

For whitespace-only values, prefer rejecting them at schema + validator level. GROQ does not trim strings by default; do not pretend it does.

## Deterministic ordering parity

If a validator claims a projected order, compare it to the documented query:

- Use explicit sentinels for missing sort keys when “missing sorts last” matters.
- Add a stable final tie-breaker such as `_id asc`.
- Note whether string comparisons are locale-aware or code-point / byte-ish; validators should match the query engine, not user-facing sort behavior.

## Synthetic fixture safety

Fixtures for public copy, reviews, testimonials, case studies, or client claims should be unmistakably synthetic unless source-backed and approved:

- Use names like `Sample Reviewer` / `Example Customer`, not plausible real names.
- Use `example.com` / fixture IDs like `fixture/not-a-real-...`.
- Do not include approval, consent, or source-authenticity claims unless they are true and evidenced.

## PR-bus discipline for terminal-only reviewer findings

If a reviewer CLI returns blocking findings only in terminal output, post a compact blocker capsule to the PR before sending the fix lane. This preserves the PR as the coordination bus and gives the builder/fix lane a live GitHub source to read. After the fix, post a closeout comment with the head SHA and verification commands.
