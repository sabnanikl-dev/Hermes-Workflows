# Vendor Image Uploads to Sanity

Use this when Issue/work asks to populate Femme Events vendor images in Sanity without committing third-party media to the repo.

## Durable Pattern

1. Query published vendors from Sanity first:
   - `_type == "vendor" && published != false`
   - collect `_id`, `name`, `websiteUrl`, `instagramHandle`, and existing `image.asset._ref`.
2. Source images from official vendor-controlled surfaces only:
   - preferred: vendor website logo/header/favicon/brand image
   - acceptable fallback: official site portfolio/team image when no clean logo exists
   - Instagram is acceptable if needed, but official websites are usually easier to scrape and verify.
3. Do not save sourced/vendor media in the repo.
   - use `/tmp/femme-vendor-cms-assets` or another temp directory
   - remove any temporary scripts/files created inside the repo before closeout.
4. Normalize every upload candidate to a square avatar before upload:
   - 800x800 PNG works well for Sanity + circular `object-cover` overlays
   - logos: place on a neutral brand-safe background (`#f7edf0` worked well), or dark background for white-only marks
   - photos: center-crop to 800x800
5. Create a contact sheet and visually QA before uploading.
   - look for blank marks, white-on-white logos, unreadable tiny logos, wrong partner/client logos, or bad crops
   - iterate until the sheet is acceptable.
6. Upload via `@sanity/client` and patch each vendor:
   - `client.assets.upload('image', stream, {filename, contentType: 'image/png', title})`
   - then set `image` to `{_type:'image', asset:{_type:'reference', _ref: asset._id}, hotspot:{x:.5,y:.5,width:1,height:1}, crop:{top:0,bottom:0,left:0,right:0}}`
7. Verify Sanity state, not just upload output:
   - every published vendor has `image.asset._ref` and `image.asset->url`
   - asset refs include expected dimensions, e.g. `-800x800-`
   - `HEAD` each Sanity CDN URL and require no failures.
8. Verify frontend rendering if scope requires live-site acceptance:
   - load local or deployed site with Sanity env configured
   - click each vendor overlay
   - confirm the circular avatar renders an `<img>` from `cdn.sanity.io`, not initials.

## Sanity Auth Notes

If no write token is in env, the Sanity CLI may have a local auth token at:

`~/.config/sanity/config.json` → `authToken`

Use it as a fallback for local scripts, but never print or store the token in skill docs, repo files, logs, or final replies.

## Asset Upload Quirk

Do not pass a `source` object to `client.assets.upload()` unless you also have a valid Sanity `sourceId`. Passing only `source.name` / `source.url` can fail with:

`Bad Request - Validation failed ... "sourceId" is required`

For this workflow, omit `source` and keep source URLs in a temporary manifest/contact-sheet record only.

## ImageMagick Commands

Example logo normalization:

```bash
magick input \
  -auto-orient \
  -background none -alpha on -trim +repage \
  -resize '680x680>' \
  -background '#f7edf0' -gravity center -extent 800x800 \
  -alpha remove -alpha off \
  output.png
```

Example photo normalization:

```bash
magick input \
  -auto-orient \
  -resize '800x800^' \
  -gravity center -extent 800x800 \
  output.png
```

## Closeout Evidence

Report:

- count of published vendors
- count uploaded/patched
- count missing image refs after verification
- CDN HEAD failures, if any
- whether local/live overlay rendering was verified
- explicitly state that no vendor image files were saved to the repo
