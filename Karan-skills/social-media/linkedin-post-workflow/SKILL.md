---
name: linkedin-post-workflow
description: "Use when drafting or publishing Karan's LinkedIn posts."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [linkedin, writing, personal-brand, ai, social-media, publishing]
    related_skills: [writing-humanization-and-voice-editing, treg, media-content-workflows]
---

# Karan's LinkedIn post workflow

## When to Use

Use for Karan's LinkedIn post ideas, series planning, drafts, revisions, accompanying media, approval packages and explicitly authorized publication. Also use when he asks for the next post or a retrospective about AI tools/projects. For profile/resume editing alone, use the voice-editing skill instead.

## Purpose and authority

Turn Karan's actual AI work into approachable posts that teach a novice something useful and demonstrate business judgment to recruiters, operators and potential collaborators. Deliver the post itself, not only a strategy.

This is an editorial workflow, not standing permission to publish. Drafting, liking copy, preparing media and asking to use treg do not authorize publication. Require explicit approval of the immediately preceding bounded caption/media/destination before publishing. Scheduling, tagging people, cross-posting and outreach are separate actions.

## Load the relevant supporting skills

- `writing-humanization-and-voice-editing` for drafting/editing.
- `treg` for LinkedIn account checks, capabilities, uploads, publishing and verification. It owns API mechanics and spending rules; do not duplicate them here.
- `hermes-agent` plus official documentation for Hermes feature claims; primary product sources for competitor comparisons.
- `media-content-workflows` for supplied video/audio. Creative/rendering skills only when making a visual artifact.

For an existing series, read the exact project plan and latest approved draft. Do not bulk-read vaults or treat a planning document as current publication state.

## 1. Find the reader's reason to care

Infer obvious context from the conversation and project artifacts before asking questions. Identify one real workflow/decision, one takeaway a novice can use, what the example demonstrates about Karan, and a defensible opinion with its tradeoff.

Use `templates/post-brief.md` as a lightweight aid, not a mandatory interview. Ask only about material gaps that cannot be retrieved, especially personal motivations and permission to disclose client information.

Position Karan as a business/strategy person who can take AI-assisted work through implementation. Do not imply sole handwritten authorship, model training, senior ML expertise, or ownership of upstream tools.

## 2. Choose a focused angle

Lead with a recognizable experience or problem; explain a tool's purpose before naming its architecture. Use projects as evidence, not a résumé inventory. For Karan’s work-led educational posts, derive the reader’s practical takeaway from work he has actually done. Do not add unrelated hypothetical business examples merely to make the lesson concrete; the post should teach through his demonstrated decisions and implementation. Clearly distinguish a proposed extension from completed work if an extension is requested.

A flexible structure:
1. Concrete opening grounded in actual work.
2. Specific workflow or example.
3. Why Karan chose it, in plain language.
4. Honest limitations/tradeoffs where relevant.
5. An actionable takeaway and clear personal conclusion.

Each post stands alone. Split distinct lessons into a series rather than squeezing every project into one post. Do not promise a cadence or public numbering without Karan choosing that commitment.

Apply a novelty/usefulness gate before proposing a topic. Karan considers basic explanations of skills too common and obvious to justify a standalone post. Do not default to skills primers or substitute another basic agent concept. Prefer a consequential decision, specific discovery, demonstrated result, or honest tradeoff from his work; explain familiar concepts only as needed to support that story. A skills-related story needs a distinctive practical result beyond explaining reusable instructions.

For build/review posts, read the actual multi-agent development and risk-proportional review skills as source material. Explain the useful mechanism—separate builder and evaluator, clear judging criteria, validated feedback and proportionate review—before implementation safeguards. Introduce LLM-as-a-judge in plain language when central; do not let version binding or review infrastructure overwhelm the novice takeaway. Frame Karan's observed model strengths as personal experience, not comparative benchmarks or universal superiority. When illustrating Karan's Claude/Codex workflow, preserve the two separate Codex reviewer lanes and their different jobs: A checks correctness/security/tests; B checks requirements/scope/maintainability. Show parallel review and feedback from both rather than collapsing them into one generic reviewer. Keep this editorial representation distinct from changing operational review-tier policy.

