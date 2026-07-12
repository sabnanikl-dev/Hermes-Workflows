<!-- Archived source skill consolidated into `research-workflow` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: productized-service-research-report
description: Build a polished HTML business brief for a productized service idea by combining tool/vendor research, competitor analysis, economics, ICPs, GTM, and risks.
---

# Productized Service Research Report

## When to Use
Use this when Karan asks for research on turning an AI/automation capability into a product or service for Papi AI Consulting, especially if the deliverable should be a business brief, market report, competitive analysis, or HTML report.

Examples:
- "Research building AI receptionists for small businesses."
- "Can this be a product for my AI consultancy?"
- "Find tools, competitors, economics, and best customer types."
- "Bring it into one report I can view."

## Core Positioning Principle
For Papi AI Consulting research, keep the service **human-led and AI-enhanced**. Karan wants to remain the main product/trusted advisor; AI is the leverage layer, not the headline.

Avoid narrowing Papi into only lead-generation or AI receptionist offers unless the user explicitly asks. Preferred broader positioning:
- practical content, operations, and automation systems for brick-and-mortar/small businesses
- owners get repetitive work off their plate so they can focus on what makes the business special
- build the underlying systems/workflows first; only migrate repeated patterns into an OS/dashboard/front-end later
- use existing tools as infrastructure before building custom SaaS
- keep human approvals for brand voice, customer-facing messages, posting, and sensitive workflows

For SMB automation products, avoid framing as replacing humans unless the user explicitly wants that. Prefer augmentation language:
- captures work that falls through cracks
- owner time-back
- operational clarity
- content consistency
- staff augmentation
- human escalation
- ROI visibility

## Papi Business OS / Systems-First Planning Pattern

When Karan is exploring Papi AI Consulting strategy, especially “Business OS,” custom tools, content automation, or SMB operations offers:

1. **Start from current project memory** — read Obsidian project status, Papi pages, relevant client pages (especially JMD), recent logs, and any prior research artifacts before ideating.
2. **Use parallel sub-agents** for broad exploration:
   - one sub-agent for current/local client files and domain context
   - one sub-agent for external market/tool research
   - one sub-agent for workflow/service packaging if needed
3. **Synthesize into a living wiki artifact** when the output is strategic, not just a one-off answer. Preferred path for Papi strategy: `~/obsidian-vault/hermes-brain/wiki/consultancy/business-plan.md`.
4. **Systems-first, SaaS-later:** recommend building workflows, schemas, SOPs, automations, reports, and lightweight tools first. Only recommend a custom portal/SaaS when repeated client patterns prove stable requirements.
5. **Include technical detail**: tool stack, connection methods (API/MCP/CSV/webhook/OAuth), agent roles (Hermes/Claude Code/Codex), data model, approval gates, risks, and client-specific constraints such as Comcash/Trumpia for JMD.
6. **Log and index**: update the daily log and Obsidian index after creating/updating living docs.

## Workflow

### 1. Load prerequisite skills
- `research-workflow` for source gathering and synthesis.
- `local-web-preview` if building an HTML report to preview.
- `daily-log` before ending, because this is usually a meaningful multi-step task.

### 2. Frame the research scope
Write or internally define:
- target customer / ICP
- product promise
- capabilities needed
- tool categories
- competitor categories
- business economics questions
- risks/compliance questions
- desired final artifact

For Papi AI Consulting, include practical business angles, not just feature lists.

### 3. Use parallel sub-agents
Spawn at least two sub-agents when the research is broad:

**Sub-agent A: Tool/platform deep dive**
Ask for:
- individual tools/vendors
- capabilities
- integrations
- pricing/cost notes
- compliance notes
- build-vs-buy recommendations
- source URLs

**Sub-agent B: Competitor + economics analysis**
Ask for:
- direct competitors
- adjacent/hybrid competitors
- positioning and pricing
- target industries
- revenue model
- COGS and gross margin estimates
- implementation effort
- risks
- go-to-market recommendations
- source URLs

Add task-specific context: Karan/Papi AI, local SMBs, productized consulting offer, safety-net positioning.

### 4. Synthesize into an opinionated strategy
Do not simply concatenate sub-agent reports. Produce:
- executive recommendation
- best first ICP / beachhead
- package/pricing recommendation
- tool stack recommendation
- competitive differentiation
- business economics
- go-to-market plan
- compliance/risk checklist
- roadmap
- source links

Make the report decision-oriented: “recommended default,” “avoid,” “use later,” “first ICP,” “next step.”

### 5. Build a polished HTML report
Create a single self-contained `.html` file under a project directory such as:
`~/projects/<topic>-research/<topic>-business-brief.html`

Good report structure:
- hero section with date/context
- sticky/anchor navigation or top nav pills
- executive summary
- market/pricing metrics
- best-fit customer segments table
- tools/platform comparison table
- competitor analysis table
- business economics section
- go-to-market section
- risks/compliance section
- roadmap
- source links

Design guidance:
- executive dark-mode style works well for dense research
- use cards, badges, and tables for scanning
- make it mobile tolerant with responsive grids and horizontal table scroll
- include print-friendly styles if useful
- for client-facing reports, do not let the visuals hide generic wording: speak to the named decision-makers, start with what is working, then list exact fixes and approvals, and tie every recommendation to a practical business outcome

### 6. Verify the artifact
Before reporting done:
- check file exists and key sections are present
- start a local HTTP server on an available port
- preview with browser tools
- use browser vision to catch obvious layout problems
- if port is busy, retry a different port instead of stopping

Example verification commands:
```bash
python3 - <<'PY'
from pathlib import Path
p=Path('/path/to/report.html')
text=p.read_text()
for s in ['Executive summary','Competitive analysis','Business economics','Source links']:
    print(s, 'OK' if s in text else 'MISSING')
print(p.stat().st_size)
PY
```

```bash
python3 -m http.server 8766 --directory /path/to/report-dir
```

### 7. Log meaningful work
Use `daily-log` to record:
- what was researched
- sub-agent split
- report path
- key decision/recommendation
- next step

## Pitfalls
- Do not over-index on cheap SaaS pricing; Karan’s opportunity is often done-for-you implementation and outcomes.
- Do not skip compliance sections for phone, healthcare, legal, SMS, or data retention workflows.
- Do not trust a local HTML file without browser preview; visual polish matters.
- Do not present raw research dumps; synthesize into a practical recommendation.
- If one local server port is busy, use another port and verify again.

## Output Style
Final response should be concise and include:
- path or media attachment to the HTML report
- one-line confirmation of verification
- 3–6 bullets summarizing what is inside
- the main strategic recommendation
