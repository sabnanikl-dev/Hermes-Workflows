# JMD client backend explainer decks

Use this when creating or revising a client-facing deck/report for Lucky/Danny explaining the JMD website backend, Sanity, n8n, Google Drive, or showroom-photo automation.

## Deck shape

- Keep owner-facing backend explainers concise by default: aim for roughly **6–8 slides**, not a long 12–15 slide training deck, unless Karan explicitly asks for depth.
- Lead with simple owner language: Drive = normal drop-off folder, n8n = backstage assistant/checklist, Sanity = website backend/control room, frontend = polished public website.
- Avoid tutorial-ish phrasing and excessive technical narration. Lucky should understand the value without feeling like he is being trained to operate n8n.
- Separate owner choices clearly: automation is convenience, not lock-in. If they stop paying for/maintaining automation, they can still manage content manually in Sanity.

## Visual requirements

- Use the actual JMD website/Sanity public feed photos when the deck is meant to explain the current website. Do **not** substitute older merchandise photos from local asset folders if the user asks for one-to-one/current-site visuals.
- Current public feed source pattern: `site/assets/js/on-the-floor.data.js` contains the Sanity CDN URLs used by the static website feed. Extract/download a small set from that file and embed optimized deck copies or data URIs.
- Keep JMD brand styling consistent: navy `#010092`, midnight `#000846`, gold `#C8A24A`, cotton `#F7F7F4`, premium menswear cards, mono labels, generous spacing.
- QA every important slide thumbnail for clipping/legibility. In this session, Quick Look thumbnails (`qlmanage -t -s 1400`) caught clipped subtitle/footer and cut-off timing cards that normal file existence checks would miss.

## Timing/counts explanation to include

When explaining the n8n workflow timing, include these concepts in plain English and verify current values before client-facing claims:

- **Sync cadence:** photos are picked up on the next scheduled n8n reconciliation, not instantly. Verified local export in this session showed every **6 hours**.
- **Current public feed count:** state the count from `site/assets/js/on-the-floor.data.js` when relevant; it was **29** in this session.
- **Website cap / live window:** newest-N published photos, currently described as **50 max website photos** when config confirms `LIVE_LIMIT=50`.
- **Age policy:** older photos can rotate out after the configured age window; in this session config showed **90 days**.
- **Minimum kept live:** newest **3** are protected so the section does not go empty when age policy applies.
- **Archive behavior:** removed or aged-out photos are hidden from the public feed by archive status, **not deleted** from Drive or hard-deleted from Sanity.
- **Safety threshold:** too many archive candidates in one run should fail closed; in this session config showed **40 per run**.

## Client-safe wording

Good owner-safe wording:

> Photos are picked up by the backend on the next scheduled sync. Once the website feed is refreshed and published, they appear on the site. The site is capped at the newest approved showroom photos, and older or removed photos are archived from the public feed rather than deleted.

Avoid:

- “Instant upload to the website.”
- “Direct Google Drive to frontend publishing.”
- “Live inventory,” “stock count,” “availability,” “checkout,” or price/size implications.
- Raw Drive IDs, private folder names, credential details, or n8n internals in owner-facing slides.
