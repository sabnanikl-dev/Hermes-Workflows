# Portable interactive HTML review state

Use this for private HTML review packets with checkboxes, approvals, comments, or other browser-local decisions that the user must return from a phone or another device.

## Core rule

`localStorage`, session storage, and in-memory checkbox state belong to one browser origin/profile. Saving or forwarding the original `.html` file does not reliably carry that state.

A returnable review artifact must export the state into the file itself.

## Recommended contract

1. Give every review item a stable ID.
2. Make the action semantically explicit—for example, **Approve edit**, not generic **Reviewed**.
3. Define the polarity in the page and handoff:
   - checked = approve the proposed change;
   - unchecked = reject it as written / requires rewrite.
4. On export, serialize selected IDs into a portable attribute or embedded JSON payload such as `data-reviewed-ids`.
5. On load, restore from the embedded payload first; use the existing `localStorage` key only as a same-browser fallback.
6. Export a newly named reviewed file that includes counts, e.g. `reviewed-89-approved.html`.
7. On mobile, offer native Share when available and a normal Download fallback.
8. Treat the returned exported file—not the original report and not chat recollection—as the authoritative review state.

## End-to-end verification

Static source inspection is insufficient. Exercise the lifecycle in a real browser:

1. open the review report over its intended delivery mode;
2. select a known set of IDs;
3. export/download the reviewed HTML;
4. open the exported file in a fresh page/context with storage unavailable or empty;
5. assert the same IDs and counts restore from the embedded payload;
6. assert all review cards still exist and mobile layout has no horizontal overflow;
7. parse the returned file independently and verify approved/rejected totals before acting.

## Pitfalls

- Do not claim “checkboxes are saved” when only `localStorage` is used.
- Do not infer that unchecked means “not reviewed”; define whether it means rejected or pending.
- Do not overwrite the original report while adding export capability.
- Do not ask the user to redo a large review if the enhanced report can reuse the original storage key as a one-time migration fallback.
- Do not apply unchecked proposed wording unchanged; route it through a bounded rewrite ledger while freezing checked items.
