# JMD About Page Response Ingestion

Use when Lucky/Danny reply to an About-page or general website-copy intake email and Karan asks to turn the responses into repo docs and GitHub issues.

## Goal

Turn client source material into a repo-local implementation source document, then create/update GitHub issues so builders can safely add it to the website without inventing facts or publishing unapproved copy.

## Recommended workflow

1. **Find the source email**
   - Prefer the `google-workspace` Gmail wrapper over Himalaya when Gmail OAuth is configured.
   - Search terms that worked for this class of task:
     - `JMD Lucky about page copy OR general website copy newer_than:90d`
     - subject/thread terms such as `Quick About JMD questions for the new website page`.
   - Read the full message and treat it as source material, not polished public copy.

2. **Reconstruct repo state first**
   - Use the JMD website repo: `~/projects/consultancy/JMD-Menswear/deliverables/JMD-Website` unless Karan says another repo.
   - Read `AGENTS.md`, `docs/spec.md`, current branch/status, recent issues, and existing About/blog issues before creating duplicates.
   - If the current worktree has unrelated local changes, create a clean git worktree from `origin/main` for the docs PR.

3. **Create a repo-local source document**
   - Preferred path: `docs/content/jmd-about-and-site-copy-source.md` or a similarly named `docs/content/` file.
   - Include:
     - source email/date/thread summary
     - executive synthesis
     - clean source facts approved for drafting
     - direct phrases/concepts to preserve
     - draft-only copy blocks builders may adapt
     - homepage copy opportunities
     - missing/blocked inputs
     - approval checklist before public launch
   - Status must say: internal/source draft only; not approval to publish, deploy, change DNS/hosting, or send client-facing content.

4. **Preserve source truth, do not launder it into fake facts**
   - Fix typos only in synthesized draft copy, not in the source-fact record.
   - Do not invent dates, awards, business history, customer stories, photos, pricing, stock counts, or exact availability.
   - If Lucky says a customer story can be made up, still do **not** fabricate one by default. If a composite/anonymized story is useful, flag it for Karan/Lucky approval first.
   - Keep Danny-sensitive language conservative: no live inventory, guaranteed availability, online checkout, hard prices, or reorder promises.

5. **Branch, commit, PR, and verify**
   - Create a doc-only branch such as `docs/about-copy-synthesis`.
   - Commit the source document and push.
   - Verify remote branch SHA matches local SHA before reporting.
   - Open a PR with summary, validation, and approval/deployment safety notes.
   - Verify the PR includes the expected commit via `gh pr view --json commits`.

6. **Create/update GitHub issues**
   - Search existing issues first. If an About page issue already exists, comment with the new source doc and source-summary instead of duplicating it.
   - Create granular implementation issues for distinct website workstreams, e.g.:
     - homepage story/exclusivity copy refinements
     - showroom/try-on experience copy and CTAs
     - local service-area + event-intent SEO copy
     - approved owner/team photo intake and integration
   - Each issue should include the source doc path, context, recommended scope, guardrails, acceptance criteria, and draft-only approval status.
   - If Karan explicitly says to “generate/create GitHub issues,” that is enough approval for issue creation; still do duplicate search and verify after creation.

## JMD-specific source facts from the 2026-05-28 response

Use as examples of the kind of facts to capture, but always re-read the current repo doc/email before implementing:

- Danny + Lucky described 70+ years combined experience in men’s custom clothing and retail.
- Cornell helps with visual merchandising and unique outfit combinations.
- Core positioning: exclusivity, latest fashions, great service.
- Limited-floor model: often one piece per size, small total runs, and fashion garments are not simply reordered.
- Showroom value: customers can feel the garment, verify fit, eliminate uncertainty, and see mannequin/styled combinations.
- Local/event relevance: Conyers and surrounding areas; prom, weddings, quinceañeras, church events, banquets, interviews, photoshoots, date nights, galas.

## Verification checklist

- Source email was read directly.
- Repo source document exists and is committed.
- Branch push is verified by matching local and remote SHAs.
- PR is open and contains the expected commit.
- Issues/comments are verified by reading them back and checking source-doc references + acceptance criteria.
- Daily log records the raw source ingestion and tracker updates.
