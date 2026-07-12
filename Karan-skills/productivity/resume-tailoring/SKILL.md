---
name: resume-tailoring
description: Tailor resumes for specific job descriptions, especially one-page executive/ATS versions in Google Docs or polished one-page HTML, using honest positioning, quantified impact bullets, and clean human formatting.
version: 1.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [resume, careers, job-applications, google-docs, ats, formatting]
---

# Resume Tailoring

Use this skill when the user asks to tailor, rewrite, format, copy, or optimize a resume for a job description. It also covers resume-backed job-application execution, especially batching leads, filling applications, and holding at final submit for approval. It covers role targeting, ATS alignment, professional formatting, Google Docs copy workflows, and user-specific preferences learned from resume/job-application sessions.

## Job application execution workflow

Use this when Karan asks to apply to jobs using an existing resume, including bulk job-lead sheets.

1. **Respect the user's tailoring choice**
   - If Karan says to skip tailoring, do not create per-role resume variants or cover letters unless a portal requires one.
   - Use the provided resume as-is and focus on application execution.

2. **Build and track the queue**
   - Extract all saved leads, including hidden hyperlinks from Sheets cells when needed.
   - Deduplicate by apply URL first, then company + role.
   - Keep a local status tracker with row/company/role/status/reason/application URL/verification so work can resume after approvals or browser restarts.
   - Mark expired/closed/not-available leads explicitly; do not waste approval cycles on dead posts.

3. **Walk each viable application to final submit**
   - Fill only source-backed facts from the resume or user-provided defaults.
   - Do not answer legal/work-authorization, EEO, disability, veteran, age, salary, start-date, portal-account/password, or SMS opt-in questions by guessing. Stop and collect reusable defaults.
   - Upload the resume and verify the filename/selected file appears before treating the draft as ready.
   - Stop before final submission and ask for explicit approval. The approval prompt should be compact and include exactly the decision-relevant lines Karan requested: brief job title, brief job description, one line for pay, one line for fit.

4. **Submit only after approval, then verify**
   - After approval, click submit and wait for a confirmation page/message.
   - Report the exact confirmation text, e.g. “Your response has been recorded” or “Your application has been submitted successfully.”
   - Update the local tracker with submitted_at and verification text.