For assistant/tool-selection posts, keep **the ability to shape the system around how Karan works** central. Project context, reusable procedures, checking standards and approval boundaries explain personalization better than a friendly persona. Privacy and control support that benefit; do not let them replace it.

## 3. Write and revise in Karan's voice

- Use first-person, casual-polished language, accessible enthusiasm and concrete opinions.
- Explain unfamiliar terms briefly: a skill is reusable operating instructions; a code merge incorporates a reviewed change.
- Use short paragraphs and occasional bullets with varied sentence lengths. Avoid dramatic one-sentence paragraphs throughout.
- Prefer useful specifics over stack lists, generic AI predictions, inflated autonomy or jargon.
- Default all of Karan’s LinkedIn posts to an Alex Finn X-post-inspired editorial approach, not his YouTube thumbnail aesthetic. Lead with something concrete Karan built, tried, or discovered; express genuine personal enthusiasm or a defensible opinion; explain what it enables in conversational language; then give a useful takeaway a novice can apply. Let the project demonstrate business judgment instead of opening with abstract instruction. Adapt these broad traits in Karan’s own voice, without copying distinctive phrasing or importing Alex’s experiences, hype, revenue claims, absolute privacy claims, or unsupported autonomy claims. This is the standing default unless Karan requests another direction.
- For accompanying media, favor tangible project evidence—a readable, permission-cleared screenshot, result, or short demonstration—over a dense educational flowchart. Let the caption teach the reasoning and the image make the project concrete. Use diagrams when they genuinely clarify the central takeaway, not a secondary implementation detail; visibly label illustrative mockups and never present them as actual screenshots. Do not default to shocked faces, neon YouTube thumbnail treatments, or slogan-only graphics.
- Karan's standing image preferences for this series: default to portrait 4:5 (1080×1350 rendered at 2x) rather than landscape, and when the lesson is about a tool or interface, recreate the familiar desktop UI readers would see on their own computers (a real-looking app window: title bar, sidebar, editor pane, graph view, file list) instead of abstract boxes-and-arrows. When distinguishing related concepts (agent vs. second brain vs. repository), stack them as labeled layers/windows with connector arrows showing what flows between them. Keep the visible illustrative-recreation label on any recreated UI.
- Do not add emoji chains, fancy Unicode fonts, hashtag piles, forced engagement questions or “comment AI” bait by default.
- End in language a novice understands without explanation. Return to the main benefit, not an abstract slogan.
- Preserve what Karan explicitly liked across revisions. Make requested edits locally; do not quietly replace an accepted hook, thesis or conclusion while polishing another section.
- Keep evidence notes, caveats about verification and publication status outside the copy-ready caption.

See `references/editorial-patterns.md` for approved patterns and common failures.

## 4. Ground the claims

Separate personal preference, documented feature, observed execution and measured outcome.

- Inspect actual project evidence. Distinguish proposed, implemented, deployed and in-development work.
- Check current primary sources for product comparisons. Do not describe competitors as chat-only if they have tools, memory and background work. Explain personal fit rather than inventing head-to-head testing or universal superiority.
- Do not invent savings, revenue, engagement, adoption, security guarantees or perfect memory.
- Saving a skill means reusable context, not model retraining. Distinguish AI-assisted development from AI making decisions inside the application.
- For sovereignty/privacy, distinguish agent hosting, data storage/processing, model providers receiving context, account access and action authorization. Self-hosted/open-source does not automatically mean private, secure, compliant or entirely local. Messaging services remain part of the data path.
- Describe approval requirements as an operating policy unless technical enforcement is separately established. Do not imply a foolproof guarantee.

## 5. Select and inspect media

Prefer a real screenshot or short recording of useful work over a fabricated exchange. A request → evidence/result → human decision sequence is often stronger than an architecture diagram.

Inspect supplied media yourself before describing or uploading it. For video, check duration, dimensions, audio streams and frames across the clip; inspect readable full-resolution frames, not only a tiny contact sheet. Inspect/transcribe relevant audio when present. A recording of an agent claiming success is not independent proof of that operation.

Review for client branding/names, private messages, identifiers, navigation/location indicators, notifications, credentials, internal URLs, PR/branch references and synthetic QA content. Surface material exposure before approval. Offer scoped cropping/redaction, preserve the source and verify the derivative. Do not promise comprehensive privacy clearance from sparse sampling.

