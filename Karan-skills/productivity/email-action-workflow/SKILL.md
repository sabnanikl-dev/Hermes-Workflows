---
name: email-action-workflow
description: Workflow for taking action on emails referenced by the user — especially from cronjob reports, forwards, or summaries. Prevents the common failure mode of drafting replies without reading the source.
---

# Email Action Workflow

## When to Use
- User says "take action on that email" referencing a cronjob report, Gmail summary, or forwarded message
- User asks to draft a reply, follow-up, or response to an email they mentioned
- User forwards an email and asks for next steps

## The Pitfall
**Never draft a reply based on summaries, wiki context, or old draft files alone.** The cronjob report only shows sender, subject, and a one-line preview. The actual email body contains the tone, specific ask, forwarded content, and thread history — all of which determine what the draft should say.

## Step-by-Step Process

### 1. Fetch the Actual Email
```python
# Using the google-workspace skill
python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py gmail get <message_id>
```
- The message ID is usually visible in the cronjob report or email summary
- If unknown, search Gmail for the subject/sender to locate it
- For Karan, prefer the `google-workspace` direct API / CLI path over Gmail MCP. If an MCP Gmail search/get call times out or hangs, stop retrying MCP and switch to `google_api.py` or the raw Gmail API with the existing token.

### 2. Read the Full Body — Including Forwarded Content
- Read the entire `body` field from the API response
- **Pay special attention to forwarded messages** — the user's actual ask is often in their preamble, but the content/tone of the forwarded message determines how to draft the reply
- Note: tone (casual "Hey guys" vs. formal), recipients, specific asks, attachments/links mentioned

### 3. Check for Existing Drafts or Context
- Search `~/projects/` or the Obsidian wiki for related context (client info, project status, previous emails)
- If an old draft exists, treat it as reference only — do NOT use it as the basis for the reply unless the source email confirms it's still relevant

### 3.5 Ground Technical/Repo Claims Before Drafting
When an email describes a website, automation, integration, dashboard, or repo-backed system:
- Inspect the relevant repo/docs/live preview before writing client-facing copy.
- Verify whether the capability already exists, is live in non-prod/staging, is fixture-only, or is merely planned.
- Avoid hypothetical language like “we can set up a system” when the system is already built or running in a review environment.
- Describe the real current state plainly: what exists now, what data/source it uses, what is intentionally gated, and what remains managed/manual.
- For client-facing sales/value-prop emails, turn verified technical facts into layperson language without weakening them into vague future promises.

### 4. Draft Based on the Source Email and Current System State
- Match the tone of the original email thread, not a generic business template
- Address the specific ask from the actual email, not assumptions from wiki files
- If it's a follow-up, reference the specific timing ("2 days since the pitch") from the source email
- If the user corrects the draft as under-informed, re-check the repo/source of truth and rewrite from verified state rather than defending or lightly editing the first draft

### 5. Stakeholder-gate outreach (new email, not a reply)

When the email is meant to close approvals for a repo-backed client decision:
1. Inspect the live/repo state first. Translate technical facts into plain language, but do not hide material reliability findings.
2. Prefill decisions the user has already made. Ask the stakeholder only for unresolved, decision-shaped answers; use short reply fields or Yes/No/Not-yet options.
3. Separate the actual site behavior from external systems precisely. Describe a third-party configurator as an external handoff rather than calling it a site redirect or checkout unless the evidence proves that behavior.
4. If an external embed is proposed, make it a separate QA/approval choice. Do not imply that an iframe is safe merely because a URL returns HTTP 200; require browser/mobile verification of the real customer flow.
5. State what will *not* happen without approval (for example: no cart, checkout, price, inventory, deployment, or public publication) so stakeholders can answer confidently.

### 5.5 Fillable stakeholder-intake formatting
When an outreach email asks a stakeholder to supply facts or approvals:
- Make it reply-ready: put a short bracketed response field immediately beneath every question, using `[Answer: ]` or a specific variant such as `[Answer or corrections: ]`.
- For confirmation statements, ask the stakeholder to write `Correct` or replace the text in the same bracketed field.
- Do not use underscore lines, large blank writing areas, or prose telling the recipient where to answer when bracketed fields will do. Karan prefers compact `[Answer: ]` placeholders so the stakeholder can reply inline without reformatting the email.
- Prefill verified details and ask only for confirmation/correction rather than making the stakeholder restate them.
- Keep the approval boundary explicit: stakeholder answers become source material for a draft and do not publish, deploy, or mutate live systems by themselves.
- Reusable starter: `templates/stakeholder-intake-email.txt`.

### 6. Present the Draft to the User Before Sending
- Always get approval before sending emails on the user's behalf
- Include the recipient list and subject line so the user can verify

### 7. Send + Verify When Approved
- Once the user explicitly approves sending, send the email and then verify the sent message from Gmail, not just the CLI return text.
- Verify recipient, subject, `SENT` label when available, and key body strings/links.
- If `gws` can read Gmail but sending fails with insufficient scopes, see `references/gmail-send-gws-scope-fallback.md` for the Python-helper fallback that hides `gws` from `PATH` and uses the Hermes OAuth token directly.
- For client/consultancy emails, preserve the required signature exactly when applicable: `Hermes, Karan’s personal agent`.

## Example: What Went Wrong vs. Right

**Wrong approach:**
- Saw cronjob report: "Fwd: JMD Digital Strategy follow-up"
- Read wiki file `Client JMD Menswear.md` and old draft `jmd-email-draft.txt`
- Drafted a formal pre-meeting pitch follow-up (wrong — meeting already happened)

**Right approach:**
- Fetched the actual email (message ID `19db6d5b06233e58`)
- Read the body: Karan's casual "Hey guys" tone, the pitch was Monday, it's been 2 days
- Drafted a light check-in matching that tone

## Key Rules
1. **Source email > wiki > old drafts** — always in that order
2. **Forwarded emails have two layers** — the user's preamble (what they want you to do) and the forwarded content (the thread you're replying into)
3. **Tone matching matters** — if the thread is casual, don't send a formal business letter
4. **Never assume timing** — the source email tells you when things actually happened