5. **Common portal tactics**
   - For Google Forms file-upload questions, the signed-in Google account may be recorded; warn Karan before submit if it is not Amanda's account.
   - Playwright uploads may be restricted to allowed roots. Copy the resume into the Playwright output/upload directory, then upload from that allowed path.
   - Aggregator pages may show an active description but route to expired posts; prefer employer-hosted/direct apply pages when search can find them.
   - SuccessFactors/Workday/Phenom-style portals often require account creation, multi-step review pages, legal attestations, EEO/disability/veteran questions, salary/start-date answers, and custom widgets. Collect a reusable default-answer packet once instead of blocking at every portal, but never guess these answers.
   - Portal password rules can block otherwise-complete applications. Before investing in a long SuccessFactors-style form, check visible constraints (for example, 8–18 characters) against the user-provided password; if it fails, mark the role blocked and ask for a compliant replacement rather than trying to improvise credentials.
   - If the user provides a portal password and asks to save it, keep it in a separate restricted-permission file (`chmod 600`) in the project folder. Do not include credentials in status JSON, summaries, approval prompts, or compaction handoffs.
   - Lever and similar forms may show hCaptcha only after the form is filled or when Submit is reached. Treat a visible captcha as a manual checkpoint: fill to final-submit, warn Karan in the approval prompt, and do not claim submission until the captcha and confirmation page are actually completed.
   - Greenhouse may allow the first submit click, then send an 8-character email security code as the final human-verification gate. Enter codes with exact case, verify each one-character input, and stop retrying if the page returns `Incorrect security code` / `Invalid security code`; request a fresh/newest code or have the applicant submit manually from their email/browser session. If no resend path is visible and the user still wants to proceed, a clean reload/refill of the same approved Greenhouse role can clear a wedged code gate and submit successfully; verify `/confirmation` and “Your application has been received” before marking submitted.
   - Paylocity applications may require full address line 1, city, county, state, and zip in Step 1. Never fake a street address from resume city/zip context; block and ask for the applicant’s full address before continuing. Paylocity resume parsing may auto-create work-history/education entries whose nested address fields become required; if the parsed entries are incomplete and not needed, delete the auto-created Work History/Education blocks rather than fabricating employer/school addresses.
   - Paylocity can require references mid-flow even if the initial step validates. If Step 3 asks for references, block and ask for two references with name, phone, Personal/Work type, and optional email; do not invent references. If the user provides real references but omits Personal/Work type, save the PII to a local project artifact for future use and leave the type blank when optional; if required, ask for/confirm the type rather than guessing.
   - Paylocity final review may require an acknowledgement that the application facts are true and complete. Treat checking that acknowledgement plus clicking Submit as the approval-gated final submit; stop and ask before checking it.
   - Paylocity custom select widgets can display a selected value while the hidden input remains empty and `:invalid` still flags it. Verify both visible wrapper text and `:invalid`; pressing Enter after typing the option may satisfy the hidden input, but avoid DOM hacks except as a diagnostic, and re-check before moving forward.
   - Greenhouse React-select dropdowns must be selected from the option list; typing visible text alone can leave hidden required inputs invalid. Inspect `.select__option` labels when a value fails (for example `She / Her` vs `She/her`) and re-check `:invalid` before approval.
   - Stretch-role custom questions should be answered transparently from adjacent experience, not inflated. If Amanda lacks direct cybersecurity/SKO/tradeshow experience, say that plainly and pivot to relevant event operations, vendor, budget, client, and onsite execution experience.
   - Goodwin Recruiting/Salesforce Sites forms may have a two-step route: employer job page → `goodwinrecruiting.my.salesforce-sites.com/jobboard/Jobregister?...`. Use the direct Salesforce form, fill email/name/phone/zip/country, choose the closest remote-availability option, upload the resume, verify the `C:\\fakepath\\...pdf` file value, then stop at the Salesforce `Submit` input for approval. After approval, the click may time out while navigation continues; wait and verify the thank-you page/body (e.g. “We have received your job application”) before reporting success.
   - Greenhouse job links can go stale while the same role is reposted under a new job ID on the company board. If a direct Greenhouse URL redirects to the board with `error=true`, search the board text/links for the same company + role, navigate to the new job ID, and continue rather than marking expired immediately.
   - Greenhouse/React-select comboboxes may not retain typed text unless an actual option is selected. For fields like Country, Location, source, travel, work authorization, sponsorship, EEO, and pronouns: click the input, type the option text, wait for `.select__option`, click the matching option, then verify `:invalid` is empty. Pronoun options may be formatted as `She / Her` rather than `She/her`.
   - When a queue role blocks on reusable defaults, CAPTCHA, account creation, ZipRecruiter alert/account consent, or missing source facts, do not stop the whole batch unless the user asked to focus there. Record a precise status/reason in the local ledger and continue triaging later leads. See `references/bulk-job-application-blocker-triage.md` for status labels and default-packet gaps.

See `references/bulk-job-application-session.md` for a compact example of the queue/status pattern and approval copy shape. See `references/job-application-final-submit-workflow.md` for default-answer packets, sensitive-data handling, and portal quirks.

## Core workflow

1. **Gather the source material**
   - Read the current resume source/copy before editing.
   - If Karan asks for a new role-tailored resume and does not provide a source, use the master resume Google Doc as the source of truth: `https://docs.google.com/document/d/1n1tD6WvbPSth4KdXqpsugKNUaQBblX0gR2e69b-mw9k/edit?tab=t.0`.
   - For Amanda job-application work, her current resume source may be a local PDF under `/Users/creator/projects/Resume/Amanda Job Search/`; verify the exact path provided by the user before applying.
   - Fetch the job description from the most authoritative available source. If LinkedIn blocks extraction, search the job ID/title and use the employer-hosted posting or a reputable mirror; if still blocked, ask for pasted job text.
   - Recall relevant project/work context only when it materially improves fit; avoid inventing experience.


2. **Identify the role thesis**
   - Extract the job’s top 5–8 requirements and implied hiring narrative: title, mission, responsibilities, tools/systems, required experience, repeated keywords, and hidden success criteria.
   - Decide the honest positioning: e.g. Analytics Engineer, Revenue Systems / AI Operations, Business Systems Lead.
   - Note gaps explicitly to yourself and avoid overclaiming them. Frame adjacent experience truthfully.

