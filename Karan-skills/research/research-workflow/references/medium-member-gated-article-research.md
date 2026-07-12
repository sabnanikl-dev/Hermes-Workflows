# Medium Member-Gated Article Research

Use when a user asks to read/summarize a Medium article and the public page shows a member-only/login gate.

## What worked in this session

For a Medium member-only article, the normal `web_extract` and browser snapshot retrieved only the public preview and regwall. Useful public metadata still included:
- title, author, date, read time
- public intro paragraphs
- table of contents/headings visible before the gate
- diagram/image URLs
- Medium RSS feed preview
- search-result snippets from indexed sections
- comments/responses that can reveal reader takeaways

## Recommended sequence

1. Try clean extraction first:
   - `web_extract([medium_url])`
   - browser render + `document.body.innerText` if needed
2. Check public alternate surfaces:
   - author RSS feed: `https://medium.com/feed/@username` or `https://<subdomain>.medium.com/feed`
   - search exact title and article id
   - search unique visible headings, e.g. `"Token Efficiency Ranking" "Ontology" "Skills"`
   - search snippets around framework/tool names referenced by the article
3. Check archival/mirror options:
   - Wayback CDX for the exact URL
   - readable proxy/extraction services only if they return publicly available content and do not require bypassing auth
4. Extract supporting sources from visible clues:
   - if the article references a library/framework, fetch that source directly
   - use diagrams/images when visible to reconstruct the article’s conceptual model
5. Report access honestly:
   - state that the full article is member-only/login-gated
   - list workarounds attempted
   - separate “confirmed from article preview” from “inferred from supporting sources”

## Pitfalls

- Do not claim to have read the full article if only the preview was accessible.
- Do not treat RSS excerpts or search snippets as full article text.
- Avoid persistent negative claims like “Medium cannot be read”; this is article/account/access dependent.
- If the user can provide a logged-in account/session or text export, continue from that instead of overworking public snippets.
