# Hermes Brain cleanup boundaries — 2026-05-05

Session-specific decisions from Karan during the Hermes Brain vault review.

## Confirmed boundaries
- Karpathy's LLM Wiki pattern is the intended standard for Hermes Brain.
- Hermes Brain remains primarily agent/business memory.
- Karan OS is the separate personal vault at `/Users/creator/Documents/Obsidian Vault/Karan OS`.
- Do not merge personal-vault implementation content back into Hermes Brain.
- Project trackers should not live in Hermes Brain. Use Linear/GitHub/project repos for active execution state; Hermes Brain should summarize durable facts, decisions, lessons, and links only.

## Cleanup preference
- Move root-level orphan/misplaced files into the correct `wiki/` folders when they are real content.
- Delete confirmed-empty root stubs after verification.
- Keep the vault root boring: `SCHEMA.md`, `index.md`, `log.md`, `raw/`, `wiki/`, `logs/`, and intentional Obsidian support files only.

## Large-page exception
- `wiki/consultancy/business-plan.md` should stay large. It is a living Papi AI strategy/business-plan document that Karan and Hermes will continue iterating as the business pivots.
- Do not split it merely because it exceeds the usual size threshold. Size triage applies to stale research dumps, raw transcripts, or pages that are hard to navigate.

## Batch 1 result
- Deleted empty root stubs:
  - `2026-04-29 Daily Log Model Not Found.md`
  - `Linear Board and Issue System.md`
- Moved `linear-workflow.md` to `wiki/consultancy/playbooks/linear-workflow.md`.
- Moved `notion-vs-linear-comparison.md` to `wiki/consultancy/research/notion-vs-linear-comparison.md`.
- Inspected `Untitled.base`; it contained a minimal Obsidian Bases table stub and was left unchanged for later review.

## Batch 2 result
- Moved lesson content from root `shared/lessons/` into `wiki/shared/lessons/`.
- Moved `shared/projects/ARCHIVED.md` to `wiki/shared/projects/Archived Project Summaries.md` and normalized frontmatter.
- Folded durable Femme Events facts into `wiki/femme-events/Femme Events Overview.md`.
- Folded durable Papi AI Consulting facts into `wiki/shared/business/Papi AI Consulting.md`.
- Deleted stale root project trackers for Femme Events, HKT Clothiers, JMD Menswear, and Papi AI Consulting after durable facts were preserved.
- Removed the duplicate root `shared/` directory entirely.
- Updated `Project Status.md` and `index.md` references; verified no non-log markdown files referenced the deleted root tracker paths.

## Batch 3 result
- Cleaned `index.md` navigation.
- Removed stale `[[Hermes Proposed User Vault]]` reference.
- Added Karan OS boundary path: `/Users/creator/Documents/Obsidian Vault/Karan OS`.
- Indexed all current `wiki/` pages while keeping `index.md` under 3,000 chars.
- Collapsed daily logs to a folder pointer (`logs/YYYY/MM/YYYY-MM-DD.md`) instead of listing each daily log.
- Verified no unresolved wikilinks inside `index.md` and no missing `wiki/` pages by strict filename/stem check.

## Batch 4 result
- Updated `SCHEMA.md` to encode Hermes Brain vs Karan OS boundaries.
- Encoded project-tracker boundary: Linear/GitHub/project repos own active tasks; Hermes Brain summarizes durable facts only.
- Encoded root hygiene rule and approved root entries.
- Encoded living-document exception for `wiki/consultancy/business-plan.md`.
- Added Karpathy LLM Wiki operating principles and daily log conventions.

## Batch 5 result
- Normalized frontmatter on 17 wiki pages without changing body content.
- Added missing `title`, `domain`, `type`, `status`, `created`, and `updated` fields where needed.
- Fixed one malformed frontmatter opener in `website-design-framework-10k.md`.
- Changed `Client JMD Menswear.md` schema status from `engaged` to `active` and preserved the business-specific state as `client_status: "engaged"`.
- Expanded `SCHEMA.md` type examples to include current page types such as `workflow`, `checklist`, `project-dashboard`, `project-archive`, and `business-plan`.

## Batch 6 result
- Fixed all 3 broken wikilinks:
  - `Karan Sabnani.md` now links to `Karan-Personal-Obsidian-Vault-Approach` instead of the removed `Hermes Proposed User Vault`.
  - `intake-workflow.md` and `triage-playbook.md` now link to `linear-workflow.md` instead of the deleted `Linear Board and Issue System` stub.
- Added meaningful `Related` links to the 3 orphan pages:
  - `linear-workflow.md`
  - `notion-vs-linear-comparison.md`
  - `Karan-Personal-Obsidian-Vault-Approach.md`
- Added useful outbound links to remaining deadend pages where the links aided retrieval: lessons, harness best practices, and Antigravity/website-design source notes.
- Compacted the daily log to stay under the 3,000 character cap.
- Verified graph health: 0 broken wikilinks, 0 orphans, 0 deadends.

## Batch 7 result
- Completed long research/source-dump triage for the most obvious transcript-like pages.
- Moved full timestamped transcripts out of curated wiki pages and into immutable raw sources:
  - `raw/shared/video-transcripts/vibecode-beautiful-websites-antigravity-jack-roberts-transcript.md`
  - `raw/shared/video-transcripts/karan-personal-obsidian-vault-aios-transcript.md`
- Compacted the corresponding wiki pages into source-linked synthesis pages:
  - `wiki/shared/tools/Youtube Video learnings/vibecode-beautiful-websites-antigravity-jack-roberts.md`
  - `wiki/shared/research/Karan-Personal-Obsidian-Vault-Approach.md`
- Added a concise AIOS interpretation to the Karan personal-vault research note: useful patterns are portable `me.md`, vault map, and skills/process map; avoid merging Karan OS into Hermes Brain or overbuilding multi-vault automation before proven.
- Documented `raw/shared/` in `SCHEMA.md` and relevant skills as the place for cross-domain raw sources/transcripts.
- Preserved `wiki/consultancy/business-plan.md` unchanged as an approved large living strategy document.

## Next likely cleanup class
Optional AIOS patterns page:
- Only create if Karan wants a small compiled pattern note.
- Keep it practical and boundary-aware: Hermes Brain remains agent/business memory; Karan OS remains personal operating context.
- Do not import a full AIOS/AIS-OS architecture wholesale.