3. **Tailor content with evidence**
   - Prefer bullets in the shape: **Action verb + asset/process built + tools/data used + quantified or leadership impact**.
   - Lead with the most job-relevant work, not chronological completeness.
   - Use real metrics already known or provided: `$1.5B`, `15 sales teams`, `26+ quota and compensation components`, `90-110% attainment`, `18% margin improvement`, `25 coordinators`, `2,000+ customers`, `37 branches`, and similar source-backed metrics.
   - Keep Cox experience dominant for analytics/revenue/data roles. Keep Papi AI, Insight Global, and Innova shorter unless the target role makes them more important.
   - Add consultancy/founder work only when it reinforces the target role. Keep it credible and professional, not inflated.
   - Prefer role-fit wording in the summary, skills, and strongest experience bullets instead of adding a large “Role Match” block. Add such a block only if it does not threaten one-page fit.

4. **Formatting / deliverable pass**
   - Default to a clean, human, executive/ATS format. Avoid “AI resume builder” visual clutter.
   - Use simple company/title/date structure, compact bullets, restrained bolding, and clear section rules.
   - For one-pagers: compress hard. Keep only the highest-signal bullets and remove interests/older detail unless space allows.
   - For local HTML resume drafts, do not overwrite the source file unless asked. Create a separate clearly named file like `karan_sabnani_<company>_<role>_resume.html` or a versioned copy like `*_v2.html`.
   - For HTML deliverables, prefer a polished content-forward Letter page over Canva/visual generators unless the user asks otherwise. Use: header, targeted summary, technical skills, professional experience, education, and optional interests if space allows.
   - Open/render the HTML when possible and visually inspect that it fits one page. Adjust spacing, section count, and bullet length until bottom content is not cut off.
   - Before/after a tailoring pass, run a lightweight keyword audit against the job description and resume text. Use it to identify missing terms, but add them only where truthful and natural.
## Google Docs execution
5. **Google Docs execution**
   - For user-owned source docs, create a copy before major tailoring unless the user explicitly says to edit that copy directly.
   - When using the Google Docs API, replace content, then apply document-level styling: margins, font, line spacing, section headers, bullets, and selective emphasis.
   - Verify after writing by re-reading the document body and checking required sections/keywords are present.
   - If sharing a copied doc, verify permissions by listing permissions after creating them.

6. **Job application execution / final-submit workflow**
   - If Karan explicitly says to skip tailoring, do **not** tailor the resume or add role-specific cover letters. Use the provided resume as-is and keep optional cover-letter fields blank unless required.
   - Triage each saved lead before filling: verify the live application page is still active. Record expired, closed, 404, or redirected/dead roles instead of trying to force an application.
   - Walk viable applications up to the final submit button, then stop for approval. Do not submit job applications without explicit approval for that exact role.
   - Approval prompt format should be compact and decision-ready:
     - `Job title:` company + role
     - `Brief description:` one short sentence on responsibilities
     - `Pay:` official range if available, otherwise sheet/source estimate with caveat
     - `Fit:` rating plus one-line reason/stretch note
   - After approval, submit and verify the confirmation page/message before reporting success. Save lightweight local status when processing a batch so the next turn can resume without re-triaging.
   - For application forms with file upload in Playwright: if upload is denied because the resume is outside allowed roots, copy the resume into the Playwright MCP allowed upload area and upload that copy. For Google Forms file pickers, click the form upload button, click the picker’s Browse button, then call file upload; direct upload before the modal exists will fail.

## HTML resume workflow Karan likes

Use this when Karan asks to apply to saved jobs, especially from a Google Sheet/Drive queue.

- Treat external application submission as approval-gated. Fill applications up to final submit, then stop and ask for explicit approval before clicking Submit/Send.
- If the user says to skip resume tailoring, do not spend time making role-specific resumes. Use the provided resume as-is and focus on application completion.
- Read real hyperlinks from Sheets cells, not just visible link text. Deduplicate leads by application URL first, then company + role.
- Process the queue actively: mark dead/expired links and move on instead of stopping for each expired posting.
- Use only source-backed personal facts from the resume/user. If a form asks for a metric not in the source (e.g. largest annual sales target), answer transparently rather than inventing a number.
- Approval prompt format Karan requested:
  - brief job title
  - brief description of the job
  - one line for pay
  - one line for fit
  - short note of notable filled fields/assumptions, especially blanks, account metadata, and resume upload
- For browser uploads, if Playwright rejects a local path because it is outside allowed roots, copy the file into the Playwright MCP upload/output directory, then upload from that copied path after a real file chooser is open. See `references/job-application-final-submit-workflow.md`.

## HTML resume workflow Karan likes

Use this when Karan asks for an HTML resume, gives a local `.html` resume path, or references the Codex `tailor-resume-html` workflow.

