# JMD Content Engine — Video Automation Research Notes

Research captured from the 2026-05-27 deep dive into automating JMD Menswear short-form social videos.

## Client constraints

- Lucky/Danny shoot real phone footage in the store.
- Karan clips, brands, reviews, and posts/schedules after approval.
- No AI-generated people, garments, storefronts, backgrounds, or fake owner/customer voice.
- Lucky/Karan approval required before anything public goes live.
- Real inventory and pricing claims can become stale; approval needs inventory/offer checks.

## Recommended architecture

Near-term workflow:

1. Phone footage from Lucky/Danny.
2. Intake via Google Drive, Dropbox, Telegram, or Frame.io later.
3. Tracker in Airtable, Google Sheet, or similar with status, platform, caption, approval, consent, inventory/offer checks, posted URL.
4. Processing with FFmpeg for normalization/proxies/thumbnails and Whisper/OpenAI transcription for captions.
5. Clip suggestions via OpusClip/`opus-skills` or transcript/rule-based heuristics.
6. Branded edit via Hyperframes/Remotion for deterministic lower thirds, captions, price/product callouts, end cards, and platform variants.
7. Optional CapCut CLI bridge if Karan wants agent-generated drafts that can be inspected/polished in CapCut.
8. Lucky/Karan approval gate.
9. Manual/native posting first; API publishing later via Ayrshare or direct Meta/TikTok APIs only after the operating model is stable.

Safety invariant: nothing posts until `Status = Approved`, `Approver = Lucky/Karan`, release/music/inventory checks pass, and platform-specific asset/caption exist.

## Tool verdicts

### OpusClip / `opus-pro/opus-skills`

Best role: candidate short discovery from raw phone footage.

- Agent skill/CLI around OpusClip API.
- Handles submit/upload, clip generation, previews, collections, server-side edits, captions, social copy, publish/schedule.
- Active but young/beta; API requires OpusClip Pro/Enterprise key.
- Use for suggestions and previews; do not enable auto-posting in JMD v1.
- Source: https://github.com/opus-pro/opus-skills

### Hyperframes / Remotion

Best role: branded deterministic rendering.

- Hyperframes: HTML/CSS/JS-to-video framework using browser rendering + FFmpeg; agent-friendly for motion graphics.
- Remotion: mature React/video rendering engine with strong developer control.
- Use for lower thirds, captions, callouts, end cards, platform crops, brand consistency.
- Needs clip source/selection layer; not itself a semantic clip finder.
- Sources: https://github.com/heygen-com/hyperframes and https://www.remotion.dev/docs/cli/

### CapCut CLI / `renezander030/capcut-cli`

Best role: human-review bridge into CapCut.

- Reverse-engineered CapCut/JianYing draft JSON automation.
- Can create/edit draft cuts, subtitles, text, keyframes, masks, filters, templates, SRT/ASS imports.
- Good if Karan wants to open generated drafts in CapCut for manual polish.
- Risk: CapCut schema/export automation can break; keep backups and avoid making it the only render path.
- Source: https://github.com/renezander030/capcut-cli

### HeyGen CLI

Best role: not core for JMD.

- Official CLI for HeyGen AI videos, avatars, voices, lipsync, translation, assets, webhooks.
- Technically strong but centered on AI-generated/avatar workflows.
- Avoid as the JMD core content engine because it conflicts with real-footage-only direction.
- Source: https://github.com/heygen-com/heygen-cli

### Creatomate / Shotstack

Best role: managed API rendering alternative.

- Creatomate is strong for template-driven marketing/social videos with REST API and editor; faster MVP if avoiding custom render infra.
- Shotstack is a mature cloud video editing API for scalable rendering, overlays, templates, SDKs.
- Consider if Hyperframes/Remotion ops burden becomes too high.
- Sources: https://creatomate.com/docs/api/quick-start/introduction and https://shotstack.io/product/video-editing-api/

### Ayrshare / Meta / TikTok APIs

Publishing recommendation:

- Start manual/native for reliability and platform-native features.
- Ayrshare is the easiest approval-gated unified social publishing API if budget allows.
- Direct Meta/TikTok APIs require app setup, scopes, review, and do not always mirror native app features/trending audio.
- Sources: https://docs.ayrshare.com/rest-api/endpoints/post, https://developers.facebook.com/docs/instagram-platform/content-publishing/, https://developers.tiktok.com/doc/content-posting-api-reference-direct-post

## Phased rollout

### Phase 0 — guardrails

- Folder taxonomy: raw uploads, selected clips, edits in progress, review, approved, posted, archive.
- Metadata: shoot date, shooter, product/inventory, release status, caption idea, platform, approval, posted URL.
- Rules: no AI-generated visuals, approval required, no unlicensed music, no customer footage without consent, verify inventory/offer claims.

### Phase 1 — manual but organized

- Drive/Dropbox + tracker + CapCut/Canva/Descript optional + manual/native posting.
- Produce 10–20 clips and identify repeatable formats before heavy automation.

### Phase 2 — deterministic automation

- n8n/Zapier watches uploads.
- FFmpeg creates proxies/thumbnails/normalized versions.
- Whisper generates transcript/captions.
- Hyperframes/Remotion renders branded versions.
- Approval link/file routed to Lucky/Karan.

### Phase 3 — approval-gated publishing

- Ayrshare or direct Meta/TikTok APIs after workflow stability.
- Publishing action must be explicit and approval-gated.

### Phase 4 — scale loop

- Analytics dashboard, winning hook library, seasonal templates, inventory-linked video templates, paid ad cutdowns.

## Content formats to test first

- Fit check / outfit-of-the-day.
- New arrival closeups.
- “When it’s gone, it’s gone” inventory spotlight.
- Prom/wedding/quinceañera rental education.
- Lucky talking-to-camera trust clips.
- Before/after styling and accessory detail shots.

## Pitfalls

- Do not over-automate publishing before the creative workflow is proven.
- Do not let clipping tools make final editorial decisions without review.
- Do not use generated-avatar/video tools for JMD core content.
- Track consent and commercial music usage explicitly.
- Keep raw footage and final exports archived for traceability.
