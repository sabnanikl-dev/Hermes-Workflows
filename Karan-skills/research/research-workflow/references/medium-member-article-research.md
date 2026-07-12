# Medium Member-Only Article Research

Use when the user asks to read/summarize a Medium article, especially member-only/gated stories.

## Recommended workflow

1. Try normal extraction first (`web_extract` / Firecrawl / browser snapshot) to determine whether the public preview is enough or a regwall appears.
2. If gated, inspect the public preview for:
   - Title, author, date, reading time
   - Table of contents
   - visible claims/examples
   - reference links and image URLs
3. Try legitimate alternate sources before asking the user for access:
   - Medium RSS feed (`https://medium.com/feed/@username` or `https://subdomain.medium.com/feed`)
   - Search snippets for exact article title / post ID
   - Wayback Machine CDX for archived copies
   - Readability proxies only if they do not require bypassing private/internal network restrictions
4. If the user provides or authorizes an account, use Medium's email login flow when available:
   - Click **Sign in with email** rather than Google OAuth if Google password/2FA would block automation.
   - Enter the authorized email.
   - Use the Google Workspace/Gmail skill/API wrapper to read the Medium login-code email from `noreply@medium.com`.
   - Enter the six-digit code in the browser.
   - Verify the article is unlocked by checking for the full table of contents/body, not just the headline.
5. Once unlocked, extract `document.body.innerText` from the browser console for a complete clean text pass.
6. Read the article's cited links separately. For GitHub/reference links, prefer raw files when useful:
   - Raw README/docs files
   - Raw source files mentioned by the article
   - Raw config/prompt/ontology files mentioned by the article
7. Synthesize with clear source-status labels:
   - What was directly read from the full article
   - What was confirmed from references
   - What is your interpretation/recommendation

## Pitfalls

- Do not report that the full article was read from a public preview. Medium may expose title, intro, and TOC but hide the real body behind a regwall.
- If Google OAuth asks for a password, avoid asking the user for credentials when Medium email-code login is available.
- Medium may show “This member-only story is on us” for a newly created/free account; that is enough to read that article, but not evidence of an active paid subscription.
- Search/readability tools may show snippets from hidden sections; treat snippets as partial evidence until the full browser body is available.

## Output pattern

- Start with access status and verification method.
- Summarize the article thesis and structure.
- Summarize key claims by section.
- Include a short critique: what is useful, what is overstated, and how it applies to the user's systems.
- Summarize linked references separately from the article itself.
