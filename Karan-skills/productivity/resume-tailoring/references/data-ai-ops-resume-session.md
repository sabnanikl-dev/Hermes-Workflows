# Data / AI Operations Resume Tailoring Session Notes

Session context: Karan asked Hermes to tailor a Google Docs resume copy for a Cox Analytics Engineer role, improve formatting using Resume Worded data engineer guidance, add consulting experience, then create a one-page copy for an Anthropic Partner Business Systems & AI Operations Lead role.

## Useful role patterns

### Cox Analytics Engineer
Strong alignment terms:
- SQL, Snowflake, Power BI, Tableau
- data assets, data modeling, BI infrastructure
- data dictionaries, query repositories, metric documentation
- data quality, anomaly detection, diagnostic dashboards
- GitHub, pull requests, code review, CI/CD concepts
- AI-assisted workflows: Claude Code, Codex, Copilot-style tools

Good truthful framing for Karan:
- Analytics-focused sales strategy professional with 8+ years of experience.
- Builds SQL/Snowflake/Power BI/Tableau/Anaplan/Excel assets for revenue planning, quota strategy, compensation analytics, performance reporting, and executive decision support.
- Uses GitHub and AI-assisted workflows in consulting/project work.
- If direct dbt production experience is not established, say “dbt-style modular modeling concepts” or “SQL transformation layers,” not “dbt owner.”

### Anthropic Partner Business Systems & AI Operations Lead
Strong alignment terms:
- revenue systems, partner/business systems, AI operations
- agentic workflows, LLM-driven triage/drafting/QA
- data quality standards, process instrumentation, cycle times, queue depth, SLA adherence
- governance, validation rules, schema/program-rule translation
- automation tools: n8n/Zapier/Workato/Make equivalents; for Karan use Copilot Studio, Power Automate, SharePoint connectors, reusable notebooks
- SQL fluency and data quality checks

Good truthful framing for Karan:
- Do not claim Salesforce/PRM ownership unless supplied later.
- Position adjacent strengths: compensation-plan mechanics, quota rules, data/process troubleshooting, systematized analytics, executive reporting, QA standards, AI-assisted operating workflows.
- Phrase gap-aware fit: “translates program rules into data structures/workflows” rather than “owns Salesforce schema.”

## Resume Worded-style patterns that worked

- Use **action + built asset/process + tools/data + business impact**.
- Quantify naturally: $1.5B book of business, 15 sales teams, 26+ components, 90–110% attainment target, 18% margin improvement, 60+ team members, 2,000+ customers.
- Prefer impact and deliverables over responsibilities.
- Keep education brief for senior roles.
- ATS-safe docs: simple fonts, real text, section headers, bullets, PDF-ready.

## Formatting lessons from user feedback

Karan disliked a formatting pass that looked too keyword-bolded and template-like. Future resume work should:
- avoid bolding every tool keyword;
- use selective emphasis only for name, section headers, company/title, a few role-critical concepts, and major metrics;
- prefer Calibri/Aptos/Arial with compact margins;
- use restrained section dividers;
- keep one-page versions dense but readable;
- avoid a bloated “Core Skills” block if it visually dominates the page — “Technical Skills” or “Relevant Systems & Tools” is cleaner.

## Google Docs API technique

When creating a tailored copy:
1. Use Drive `files.copy` from the master/source document.
2. Replace document body content with `documents.batchUpdate`: delete old range then insert tailored text.
3. Apply document style: margins, global font, font size, line spacing.
4. Apply paragraph/text style ranges for name, contact, target title, section headers, company/title lines, bullets, and a small set of key metrics.
5. Re-read the document body and assert required role keywords/sections are present.
6. If user requests access, create a permission and verify by listing permissions.

## Good section structures

### Clean full resume
- Name/contact
- Target title
- Summary
- Technical Skills
- Professional Experience
- Education
- Interests only if desired/space permits

### One-page tailored resume
- Name/contact
- Role thesis line
- Target role line
- Summary
- Relevant Systems & Tools
- Professional Experience
- Education

Keep older roles to 2–3 bullets or remove low-relevance detail to preserve one page.
