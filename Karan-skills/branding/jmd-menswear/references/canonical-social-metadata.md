# JMD Canonical URL + Social Metadata

Use this when finalizing SEO/social metadata for JMD website repo work.

## Canonical URL decision pattern

For JMD, determine the canonical URL from the live domain's redirect behavior before adding metadata. Use evidence from both apex and `www`, HTTP and HTTPS:

- `https://jmdmenswear.com/` returned `200` on the current public WordPress/HostGator site.
- `http://jmdmenswear.com/` redirected to `https://jmdmenswear.com/`.
- `https://www.jmdmenswear.com/` redirected to `https://jmdmenswear.com/`.
- `http://www.jmdmenswear.com/` redirected to `https://jmdmenswear.com/`.
- Current WordPress headers advertised the apex URL as the shortlink.

Current repo metadata preference: **canonical = HTTPS apex**:

```text
https://jmdmenswear.com/
```

Treat `www` as redirecting to apex unless future live evidence or Karan approval changes this.

## Metadata fields to keep consistent

When issue scope authorizes canonical/social metadata, keep these values identical where appropriate:

- `<link rel="canonical" href="https://jmdmenswear.com/">`
- `<meta property="og:url" content="https://jmdmenswear.com/">`
- JSON-LD `url`: `https://jmdmenswear.com/`
- `robots.txt` sitemap directive: `https://jmdmenswear.com/sitemap.xml`
- `sitemap.xml` `<loc>`: `https://jmdmenswear.com/`

For the social image:

- Use a real JMD design/brand asset only.
- No stock or AI imagery.
- Prefer a 1200×630 generated/cropped JPEG for Open Graph.
- Record source path, dimensions, bytes, SHA-256, approval/source note, and final-public-approval caveat in asset docs/evidence.

## Social preview asset chosen for issue #22

Source authorized by Karan for this implementation pass:

```text
/Users/creator/projects/consultancy/JMD-Menswear/assets/Design/JMD-logo-refresh-middle-menswear.png
```

Generated repo asset:

```text
site/assets/jmd-og-social-preview.jpg
```

Generation shape:

- Crop/resize to `1200×630`.
- JPEG, optimized/progressive, quality around 88.
- Verify visually that the JMD logo remains readable and not meaningfully cropped/distorted.

## Verification checklist

Before PR closeout, verify:

1. Apex/`www` redirect evidence is captured in PR body or evidence docs.
2. Canonical URL, `og:url`, JSON-LD `url`, sitemap, and robots agree.
3. `og:image`, `og:image:secure_url`, and JSON-LD `image` agree.
4. Declared `og:image:width`/`height` match actual image dimensions.
5. JSON-LD parses and contains no `TODO` strings.
6. `sitemap.xml` parses as XML.
7. Local static server returns 200 for `/`, the social image, `robots.txt`, and `sitemap.xml`.
8. Browser console has no errors after loading the local preview.
9. PR body explicitly says no DNS, HostGator, GoDaddy, Vercel, SSL, email, deploy, or live account changes were made.

## Pitfall

Do not treat canonical/social metadata as approval to deploy. Metadata can be prepared in the repo while still carrying the normal JMD approval gates: final public visual approval, no live hosting/account changes, and Karan approval before deployment.