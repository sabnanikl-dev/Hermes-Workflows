# JMD Inventory Backend + Drive Automation Plan Reference

Use this when Karan asks about the previously discussed automation for taking JMD photos from Google Drive, identifying new/old images, adding approved images to the website, and rotating/archive old photos.

## Canonical plan location

Primary tracker home:

- **Linear JMD-23** — the actual May 14 JMD website/photo-automation plan packet, with child issues.

Supporting local repo doc:

`/Users/creator/projects/consultancy/JMD-Menswear/deliverables/JMD-Website/docs/research/inventory-backend-automation-plan.md`

Status note:

- The local repo doc is supporting research/draft material and may predate the finalized JMD-23 packet.
- When Karan asks where the plan is, point to **JMD-23 first**, then mention the repo doc as source/supporting material.

## Recommended architecture from the draft

- Google Drive = owner photo intake dock for Lucky/Danny.
- Sanity = website backend/CMS and image asset delivery.
- Google Sheet or Sanity Studio = approval ledger/status view.
- Vercel Cron or GitHub Actions = scheduled worker/automation runner.
- Website language = showroom/recent highlights, not live e-commerce inventory.

Safe flow:

1. Drive upload creates an intake record.
2. Karan/Lucky/Danny approval marks it ready.
3. Approved image imports into Sanity.
4. Automation schedules/publishes after configurable X days.
5. Rotation archives after configurable Y days.

Important constraint: do not publish raw Drive uploads directly to the public website. Human approval is required for MVP.

## Draft tracker issues inside the plan

Draft Linear issues:

1. Decide and document JMD inventory backend architecture.
2. Define Sanity showroom inventory schema.
3. Build CMS-powered “Recently on the floor” website section.
4. Create Drive intake folder and approval ledger workflow.
5. Implement Drive intake sync worker.
6. Implement Drive-to-Sanity image importer.
7. Implement scheduled publish and rotation job.
8. Write owner SOP and operational handoff.

Draft GitHub issues:

1. Add Sanity inventory backend architecture doc.
2. Add Sanity configuration and showroom item schema.
3. Render published showroom items on website.
4. Build Drive intake sync worker with dry-run mode.
5. Implement approved Drive image → Sanity importer.
6. Add scheduled publish/archive rotation job.
7. Add inventory pipeline SOP and client-safe photo guide.

## Search/retrieval lesson

If Karan says he remembers this idea but cannot find it in Linear/GitHub, do not stop after tracker searches. Check:

- session history/Hindsight for prior summary,
- Hermes Brain daily logs,
- JMD repo docs under `docs/research/`,
- local JMD project folders under `deliverables/JMD-Website/` and `coding-harnesses/`.

In the May 2026 case, the daily log pointed to a draft repo research doc, while Linear/GitHub correctly had no created issues yet.

### Date-based “where is the plan doc?” lookup

When Karan asks for a JMD plan doc “we discussed on <date>”:

1. Load this skill first, then check the relevant Hermes Brain daily log, e.g. `~/obsidian-vault/hermes-brain/logs/YYYY/MM/YYYY-MM-DD.md`.
2. Search local JMD project files for likely plan names under `~/projects/consultancy/JMD-Menswear/`, especially `deliverables/JMD-Website/docs/research/` and `plans/`.
3. Use modification dates only as supporting evidence, not the sole source: the canonical doc may predate the later conversation that refined the direction.
4. Report the exact path first, then a one-sentence note about status/staleness.

Specific May 14, 2026 note: the canonical plan doc remains `deliverables/JMD-Website/docs/research/inventory-backend-automation-plan.md`, but the May 14 discussion refined the direction toward deterministic n8n scheduled reconciliation: Google Drive approved folder as source of truth, Sanity as CMS/assets, website reads Sanity only, archive rather than hard-delete. If using the doc for implementation, refresh any older Vercel Cron/GitHub Actions language against the n8n direction before building.
