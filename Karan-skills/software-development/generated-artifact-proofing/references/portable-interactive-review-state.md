# Portable Interactive Review State

Use this recipe for standalone HTML review packets, approval checklists, QA reports, or handoff documents whose controls mutate browser state.

## Contract

A useful interactive review artifact must distinguish three different guarantees:

1. **In-browser persistence:** choices survive refresh/reopen in the same browser origin.
2. **Portable export:** choices are embedded into a new file that can be moved to another browser/device or returned to the agent.
3. **Decision semantics:** the artifact states exactly what checked and unchecked mean. Do not label a checkbox merely “Reviewed” when the owner is using it as approval.

Saving or sharing the original HTML does not serialize `localStorage`, and changing `input.checked` changes a DOM property rather than the HTML `checked` attribute. Therefore local storage alone is not a portable handoff.

## Recommended Design

### 1. Make semantics explicit

Use labels and a visible decision key such as:

- checked = approve this edit;
- unchecked = reject or request a rewrite.

If unchecked can also mean “not reviewed yet,” use a three-state control instead of overloading a checkbox.

### 2. Keep live state locally

Use a stable, artifact-versioned storage key so a corrected/export-enabled replacement can recover choices when opened in the same browser origin. Wrap storage reads/writes in `try/catch`, because file viewers and privacy modes may restrict storage.

### 3. Mirror state into the document

Keep the selected IDs in a deterministic document attribute such as:

```html
<html data-reviewed-ids="[12,27,41]">
```

On load, prefer embedded state when present; otherwise fall back to local storage. Sort IDs numerically before serialization. Update the attribute whenever the user changes a decision.

### 4. Export the live DOM as a self-contained HTML file

On export:

1. persist and sort the current IDs;
2. clone `document.documentElement`;
3. set the embedded state attribute on the clone;
4. set or remove each checkbox’s literal `checked` attribute to match the live property;
5. remove transient search/filter `hidden` classes so the saved artifact contains every review item even if JavaScript is unavailable;
6. serialize with `<!doctype html>` plus `clone.outerHTML`;
7. create a `File`/`Blob` with MIME type `text/html`;
8. prefer `navigator.share({files:[file]})` on mobile when `navigator.canShare` accepts it;
9. fall back to a temporary `<a download>` Blob URL on desktop/unsupported browsers;
10. give the filename a useful count or timestamp, without exposing private content.

Do not send the review state to a server unless the user explicitly approved that external mutation.

### 5. Protect destructive controls

A one-tap “Clear” button can destroy a long review. Require confirmation and keep the original tab/file open until the exported copy has been reopened and verified.

## Migration From a Non-Exportable Version

When replacing an already-used report:

1. retain the same local-storage key in the corrected artifact;
2. instruct the user to open it in the same browser app/origin;
3. compare the recovered approval count with the old tab before continuing;
4. if the count differs, stop—do not tell the user to redo the review or close the old tab;
5. preserve the old tab until the exported HTML has been saved and reopened successfully.

Origin behavior differs among attachment viewers, `file:` URLs, and in-app browsers, so recovery is a verified migration step, not an assumption.

## Deterministic Verification

Exercise the real interaction in a browser:

1. open the source artifact at a mobile viewport;
2. select a nontrivial sample of IDs, including early/middle/late cards;
3. assert progress and decision-summary counts;
4. trigger export and capture the downloaded file;
5. inspect the file for the sorted embedded IDs and literal `checked` attributes;
6. reopen it in a fresh browser context with empty storage;
7. assert the same sample IDs are checked and the same counts appear;
8. assert all cards are present and no current filter left content hidden;
9. assert no page errors and `scrollWidth <= innerWidth` at the target mobile width;
10. separately test the mobile share path where the target browser supports file sharing.

A passing local-storage refresh test is insufficient: the key proof is restoration from the exported file in isolated storage.

## Common Pitfalls

- Claiming choices are “saved” without saying they are browser-local only.
- Assuming Share/Save Original HTML captures live checkbox state.
- Using print/PDF as the sole handoff when print CSS hides checkboxes.
- Serializing `outerHTML` without synchronizing checkbox attributes.
- Exporting a filtered DOM that leaves unreviewed cards hidden.
- Providing only the Web Share path or only `<a download>` rather than both.
- Replacing a report mid-review without a same-key recovery check.
- Using ambiguous “Reviewed” labels for accept/reject decisions.