- Treat the master resume as the factual source of truth, and the target job as the alignment target.
- Create or edit a standalone one-page HTML file in the working/project folder; do not mutate the master resume or source draft unless asked.
- Recommended fixed-page CSS pattern:
  - `@page { size: Letter; margin: 0; }`
  - `.page { width: 8.5in; min-height: 11in; }`
  - restrained color accent, clear section rules, no photos, no decorative sidebars, no icons.
- Keep it recruiter-readable and content-forward: strong name/header, compact target headline, concise summary, 2-column skills, role hierarchy, short bullets.
- If the page overflows, remove optional sections first, then shorten less relevant earlier experience, then tighten spacing.
- If Karan wants interests and space allows, use the known interests exactly: `Travel • Film • ATL Sports • Tame Impala • UFC • Music Production/DJ • Health & Fitness • Android OS`.
- The supporting script `scripts/build_resume_html.py` can generate a polished HTML shell from structured JSON; hand-edit output afterward when needed for fit and polish.

## Karan-specific resume preferences

- Karan likes the local one-page HTML workflow from Codex’s `tailor-resume-html` skill; prefer it when he asks for polished role-specific resume files rather than live Google Doc edits.
- Karan disliked formatting that felt too keyword-bolded, noisy, or template-generated. Do **not** bold every tool/keyword.
- Prefer polished, human-readable formats over aggressive ATS keyword blocks.
- Use a clean structure like:
  - Name/contact centered
  - Target title or role thesis
  - Summary
  - Technical Skills / Relevant Systems & Tools
  - Professional Experience
  - Education
- For tailored one-page versions, make it “beautiful but still ATS-safe”: restrained color, compact margins, light section dividers, and selective emphasis only on target-role concepts or metrics.
- Karan values practical AI/operator experience being represented clearly: Claude Code, Codex, Google Antigravity, GitHub workflows, Copilot Studio, Power Automate, SharePoint connectors, reusable notebooks, QA frameworks, and agentic workflows where true.

## Pitfalls

- **Do not overclaim.** If the job asks for Salesforce/PRM/dbt and the resume has adjacent but not direct experience, phrase it as adjacent systems/data-modeling/process work rather than direct ownership.
- **Do not invent source material.** No fake websites, fake addresses, certifications, projects, volunteer work, tools, or ownership claims unless present in the master resume/source material.
- **Do not make the format look auto-generated.** Excessive bolding, dense keyword stuffing, decorative sidebars, icons, and too many sections make the resume worse.
- **Do not bury the job match.** The first half-page should make the hiring thesis obvious.
- **Do not keyword-stuff from the audit.** If the audit finds missing target terms like dbt, CI/CD, semantic layer, vendor tooling, Salesforce, or PRM, distinguish direct experience from adjacent exposure. Use phrases like “dbt-style modular modeling concepts,” “CI/CD concepts,” “semantic-layer-style specs,” or “revenue systems/workflow documentation” when that is the honest fit.
- **Do not let HTML overflow silently.** If using a fixed-height `.page` with `overflow: hidden`, render/inspect when possible; otherwise, reduce content rather than trusting that the full resume is visible.
- **Do not report success until verified.** After Google Docs edits or shares, re-read/verify the doc and permissions. For local HTML copies, verify the new file exists and required target keywords/sections are present.

## References

- `references/data-ai-ops-resume-session.md` — session notes from tailoring Karan’s resume for Cox Analytics Engineer and Anthropic Partner Business Systems & AI Operations Lead, including source-role patterns and formatting lessons.
- `references/job-application-final-submit-workflow.md` — batch job-application workflow: lead triage, final-submit approval format, status tracking, and browser upload quirks.
- `references/bulk-job-application-portal-verification.md` — session notes on Greenhouse email-code gates, React-select dropdowns, Goodwin/Salesforce forms, and verification pitfalls.
- `references/bulk-job-application-paylocity-and-greenhouse-notes.md` — compact portal tactics for Greenhouse code gates/stale IDs, Goodwin/Salesforce confirmation, and Paylocity address/reference/select-widget blockers.
- `references/bulk-job-application-blocker-triage.md` — queue-continuation pattern for classifying blocked applications, collecting reusable defaults, and updating the ledger without stopping at the first blocker.
- `scripts/build_resume_html.py` — helper script ported from Karan’s preferred Codex `tailor-resume-html` workflow for generating one-page HTML resumes from structured JSON.
