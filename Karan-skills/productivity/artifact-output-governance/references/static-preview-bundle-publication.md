# Static preview bundle publication

Use when uploaded HTML mockups or reports must become a hosted multi-file preview. This is a publication preflight, not proof that a particular network or host has been configured.

## 1. Establish authoritative inputs

Inventory the current attachments and their intended entry point. When the user replaces or withdraws a file, exclude it from staging; never silently reuse it to fill a missing dependency.

## 2. Resolve the dependency tree

Parse HTML `href`, `src`, iframe targets, and fragment references with an HTML parser; inspect CSS `url()`/imports and script-loaded assets. Resolve paths relative to each containing file, including parent-directory references. Distinguish external resources from local dependencies, and verify SVG fragment targets supplied by scripts after rendering.

Request the complete containing folder as a ZIP when dependencies are absent. Do not fabricate replacement styling, behavior, or prior-version comparison pages merely to make a preview appear complete.

## 3. Stage and transfer

Preserve relative directories rather than flattening or renaming files. Stage only approved publication assets; exclude credentials, repository metadata, private exports, and unrelated documents.

For occasional cross-device handoff, prefer an intact archive through an available approved transfer channel. A private network transports files; it does not inherently provide folder sync, validate dependencies, or make public hosting private. Keep received files in staging, never an auto-publishing inbox. Check current provider prerequisites before proposing network setup; do not describe an unexercised transfer method as verified.

## 4. Inspect the existing publisher

Read its documentation, deployment code, registry, and cleanup policy before deciding whether an upgrade is needed. Confirm nested-asset and directory-bundle support rather than inferring a single-file limitation from previous standalone shares.

Determine whether deployment replaces the entire site. Prefer one publishing owner for an existing shared site; a second machine must not deploy an incomplete snapshot that removes unrelated shares. Use a separate project only when independently managed publishing is actually needed and approved.

## 5. Exercise the staged preview

Serve the root containing the entire dependency tree over loopback HTTP, for example:

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory /absolute/path/to/staged-bundle
```

Choose an available port and track the server process. Navigate to the actual nested entry point in a real browser. Check:

- Every comparison iframe and local navigation target.
- Styles, fonts, images, and script-injected icons.
- Implemented theme/state switches, filters, sorting, sidebars, and dialog validation.
- Desktop and narrow layouts.
- Missing requests, uncaught JavaScript errors, and failed asset decoding.

Distinguish deliberately inert mockup controls from broken implemented behavior. A successful top-level HTML response is not proof that child frames and resources work.

## 6. Preserve security and lifecycle semantics

Permit same-origin framing for comparison previews; do not apply `X-Frame-Options: DENY`. Explain that indexing directives and cache headers are not access control.

Check how the existing expiration policy applies to nested bundles before carrying it forward. Do not create new recurring deletion jobs as an incidental part of a transfer or handoff.

## 7. Deploy, verify, and hand off

After publication approval, deploy through the established owner and repeat critical asset, iframe, and interaction checks against the actual hosted URLs. Do not substitute localhost proof or a deploy success message for production verification.

Deliver the comparison landing URL plus useful direct-page links, genuine limitations, and lifecycle information. For another-machine handoff, record the publication source directory, project, deployment command, and verification steps without credentials.