If a mockup is requested, visibly label it illustrative; never pass it off as a real captured exchange. A rejected mockup is not the selected attachment.

For educational process graphics, make illustrations explain the mechanism rather than decorate a list of cards: show a sample screen for product, connected parts for architecture, inputs/responsibilities/outputs for program design, and cross-layer features for slices. Use plain-language captions so readers need not decipher the diagram's smaller labels. Show orchestration boundaries accurately: when n8n executes integrations, place its read/check/write node groups inside an n8n workflow container rather than showing n8n as a peer stage between external services. Distinguish external storage/services and downstream consumers from the nodes that access them. Check at phone-feed size, and keep details reserved for a later post out of both the graphic and caption. If the graphic is hard to read or understand, reduce its scope to one demonstrated decision with large labels; do not keep shrinking text to fit the whole architecture, safeguards, and development process. Let the caption supply the surrounding detail. Render/no-overflow checks alone do not establish readability. When Karan requests Stop Slop, apply the voice-editing skill's source-based pass to graphic copy as well as the caption; retain useful labels and factual qualifiers rather than mechanically stripping them.

Store final media durably in the project folder rather than only in expiring chat cache. Verify the copy/transformation. For generated diagrams, keep the editable source file (e.g. HTML/SVG) next to the exported image so approval-cycle edits don't rebuild from scratch, export at 2x scale for crisp feed rendering, and verify the saved asset hash-matches the capture. Do not upload media merely to test capability during draft-only work.

## 6. Prepare the exact approval package

Save a plain-text, copy-ready caption, selected media and a separate short review note. Keep the latest candidate clear; preserve earlier versions when useful.

Count characters with a tool against the applicable limit (currently 3,000 for this ordinary-post workflow; recheck if the API/product changes). Ensure saved caption and displayed candidate match, including intended bullets and line breaks. Do not rely on chat Markdown for LinkedIn formatting.

State what caption/media are under review, unresolved disclosure concerns, and whether the result is local draft, native draft, scheduled or published.

For drafting through treg, follow its draft-versus-publish guidance. Do not invoke publication to simulate saving a draft; disclose a local-only fallback honestly.

## 7. Publish only after explicit approval

Load `treg` and follow its current workflow. Verify connected member and intended destination; resolve material audience ambiguity and set visibility explicitly. A requested destination that matches neither the connected member nor any connected page is a hard stop — ask before any write, because a public post is effectively irreversible.

Use only the approved caption/media. Do not add tags, hashtags, claims, a CTA or substantive edits afterward. Routine encoding needed to preserve approved text is allowed; material media changes need review.

For video, finalize upload and verify AVAILABLE before post creation. Preserve the returned post identifier even if the response body is empty. Record create attempts; reconcile lost responses instead of risking duplicate posts.

Read back the exact external target: author/audience, complete caption equality, correct media asset and loaded media. Preserve the canonical live URL. If API readback is forbidden, use public/browser readback per `treg`; missing read permission does not mean publication failed. If verification remains blocked, distinguish creation evidence from the unresolved limitation.

Return a concise confirmation and clickable live link. No new scheduling, comments or monitoring without authorization.

## 8. Closeout and reuse

Keep caption, media provenance, publication IDs/links and verification evidence in project artifacts. Planning/current series state belongs there, not in global memory or this skill. Durable editorial corrections and procedures belong here or in the owning supporting skill.

For the next post, retrieve the series plan and prior approved example, then choose a new useful lesson. Do not repeat the same post with different tool names or invent prior-post performance. Karan OS capture remains explicit/proposal-first; create no filler wiki artifact.

## Completion checks

- [ ] One clear central idea and useful novice takeaway.
- [ ] Grounded work/claims; honest authorship, stage and tradeoffs.
- [ ] Accepted voice and customization thesis preserved where relevant.
- [ ] Clear conclusion; no confusing analogy or generic engagement bait.
- [ ] Media inspected, disclosure issues surfaced, selected asset verified.
- [ ] Exact caption saved, character-counted and consistent with approval.
- [ ] No unapproved upload, paid call, publication or schedule.
- [ ] If published: live caption/author/media verified and link delivered.
