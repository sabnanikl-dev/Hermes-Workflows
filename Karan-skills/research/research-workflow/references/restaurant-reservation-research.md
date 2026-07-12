<!-- Archived source skill consolidated into `research-workflow` by Hermes skill curator. Original directory moved to .archive/curator-umbrella-20260508-195103. -->

---
name: restaurant-reservation-research
description: Research restaurants for a specific date/time/party size, especially when availability and ambiance matter. Uses reservation platforms first, with browser fallbacks for bot-blocked search.
version: 1.0.0
metadata:
  hermes:
    tags: [restaurants, reservations, local, dining, resy, opentable]
    related_skills: [find-nearby]
---

# Restaurant Reservation Research

Use this when the user asks for a restaurant for a specific occasion, date, time, party size, cuisine, or vibe (e.g. birthday dinner, nice ambiance).

## Workflow

1. **Extract constraints**
   - Location/area radius
   - Cuisine
   - Date and target time(s)
   - Party size
   - Occasion/vibe
   - Budget or formality, if stated

2. **Check reservation platforms before generic search**
   - Resy is often browser-accessible and exposes useful results in page text.
   - Example URL pattern:
     `https://resy.com/cities/<city-slug>/search?date=YYYY-MM-DD&seats=N&query=<CuisineOrRestaurant>`
   - After page load, use `browser_console` to extract concise page text:
     `document.body.innerText.slice(0,20000)`
   - For time filtering, Resy may not honor URL time params. Use JS to change the time `<select>`:
     ```js
     (() => {
       const s=[...document.querySelectorAll('select')].find(x=>x.innerText.includes('7:30 PM'));
       s.value=[...s.options].find(o=>o.textContent.trim()==='7:30 PM')?.value;
       s.dispatchEvent(new Event('change',{bubbles:true}));
       return {value:s.value, text:s.options[s.selectedIndex].text};
     })()
     ```
   - Then re-run `document.body.innerText` to capture availability around that time.

3. **Collect direct booking links**
   - Use JS to extract venue links:
     ```js
     [...document.querySelectorAll('a')].map(a=>({text:a.innerText.trim(), href:a.href})).filter(x=>x.text)
     ```
   - Include links with date/seats parameters when possible.

4. **Generic search fallbacks**
   - If `web_search` fails due to Firecrawl credits, use browser navigation/search or direct known platforms.
   - Google and DuckDuckGo may bot-block; avoid wasting time on CAPTCHA pages.
   - Bing may load but can return script-heavy/noisy pages; direct platform URLs are usually better.

5. **OpenTable caveat**
   - Browser navigation to OpenTable may fail with `ERR_HTTP2_PROTOCOL_ERROR`, and terminal `requests` may time out. If this happens, do not rely on OpenTable for verified availability unless another route works.
   - If the OpenTable page renders as an apparently empty page/snapshot, still run `document.body.innerText` in the browser console before giving up. In one ATL large-party search, the snapshot was empty but page text contained usable availability, restaurant names, times, and links.

6. **Resy city slug pitfall**
   - For Atlanta, `resy.com/cities/atlanta/...` can resolve to the wrong city/location state (e.g. Chandler) or no results. Use `https://resy.com/cities/atlanta-ga/search?date=YYYY-MM-DD&seats=N&query=...`.

7. **Large-party deep-cut handling**
   - For parties around 10-20, many deep-cut/classic restaurants are not on Resy/OpenTable or cap online booking. Treat direct site details (phone, event/private dining notes, minimums, walk-in-only notes) as first-class research output alongside verified platform availability.
   - Separate “bookable now” options from “call/inquire” options. For classic/deep-cut picks, direct phone confirmation is often the right next action.

8. **Direct restaurant site caveat**
   - Restaurant reservation widgets (BentoBox/OpenTable embeds, reCAPTCHA) may hang or be hard to verify programmatically. Treat these as “worth calling/checking manually” unless the tool returns a confirmed slot.

## Ranking guidance

For occasion dining, do not rank only by availability. Prioritize:
1. Fits vibe/occasion (ambiance, birthday-worthy, upscale/fun)
2. Verified availability for the requested party/time
3. Location convenience
4. Reviews/ratings and price/formality
5. Backup options with nearby times

If the user pushes back from cuisine/availability toward **pure vibe**, change course immediately:
- Broaden beyond the original cuisine and search by vibe terms: `pink`, `girly`, `sexy`, `floral`, `disco`, `rooftop`, `cocktail lounge`, `birthday`, `hot girl night out`, `romantic`, `photo-friendly`.
- Use reservation platforms for availability, but use official restaurant pages/Instagram-style gallery text to validate the actual look/feel.
- For vibe-first birthdays, explicitly rank “vibe fit” and “food quality” separately; some top vibe picks are drinks/photo-first rather than dinner-first.
- For group sizes over 6, check whether the venue requires premium tables, minimum spend, or private dining inquiry even if it appears searchable elsewhere.
- Example ATL lesson: The Garden Room is a strong pink/floral/girly birthday vibe, but parties over 6 require Premium Tables/private dining inquiry rather than standard booking; present it as best vibe but with booking friction.

Clearly separate:
- **Verified availability** from reservation platform text
- **Likely good fit but unverified** direct-site/manual-call options
- **Skip/backup** options that are available but wrong vibe

## Response format

Keep it decision-oriented:
- “My pick” with why and booking link
- 2–3 strong backups
- Note any unavailable ideal options
- Mention verification limitations only when relevant
